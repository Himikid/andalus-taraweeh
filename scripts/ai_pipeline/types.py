from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    words: list["TranscriptWord"] = field(default_factory=list)


@dataclass
class TranscriptWord:
    start: float
    end: float
    text: str


@dataclass
class PrayerSegment:
    index: int
    start: int
    end: int
    reciter: str | None = None


@dataclass
class Marker:
    time: int
    surah: str
    ayah: int
    surah_number: int | None = None
    juz: int | None = None
    quality: str = "high"
    reciter: str | None = None
    confidence: float | None = None
    arabic_text: str | None = None
    english_text: str | None = None
