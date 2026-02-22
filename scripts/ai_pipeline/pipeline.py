from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import soundfile as sf

from .audio import prepare_audio_source
from .io import write_json
from .prayers import (
    build_prayer_segments,
    detect_fatiha_starts,
    detect_prayer_starts,
    merge_rakah_starts,
    read_mono_audio,
)
from .quran import (
    STRICT_NORMALIZATION,
    clean_transcript_for_matching,
    enrich_marker_texts,
    get_juz_for_ayah,
    load_asad_translation,
    load_corpus,
    match_quran_markers,
)
from .reciters import assign_reciters
from .transcribe import transcribe_audio
from .types import Marker, PrayerSegment, TranscriptSegment, TranscriptWord


def _map_reciter_to_markers(markers: list[Marker], prayers: list[PrayerSegment]) -> list[Marker]:
    if not markers or not prayers:
        return markers

    for marker in markers:
        assigned = "Unknown"
        for prayer in prayers:
            if prayer.start <= marker.time < prayer.end:
                assigned = prayer.reciter or "Unknown"
                break
        marker.reciter = assigned

    return markers


def _is_known_reciter(label: str | None) -> bool:
    normalized = (label or "").strip().lower()
    if not normalized:
        return False
    if normalized in {"unknown", "talk"}:
        return False
    return "hasan" in normalized or "samir" in normalized


def _filter_transcript_by_known_reciter(
    transcript_segments: list[TranscriptSegment],
    prayers: list[PrayerSegment],
    edge_padding_seconds: float = 1.5,
    min_keep_ratio: float = 0.2,
    min_keep_segments: int = 80,
) -> tuple[list[TranscriptSegment], dict]:
    if not transcript_segments or not prayers:
        return transcript_segments, {
            "enabled": False,
            "reason": "no_transcript_or_prayers",
            "kept_segments": len(transcript_segments),
            "total_segments": len(transcript_segments),
        }

    windows: list[tuple[float, float]] = []
    for prayer in prayers:
        if not _is_known_reciter(prayer.reciter):
            continue
        start = max(0.0, float(prayer.start) - edge_padding_seconds)
        end = float(prayer.end) + edge_padding_seconds
        if end <= start:
            continue
        windows.append((start, end))

    if not windows:
        return transcript_segments, {
            "enabled": False,
            "reason": "no_known_reciter_windows",
            "kept_segments": len(transcript_segments),
            "total_segments": len(transcript_segments),
        }

    windows.sort(key=lambda item: item[0])
    merged: list[tuple[float, float]] = []
    for start, end in windows:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    kept: list[TranscriptSegment] = []
    window_index = 0
    for segment in transcript_segments:
        midpoint = (float(segment.start) + float(segment.end)) / 2.0
        while window_index < len(merged) and merged[window_index][1] < midpoint:
            window_index += 1
        if window_index >= len(merged):
            break
        start, end = merged[window_index]
        if start <= midpoint <= end:
            kept.append(segment)

    keep_ratio = (len(kept) / len(transcript_segments)) if transcript_segments else 0.0
    if len(kept) < min_keep_segments or keep_ratio < min_keep_ratio:
        return transcript_segments, {
            "enabled": False,
            "reason": "insufficient_kept_coverage",
            "kept_segments": len(kept),
            "total_segments": len(transcript_segments),
            "keep_ratio": round(keep_ratio, 3),
            "windows": len(merged),
        }

    return kept, {
        "enabled": True,
        "reason": "known_reciter_windows",
        "kept_segments": len(kept),
        "total_segments": len(transcript_segments),
        "keep_ratio": round(keep_ratio, 3),
        "windows": len(merged),
    }


def _quality_rank(value: str | None) -> int:
    quality = (value or "").strip().lower()
    if quality == "manual":
        return 4
    if quality == "high":
        return 3
    if quality == "ambiguous":
        return 2
    if quality == "inferred":
        return 1
    return 0


def _apply_day_final_ayah_override(
    day: int,
    markers: list[Marker],
    overrides_path: Path | None,
    corpus_entries: list,
) -> tuple[list[Marker], dict | None]:
    if not markers or overrides_path is None or not overrides_path.exists():
        return markers, None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return markers, None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return markers, None

    final_surah = str(day_config.get("final_surah", "")).strip()
    final_ayah_raw = day_config.get("final_ayah")
    start_time_raw = day_config.get("start_time")
    final_time_raw = day_config.get("final_time")

    try:
        final_ayah = int(final_ayah_raw) if final_ayah_raw is not None else None
    except (TypeError, ValueError):
        final_ayah = None
    try:
        start_time = int(start_time_raw) if start_time_raw is not None else None
    except (TypeError, ValueError):
        start_time = None
    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None

    if final_ayah is None and final_time is None and start_time is None:
        return markers, None

    final_surah_number: int | None = None
    if final_surah:
        for marker in markers:
            if marker.surah == final_surah and marker.surah_number is not None:
                final_surah_number = int(marker.surah_number)
                break

    def keep(marker: Marker) -> bool:
        if start_time is not None and marker.time < start_time:
            return False
        if final_time is not None and marker.time > final_time:
            return False
        if final_ayah is None:
            return True
        if final_surah:
            if marker.surah_number is not None and final_surah_number is not None:
                if marker.surah_number > final_surah_number:
                    return False
                if marker.surah_number < final_surah_number:
                    return True
            elif marker.surah != final_surah:
                return True
        if final_surah and marker.surah != final_surah:
            return True
        return marker.ayah <= final_ayah

    filtered = [marker for marker in markers if keep(marker)]
    if not filtered:
        return markers, None

    inserted_terminal = False
    inserted_time: int | None = None

    if final_ayah is not None and final_surah:
        has_terminal = any(marker.surah == final_surah and marker.ayah == final_ayah for marker in filtered)
        if not has_terminal:
            same_surah = sorted(
                [marker for marker in filtered if marker.surah == final_surah],
                key=lambda marker: (marker.ayah, marker.time),
            )
            anchor = None
            for marker in same_surah:
                if marker.ayah <= final_ayah:
                    anchor = marker
                else:
                    break

            step_candidates: list[float] = []
            for left, right in zip(same_surah, same_surah[1:]):
                ayah_gap = right.ayah - left.ayah
                time_gap = right.time - left.time
                if ayah_gap <= 0 or time_gap <= 0:
                    continue
                step_candidates.append(time_gap / ayah_gap)

            if step_candidates:
                sorted_steps = sorted(step_candidates)
                step_seconds = sorted_steps[len(sorted_steps) // 2]
            else:
                step_seconds = 18.0

            if final_time is not None:
                terminal_time = final_time
            elif anchor is not None:
                terminal_time = int(round(anchor.time + (max(0, final_ayah - anchor.ayah) * step_seconds)))
            else:
                terminal_time = filtered[-1].time

            if filtered:
                terminal_time = max(terminal_time, filtered[-1].time)

            entry_lookup = {
                (str(entry.surah), int(entry.ayah)): entry
                for entry in corpus_entries
            }
            entry = entry_lookup.get((final_surah, final_ayah))
            surah_number = entry.surah_number if entry is not None else final_surah_number
            if surah_number is None:
                for marker in reversed(filtered):
                    if marker.surah == final_surah and marker.surah_number is not None:
                        surah_number = int(marker.surah_number)
                        break

            filtered.append(
                Marker(
                    time=terminal_time,
                    start_time=terminal_time,
                    end_time=terminal_time,
                    surah=final_surah,
                    surah_number=surah_number,
                    ayah=final_ayah,
                    juz=get_juz_for_ayah(surah_number or 1, final_ayah),
                    quality="manual",
                    confidence=1.0,
                )
            )
            filtered.sort(key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))
            inserted_terminal = True
            inserted_time = terminal_time

    info = {
        "path": str(overrides_path),
        "final_surah": final_surah or None,
        "final_ayah": final_ayah,
        "start_time": start_time,
        "final_time": final_time,
        "markers_before": len(markers),
        "markers_after": len(filtered),
        "inserted_terminal": inserted_terminal,
        "inserted_terminal_time": inserted_time,
    }
    return filtered, info


def _fill_override_surah_range(
    day: int,
    markers: list[Marker],
    overrides_path: Path | None,
    corpus_entries: list,
) -> tuple[list[Marker], dict | None]:
    if not markers or overrides_path is None or not overrides_path.exists():
        return markers, None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return markers, None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return markers, None

    final_surah = str(day_config.get("final_surah", "")).strip()
    final_ayah_raw = day_config.get("final_ayah")
    final_time_raw = day_config.get("final_time")

    if not final_surah:
        return markers, None
    try:
        final_ayah = int(final_ayah_raw)
    except (TypeError, ValueError):
        return markers, None
    if final_ayah <= 0:
        return markers, None
    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None

    target_surah_number: int | None = None
    for entry in corpus_entries:
        if str(entry.surah) == final_surah:
            target_surah_number = int(entry.surah_number)
            break
    if target_surah_number is None:
        return markers, None

    relevant = [marker for marker in markers if marker.surah_number == target_surah_number and marker.ayah <= final_ayah]
    if not relevant:
        return markers, None

    best_by_ayah: dict[int, Marker] = {}
    for marker in relevant:
        existing = best_by_ayah.get(marker.ayah)
        if existing is None:
            best_by_ayah[marker.ayah] = marker
            continue
        marker_rank = _quality_rank(marker.quality)
        existing_rank = _quality_rank(existing.quality)
        marker_conf = float(marker.confidence or 0.0)
        existing_conf = float(existing.confidence or 0.0)
        if marker_rank > existing_rank:
            best_by_ayah[marker.ayah] = marker
        elif marker_rank == existing_rank and marker_conf > existing_conf:
            best_by_ayah[marker.ayah] = marker
        elif marker_rank == existing_rank and marker_conf == existing_conf and marker.time < existing.time:
            best_by_ayah[marker.ayah] = marker

    existing_ayahs = sorted(best_by_ayah.keys())
    if not existing_ayahs:
        return markers, None

    adjacent_steps: list[int] = []
    for left_ayah, right_ayah in zip(existing_ayahs, existing_ayahs[1:]):
        if right_ayah != left_ayah + 1:
            continue
        left = best_by_ayah[left_ayah]
        right = best_by_ayah[right_ayah]
        gap = int(right.time) - int(left.time)
        if 0 < gap < 240:
            adjacent_steps.append(gap)
    if adjacent_steps:
        adjacent_steps.sort()
        fallback_step = max(6, adjacent_steps[len(adjacent_steps) // 2])
    else:
        fallback_step = 20

    full_timeline = sorted(markers, key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))

    def reciter_for_time(target_time: int) -> str | None:
        chosen: str | None = None
        for item in full_timeline:
            item_time = int(item.start_time or item.time)
            if item_time <= target_time:
                chosen = item.reciter
            else:
                break
        return chosen

    additions: list[Marker] = []
    for ayah in range(1, final_ayah + 1):
        if ayah in best_by_ayah:
            continue

        prev_ayah = ayah - 1
        next_ayah = ayah + 1
        prev_marker: Marker | None = None
        next_marker: Marker | None = None
        while prev_ayah >= 1:
            if prev_ayah in best_by_ayah:
                prev_marker = best_by_ayah[prev_ayah]
                break
            prev_ayah -= 1
        while next_ayah <= final_ayah:
            if next_ayah in best_by_ayah:
                next_marker = best_by_ayah[next_ayah]
                break
            next_ayah += 1

        if prev_marker is not None and next_marker is not None and next_marker.ayah > prev_marker.ayah and next_marker.time > prev_marker.time:
            ratio = (ayah - prev_marker.ayah) / max(1, next_marker.ayah - prev_marker.ayah)
            inferred_time = int(round(prev_marker.time + ((next_marker.time - prev_marker.time) * ratio)))
            inferred_time = max(inferred_time, prev_marker.time + 1)
            inferred_time = min(inferred_time, next_marker.time - 1)
        elif prev_marker is not None:
            inferred_time = int(prev_marker.time + ((ayah - prev_marker.ayah) * fallback_step))
        elif next_marker is not None:
            inferred_time = int(max(0, next_marker.time - ((next_marker.ayah - ayah) * fallback_step)))
        else:
            continue

        if final_time is not None:
            inferred_time = min(inferred_time, final_time)

        marker = Marker(
            time=inferred_time,
            start_time=inferred_time,
            end_time=inferred_time,
            surah=final_surah,
            surah_number=target_surah_number,
            ayah=ayah,
            juz=get_juz_for_ayah(target_surah_number, ayah),
            quality="inferred",
            confidence=0.56,
            reciter=reciter_for_time(inferred_time),
        )
        additions.append(marker)
        best_by_ayah[ayah] = marker
        full_timeline.append(marker)
        full_timeline.sort(key=lambda item: (item.time, item.surah_number or 0, item.ayah))

    if not additions:
        return markers, {
            "surah": final_surah,
            "surah_number": target_surah_number,
            "target_final_ayah": final_ayah,
            "added_markers": 0,
            "fallback_step_seconds": fallback_step,
        }

    merged = markers + additions
    merged.sort(key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))
    info = {
        "surah": final_surah,
        "surah_number": target_surah_number,
        "target_final_ayah": final_ayah,
        "added_markers": len(additions),
        "fallback_step_seconds": fallback_step,
    }
    return merged, info


def _apply_marker_time_overrides(
    day: int,
    part: int | None,
    markers: list[Marker],
    overrides_path: Path | None,
    corpus_entries: list | None = None,
) -> tuple[list[Marker], list[dict]]:
    if not markers or overrides_path is None or not overrides_path.exists():
        return markers, []

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return markers, []

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return markers, []

    marker_overrides = day_config.get("marker_overrides", [])
    if not isinstance(marker_overrides, list) or not marker_overrides:
        return markers, []

    applied: list[dict] = []
    entry_lookup: dict[tuple[int, int], object] = {}
    for entry in corpus_entries or []:
        surah_number = getattr(entry, "surah_number", None)
        ayah = getattr(entry, "ayah", None)
        if surah_number is None or ayah is None:
            continue
        entry_lookup[(int(surah_number), int(ayah))] = entry

    for item in marker_overrides:
        if not isinstance(item, dict):
            continue

        item_part = item.get("part")
        if item_part is not None:
            try:
                if int(item_part) != int(part or 0):
                    continue
            except (TypeError, ValueError):
                continue

        surah_number = item.get("surah_number")
        ayah = item.get("ayah")
        start_time = item.get("start_time")
        end_time = item.get("end_time")
        if surah_number is None or ayah is None or start_time is None:
            continue

        try:
            target_surah_number = int(surah_number)
            target_ayah = int(ayah)
            target_start_time = int(start_time)
            target_end_time = int(end_time) if end_time is not None else int(start_time)
        except (TypeError, ValueError):
            continue

        found = False
        for marker in markers:
            if marker.surah_number == target_surah_number and marker.ayah == target_ayah:
                marker.start_time = target_start_time
                marker.time = target_start_time
                marker.end_time = max(target_start_time, target_end_time)
                marker.quality = "manual"
                marker.confidence = 1.0
                found = True
                applied.append(
                    {
                        "surah_number": target_surah_number,
                        "ayah": target_ayah,
                        "part": part,
                        "start_time": target_start_time,
                        "end_time": max(target_start_time, target_end_time),
                    }
                )
                break

        if found:
            continue

        entry = entry_lookup.get((target_surah_number, target_ayah))
        surah_name = str(getattr(entry, "surah", "")) if entry is not None else ""
        markers.append(
            Marker(
                time=target_start_time,
                start_time=target_start_time,
                end_time=max(target_start_time, target_end_time),
                surah=surah_name,
                surah_number=target_surah_number,
                ayah=target_ayah,
                juz=get_juz_for_ayah(target_surah_number, target_ayah),
                quality="manual",
                confidence=1.0,
            )
        )
        applied.append(
            {
                "surah_number": target_surah_number,
                "ayah": target_ayah,
                "part": part,
                "start_time": target_start_time,
                "end_time": max(target_start_time, target_end_time),
                "inserted": True,
            }
        )

    if applied:
        markers.sort(key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))
    return markers, applied


def _resolve_day_start_override(
    day: int,
    overrides_path: Path | None,
) -> tuple[int, int] | None:
    if overrides_path is None or not overrides_path.exists():
        return None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return None

    surah_raw = day_config.get("start_surah_number")
    ayah_raw = day_config.get("start_ayah")
    if surah_raw is None or ayah_raw is None:
        return None

    try:
        surah_number = int(surah_raw)
        ayah = int(ayah_raw)
    except (TypeError, ValueError):
        return None
    if surah_number <= 0 or ayah <= 0:
        return None
    return surah_number, ayah


def _resolve_day_reanchor_points(
    day: int,
    part: int | None,
    overrides_path: Path | None,
) -> list[tuple[int, int, int]]:
    if overrides_path is None or not overrides_path.exists():
        return []

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return []

    raw_points = day_config.get("reanchor_points", [])
    if not isinstance(raw_points, list):
        return []

    points: list[tuple[int, int, int]] = []
    for item in raw_points:
        if not isinstance(item, dict):
            continue
        item_part = item.get("part")
        if item_part is not None:
            try:
                if int(item_part) != int(part or 0):
                    continue
            except (TypeError, ValueError):
                continue

        try:
            at_time = int(item.get("time"))
            surah_number = int(item.get("surah_number"))
            ayah = int(item.get("ayah"))
        except (TypeError, ValueError):
            continue
        if at_time < 0 or surah_number <= 0 or ayah <= 0:
            continue
        points.append((at_time, surah_number, ayah))

    points.sort(key=lambda item: item[0])
    return points


def process_day(
    day: int,
    output_path: Path,
    cache_dir: Path,
    corpus_path: Path,
    profiles_path: Path,
    youtube_url: str | None,
    audio_file: Path | None,
    whisper_model: str,
    bootstrap_reciters: bool,
    match_min_score: int = 78,
    match_min_overlap: float = 0.18,
    match_min_confidence: float = 0.62,
    match_min_gap_seconds: int = 8,
    match_require_weak_support_for_inferred: bool = True,
    match_start_surah_number: int | None = None,
    match_start_ayah: int | None = None,
    reuse_transcript_cache: bool = True,
    max_audio_seconds: int | None = None,
    asad_path: Path | None = None,
    day_overrides_path: Path | None = None,
    part: int | None = None,
) -> dict:
    total_stages = 12
    stage_index = 0
    stage_timings: dict[str, float] = {}
    pipeline_start = perf_counter()

    def stage_begin(label: str) -> float:
        nonlocal stage_index
        stage_index += 1
        percent = int((stage_index / total_stages) * 100)
        print(f"[pipeline {stage_index}/{total_stages} {percent:>3}%] {label}...", flush=True)
        return perf_counter()

    def stage_end(label: str, started_at: float) -> None:
        elapsed = perf_counter() - started_at
        stage_timings[label] = round(elapsed, 2)
        print(f"[pipeline] {label} done in {elapsed:.1f}s", flush=True)

    t = stage_begin("prepare audio source")
    normalized_audio_path, source = prepare_audio_source(
        day=day,
        youtube_url=youtube_url,
        audio_file=audio_file,
        cache_dir=cache_dir,
    )
    stage_end("prepare audio source", t)

    t = stage_begin("load normalized audio")
    audio, sample_rate = read_mono_audio(normalized_audio_path)
    transcription_audio_path = normalized_audio_path
    cache_suffix = "full"
    stage_end("load normalized audio", t)

    if max_audio_seconds is not None and max_audio_seconds > 0:
        t = stage_begin(f"trim audio to first {max_audio_seconds}s")
        max_samples = min(len(audio), max_audio_seconds * sample_rate)
        audio = audio[:max_samples]
        cache_suffix = f"{max_audio_seconds}s"
        trimmed_audio_path = normalized_audio_path.parent / f"trimmed-{cache_suffix}.wav"
        sf.write(trimmed_audio_path, audio, sample_rate)
        transcription_audio_path = trimmed_audio_path
        stage_end(f"trim audio to first {max_audio_seconds}s", t)
    else:
        # Keep the progress count stable even when no trim is requested.
        t = stage_begin("trim audio (skipped)")
        stage_end("trim audio (skipped)", t)

    total_seconds = int(len(audio) / sample_rate)

    part_suffix = f"-part-{part}" if part is not None and part > 0 else ""
    transcript_cache_path = Path("data/ai/cache") / f"day-{day}{part_suffix}-transcript-{cache_suffix}.json"
    transcript_segments: list[TranscriptSegment]
    if reuse_transcript_cache and transcript_cache_path.exists():
        t = stage_begin("load transcript cache")
        import json

        with transcript_cache_path.open("r", encoding="utf-8") as handle:
            cached_payload = json.load(handle)
        transcript_segments = [
            TranscriptSegment(
                start=float(segment.get("start", 0.0)),
                end=float(segment.get("end", 0.0)),
                text=str(segment.get("text", "")).strip(),
                words=[
                    TranscriptWord(
                        start=float(word.get("start", 0.0)),
                        end=float(word.get("end", 0.0)),
                        text=str(word.get("text", "")).strip(),
                    )
                    for word in segment.get("words", [])
                    if str(word.get("text", "")).strip()
                ],
            )
            for segment in cached_payload.get("segments", [])
            if str(segment.get("text", "")).strip()
        ]
        stage_end("load transcript cache", t)
        # Keep stage count stable.
        t = stage_begin("transcribe audio (cache hit, skipped)")
        stage_end("transcribe audio (cache hit, skipped)", t)
    else:
        # Keep stage count stable.
        t = stage_begin("load transcript cache (miss)")
        stage_end("load transcript cache (miss)", t)

        t = stage_begin(f"transcribe audio (model={whisper_model})")
        transcript_segments = transcribe_audio(transcription_audio_path, model_size=whisper_model)
        write_json(
            transcript_cache_path,
            {
                "day": day,
                "source": source,
                "segments": [asdict(segment) for segment in transcript_segments],
            },
        )
        stage_end(f"transcribe audio (model={whisper_model})", t)

    t = stage_begin("detect reciter/prayer segment starts")
    audio_segment_starts = detect_prayer_starts(audio, sample_rate, collapse_rakah_pairs=True)
    fatiha_segment_starts = detect_fatiha_starts(transcript_segments)
    reciter_segment_starts = merge_rakah_starts(audio_segment_starts, fatiha_segment_starts, min_gap_seconds=180)
    stage_end("detect reciter/prayer segment starts", t)

    t = stage_begin("assign reciters to segments")
    reciter_segments = build_prayer_segments(reciter_segment_starts, total_seconds)
    reciter_segments = assign_reciters(
        day=day,
        audio=audio,
        sample_rate=sample_rate,
        prayers=reciter_segments,
        profiles_path=profiles_path,
        bootstrap_reciters=bootstrap_reciters,
    )
    stage_end("assign reciters to segments", t)

    t = stage_begin("load Quran corpus and prepare transcript")
    corpus_entries = load_corpus(corpus_path)
    transcript_for_matching = clean_transcript_for_matching(transcript_segments)
    transcript_for_matching, reciter_filter_info = _filter_transcript_by_known_reciter(
        transcript_segments=transcript_for_matching,
        prayers=reciter_segments,
    )
    reset_markers = [float(item) for item in fatiha_segment_starts]
    effective_start_surah_number = match_start_surah_number
    effective_start_ayah = match_start_ayah
    if effective_start_surah_number is None or effective_start_ayah is None:
        day_start_override = _resolve_day_start_override(day=day, overrides_path=day_overrides_path)
        if day_start_override is not None:
            effective_start_surah_number, effective_start_ayah = day_start_override
    reanchor_points = _resolve_day_reanchor_points(day=day, part=part, overrides_path=day_overrides_path)

    forced_start_index: int | None = None
    if effective_start_surah_number is not None and effective_start_ayah is not None:
        for index, entry in enumerate(corpus_entries):
            if entry.surah_number == effective_start_surah_number and entry.ayah == effective_start_ayah:
                forced_start_index = index
                break
    stage_end("load Quran corpus and prepare transcript", t)

    t = stage_begin("match ayah markers")
    markers = match_quran_markers(
        transcript_for_matching,
        corpus_entries,
        min_score=match_min_score,
        min_gap_seconds=match_min_gap_seconds,
        min_overlap=match_min_overlap,
        min_confidence=match_min_confidence,
        require_weak_support_for_inferred=match_require_weak_support_for_inferred,
        forced_start_index=forced_start_index,
        precomputed_reset_times=reset_markers,
        reanchor_points=reanchor_points,
    )
    stage_end("match ayah markers", t)

    t = stage_begin("apply day overrides")
    markers, override_info = _apply_day_final_ayah_override(
        day=day,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    markers, marker_time_overrides = _apply_marker_time_overrides(
        day=day,
        part=part,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    markers, range_fill_info = _fill_override_surah_range(
        day=day,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    stage_end("apply day overrides", t)

    t = stage_begin("enrich marker text + reciter mapping")
    asad_lookup = load_asad_translation(asad_path) if asad_path else {}
    markers = enrich_marker_texts(markers, corpus_entries, asad_lookup)
    markers = _map_reciter_to_markers(markers, reciter_segments)
    stage_end("enrich marker text + reciter mapping", t)

    t = stage_begin("write output JSON")
    payload = {
        "day": day,
        "source": source,
        "markers": [asdict(marker) for marker in markers],
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audio_path": str(normalized_audio_path),
            "part": part,
            "whisper_model": whisper_model,
            "markers_detected": len(markers),
            "transcript_segments_raw": len(transcript_segments),
            "transcript_segments_for_matching": len(transcript_for_matching),
            "transcript_reset_markers": len(reset_markers),
            "reciter_segments_detected": len(reciter_segments),
            "corpus_loaded": bool(corpus_entries),
            "asad_loaded": bool(asad_lookup),
            "transcript_path": str(transcript_cache_path),
            "segment_detection": {
                "audio_starts": len(audio_segment_starts),
                "fatiha_starts": len(fatiha_segment_starts),
                "merged_starts": len(reciter_segment_starts),
            },
            "reciter_filter": reciter_filter_info,
            "match_config": {
                "min_score": match_min_score,
                "min_overlap": match_min_overlap,
                "min_confidence": match_min_confidence,
                "min_gap_seconds": match_min_gap_seconds,
                "strict_normalization": STRICT_NORMALIZATION,
                "require_weak_support_for_inferred": match_require_weak_support_for_inferred,
                "start_surah_number": effective_start_surah_number,
                "start_ayah": effective_start_ayah,
            },
            "manual_override": override_info,
            "marker_time_overrides": marker_time_overrides,
            "override_surah_fill": range_fill_info,
            "pipeline_timings_seconds": stage_timings,
        },
    }

    write_json(output_path, payload)
    stage_end("write output JSON", t)
    total_elapsed = perf_counter() - pipeline_start
    print(f"[pipeline] complete in {total_elapsed:.1f}s", flush=True)
    return payload
