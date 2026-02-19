from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import requests
from rapidfuzz import fuzz

from .types import Marker, TranscriptSegment

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
ARABIC_PUNCT = re.compile(r"[^\u0621-\u063A\u0641-\u064A\s]")
MULTI_SPACE = re.compile(r"\s+")
ASAD_API_URL = "https://api.alquran.cloud/v1/quran/en.asad"
MUQATTAAT_SPOKEN_FORMS: dict[str, list[str]] = {
    "الم": ["الف لام ميم"],
    "المر": ["الف لام ميم را"],
    "الر": ["الف لام را"],
    "كهيعص": ["كاف ها يا عين صاد"],
    "طه": ["طا ها"],
    "طسم": ["طا سين ميم"],
    "طس": ["طا سين"],
    "يس": ["يا سين"],
    "ص": ["صاد"],
    "حم": ["حا ميم"],
    "عسق": ["عين سين قاف"],
    "ق": ["قاف"],
    "ن": ["نون"],
}
FATIHA_HINTS = [
    "الحمد لله رب العالمين",
    "الرحمن الرحيم",
    "مالك يوم الدين",
    "اياك نعبد واياك نستعين",
    "اهدنا الصراط المستقيم",
    "صراط الذين انعمت عليهم غير المغضوب عليهم ولا الضالين",
]
FATIHA_HINTS_NORM: list[str] = []
ARABIC_ANCHOR_STOPWORDS = {
    "و",
    "ف",
    "ثم",
    "لا",
    "ما",
    "من",
    "في",
    "على",
    "الى",
    "إلى",
    "ب",
    "الذي",
    "الذين",
    "هذا",
    "ذلك",
}


@dataclass
class AyahEntry:
    surah_number: int
    surah: str
    ayah: int
    text: str
    normalized: str
    match_forms: list[str]


def is_excluded_surah(surah: str) -> bool:
    normalized = surah.casefold().replace("-", "").replace(" ", "")
    return "fatiha" in normalized or "faatiha" in normalized or "فاتحة" in surah


def normalize_arabic(text: str) -> str:
    text = ARABIC_DIACRITICS.sub("", text)
    text = ARABIC_PUNCT.sub(" ", text)
    text = MULTI_SPACE.sub(" ", text).strip()
    return text


def _build_match_forms(ayah_number: int, normalized_text: str) -> list[str]:
    forms = [normalized_text]
    compact = normalized_text.replace(" ", "")

    # Muqatta'at are often recited as spoken letter names rather than compact letters.
    if ayah_number == 1 and compact in MUQATTAAT_SPOKEN_FORMS:
        for variant in MUQATTAAT_SPOKEN_FORMS[compact]:
            normalized_variant = normalize_arabic(variant)
            if normalized_variant and normalized_variant not in forms:
                forms.append(normalized_variant)
    return forms


def _score_segment_against_entry(normalized_segment: str, entry: AyahEntry) -> tuple[float, float]:
    top_score = -1.0
    top_overlap = 0.0
    for candidate in entry.match_forms:
        partial = float(fuzz.partial_ratio(normalized_segment, candidate))
        ratio = float(fuzz.ratio(normalized_segment, candidate))
        score = (0.75 * partial) + (0.25 * ratio)
        if score > top_score:
            top_score = score
            top_overlap = _token_overlap(normalized_segment, candidate)
    return top_score, top_overlap


def _anchor_tokens_for_form(form: str) -> list[str]:
    tokens = [token for token in form.split() if token]
    if not tokens:
        return []

    strong = [token for token in tokens if len(token) >= 4 and token not in ARABIC_ANCHOR_STOPWORDS]
    if strong:
        return strong

    medium = [token for token in tokens if len(token) >= 3]
    if medium:
        return medium

    return tokens


def _estimate_marker_onset_time(segment: TranscriptSegment, entry: AyahEntry) -> int:
    words = getattr(segment, "words", None) or []
    if not words:
        return int(round(segment.start))

    best_time: float | None = None
    best_score = -1.0

    for form in entry.match_forms:
        anchors = _anchor_tokens_for_form(form)
        if not anchors:
            continue

        for word in words:
            normalized_word = normalize_arabic(str(getattr(word, "text", "")))
            if not normalized_word:
                continue

            local_score = max(
                max(float(fuzz.ratio(normalized_word, anchor)), float(fuzz.partial_ratio(normalized_word, anchor)))
                for anchor in anchors
            )
            if local_score >= 80:
                word_start = float(getattr(word, "start", segment.start))
                if best_time is None or word_start < best_time:
                    best_time = word_start
                if local_score > best_score:
                    best_score = local_score

    return int(round(best_time if best_time is not None else segment.start))


def _is_fatiha_like_segment(normalized_segment: str, min_score: int = 90) -> bool:
    global FATIHA_HINTS_NORM
    if len(normalized_segment) < 10:
        return False
    if len(normalized_segment) > 80:
        return False

    if not FATIHA_HINTS_NORM:
        FATIHA_HINTS_NORM = [normalize_arabic(text) for text in FATIHA_HINTS]

    scores = [float(fuzz.partial_ratio(normalized_segment, phrase)) for phrase in FATIHA_HINTS_NORM]
    if not scores:
        return False

    medium_hits = sum(score >= (min_score - 6) for score in scores)
    long_hit = any(len(phrase) >= 18 and score >= (min_score - 2) for phrase, score in zip(FATIHA_HINTS_NORM, scores))
    return long_hit or medium_hits >= 2


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
                    match_forms=_build_match_forms(ayah_number, normalized),
                )
            )

    return entries


def _parse_translation_payload(payload: dict) -> tuple[dict[tuple[int, int], str], dict]:
    root = payload.get("data", payload)
    surahs = root.get("surahs", [])
    transformed: dict = {"surahs": []}
    lookup: dict[tuple[int, int], str] = {}

    for surah in surahs:
        surah_number = int(surah.get("number", 0))
        if surah_number <= 0:
            continue

        ayahs_out: list[dict] = []
        for ayah in surah.get("ayahs", []):
            ayah_number = int(ayah.get("numberInSurah", ayah.get("number", 0)))
            text = str(ayah.get("text", "")).strip()
            if ayah_number <= 0 or not text:
                continue

            ayahs_out.append({"number": ayah_number, "text": text})
            lookup[(surah_number, ayah_number)] = text

        transformed["surahs"].append({"number": surah_number, "ayahs": ayahs_out})

    return lookup, transformed


def load_asad_translation(asad_path: Path) -> dict[tuple[int, int], str]:
    if asad_path.exists():
        with asad_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        lookup, _ = _parse_translation_payload(payload)
        if lookup:
            return lookup

    try:
        response = requests.get(ASAD_API_URL, timeout=45)
        response.raise_for_status()
        payload = response.json()
        lookup, transformed = _parse_translation_payload(payload)
        if lookup:
            asad_path.parent.mkdir(parents=True, exist_ok=True)
            with asad_path.open("w", encoding="utf-8") as handle:
                json.dump(transformed, handle, ensure_ascii=False, indent=2)
        return lookup
    except requests.RequestException:
        return {}


def enrich_marker_texts(
    markers: list[Marker],
    corpus_entries: list[AyahEntry],
    asad_lookup: dict[tuple[int, int], str],
) -> list[Marker]:
    if not markers:
        return markers

    arabic_lookup: dict[tuple[int, int], str] = {}
    for entry in corpus_entries:
        arabic_lookup[(entry.surah_number, entry.ayah)] = entry.text

    for marker in markers:
        if marker.surah_number is None:
            continue
        key = (marker.surah_number, marker.ayah)
        marker.arabic_text = arabic_lookup.get(key)
        marker.english_text = asad_lookup.get(key)

    return markers


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


def _find_best_ayah_timestamp(
    transcript_segments: list[TranscriptSegment],
    entry: AyahEntry,
    window_start: int,
    window_end: int,
    expected_time: int,
    min_score: int,
    min_overlap: float,
    min_confidence: float,
    ambiguous_min_score: int,
    ambiguous_min_confidence: float,
) -> tuple[int, str, float] | None:
    if window_end <= window_start:
        return None

    top_segment: TranscriptSegment | None = None
    top_score = -1.0
    second_score = -1.0
    top_overlap = 0.0

    for segment in transcript_segments:
        if segment.end < window_start or segment.start > window_end:
            continue

        normalized_segment = normalize_arabic(segment.text)
        if len(normalized_segment) < 10:
            continue

        score, overlap = _score_segment_against_entry(normalized_segment, entry)

        if score > top_score:
            second_score = top_score
            top_score = score
            top_segment = segment
            top_overlap = overlap
        elif score > second_score:
            second_score = score

    if top_segment is None or top_score < ambiguous_min_score:
        return None

    top_time = _estimate_marker_onset_time(top_segment, entry)
    margin = max(0.0, top_score - max(0.0, second_score))
    window_span = max(1, window_end - window_start)
    proximity = 1.0 - min(1.0, abs(top_time - expected_time) / window_span)
    confidence = (
        (0.5 * (top_score / 100.0))
        + (0.2 * min(1.0, margin / 20.0))
        + (0.2 * top_overlap)
        + (0.1 * proximity)
    )

    is_high = top_score >= min_score and top_overlap >= min_overlap and confidence >= min_confidence
    is_ambiguous = top_score >= ambiguous_min_score and confidence >= ambiguous_min_confidence
    if not is_high and not is_ambiguous:
        return None

    return top_time, ("high" if is_high else "ambiguous"), round(confidence, 3)


def _quality_rank(quality: str | None) -> int:
    if quality == "high":
        return 3
    if quality == "ambiguous":
        return 2
    if quality == "inferred":
        return 1
    return 0


def _estimate_step_seconds(surah_markers: dict[int, Marker], default_step: int = 8) -> int:
    pairs = sorted(surah_markers.items(), key=lambda item: item[0])
    deltas: list[float] = []
    for (left_ayah, left_marker), (right_ayah, right_marker) in zip(pairs, pairs[1:]):
        ayah_gap = right_ayah - left_ayah
        time_gap = right_marker.time - left_marker.time
        if ayah_gap <= 0 or time_gap <= 0:
            continue
        deltas.append(time_gap / ayah_gap)

    if not deltas:
        return default_step

    deltas.sort()
    median = deltas[len(deltas) // 2]
    return int(max(4, min(20, round(median))))


def _fill_surah_coverage_markers(
    existing_markers: list[Marker],
    entry_lookup: dict[tuple[str, int], AyahEntry],
) -> list[Marker]:
    surah_map: dict[str, dict[int, Marker]] = {}
    for marker in sorted(existing_markers, key=lambda m: m.time):
        ayah_map = surah_map.setdefault(marker.surah, {})
        existing = ayah_map.get(marker.ayah)
        if existing is None:
            ayah_map[marker.ayah] = marker
            continue
        if _quality_rank(marker.quality) > _quality_rank(existing.quality):
            ayah_map[marker.ayah] = marker
        elif _quality_rank(marker.quality) == _quality_rank(existing.quality) and marker.time < existing.time:
            ayah_map[marker.ayah] = marker

    coverage_inferred: list[Marker] = []

    for surah, ayah_map in surah_map.items():
        if not ayah_map:
            continue

        known_ayahs = sorted(ayah_map.keys())
        min_ayah = known_ayahs[0]
        max_ayah = known_ayahs[-1]
        step_seconds = _estimate_step_seconds(ayah_map)

        for ayah in range(min_ayah, max_ayah + 1):
            if ayah in ayah_map:
                continue

            left_ayahs = [a for a in known_ayahs if a < ayah]
            right_ayahs = [a for a in known_ayahs if a > ayah]
            left_ayah = left_ayahs[-1] if left_ayahs else None
            right_ayah = right_ayahs[0] if right_ayahs else None

            inferred_time: int
            if left_ayah is not None and right_ayah is not None:
                left_marker = ayah_map[left_ayah]
                right_marker = ayah_map[right_ayah]
                span_ayahs = right_ayah - left_ayah
                span_secs = right_marker.time - left_marker.time
                ratio = (ayah - left_ayah) / max(1, span_ayahs)
                if span_secs > 0:
                    inferred_time = int(round(left_marker.time + (span_secs * ratio)))
                else:
                    inferred_time = left_marker.time + ((ayah - left_ayah) * step_seconds)
            elif left_ayah is not None:
                left_marker = ayah_map[left_ayah]
                inferred_time = left_marker.time + ((ayah - left_ayah) * step_seconds)
            elif right_ayah is not None:
                right_marker = ayah_map[right_ayah]
                inferred_time = max(0, right_marker.time - ((right_ayah - ayah) * step_seconds))
            else:
                continue

            entry = entry_lookup.get((surah, ayah))
            left_reciter = ayah_map[left_ayah].reciter if left_ayah is not None else None
            right_reciter = ayah_map[right_ayah].reciter if right_ayah is not None else None
            reciter = left_reciter or right_reciter
            surah_number = entry.surah_number if entry else ayah_map[known_ayahs[0]].surah_number

            coverage_inferred.append(
                Marker(
                    time=max(0, inferred_time),
                    surah=surah,
                    surah_number=surah_number,
                    ayah=ayah,
                    juz=get_juz_for_ayah(surah_number or 1, ayah),
                    quality="inferred",
                    reciter=reciter,
                    confidence=0.56,
                )
            )

    return coverage_inferred


def _dedupe_by_local_time_window(markers: list[Marker], window_seconds: int = 90) -> list[Marker]:
    if not markers:
        return []

    sorted_markers = sorted(markers, key=lambda marker: marker.time)
    deduped: list[Marker] = []

    for marker in sorted_markers:
        merged = False
        for index in range(len(deduped) - 1, -1, -1):
            candidate = deduped[index]
            if marker.time - candidate.time > window_seconds:
                break
            if marker.surah == candidate.surah and marker.ayah == candidate.ayah:
                if _quality_rank(marker.quality) > _quality_rank(candidate.quality):
                    deduped[index] = marker
                elif _quality_rank(marker.quality) == _quality_rank(candidate.quality) and marker.time < candidate.time:
                    deduped[index] = marker
                merged = True
                break
        if not merged:
            deduped.append(marker)

    return deduped


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
    allow_unverified_leading_infer: bool = True,
    duplicate_ayah_window_seconds: int = 120,
    max_forward_jump_ayahs: int = 14,
) -> list[Marker]:
    if not transcript_segments or not corpus_entries:
        return []

    surah_totals: dict[str, int] = {}
    for item in corpus_entries:
        current = surah_totals.get(item.surah, 0)
        if item.ayah > current:
            surah_totals[item.surah] = item.ayah

    markers: list[Marker] = []
    marker_positions: dict[tuple[str, int], int] = {}
    last_matched_index = -1
    last_marker_time = -1
    stale_segments = 0

    for segment_index, segment in enumerate(transcript_segments):
        normalized_segment = normalize_arabic(segment.text)
        if _is_fatiha_like_segment(normalized_segment):
            # During Fatiha we should not advance Quran progression markers.
            continue

        segment_variants: list[tuple[str, float]] = [(normalized_segment, 0.0)]
        combined_text = normalized_segment
        previous_end = float(segment.end)
        for offset in range(1, 7):
            next_idx = segment_index + offset
            if next_idx >= len(transcript_segments):
                break
            next_segment = transcript_segments[next_idx]
            if float(next_segment.start) - previous_end > 2.5:
                break
            next_normalized = normalize_arabic(next_segment.text)
            if len(next_normalized) < 2:
                break
            combined_text = f"{combined_text} {next_normalized}".strip()
            # Penalize longer merged windows slightly to avoid over-eager matches.
            segment_variants.append((combined_text, float(offset) * 1.1))
            previous_end = float(next_segment.end)

        if max(len(text) for text, _ in segment_variants) < 14:
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
        top_overlap = 0.0

        for index in range(search_start, search_end):
            entry = corpus_entries[index]
            if is_excluded_surah(entry.surah):
                continue

            score = -1.0
            overlap = 0.0
            for variant_text, penalty in segment_variants:
                variant_score, variant_overlap = _score_segment_against_entry(variant_text, entry)
                adjusted_score = variant_score - penalty
                if adjusted_score > score:
                    score = adjusted_score
                    overlap = variant_overlap

            if score > top_score:
                second_score = top_score
                top_score = score
                top_index = index
                top_overlap = overlap
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

        overlap = top_overlap
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

        marker_time = _estimate_marker_onset_time(segment, entry)

        if markers:
            previous = markers[-1]
            if marker_time - previous.time < min_gap_seconds:
                stale_segments += 1
                continue
            if previous.surah != entry.surah:
                previous_total = surah_totals.get(previous.surah, previous.ayah)
                near_end_of_previous = previous.ayah >= max(1, previous_total - 5)
                next_surah = (
                    previous.surah_number is not None
                    and entry.surah_number is not None
                    and entry.surah_number == previous.surah_number + 1
                )
                # Block random cross-surah jumps; only allow natural progression near a surah boundary.
                if not (near_end_of_previous and next_surah):
                    stale_segments += 1
                    continue
            if previous.surah == entry.surah:
                ayah_delta = entry.ayah - previous.ayah
                elapsed = max(1, marker_time - previous.time)
                allowed_jump = max_forward_jump_ayahs + int(elapsed // 25)

                # Preserve forward progression and block implausible large jumps.
                if ayah_delta < 0:
                    stale_segments += 1
                    continue
                if ayah_delta > allowed_jump:
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
            if abs(marker_time - existing.time) <= duplicate_ayah_window_seconds:
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
    entry_lookup: dict[tuple[str, int], AyahEntry] = {(entry.surah, entry.ayah): entry for entry in corpus_entries}
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

            expected_time = int(round(left.time + (step_seconds * offset)))
            window_half = max(10, int(round(step_seconds * 0.8)))
            window_start = max(left.time + min_gap_seconds, expected_time - window_half)
            window_end = min(right.time - min_gap_seconds, expected_time + window_half)

            marker_to_add: Marker | None = None
            entry = entry_lookup.get(key)
            if entry is not None:
                best = _find_best_ayah_timestamp(
                    transcript_segments=transcript_segments,
                    entry=entry,
                    window_start=window_start,
                    window_end=window_end,
                    expected_time=expected_time,
                    min_score=min_score,
                    min_overlap=min_overlap,
                    min_confidence=min_confidence,
                    ambiguous_min_score=ambiguous_min_score,
                    ambiguous_min_confidence=ambiguous_min_confidence,
                )
                if best is not None:
                    matched_time, quality, confidence = best
                    bounded_time = max(window_start, min(window_end, matched_time))
                    marker_to_add = Marker(
                        time=bounded_time,
                        surah=left.surah,
                        surah_number=left.surah_number,
                        ayah=ayah_number,
                        juz=get_juz_for_ayah(left.surah_number or 1, ayah_number),
                        quality=quality,
                        confidence=confidence,
                    )

            if marker_to_add is None:
                inferred_time = int(round(left.time + (step_seconds * offset)))
                marker_to_add = Marker(
                    time=inferred_time,
                    surah=left.surah,
                    surah_number=left.surah_number,
                    ayah=ayah_number,
                    juz=get_juz_for_ayah(left.surah_number or 1, ayah_number),
                    quality="inferred",
                    confidence=round(min(left.confidence or 0.58, right.confidence or 0.58, 0.6), 3),
                )

            inferred_markers.append(marker_to_add)
            keyed_markers[key] = marker_to_add

    # Backfill leading ayahs if the first strong anchor starts after ayah 1.
    # Try to find best evidence in the pre-anchor audio window before falling back to inferred placement.
    if anchors:
        first = anchors[0]
        if first.ayah > 1 and first.ayah - 1 <= max_leading_infer_ayahs:
            time_step = max(4, int(round(first.time / max(1, first.ayah))))
            for ayah_number in range(first.ayah - 1, 0, -1):
                key = (first.surah, ayah_number)
                if key in keyed_markers:
                    continue

                offset = first.ayah - ayah_number
                leading_step = max(4, min(8, time_step))
                expected_time = max(0, first.time - (leading_step * offset))
                window_half = max(8, time_step)
                window_start = max(0, expected_time - window_half)
                window_end = min(max(0, first.time - min_gap_seconds), expected_time + window_half)

                marker_to_add: Marker | None = None
                entry = entry_lookup.get(key)
                if entry is not None:
                    best = _find_best_ayah_timestamp(
                        transcript_segments=transcript_segments,
                        entry=entry,
                        window_start=window_start,
                        window_end=window_end,
                        expected_time=expected_time,
                        min_score=min_score,
                        min_overlap=max(min_overlap, 0.18),
                        min_confidence=min_confidence,
                        ambiguous_min_score=ambiguous_min_score,
                        ambiguous_min_confidence=ambiguous_min_confidence,
                    )
                    if best is not None:
                        matched_time, quality, confidence = best
                        bounded_time = max(window_start, min(window_end, matched_time))
                        marker_to_add = Marker(
                            time=bounded_time,
                            surah=first.surah,
                            surah_number=first.surah_number,
                            ayah=ayah_number,
                            juz=get_juz_for_ayah(first.surah_number or 1, ayah_number),
                            quality=quality,
                            confidence=confidence,
                        )

                if marker_to_add is None and not allow_unverified_leading_infer:
                    continue

                if marker_to_add is None:
                    marker_to_add = Marker(
                        time=expected_time,
                        surah=first.surah,
                        surah_number=first.surah_number,
                        ayah=ayah_number,
                        juz=get_juz_for_ayah(first.surah_number or 1, ayah_number),
                        quality="inferred",
                        confidence=round(min(first.confidence or 0.58, 0.58), 3),
                    )

                inferred_markers.append(marker_to_add)
                keyed_markers[key] = marker_to_add

    merged = markers + inferred_markers
    coverage_inferred = _fill_surah_coverage_markers(merged, entry_lookup)
    merged.extend(coverage_inferred)

    return _dedupe_by_local_time_window(merged, window_seconds=90)
