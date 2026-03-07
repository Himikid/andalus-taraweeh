from __future__ import annotations

from pathlib import Path

from .transcribe import transcribe_audio
from .types import TranscriptSegment


def transcribe_with_profile(
    audio_path: Path,
    *,
    model_size: str = "small",
) -> list[TranscriptSegment]:
    # Keep current non-chunked behavior for compatibility.
    return transcribe_audio(audio_path=audio_path, model_size=model_size)


__all__ = ["transcribe_with_profile"]

