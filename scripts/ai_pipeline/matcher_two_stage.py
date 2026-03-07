from __future__ import annotations

from dataclasses import dataclass

from .quran import (
    ARABIC_ANCHOR_STOPWORDS,
    AyahEntry,
    _has_anchor_token_hit,
    _is_fatiha_like_segment,
    _is_non_recitation_segment,
    _score_segment_against_entry,
    normalize_arabic,
)
from .types import Marker, TranscriptSegment


@dataclass
class SegmentCandidate:
    segment_index: int
    corpus_index: int
    start_time: float
    end_time: float
    normalized_text: str
    score: float
    overlap: float
    has_anchor: bool
    adjusted_score: float


@dataclass
class BeamNode:
    candidate: SegmentCandidate | None
    prev: "BeamNode | None"


@dataclass
class BeamState:
    score: float
    last_index: int
    last_time: float
    emissions: int
    node: BeamNode | None


def _entry_tokens(entry: AyahEntry) -> set[str]:
    return {
        token
        for token in entry.normalized.split()
        if len(token) >= 3 and token not in ARABIC_ANCHOR_STOPWORDS
    }


def _segment_tokens(normalized_text: str) -> list[str]:
    return [
        token
        for token in normalized_text.split()
        if len(token) >= 3 and token not in ARABIC_ANCHOR_STOPWORDS
    ]


def _build_token_index(corpus_entries: list[AyahEntry]) -> dict[str, list[int]]:
    token_index: dict[str, list[int]] = {}
    for idx, entry in enumerate(corpus_entries):
        for token in _entry_tokens(entry):
            rows = token_index.setdefault(token, [])
            rows.append(idx)
    return token_index


def _constraint_range_for_time(
    t: float,
    constraints: list[tuple[float, float, int | None, int | None]] | None,
) -> tuple[int | None, int | None]:
    if not constraints:
        return None, None
    active: list[tuple[int | None, int | None]] = []
    for start_time, end_time, min_index, max_index in constraints:
        if float(start_time) <= t <= float(end_time):
            active.append((min_index, max_index))
    if not active:
        return None, None
    min_values = [value for value, _ in active if value is not None]
    max_values = [value for _, value in active if value is not None]
    min_index = max(min_values) if min_values else None
    max_index = min(max_values) if max_values else None
    if min_index is not None and max_index is not None and max_index < min_index:
        return max_index, min_index
    return min_index, max_index


def _build_reanchor_schedule(
    reanchor_points: list[tuple[int, int, int]] | None,
    corpus_entries: list[AyahEntry],
) -> list[tuple[float, int]]:
    if not reanchor_points:
        return []
    by_surah_ayah: dict[tuple[int, int], int] = {}
    for idx, entry in enumerate(corpus_entries):
        by_surah_ayah[(int(entry.surah_number), int(entry.ayah))] = idx
    schedule: list[tuple[float, int]] = []
    for row in reanchor_points:
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            continue
        try:
            at_time = float(row[0])
            surah_number = int(row[1])
            ayah = int(row[2])
        except (TypeError, ValueError):
            continue
        index = by_surah_ayah.get((surah_number, ayah))
        if index is None:
            continue
        schedule.append((at_time, index))
    schedule.sort(key=lambda item: item[0])
    return schedule


def _min_index_from_reanchors(t: float, schedule: list[tuple[float, int]]) -> int | None:
    value: int | None = None
    for at_time, index in schedule:
        if at_time > t:
            break
        value = index
    return value


def _max_index_before_next_reanchor(
    t: float,
    schedule: list[tuple[float, int]],
    lead_tolerance_ayahs: int = 2,
) -> int | None:
    for at_time, index in schedule:
        if at_time > t:
            return int(index + max(0, int(lead_tolerance_ayahs)))
    return None


def _candidate_pool_for_segment(
    *,
    normalized_text: str,
    token_index: dict[str, list[int]],
    forced_start_index: int | None,
    constrained_min: int | None,
    constrained_max: int | None,
    pre_anchor_max: int | None,
    reanchor_min: int | None,
    corpus_size: int,
    max_pool_size: int = 360,
) -> list[int]:
    token_scores: dict[int, float] = {}
    for token in _segment_tokens(normalized_text):
        indices = token_index.get(token)
        if not indices:
            continue
        weight = 1.0 / max(1.0, float(len(indices)))
        for idx in indices:
            token_scores[idx] = token_scores.get(idx, 0.0) + weight

    if token_scores:
        ranked = sorted(token_scores.items(), key=lambda item: item[1], reverse=True)
        candidate_indices = [idx for idx, _score in ranked[:max_pool_size]]
    else:
        candidate_indices = list(range(corpus_size))

    floor = forced_start_index if forced_start_index is not None else None
    if reanchor_min is not None:
        floor = reanchor_min if floor is None else max(floor, reanchor_min)
    if constrained_min is not None:
        floor = constrained_min if floor is None else max(floor, constrained_min)
    ceiling = constrained_max
    if pre_anchor_max is not None:
        ceiling = pre_anchor_max if ceiling is None else min(ceiling, pre_anchor_max)

    output: list[int] = []
    for idx in candidate_indices:
        if floor is not None and idx < floor:
            continue
        if ceiling is not None and idx > ceiling:
            continue
        output.append(idx)

    if output:
        return output

    # Fallback when token retrieval misses but time constraints are tight.
    left = floor if floor is not None else 0
    right = ceiling if ceiling is not None else (corpus_size - 1)
    if right < left:
        left, right = right, left
    span = max(0, int(right - left))
    if span <= 450:
        return list(range(max(0, left), min(corpus_size - 1, right) + 1))
    return []


def _build_segment_candidates(
    *,
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list[AyahEntry],
    token_index: dict[str, list[int]],
    min_score: int,
    min_overlap: float,
    forced_start_index: int | None,
    reanchor_schedule: list[tuple[float, int]],
    segment_constraints: list[tuple[float, float, int | None, int | None]] | None,
    top_k_per_segment: int,
) -> list[list[SegmentCandidate]]:
    per_segment: list[list[SegmentCandidate]] = [[] for _ in transcript_segments]
    corpus_size = len(corpus_entries)
    for segment_index, segment in enumerate(transcript_segments):
        normalized_text = normalize_arabic(str(segment.text or ""), strict=False)
        if len(normalized_text) < 3:
            continue
        if _is_fatiha_like_segment(normalized_text):
            continue
        if _is_non_recitation_segment(normalized_text):
            continue

        midpoint = (float(segment.start) + float(segment.end)) / 2.0
        constrained_min, constrained_max = _constraint_range_for_time(midpoint, segment_constraints)
        reanchor_min = _min_index_from_reanchors(midpoint, reanchor_schedule)
        pre_anchor_max = _max_index_before_next_reanchor(midpoint, reanchor_schedule)
        pool = _candidate_pool_for_segment(
            normalized_text=normalized_text,
            token_index=token_index,
            forced_start_index=forced_start_index,
            constrained_min=constrained_min,
            constrained_max=constrained_max,
            pre_anchor_max=pre_anchor_max,
            reanchor_min=reanchor_min,
            corpus_size=corpus_size,
        )
        if not pool:
            continue

        rows: list[SegmentCandidate] = []
        for corpus_index in pool:
            entry = corpus_entries[corpus_index]
            score, overlap = _score_segment_against_entry(normalized_text, entry)
            has_anchor = _has_anchor_token_hit(entry, normalized_text)
            if score < float(min_score - 14):
                continue
            if not has_anchor and overlap < max(0.08, float(min_overlap) * 0.55):
                continue
            adjusted = float(score) + (6.0 if has_anchor else 0.0) + (float(overlap) * 18.0)
            rows.append(
                SegmentCandidate(
                    segment_index=segment_index,
                    corpus_index=corpus_index,
                    start_time=float(segment.start),
                    end_time=float(segment.end),
                    normalized_text=normalized_text,
                    score=float(score),
                    overlap=float(overlap),
                    has_anchor=has_anchor,
                    adjusted_score=adjusted,
                )
            )

        if not rows:
            continue
        rows.sort(
            key=lambda row: (
                row.adjusted_score,
                row.score,
                row.overlap,
            ),
            reverse=True,
        )
        per_segment[segment_index] = rows[: max(1, int(top_k_per_segment))]
    return per_segment


def _transition_score(delta_index: int, prev_time: float, curr_time: float) -> float:
    if delta_index < 0:
        return -50.0
    if delta_index == 0:
        base = -1.8
    elif delta_index <= 3:
        base = 0.6 - (0.08 * float(delta_index - 1))
    elif delta_index <= 12:
        base = -0.20 * float(delta_index - 3)
    elif delta_index <= 40:
        base = -2.2 - (0.30 * float(delta_index - 12))
    else:
        base = -10.6 - (0.45 * float(delta_index - 40))

    dt = float(curr_time - prev_time)
    if dt <= 0:
        return base - 1.5
    if delta_index > 0:
        sec_per_ayah = dt / float(delta_index)
        if sec_per_ayah < 1.0:
            base -= 1.1
        elif sec_per_ayah > 130.0:
            base -= 1.4
    return base


def _decode_monotonic_path(
    per_segment_candidates: list[list[SegmentCandidate]],
    *,
    forced_start_index: int | None,
    beam_width: int,
    skip_penalty: float = 0.08,
) -> list[SegmentCandidate]:
    initial_index = int(forced_start_index - 1) if forced_start_index is not None else -1
    beam: list[BeamState] = [
        BeamState(
            score=0.0,
            last_index=initial_index,
            last_time=-1.0,
            emissions=0,
            node=None,
        )
    ]

    for segment_candidates in per_segment_candidates:
        if not segment_candidates:
            beam = [
                BeamState(
                    score=state.score - skip_penalty,
                    last_index=state.last_index,
                    last_time=state.last_time,
                    emissions=state.emissions,
                    node=state.node,
                )
                for state in beam
            ]
            beam.sort(key=lambda state: (state.score, state.emissions), reverse=True)
            beam = beam[: max(8, int(beam_width))]
            continue

        expanded: list[BeamState] = []
        for state in beam:
            expanded.append(
                BeamState(
                    score=state.score - skip_penalty,
                    last_index=state.last_index,
                    last_time=state.last_time,
                    emissions=state.emissions,
                    node=state.node,
                )
            )
            for candidate in segment_candidates:
                if candidate.corpus_index < state.last_index:
                    continue
                if state.last_index >= 0:
                    trans = _transition_score(
                        delta_index=int(candidate.corpus_index - state.last_index),
                        prev_time=state.last_time if state.last_time >= 0 else candidate.start_time,
                        curr_time=candidate.start_time,
                    )
                else:
                    trans = 0.0
                local = (candidate.adjusted_score / 18.0) + (0.18 if candidate.has_anchor else 0.0)
                expanded.append(
                    BeamState(
                        score=float(state.score + local + trans),
                        last_index=int(candidate.corpus_index),
                        last_time=float(candidate.start_time),
                        emissions=int(state.emissions + 1),
                        node=BeamNode(candidate=candidate, prev=state.node),
                    )
                )

        expanded.sort(key=lambda state: (state.score, state.emissions), reverse=True)
        pruned: list[BeamState] = []
        seen: set[tuple[int, int, int]] = set()
        for state in expanded:
            time_bucket = int(round(state.last_time / 6.0)) if state.last_time >= 0 else -1
            key = (state.last_index, state.emissions, time_bucket)
            if key in seen:
                continue
            seen.add(key)
            pruned.append(state)
            if len(pruned) >= max(8, int(beam_width)):
                break
        beam = pruned
        if not beam:
            beam = [
                BeamState(
                    score=0.0,
                    last_index=initial_index,
                    last_time=-1.0,
                    emissions=0,
                    node=None,
                )
            ]

    best = max(beam, key=lambda state: (state.score, state.emissions))
    ordered: list[SegmentCandidate] = []
    node = best.node
    while node is not None:
        if node.candidate is not None:
            ordered.append(node.candidate)
        node = node.prev
    ordered.reverse()
    return ordered


def _confidence_from_candidate(candidate: SegmentCandidate) -> float:
    base = (0.45 * (candidate.score / 100.0)) + (0.40 * candidate.overlap) + (0.15 if candidate.has_anchor else 0.0)
    return float(max(0.35, min(0.99, base)))


def _to_markers(
    *,
    ordered_candidates: list[SegmentCandidate],
    corpus_entries: list[AyahEntry],
    min_gap_seconds: int,
    min_score: int,
    min_overlap: float,
    min_confidence: float,
) -> list[Marker]:
    if not ordered_candidates:
        return []

    deduped: list[SegmentCandidate] = []
    by_index: dict[int, SegmentCandidate] = {}
    for candidate in ordered_candidates:
        existing = by_index.get(candidate.corpus_index)
        if existing is None or candidate.adjusted_score > existing.adjusted_score:
            by_index[candidate.corpus_index] = candidate

    deduped = sorted(by_index.values(), key=lambda row: (row.start_time, row.corpus_index))

    markers: list[Marker] = []
    last_time: int | None = None
    last_index: int | None = None
    for candidate in deduped:
        entry = corpus_entries[candidate.corpus_index]
        start_time = int(round(candidate.start_time))
        end_time = int(round(candidate.end_time))
        confidence = _confidence_from_candidate(candidate)
        quality = "high"
        if (
            candidate.score < float(min_score)
            or candidate.overlap < float(min_overlap)
            or confidence < float(min_confidence)
        ):
            quality = "ambiguous"

        if last_index is not None and candidate.corpus_index <= last_index:
            continue
        if last_time is not None and start_time <= last_time:
            start_time = last_time + 1
            end_time = max(end_time, start_time)
        if last_time is not None and (start_time - last_time) < int(min_gap_seconds):
            continue

        markers.append(
            Marker(
                time=start_time,
                start_time=start_time,
                end_time=max(start_time, end_time),
                surah=entry.surah,
                surah_number=int(entry.surah_number),
                ayah=int(entry.ayah),
                quality=quality,
                confidence=round(confidence, 3),
                origin="two_stage_sequence",
            )
        )
        last_time = start_time
        last_index = int(candidate.corpus_index)
    return markers


def match_quran_markers_two_stage(
    *,
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list[AyahEntry],
    min_score: int = 78,
    min_gap_seconds: int = 8,
    min_overlap: float = 0.18,
    min_confidence: float = 0.62,
    forced_start_index: int | None = None,
    reanchor_points: list[tuple[int, int, int]] | None = None,
    segment_constraints: list[tuple[float, float, int | None, int | None]] | None = None,
    beam_width: int = 96,
    top_k_per_segment: int = 8,
) -> list[Marker]:
    if not transcript_segments or not corpus_entries:
        return []

    token_index = _build_token_index(corpus_entries)
    reanchor_schedule = _build_reanchor_schedule(reanchor_points, corpus_entries)
    per_segment_candidates = _build_segment_candidates(
        transcript_segments=transcript_segments,
        corpus_entries=corpus_entries,
        token_index=token_index,
        min_score=min_score,
        min_overlap=min_overlap,
        forced_start_index=forced_start_index,
        reanchor_schedule=reanchor_schedule,
        segment_constraints=segment_constraints,
        top_k_per_segment=top_k_per_segment,
    )
    ordered_candidates = _decode_monotonic_path(
        per_segment_candidates,
        forced_start_index=forced_start_index,
        beam_width=beam_width,
    )
    return _to_markers(
        ordered_candidates=ordered_candidates,
        corpus_entries=corpus_entries,
        min_gap_seconds=min_gap_seconds,
        min_score=min_score,
        min_overlap=min_overlap,
        min_confidence=min_confidence,
    )
