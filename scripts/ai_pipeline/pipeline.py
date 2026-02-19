from __future__ import annotations

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
from .quran import load_corpus, match_quran_markers
from .reciters import assign_reciters
from .transcribe import transcribe_audio
from .types import Marker, PrayerSegment, TranscriptSegment


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
    match_min_score: int = 84,
    match_min_overlap: float = 0.15,
    match_min_confidence: float = 0.68,
    match_min_gap_seconds: int = 8,
    reuse_transcript_cache: bool = True,
    max_audio_seconds: int | None = None,
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

    transcript_cache_path = Path("data/ai/cache") / f"day-{day}-transcript-{cache_suffix}.json"
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
    markers = match_quran_markers(
        transcript_segments,
        corpus_entries,
        min_score=match_min_score,
        min_gap_seconds=match_min_gap_seconds,
        min_overlap=match_min_overlap,
        min_confidence=match_min_confidence,
    )
    markers = _map_reciter_to_markers(markers, reciter_segments)

    payload = {
        "day": day,
        "source": source,
        "markers": [asdict(marker) for marker in markers],
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audio_path": str(normalized_audio_path),
            "whisper_model": whisper_model,
            "markers_detected": len(markers),
            "reciter_segments_detected": len(reciter_segments),
            "corpus_loaded": bool(corpus_entries),
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
            },
        },
    }

    write_json(output_path, payload)
    return payload
