from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from rapidfuzz import fuzz

from .types import PrayerSegment


def read_mono_audio(path: Path) -> tuple[np.ndarray, int]:
    audio, sample_rate = sf.read(path)

    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)

    audio = audio.astype(np.float32)
    return audio, int(sample_rate)


def _find_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    run_start: int | None = None

    for index, value in enumerate(mask):
        if value and run_start is None:
            run_start = index
        elif not value and run_start is not None:
            runs.append((run_start, index - 1))
            run_start = None

    if run_start is not None:
        runs.append((run_start, len(mask) - 1))

    return runs


def detect_prayer_starts(
    audio: np.ndarray,
    sample_rate: int,
    min_silence_seconds: int = 12,
    min_gap_seconds: int = 90,
    max_prayers: int = 10,
    collapse_rakah_pairs: bool = True,
) -> list[int]:
    if len(audio) < sample_rate:
        return [0]

    seconds = len(audio) // sample_rate
    trimmed = audio[: seconds * sample_rate]
    frames = trimmed.reshape(seconds, sample_rate)

    rms = np.sqrt(np.mean(np.square(frames), axis=1))
    smoothed = np.convolve(rms, np.ones(5, dtype=np.float32) / 5, mode="same")

    voice_threshold = np.percentile(smoothed, 40)
    silence_threshold = np.percentile(smoothed, 20)

    active = smoothed > voice_threshold
    silence = smoothed < silence_threshold

    starts: list[int] = []

    active_runs = _find_runs(active)
    if active_runs:
        starts.append(active_runs[0][0])

    for start, end in _find_runs(silence):
        run_length = end - start + 1
        if run_length < min_silence_seconds:
            continue

        next_index = end + 1
        while next_index < len(active) and not active[next_index]:
            next_index += 1

        if next_index < len(active):
            starts.append(next_index)

    deduped: list[int] = []
    for second in sorted(set(starts)):
        if not deduped or second - deduped[-1] >= min_gap_seconds:
            deduped.append(second)

    if not deduped:
        deduped = [0]

    if collapse_rakah_pairs and len(deduped) >= 2:
        deduped = deduped[::2]

    return deduped[:max_prayers]


def build_prayer_segments(starts: list[int], total_seconds: int) -> list[PrayerSegment]:
    if not starts:
        starts = [0]

    sorted_starts = sorted(starts)
    segments: list[PrayerSegment] = []

    for index, start in enumerate(sorted_starts):
        end = sorted_starts[index + 1] if index + 1 < len(sorted_starts) else total_seconds
        segments.append(PrayerSegment(index=index + 1, start=int(start), end=int(max(start + 1, end))))

    return segments


def _normalize_arabic(text: str) -> str:
    table = str.maketrans(
        {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ة": "ه",
            "ى": "ي",
            "ؤ": "و",
            "ئ": "ي",
            "ً": "",
            "ٌ": "",
            "ٍ": "",
            "َ": "",
            "ُ": "",
            "ِ": "",
            "ّ": "",
            "ْ": "",
            "ـ": "",
        }
    )
    normalized = text.translate(table)
    cleaned = "".join(ch if ("\u0600" <= ch <= "\u06ff") or ch.isspace() else " " for ch in normalized)
    return " ".join(cleaned.split())


FATIHA_HINTS = [
    _normalize_arabic("الحمد لله رب العالمين"),
    _normalize_arabic("الرحمن الرحيم"),
    _normalize_arabic("مالك يوم الدين"),
    _normalize_arabic("اياك نعبد واياك نستعين"),
    _normalize_arabic("اهدنا الصراط المستقيم"),
]


def detect_fatiha_starts(
    transcript_segments: list[dict] | list[object],
    min_score: int = 78,
    min_gap_seconds: int = 150,
) -> list[int]:
    if not transcript_segments:
        return []

    candidates: list[int] = []

    for segment in transcript_segments:
        raw_text = getattr(segment, "text", None)
        raw_start = getattr(segment, "start", None)
        if raw_text is None and isinstance(segment, dict):
            raw_text = segment.get("text")
            raw_start = segment.get("start")

        text = _normalize_arabic(str(raw_text or ""))
        if len(text) < 12 or raw_start is None:
            continue

        score = max(float(fuzz.partial_ratio(text, phrase)) for phrase in FATIHA_HINTS)
        if score >= min_score:
            candidates.append(int(round(float(raw_start))))

    if not candidates:
        return []

    deduped: list[int] = []
    for second in sorted(set(candidates)):
        if not deduped or second - deduped[-1] >= min_gap_seconds:
            deduped.append(second)
    return deduped


def merge_rakah_starts(
    audio_starts: list[int],
    fatiha_starts: list[int],
    merge_window_seconds: int = 95,
    min_gap_seconds: int = 90,
) -> list[int]:
    merged = sorted(set(audio_starts))
    for f_start in sorted(set(fatiha_starts)):
        if not merged:
            merged.append(f_start)
            continue

        nearest_index = min(range(len(merged)), key=lambda i: abs(merged[i] - f_start))
        distance = abs(merged[nearest_index] - f_start)
        if distance <= merge_window_seconds:
            merged[nearest_index] = min(merged[nearest_index], f_start)
        else:
            merged.append(f_start)

    merged = sorted(set(merged))

    filtered: list[int] = []
    for second in merged:
        if not filtered or second - filtered[-1] >= min_gap_seconds:
            filtered.append(second)
    return filtered
