from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz

from .types import Marker, TranscriptSegment

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
ARABIC_PUNCT = re.compile(r"[^\u0621-\u063A\u0641-\u064A\s]")
MULTI_SPACE = re.compile(r"\s+")


@dataclass
class AyahEntry:
    surah_number: int
    surah: str
    ayah: int
    text: str
    normalized: str


def is_excluded_surah(surah: str) -> bool:
    normalized = surah.casefold().replace("-", "").replace(" ", "")
    return "fatiha" in normalized or "faatiha" in normalized or "فاتحة" in surah


def normalize_arabic(text: str) -> str:
    text = ARABIC_DIACRITICS.sub("", text)
    text = ARABIC_PUNCT.sub(" ", text)
    text = MULTI_SPACE.sub(" ", text).strip()
    return text


def _token_overlap(query: str, reference: str) -> float:
    query_tokens = set(query.split())
    reference_tokens = set(reference.split())
    if not query_tokens or not reference_tokens:
        return 0.0

    shared = len(query_tokens & reference_tokens)
    return shared / max(1, len(reference_tokens))


def load_corpus(corpus_path: Path) -> list[AyahEntry]:
    if not corpus_path.exists():
        return []

    with corpus_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    surahs = payload.get("surahs", [])
    entries: list[AyahEntry] = []

    for surah in surahs:
        surah_number = int(surah.get("number", 0))
        surah_name = str(surah.get("name", "Unknown Surah"))
        for ayah in surah.get("ayahs", []):
            ayah_number = int(ayah.get("number", 0))
            ayah_text = str(ayah.get("text", "")).strip()
            normalized = normalize_arabic(ayah_text)
            if not normalized:
                continue

            entries.append(
                AyahEntry(
                    surah_number=surah_number,
                    surah=surah_name,
                    ayah=ayah_number,
                    text=ayah_text,
                    normalized=normalized,
                )
            )

    return entries


JUZ_STARTS: list[tuple[int, int, int]] = [
    (1, 1, 1),
    (2, 2, 142),
    (3, 2, 253),
    (4, 3, 93),
    (5, 4, 24),
    (6, 4, 148),
    (7, 5, 82),
    (8, 6, 111),
    (9, 7, 88),
    (10, 8, 41),
    (11, 9, 93),
    (12, 11, 6),
    (13, 12, 53),
    (14, 15, 1),
    (15, 17, 1),
    (16, 18, 75),
    (17, 21, 1),
    (18, 23, 1),
    (19, 25, 21),
    (20, 27, 56),
    (21, 29, 46),
    (22, 33, 31),
    (23, 36, 28),
    (24, 39, 32),
    (25, 41, 47),
    (26, 46, 1),
    (27, 51, 31),
    (28, 58, 1),
    (29, 67, 1),
    (30, 78, 1),
]


def get_juz_for_ayah(surah_number: int, ayah_number: int) -> int:
    for juz, start_surah, start_ayah in reversed(JUZ_STARTS):
        if surah_number > start_surah:
            return juz
        if surah_number == start_surah and ayah_number >= start_ayah:
            return juz
    return 1


def match_quran_markers(
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list[AyahEntry],
    min_score: int = 76,
    min_gap_seconds: int = 8,
    min_overlap: float = 0.0,
    min_confidence: float = 0.6,
    search_window: int = 220,
    recovery_after_seconds: int = 420,
    recovery_rewind_ayat: int = 40,
    recovery_window_multiplier: float = 2.0,
    ambiguous_min_score: int = 70,
    ambiguous_min_confidence: float = 0.5,
    max_infer_gap_ayahs: int = 8,
    max_infer_gap_seconds: int = 720,
    max_leading_infer_ayahs: int = 3,
) -> list[Marker]:
    if not transcript_segments or not corpus_entries:
        return []

    markers: list[Marker] = []
    marker_positions: dict[tuple[str, int], int] = {}
    last_matched_index = -1
    last_marker_time = -1
    stale_segments = 0

    for segment in transcript_segments:
        normalized_segment = normalize_arabic(segment.text)
        if len(normalized_segment) < 14:
            continue

        is_recovery = False
        if last_marker_time >= 0 and segment.start - last_marker_time >= recovery_after_seconds:
            is_recovery = True
        if stale_segments >= 12:
            is_recovery = True

        local_min_score = min_score
        local_min_confidence = min_confidence
        local_min_overlap = min_overlap
        local_search_window = search_window

        if is_recovery and last_matched_index >= 0:
            local_min_score = max(68, min_score - 4)
            local_min_confidence = max(0.55, min_confidence - 0.07)
            local_min_overlap = max(0.0, min_overlap - 0.05)
            local_search_window = int(search_window * recovery_window_multiplier)

        if is_recovery and last_matched_index >= 0:
            search_start = max(0, last_matched_index - recovery_rewind_ayat)
        else:
            search_start = max(0, last_matched_index + 1)

        search_end = min(len(corpus_entries), search_start + local_search_window)
        if search_start >= len(corpus_entries):
            break

        top_index = -1
        top_score = -1.0
        second_score = -1.0

        for index in range(search_start, search_end):
            entry = corpus_entries[index]
            if is_excluded_surah(entry.surah):
                continue

            partial = float(fuzz.partial_ratio(normalized_segment, entry.normalized))
            ratio = float(fuzz.ratio(normalized_segment, entry.normalized))
            score = (0.75 * partial) + (0.25 * ratio)

            if score > top_score:
                second_score = top_score
                top_score = score
                top_index = index
            elif score > second_score:
                second_score = score

        if top_index < 0 or top_score < ambiguous_min_score:
            stale_segments += 1
            continue

        matched_index = top_index
        entry = corpus_entries[matched_index]
        if is_excluded_surah(entry.surah):
            stale_segments += 1
            continue

        overlap = _token_overlap(normalized_segment, entry.normalized)
        margin = max(0.0, top_score - max(0.0, second_score))
        confidence = (0.55 * (top_score / 100.0)) + (0.25 * min(1.0, margin / 20.0)) + (0.2 * overlap)
        threshold = 0.7 if last_matched_index < 0 else min_confidence
        if is_recovery and last_matched_index >= 0:
            threshold = local_min_confidence

        is_high = top_score >= local_min_score and confidence >= threshold and overlap >= local_min_overlap
        is_ambiguous = top_score >= ambiguous_min_score and confidence >= ambiguous_min_confidence
        if not is_high and not is_ambiguous:
            stale_segments += 1
            continue

        marker_time = int(round(segment.start))

        if markers:
            previous = markers[-1]
            if marker_time - previous.time < min_gap_seconds:
                stale_segments += 1
                continue

        key = (entry.surah, entry.ayah)
        existing_index = marker_positions.get(key)
        candidate = Marker(
            time=marker_time,
            surah=entry.surah,
            surah_number=entry.surah_number,
            ayah=entry.ayah,
            juz=get_juz_for_ayah(entry.surah_number, entry.ayah),
            quality="high" if is_high else "ambiguous",
            confidence=round(confidence, 3),
        )

        if existing_index is not None:
            existing = markers[existing_index]
            should_replace = False
            if existing.quality != "high" and candidate.quality == "high":
                should_replace = True
            elif existing.quality == candidate.quality and marker_time < existing.time:
                should_replace = True

            if should_replace:
                markers[existing_index] = candidate
            last_matched_index = max(last_matched_index, matched_index)
            stale_segments = 0
            continue

        markers.append(candidate)
        marker_positions[key] = len(markers) - 1
        last_matched_index = max(last_matched_index, matched_index)
        last_marker_time = marker_time
        stale_segments = 0

    inferred_markers: list[Marker] = []
    keyed_markers: dict[tuple[str, int], Marker] = {(marker.surah, marker.ayah): marker for marker in markers}
    anchors = [marker for marker in sorted(markers, key=lambda m: m.time) if marker.quality == "high"]

    for left, right in zip(anchors, anchors[1:]):
        if left.surah != right.surah:
            continue
        if left.ayah >= right.ayah:
            continue

        missing_count = right.ayah - left.ayah - 1
        if missing_count <= 0 or missing_count > max_infer_gap_ayahs:
            continue

        gap_seconds = right.time - left.time
        if gap_seconds <= min_gap_seconds or gap_seconds > max_infer_gap_seconds:
            continue

        step_seconds = gap_seconds / (missing_count + 1)
        for offset in range(1, missing_count + 1):
            ayah_number = left.ayah + offset
            key = (left.surah, ayah_number)
            if key in keyed_markers:
                continue

            inferred_time = int(round(left.time + (step_seconds * offset)))
            inferred = Marker(
                time=inferred_time,
                surah=left.surah,
                surah_number=left.surah_number,
                ayah=ayah_number,
                juz=get_juz_for_ayah(left.surah_number or 1, ayah_number),
                quality="inferred",
                confidence=round(min(left.confidence or 0.58, right.confidence or 0.58, 0.6), 3),
            )
            inferred_markers.append(inferred)
            keyed_markers[key] = inferred

    # Backfill leading ayahs if the first strong anchor starts after ayah 1.
    if anchors:
        first = anchors[0]
        if first.ayah > 1 and first.ayah - 1 <= max_leading_infer_ayahs:
            # Spread inferred ayahs before the first confident timestamp.
            time_step = max(4, int(round(first.time / max(1, first.ayah))))
            for ayah_number in range(first.ayah - 1, 0, -1):
                key = (first.surah, ayah_number)
                if key in keyed_markers:
                    continue

                offset = first.ayah - ayah_number
                inferred_time = max(0, first.time - (time_step * offset))
                inferred = Marker(
                    time=inferred_time,
                    surah=first.surah,
                    surah_number=first.surah_number,
                    ayah=ayah_number,
                    juz=get_juz_for_ayah(first.surah_number or 1, ayah_number),
                    quality="inferred",
                    confidence=round(min(first.confidence or 0.58, 0.58), 3),
                )
                inferred_markers.append(inferred)
                keyed_markers[key] = inferred

    return sorted(markers + inferred_markers, key=lambda marker: marker.time)
