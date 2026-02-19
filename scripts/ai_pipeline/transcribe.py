from __future__ import annotations

from pathlib import Path

from .types import TranscriptSegment, TranscriptWord


def transcribe_audio(audio_path: Path, model_size: str = "small") -> list[TranscriptSegment]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is required for transcription. Install dependencies from scripts/requirements-ai.txt"
        ) from exc

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="ar", vad_filter=True, word_timestamps=True)

    transcript_segments: list[TranscriptSegment] = []
    for segment in segments:
        text = (segment.text or "").strip()
        if not text:
            continue

        words: list[TranscriptWord] = []
        for word in (segment.words or []):
            if word.start is None or word.end is None:
                continue
            word_text = (word.word or "").strip()
            if not word_text:
                continue
            words.append(
                TranscriptWord(
                    start=float(word.start),
                    end=float(word.end),
                    text=word_text,
                )
            )

        transcript_segments.append(
            TranscriptSegment(
                start=float(segment.start),
                end=float(segment.end),
                text=text,
                words=words,
            )
        )

    return transcript_segments
