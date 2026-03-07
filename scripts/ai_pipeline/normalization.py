from __future__ import annotations

from pathlib import Path
from typing import Any

from .asr_corrections import apply_asr_corrections
from .quran import clean_transcript_for_matching, normalize_arabic
from .types import TranscriptSegment


def apply_transcript_corrections(
    transcript_segments: list[TranscriptSegment],
    corrections_path: Path | None,
) -> tuple[list[TranscriptSegment], dict[str, Any]]:
    return apply_asr_corrections(
        transcript_segments=transcript_segments,
        corrections_path=corrections_path,
    )


def prepare_segments_for_matching(
    transcript_segments: list[TranscriptSegment],
) -> list[TranscriptSegment]:
    return clean_transcript_for_matching(transcript_segments)


__all__ = [
    "apply_transcript_corrections",
    "normalize_arabic",
    "prepare_segments_for_matching",
]

