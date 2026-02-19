from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranscriptSegment:
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
    reciter: str | None = None
    confidence: float | None = None
