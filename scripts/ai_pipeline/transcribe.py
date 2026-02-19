from __future__ import annotations

from pathlib import Path

from .types import TranscriptSegment


def transcribe_audio(audio_path: Path, model_size: str = "small") -> list[TranscriptSegment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required for transcription. Install dependencies from scripts/requirements-ai.txt"
        ) from exc

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="ar", vad_filter=True)

    transcript_segments: list[TranscriptSegment] = []
    for segment in segments:
        text = (segment.text or "").strip()
        if not text:
            continue

        transcript_segments.append(
            TranscriptSegment(
                start=float(segment.start),
                end=float(segment.end),
                text=text,
            )
        )

    return transcript_segments
