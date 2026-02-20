from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

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
    final_time_raw = day_config.get("final_time")

    try:
        final_ayah = int(final_ayah_raw) if final_ayah_raw is not None else None
    except (TypeError, ValueError):
        final_ayah = None
    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None

    if final_ayah is None and final_time is None:
        return markers, None

    final_surah_number: int | None = None
    if final_surah:
        for marker in markers:
            if marker.surah == final_surah and marker.surah_number is not None:
                final_surah_number = int(marker.surah_number)
                break

    def keep(marker: Marker) -> bool:
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
        "final_time": final_time,
        "markers_before": len(markers),
        "markers_after": len(filtered),
        "inserted_terminal": inserted_terminal,
        "inserted_terminal_time": inserted_time,
    }
    return filtered, info


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
    normalized_audio_path, source = prepare_audio_source(
        day=day,
        youtube_url=youtube_url,
        audio_file=audio_file,
        cache_dir=cache_dir,
    )

    audio, sample_rate = read_mono_audio(normalized_audio_path)
    transcription_audio_path = normalized_audio_path
    cache_suffix = "full"

    if max_audio_seconds is not None and max_audio_seconds > 0:
        max_samples = min(len(audio), max_audio_seconds * sample_rate)
        audio = audio[:max_samples]
        cache_suffix = f"{max_audio_seconds}s"
        trimmed_audio_path = normalized_audio_path.parent / f"trimmed-{cache_suffix}.wav"
        sf.write(trimmed_audio_path, audio, sample_rate)
        transcription_audio_path = trimmed_audio_path

    total_seconds = int(len(audio) / sample_rate)

    part_suffix = f"-part-{part}" if part is not None and part > 0 else ""
    transcript_cache_path = Path("data/ai/cache") / f"day-{day}{part_suffix}-transcript-{cache_suffix}.json"
    transcript_segments: list[TranscriptSegment]
    if reuse_transcript_cache and transcript_cache_path.exists():
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
    else:
        transcript_segments = transcribe_audio(transcription_audio_path, model_size=whisper_model)
        write_json(
            transcript_cache_path,
            {
                "day": day,
                "source": source,
                "segments": [asdict(segment) for segment in transcript_segments],
            },
        )

    audio_segment_starts = detect_prayer_starts(audio, sample_rate, collapse_rakah_pairs=True)
    fatiha_segment_starts = detect_fatiha_starts(transcript_segments)
    reciter_segment_starts = merge_rakah_starts(audio_segment_starts, fatiha_segment_starts, min_gap_seconds=180)

    reciter_segments = build_prayer_segments(reciter_segment_starts, total_seconds)
    reciter_segments = assign_reciters(
        day=day,
        audio=audio,
        sample_rate=sample_rate,
        prayers=reciter_segments,
        profiles_path=profiles_path,
        bootstrap_reciters=bootstrap_reciters,
    )

    corpus_entries = load_corpus(corpus_path)
    forced_start_index: int | None = None
    if match_start_surah_number is not None and match_start_ayah is not None:
        for index, entry in enumerate(corpus_entries):
            if entry.surah_number == match_start_surah_number and entry.ayah == match_start_ayah:
                forced_start_index = index
                break
    markers = match_quran_markers(
        transcript_segments,
        corpus_entries,
        min_score=match_min_score,
        min_gap_seconds=match_min_gap_seconds,
        min_overlap=match_min_overlap,
        min_confidence=match_min_confidence,
        require_weak_support_for_inferred=match_require_weak_support_for_inferred,
        forced_start_index=forced_start_index,
    )
    markers, override_info = _apply_day_final_ayah_override(
        day=day,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    asad_lookup = load_asad_translation(asad_path) if asad_path else {}
    markers = enrich_marker_texts(markers, corpus_entries, asad_lookup)
    markers = _map_reciter_to_markers(markers, reciter_segments)

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
            "reciter_segments_detected": len(reciter_segments),
            "corpus_loaded": bool(corpus_entries),
            "asad_loaded": bool(asad_lookup),
            "transcript_path": str(transcript_cache_path),
            "segment_detection": {
                "audio_starts": len(audio_segment_starts),
                "fatiha_starts": len(fatiha_segment_starts),
                "merged_starts": len(reciter_segment_starts),
            },
            "match_config": {
                "min_score": match_min_score,
                "min_overlap": match_min_overlap,
                "min_confidence": match_min_confidence,
                "min_gap_seconds": match_min_gap_seconds,
                "strict_normalization": STRICT_NORMALIZATION,
                "require_weak_support_for_inferred": match_require_weak_support_for_inferred,
                "start_surah_number": match_start_surah_number,
                "start_ayah": match_start_ayah,
            },
            "manual_override": override_info,
        },
    }

    write_json(output_path, payload)
    return payload
