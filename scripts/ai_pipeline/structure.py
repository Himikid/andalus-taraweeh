from __future__ import annotations

from dataclasses import dataclass

from .prayers import (
    build_prayer_segments,
    detect_fatiha_starts,
    detect_prayer_starts,
    merge_rakah_starts,
)
from .types import PrayerSegment, TranscriptSegment


@dataclass
class StructureDetectionResult:
    audio_starts: list[int]
    fatiha_starts: list[int]
    merged_starts: list[int]
    reciter_segments: list[PrayerSegment]
    reset_markers: list[float]


def detect_prayer_structure(
    audio,
    sample_rate: int,
    transcript_segments: list[TranscriptSegment],
    total_seconds: int,
) -> StructureDetectionResult:
    audio_starts = detect_prayer_starts(audio, sample_rate, collapse_rakah_pairs=True)
    fatiha_starts = detect_fatiha_starts(transcript_segments)
    merged_starts = merge_rakah_starts(audio_starts, fatiha_starts, min_gap_seconds=180)
    reciter_segments = build_prayer_segments(merged_starts, total_seconds)
    reset_markers = [float(item) for item in fatiha_starts]

    return StructureDetectionResult(
        audio_starts=audio_starts,
        fatiha_starts=fatiha_starts,
        merged_starts=merged_starts,
        reciter_segments=reciter_segments,
        reset_markers=reset_markers,
    )


__all__ = ["StructureDetectionResult", "detect_prayer_structure"]

