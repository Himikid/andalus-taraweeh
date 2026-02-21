#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
from rapidfuzz import fuzz
import soundfile as sf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate day marker quality and chronology.")
    parser.add_argument("--day-json", type=Path, required=True, help="Path to generated day JSON")
    parser.add_argument(
        "--quran-corpus",
        type=Path,
        default=Path("data/quran/quran_arabic.json"),
        help="Quran corpus JSON path",
    )
    parser.add_argument(
        "--transcript-cache",
        type=Path,
        help="Transcript cache path (defaults to data/ai/cache/day-{day}-transcript-full.json)",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        help="Optional output report path (defaults to data/ai/reports/day-{day}-validation.json)",
    )
    parser.add_argument("--pass-score", type=float, default=80.0, help="Score threshold to mark a marker as pass")
    parser.add_argument("--audio-file", type=Path, help="Optional audio WAV file for strict clip re-checks")
    parser.add_argument(
        "--audio-check-samples",
        type=int,
        default=0,
        help="Number of markers to re-check by re-transcribing local audio clips.",
    )
    parser.add_argument(
        "--audio-check-model",
        type=str,
        default="tiny",
        help="Whisper model size for strict clip re-checks.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _token_overlap(a: str, b: str) -> float:
    a_tokens = set(a.split())
    b_tokens = set(b.split())
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / max(1, len(b_tokens))


def _nearest_segment_text(segments: list[dict], second: int) -> str:
    nearest: dict | None = None
    best_distance = float("inf")

    for segment in segments:
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))
        center = (start + end) / 2
        distance = abs(center - second)
        if distance < best_distance:
            best_distance = distance
            nearest = segment

    return str((nearest or {}).get("text", "")).strip()


def _corpus_map(corpus: dict) -> tuple[dict[tuple[str, int], str], dict[tuple[str, int], int], list[tuple[str, int]]]:
    text_map: dict[tuple[str, int], str] = {}
    order_map: dict[tuple[str, int], int] = {}
    ordered_keys: list[tuple[str, int]] = []
    index = 0

    for surah in corpus.get("surahs", []):
        surah_name = str(surah.get("name", ""))
        for ayah in surah.get("ayahs", []):
            ayah_num = int(ayah.get("number", 0))
            text = str(ayah.get("text", "")).strip()
            key = (surah_name, ayah_num)
            text_map[key] = text
            order_map[key] = index
            ordered_keys.append(key)
            index += 1

    return text_map, order_map, ordered_keys


def _load_transcript_segments_for_validation(transcript_path: Path) -> list[dict]:
    if not transcript_path.exists():
        return []

    payload = _load_json(transcript_path)
    offset = float(payload.get("time_offset_seconds", 0.0) or 0.0)
    rows: list[dict] = []

    for segment in payload.get("segments", []):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        start = float(segment.get("start", 0.0)) + offset
        end = float(segment.get("end", start)) + offset
        if end < start:
            end = start
        rows.append({"start": start, "end": end, "text": text})

    return rows


def _best_neighborhood_match(
    marker_key: tuple[str, int],
    normalized_text: str,
    text_map: dict[tuple[str, int], str],
    order_map: dict[tuple[str, int], int],
    ordered_keys: list[tuple[str, int]],
    neighbor_window: int = 2,
) -> tuple[float, float, tuple[str, int], int]:
    try:
        from ai_pipeline.quran import normalize_arabic
    except ImportError:
        return 0.0, 0.0, marker_key, 0

    candidate_keys: list[tuple[str, int]] = [marker_key]
    marker_surah = marker_key[0]
    order_index = order_map.get(marker_key, -1)
    if order_index >= 0:
        for offset in range(-neighbor_window, neighbor_window + 1):
            idx = order_index + offset
            if 0 <= idx < len(ordered_keys):
                candidate = ordered_keys[idx]
                if candidate[0] == marker_surah:
                    candidate_keys.append(candidate)

    best_score = 0.0
    best_overlap = 0.0
    best_key = marker_key
    best_delta = 0

    for key in dict.fromkeys(candidate_keys):
        ref_text = normalize_arabic(text_map.get(key, ""))
        if not ref_text:
            continue
        score = float(fuzz.WRatio(normalized_text, ref_text))
        overlap = _token_overlap(normalized_text, ref_text)
        if score > best_score:
            best_score = score
            best_overlap = overlap
            best_key = key
            if order_index >= 0 and key in order_map:
                best_delta = order_map[key] - order_index

    return best_score, best_overlap, best_key, best_delta


def evaluate_day_payload(
    day_payload: dict,
    quran_corpus_path: Path,
    transcript_path: Path,
    source_json_path: Path | None = None,
    pass_score: float = 80.0,
) -> dict:
    from ai_pipeline.quran import normalize_arabic

    day = int(day_payload.get("day", 0))
    markers = day_payload.get("markers", [])

    transcript_segments = _load_transcript_segments_for_validation(transcript_path)

    corpus = _load_json(quran_corpus_path)
    text_map, order_map, ordered_keys = _corpus_map(corpus)

    results: list[dict] = []
    passed = 0
    backtracks = 0
    duplicates = 0
    seen: set[tuple[str, int]] = set()
    previous_order = -1
    scores: list[float] = []

    for marker in markers:
        surah = str(marker.get("surah", ""))
        ayah = int(marker.get("ayah", 0))
        time = int(marker.get("time", 0))

        key = (surah, ayah)
        marker_text = normalize_arabic(_nearest_segment_text(transcript_segments, time))
        score = 0.0
        overlap = 0.0
        matched_key = key
        matched_delta = 0
        if marker_text:
            score, overlap, matched_key, matched_delta = _best_neighborhood_match(
                marker_key=key,
                normalized_text=marker_text,
                text_map=text_map,
                order_map=order_map,
                ordered_keys=ordered_keys,
            )
        is_pass = score >= pass_score and overlap >= 0.1

        if is_pass:
            passed += 1
        scores.append(score)

        order_index = order_map.get(key, -1)
        if order_index >= 0 and previous_order >= 0 and order_index < previous_order:
            backtracks += 1
        if order_index >= 0:
            previous_order = max(previous_order, order_index)

        if key in seen:
            duplicates += 1
        seen.add(key)

        results.append(
            {
                "time": time,
                "surah": surah,
                "ayah": ayah,
                "score": round(score, 2),
                "overlap": round(overlap, 3),
                "pass": is_pass,
                "confidence": marker.get("confidence"),
                "matched_surah": matched_key[0],
                "matched_ayah": matched_key[1],
                "matched_delta": matched_delta,
            }
        )

    marker_count = len(markers)
    mean_score = (sum(scores) / marker_count) if marker_count else 0.0
    pass_rate = (passed / marker_count) if marker_count else 0.0
    confidence_values = [float(item.get("confidence")) for item in markers if item.get("confidence") is not None]
    confidence_spread = (max(confidence_values) - min(confidence_values)) if confidence_values else 0.0

    report = {
        "day": day,
        "source_json": str(source_json_path) if source_json_path else None,
        "transcript_cache": str(transcript_path) if transcript_path.exists() else None,
        "summary": {
            "markers": marker_count,
            "pass_rate": round(pass_rate, 3),
            "mean_score": round(mean_score, 2),
            "chronology_backtracks": backtracks,
            "duplicates": duplicates,
            "confidence_spread": round(confidence_spread, 3),
        },
        "markers": results,
    }
    return report


def _strict_audio_recheck(
    report: dict,
    audio_file: Path,
    corpus_text_map: dict[tuple[str, int], str],
    order_map: dict[tuple[str, int], int],
    ordered_keys: list[tuple[str, int]],
    model_size: str,
    sample_count: int,
) -> dict | None:
    if sample_count <= 0:
        return None
    if not audio_file.exists():
        return None

    try:
        from faster_whisper import WhisperModel
        from ai_pipeline.quran import normalize_arabic
    except ImportError:
        return None

    audio, sample_rate = sf.read(audio_file)
    if isinstance(audio, np.ndarray) and audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    audio = np.asarray(audio, dtype=np.float32)

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    rows = []
    scores: list[float] = []
    passes = 0

    for marker in report.get("markers", [])[:sample_count]:
        time = int(marker.get("time", 0))
        surah = str(marker.get("surah", ""))
        ayah = int(marker.get("ayah", 0))
        ref_text = normalize_arabic(corpus_text_map.get((surah, ayah), ""))
        if not ref_text:
            continue

        clip_start = max(0, time - 2)
        clip_end = min(len(audio), (time + 10) * sample_rate)
        clip = audio[clip_start * sample_rate : clip_end]
        if len(clip) < sample_rate:
            continue

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            sf.write(tmp.name, clip, sample_rate)
            segments, _ = model.transcribe(tmp.name, language="ar", vad_filter=True)
            clip_text = " ".join((segment.text or "").strip() for segment in segments).strip()

        normalized_clip = normalize_arabic(clip_text)
        score = 0.0
        overlap = 0.0
        matched_key = (surah, ayah)
        matched_delta = 0
        if normalized_clip:
            score, overlap, matched_key, matched_delta = _best_neighborhood_match(
                marker_key=(surah, ayah),
                normalized_text=normalized_clip,
                text_map=corpus_text_map,
                order_map=order_map,
                ordered_keys=ordered_keys,
            )
        ok = score >= 78 and overlap >= 0.1
        if ok:
            passes += 1
        scores.append(score)

        rows.append(
            {
                "time": time,
                "surah": surah,
                "ayah": ayah,
                "score": round(score, 2),
                "overlap": round(overlap, 3),
                "pass": ok,
                "matched_surah": matched_key[0],
                "matched_ayah": matched_key[1],
                "matched_delta": matched_delta,
            }
        )

    if not rows:
        return None

    return {
        "checked": len(rows),
        "pass_rate": round(passes / len(rows), 3),
        "mean_score": round(sum(scores) / len(scores), 2),
        "markers": rows,
    }


def main() -> None:
    args = parse_args()

    try:
        from ai_pipeline.quran import normalize_arabic  # noqa: F401
    except ImportError as exc:
        raise SystemExit("Run from repo root and install dependencies first.") from exc

    day_payload = _load_json(args.day_json)
    day = int(day_payload.get("day", 0))
    transcript_path = args.transcript_cache or Path(f"data/ai/cache/day-{day}-transcript-full.json")
    if not transcript_path.exists():
        legacy_path = Path(f"data/ai/cache/day-{day}-transcript.json")
        if legacy_path.exists():
            transcript_path = legacy_path

    report = evaluate_day_payload(
        day_payload=day_payload,
        quran_corpus_path=args.quran_corpus,
        transcript_path=transcript_path,
        source_json_path=args.day_json,
        pass_score=args.pass_score,
    )

    corpus = _load_json(args.quran_corpus)
    text_map, order_map, ordered_keys = _corpus_map(corpus)
    strict = _strict_audio_recheck(
        report=report,
        audio_file=args.audio_file if args.audio_file else Path(""),
        corpus_text_map=text_map,
        order_map=order_map,
        ordered_keys=ordered_keys,
        model_size=args.audio_check_model,
        sample_count=args.audio_check_samples,
    )
    if strict is not None:
        report["strict_audio_check"] = strict

    out_path = args.report_out or Path(f"data/ai/reports/day-{day}-validation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)

    print(f"Saved report: {out_path}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
