from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import soundfile as sf
from rapidfuzz import fuzz

from .audio import prepare_audio_source
from .io import write_json
from .prayers import (
    build_prayer_segments,
    detect_fatiha_starts,
    detect_prayer_starts,
    merge_rakah_starts,
    read_mono_audio,
)
from .quran import (
    STRICT_NORMALIZATION,
    clean_transcript_for_matching,
    enrich_marker_texts,
    get_juz_for_ayah,
    load_asad_translation,
    load_corpus,
    match_quran_markers,
    normalize_arabic,
)
from .reciters import assign_reciters
from .transcribe import transcribe_audio
from .types import Marker, PrayerSegment, TranscriptSegment, TranscriptWord


def _map_reciter_to_markers(markers: list[Marker], prayers: list[PrayerSegment]) -> list[Marker]:
    if not markers or not prayers:
        return markers

    for marker in markers:
        assigned = "Unknown"
        for prayer in prayers:
            if prayer.start <= marker.time < prayer.end:
                assigned = prayer.reciter or "Unknown"
                break
        marker.reciter = assigned

    return markers


def _is_known_reciter(label: str | None) -> bool:
    normalized = (label or "").strip().lower()
    if not normalized:
        return False
    if normalized in {"unknown", "talk"}:
        return False
    return "hasan" in normalized or "samir" in normalized


def _filter_transcript_by_known_reciter(
    transcript_segments: list[TranscriptSegment],
    prayers: list[PrayerSegment],
    edge_padding_seconds: float = 1.5,
    min_keep_ratio: float = 0.2,
    min_keep_segments: int = 80,
) -> tuple[list[TranscriptSegment], dict]:
    if not transcript_segments or not prayers:
        return transcript_segments, {
            "enabled": False,
            "reason": "no_transcript_or_prayers",
            "kept_segments": len(transcript_segments),
            "total_segments": len(transcript_segments),
        }

    windows: list[tuple[float, float]] = []
    for prayer in prayers:
        if not _is_known_reciter(prayer.reciter):
            continue
        start = max(0.0, float(prayer.start) - edge_padding_seconds)
        end = float(prayer.end) + edge_padding_seconds
        if end <= start:
            continue
        windows.append((start, end))

    if not windows:
        return transcript_segments, {
            "enabled": False,
            "reason": "no_known_reciter_windows",
            "kept_segments": len(transcript_segments),
            "total_segments": len(transcript_segments),
        }

    windows.sort(key=lambda item: item[0])
    merged: list[tuple[float, float]] = []
    for start, end in windows:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    kept: list[TranscriptSegment] = []
    window_index = 0
    for segment in transcript_segments:
        midpoint = (float(segment.start) + float(segment.end)) / 2.0
        while window_index < len(merged) and merged[window_index][1] < midpoint:
            window_index += 1
        if window_index >= len(merged):
            break
        start, end = merged[window_index]
        if start <= midpoint <= end:
            kept.append(segment)

    keep_ratio = (len(kept) / len(transcript_segments)) if transcript_segments else 0.0
    if len(kept) < min_keep_segments or keep_ratio < min_keep_ratio:
        return transcript_segments, {
            "enabled": False,
            "reason": "insufficient_kept_coverage",
            "kept_segments": len(kept),
            "total_segments": len(transcript_segments),
            "keep_ratio": round(keep_ratio, 3),
            "windows": len(merged),
        }

    return kept, {
        "enabled": True,
        "reason": "known_reciter_windows",
        "kept_segments": len(kept),
        "total_segments": len(transcript_segments),
        "keep_ratio": round(keep_ratio, 3),
        "windows": len(merged),
    }


def _marker_key(marker: Marker) -> tuple[int, int]:
    return int(marker.surah_number or 0), int(marker.ayah)


def _merge_markers_prefer_strong(markers: list[Marker]) -> list[Marker]:
    chosen: dict[tuple[int, int], Marker] = {}
    for marker in markers:
        key = _marker_key(marker)
        existing = chosen.get(key)
        if existing is None:
            chosen[key] = marker
            continue
        rank_new = _quality_rank(marker.quality)
        rank_old = _quality_rank(existing.quality)
        conf_new = float(marker.confidence or 0.0)
        conf_old = float(existing.confidence or 0.0)
        if rank_new > rank_old:
            chosen[key] = marker
        elif rank_new == rank_old and conf_new > conf_old + 0.02:
            chosen[key] = marker
        elif rank_new == rank_old and abs(conf_new - conf_old) <= 0.02 and int(marker.time) < int(existing.time):
            chosen[key] = marker
    return sorted(chosen.values(), key=lambda item: (int(item.time), int(item.surah_number or 0), int(item.ayah)))


def _markers_to_reanchors(markers: list[Marker]) -> list[tuple[int, int, int]]:
    points: list[tuple[int, int, int]] = []
    for marker in markers:
        if marker.surah_number is None:
            continue
        quality = (marker.quality or "").strip().lower()
        confidence = float(marker.confidence or 0.0)
        if quality in {"high", "manual"} or (quality == "ambiguous" and confidence >= 0.66):
            points.append((int(marker.start_time or marker.time), int(marker.surah_number), int(marker.ayah)))
    points.sort(key=lambda item: item[0])
    return points


def _marker_set_score(markers: list[Marker]) -> float:
    quality_points = {"manual": 4.0, "high": 3.0, "ambiguous": 2.0, "inferred": 1.0}
    score = 0.0
    inferred_run = 0
    longest_inferred = 0
    ordered = sorted(markers, key=lambda item: (int(item.surah_number or 0), int(item.ayah)))
    for marker in ordered:
        quality = str(marker.quality or "").strip().lower()
        score += quality_points.get(quality, 0.0)
        if quality == "inferred":
            inferred_run += 1
            if inferred_run > longest_inferred:
                longest_inferred = inferred_run
        else:
            inferred_run = 0
    score += min(50.0, len(markers) * 0.2)
    score -= min(40.0, float(longest_inferred) * 0.6)
    return score


def _build_matching_blocks(
    transcript_segments: list[TranscriptSegment],
    prayers: list[PrayerSegment],
    total_seconds: int,
    edge_padding_seconds: float = 2.0,
) -> list[dict]:
    if not transcript_segments:
        return []
    if not prayers:
        return [
            {"label": "full", "start": 0.0, "end": float(total_seconds), "segments": list(transcript_segments)},
        ]

    blocks: list[dict] = []
    for prayer in prayers:
        span = float(prayer.end) - float(prayer.start)
        if span < 45.0:
            continue
        start = max(0.0, float(prayer.start) - edge_padding_seconds)
        end = min(float(total_seconds), float(prayer.end) + edge_padding_seconds)
        if end <= start:
            continue
        block_segments = [
            segment
            for segment in transcript_segments
            if not (float(segment.end) < start or float(segment.start) > end)
        ]
        if not block_segments:
            continue
        blocks.append(
            {
                "label": str(prayer.reciter or "Unknown"),
                "start": start,
                "end": end,
                "segments": block_segments,
            }
        )

    if not blocks:
        return [
            {"label": "full", "start": 0.0, "end": float(total_seconds), "segments": list(transcript_segments)},
        ]

    # Merge overlapping blocks while preserving dominant reciter label where possible.
    blocks.sort(key=lambda item: float(item["start"]))
    merged: list[dict] = []
    for block in blocks:
        if not merged or float(block["start"]) > float(merged[-1]["end"]):
            merged.append(block)
            continue
        merged[-1]["end"] = max(float(merged[-1]["end"]), float(block["end"]))
        merged[-1]["segments"] = sorted(
            {id(seg): seg for seg in list(merged[-1]["segments"]) + list(block["segments"])}.values(),
            key=lambda seg: float(seg.start),
        )

    # If everything collapsed into one broad block, split again by long transcript gaps.
    if len(merged) == 1:
        ordered_segments = sorted(transcript_segments, key=lambda seg: float(seg.start))
        split_points: list[int] = []
        for idx in range(1, len(ordered_segments)):
            gap = float(ordered_segments[idx].start) - float(ordered_segments[idx - 1].end)
            if gap >= 120.0:
                split_points.append(idx)

        if split_points:
            ranges: list[tuple[int, int]] = []
            left = 0
            for split_index in split_points:
                ranges.append((left, split_index))
                left = split_index
            ranges.append((left, len(ordered_segments)))

            gap_blocks: list[dict] = []
            for block_idx, (left_idx, right_idx) in enumerate(ranges):
                part_segments = ordered_segments[left_idx:right_idx]
                if not part_segments:
                    continue
                gap_blocks.append(
                    {
                        "label": f"gap-block-{block_idx + 1}",
                        "start": float(part_segments[0].start),
                        "end": float(part_segments[-1].end),
                        "segments": part_segments,
                    }
                )
            if gap_blocks:
                return gap_blocks
    return merged


def _run_two_pass_match(
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list,
    min_score: int,
    min_gap_seconds: int,
    min_overlap: float,
    min_confidence: float,
    require_weak_support_for_inferred: bool,
    forced_start_index: int | None,
    precomputed_reset_times: list[float],
    reanchor_points: list[tuple[int, int, int]],
    resume_chain_reanchors: list[tuple[int, int, int]] | None = None,
    debug_trace: list[dict] | None = None,
) -> tuple[list[Marker], dict]:
    single_markers = match_quran_markers(
        transcript_segments,
        corpus_entries,
        min_score=min_score,
        min_gap_seconds=min_gap_seconds,
        min_overlap=min_overlap,
        min_confidence=min_confidence,
        require_weak_support_for_inferred=require_weak_support_for_inferred,
        forced_start_index=forced_start_index,
        precomputed_reset_times=precomputed_reset_times,
        reanchor_points=reanchor_points,
        resume_chain_reanchors=resume_chain_reanchors,
        debug_trace=debug_trace,
    )
    strict_debug: list[dict] = [] if debug_trace is not None else None  # type: ignore[assignment]
    strict_markers = match_quran_markers(
        transcript_segments,
        corpus_entries,
        min_score=min(95, int(min_score) + 4),
        min_gap_seconds=min_gap_seconds,
        min_overlap=min(0.30, float(min_overlap) + 0.04),
        min_confidence=min(0.84, float(min_confidence) + 0.10),
        require_weak_support_for_inferred=True,
        forced_start_index=forced_start_index,
        precomputed_reset_times=precomputed_reset_times,
        reanchor_points=reanchor_points,
        resume_chain_reanchors=resume_chain_reanchors,
        debug_trace=strict_debug,
    )
    strict_anchors = _markers_to_reanchors(strict_markers)
    combined_reanchors = sorted(
        list(reanchor_points) + strict_anchors,
        key=lambda item: item[0],
    )

    main_debug: list[dict] = [] if debug_trace is not None else None  # type: ignore[assignment]
    main_markers = match_quran_markers(
        transcript_segments,
        corpus_entries,
        min_score=min_score,
        min_gap_seconds=min_gap_seconds,
        min_overlap=min_overlap,
        min_confidence=min_confidence,
        require_weak_support_for_inferred=require_weak_support_for_inferred,
        forced_start_index=forced_start_index,
        precomputed_reset_times=precomputed_reset_times,
        reanchor_points=combined_reanchors,
        resume_chain_reanchors=resume_chain_reanchors,
        debug_trace=main_debug,
    )
    merged = _merge_markers_prefer_strong(strict_markers + main_markers)
    options = [
        ("single", single_markers),
        ("strict", strict_markers),
        ("main", main_markers),
        ("merged", merged),
    ]
    selected_label, selected_markers = max(options, key=lambda item: _marker_set_score(item[1]))

    if debug_trace is not None:
        debug_trace.extend(strict_debug or [])
        debug_trace.extend(main_debug or [])
    return selected_markers, {
        "selected": selected_label,
        "single_markers": len(single_markers),
        "strict_markers": len(strict_markers),
        "strict_reanchors": len(strict_anchors),
        "main_markers": len(main_markers),
        "merged_markers": len(merged),
    }


def _postcheck_marker_spans(markers: list[Marker]) -> tuple[list[Marker], dict]:
    if len(markers) < 3:
        return markers, {"applied": False, "adjusted": 0}

    ordered = sorted(markers, key=lambda item: (int(item.time), int(item.surah_number or 0), int(item.ayah)))
    adjusted = 0
    for idx in range(1, len(ordered)):
        left = ordered[idx - 1]
        right = ordered[idx]
        if left.surah != right.surah:
            continue
        left_start = int(left.start_time or left.time)
        right_start = int(right.start_time or right.time)
        if int(right.ayah) <= int(left.ayah) and right_start <= left_start:
            right.start_time = left_start + 1
            right.time = right.start_time
            right.end_time = max(int(right.end_time or right.start_time), right.start_time)
            adjusted += 1
    return ordered, {"applied": adjusted > 0, "adjusted": adjusted}


def _quality_rank(value: str | None) -> int:
    quality = (value or "").strip().lower()
    if quality == "manual":
        return 4
    if quality == "high":
        return 3
    if quality == "ambiguous":
        return 2
    if quality == "inferred":
        return 1
    return 0


def _apply_day_final_ayah_override(
    day: int,
    markers: list[Marker],
    overrides_path: Path | None,
    corpus_entries: list,
) -> tuple[list[Marker], dict | None]:
    if not markers or overrides_path is None or not overrides_path.exists():
        return markers, None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return markers, None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return markers, None

    final_surah = str(day_config.get("final_surah", "")).strip()
    final_ayah_raw = day_config.get("final_ayah")
    start_time_raw = day_config.get("start_time")
    final_time_raw = day_config.get("final_time")

    try:
        final_ayah = int(final_ayah_raw) if final_ayah_raw is not None else None
    except (TypeError, ValueError):
        final_ayah = None
    try:
        start_time = int(start_time_raw) if start_time_raw is not None else None
    except (TypeError, ValueError):
        start_time = None
    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None

    if final_ayah is None and final_time is None and start_time is None:
        return markers, None

    final_surah_number: int | None = None
    if final_surah:
        for marker in markers:
            if marker.surah == final_surah and marker.surah_number is not None:
                final_surah_number = int(marker.surah_number)
                break

    def keep(marker: Marker) -> bool:
        if start_time is not None and marker.time < start_time:
            return False
        if final_time is not None and marker.time > final_time:
            return False
        if final_ayah is None:
            return True
        if final_surah:
            if marker.surah_number is not None and final_surah_number is not None:
                if marker.surah_number > final_surah_number:
                    return False
                if marker.surah_number < final_surah_number:
                    return True
            elif marker.surah != final_surah:
                return True
        if final_surah and marker.surah != final_surah:
            return True
        return marker.ayah <= final_ayah

    filtered = [marker for marker in markers if keep(marker)]
    if not filtered:
        return markers, None

    inserted_terminal = False
    inserted_time: int | None = None

    if final_ayah is not None and final_surah:
        has_terminal = any(marker.surah == final_surah and marker.ayah == final_ayah for marker in filtered)
        if not has_terminal:
            same_surah = sorted(
                [marker for marker in filtered if marker.surah == final_surah],
                key=lambda marker: (marker.ayah, marker.time),
            )
            anchor = None
            for marker in same_surah:
                if marker.ayah <= final_ayah:
                    anchor = marker
                else:
                    break

            step_candidates: list[float] = []
            for left, right in zip(same_surah, same_surah[1:]):
                ayah_gap = right.ayah - left.ayah
                time_gap = right.time - left.time
                if ayah_gap <= 0 or time_gap <= 0:
                    continue
                step_candidates.append(time_gap / ayah_gap)

            if step_candidates:
                sorted_steps = sorted(step_candidates)
                step_seconds = sorted_steps[len(sorted_steps) // 2]
            else:
                step_seconds = 18.0

            if final_time is not None:
                terminal_time = final_time
            elif anchor is not None:
                terminal_time = int(round(anchor.time + (max(0, final_ayah - anchor.ayah) * step_seconds)))
            else:
                terminal_time = filtered[-1].time

            if filtered:
                terminal_time = max(terminal_time, filtered[-1].time)

            entry_lookup = {
                (str(entry.surah), int(entry.ayah)): entry
                for entry in corpus_entries
            }
            entry = entry_lookup.get((final_surah, final_ayah))
            surah_number = entry.surah_number if entry is not None else final_surah_number
            if surah_number is None:
                for marker in reversed(filtered):
                    if marker.surah == final_surah and marker.surah_number is not None:
                        surah_number = int(marker.surah_number)
                        break

            filtered.append(
                Marker(
                    time=terminal_time,
                    start_time=terminal_time,
                    end_time=terminal_time,
                    surah=final_surah,
                    surah_number=surah_number,
                    ayah=final_ayah,
                    juz=get_juz_for_ayah(surah_number or 1, final_ayah),
                    quality="manual",
                    confidence=1.0,
                )
            )
            filtered.sort(key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))
            inserted_terminal = True
            inserted_time = terminal_time

    info = {
        "path": str(overrides_path),
        "final_surah": final_surah or None,
        "final_ayah": final_ayah,
        "start_time": start_time,
        "final_time": final_time,
        "markers_before": len(markers),
        "markers_after": len(filtered),
        "inserted_terminal": inserted_terminal,
        "inserted_terminal_time": inserted_time,
    }
    return filtered, info


def _fill_override_surah_range(
    day: int,
    markers: list[Marker],
    overrides_path: Path | None,
    corpus_entries: list,
) -> tuple[list[Marker], dict | None]:
    if not markers or overrides_path is None or not overrides_path.exists():
        return markers, None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return markers, None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return markers, None

    final_surah = str(day_config.get("final_surah", "")).strip()
    final_ayah_raw = day_config.get("final_ayah")
    final_time_raw = day_config.get("final_time")

    if not final_surah:
        return markers, None
    try:
        final_ayah = int(final_ayah_raw)
    except (TypeError, ValueError):
        return markers, None
    if final_ayah <= 0:
        return markers, None
    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None

    target_surah_number: int | None = None
    for entry in corpus_entries:
        if str(entry.surah) == final_surah:
            target_surah_number = int(entry.surah_number)
            break
    if target_surah_number is None:
        return markers, None

    relevant = [marker for marker in markers if marker.surah_number == target_surah_number and marker.ayah <= final_ayah]
    if not relevant:
        return markers, None

    best_by_ayah: dict[int, Marker] = {}
    for marker in relevant:
        existing = best_by_ayah.get(marker.ayah)
        if existing is None:
            best_by_ayah[marker.ayah] = marker
            continue
        marker_rank = _quality_rank(marker.quality)
        existing_rank = _quality_rank(existing.quality)
        marker_conf = float(marker.confidence or 0.0)
        existing_conf = float(existing.confidence or 0.0)
        if marker_rank > existing_rank:
            best_by_ayah[marker.ayah] = marker
        elif marker_rank == existing_rank and marker_conf > existing_conf:
            best_by_ayah[marker.ayah] = marker
        elif marker_rank == existing_rank and marker_conf == existing_conf and marker.time < existing.time:
            best_by_ayah[marker.ayah] = marker

    existing_ayahs = sorted(best_by_ayah.keys())
    if not existing_ayahs:
        return markers, None

    adjacent_steps: list[int] = []
    for left_ayah, right_ayah in zip(existing_ayahs, existing_ayahs[1:]):
        if right_ayah != left_ayah + 1:
            continue
        left = best_by_ayah[left_ayah]
        right = best_by_ayah[right_ayah]
        gap = int(right.time) - int(left.time)
        if 0 < gap < 240:
            adjacent_steps.append(gap)
    if adjacent_steps:
        adjacent_steps.sort()
        fallback_step = max(6, adjacent_steps[len(adjacent_steps) // 2])
    else:
        fallback_step = 20

    full_timeline = sorted(markers, key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))

    def reciter_for_time(target_time: int) -> str | None:
        chosen: str | None = None
        for item in full_timeline:
            item_time = int(item.start_time or item.time)
            if item_time <= target_time:
                chosen = item.reciter
            else:
                break
        return chosen

    additions: list[Marker] = []
    for ayah in range(1, final_ayah + 1):
        if ayah in best_by_ayah:
            continue

        prev_ayah = ayah - 1
        next_ayah = ayah + 1
        prev_marker: Marker | None = None
        next_marker: Marker | None = None
        while prev_ayah >= 1:
            if prev_ayah in best_by_ayah:
                prev_marker = best_by_ayah[prev_ayah]
                break
            prev_ayah -= 1
        while next_ayah <= final_ayah:
            if next_ayah in best_by_ayah:
                next_marker = best_by_ayah[next_ayah]
                break
            next_ayah += 1

        if prev_marker is not None and next_marker is not None and next_marker.ayah > prev_marker.ayah and next_marker.time > prev_marker.time:
            ratio = (ayah - prev_marker.ayah) / max(1, next_marker.ayah - prev_marker.ayah)
            inferred_time = int(round(prev_marker.time + ((next_marker.time - prev_marker.time) * ratio)))
            inferred_time = max(inferred_time, prev_marker.time + 1)
            inferred_time = min(inferred_time, next_marker.time - 1)
        elif prev_marker is not None:
            inferred_time = int(prev_marker.time + ((ayah - prev_marker.ayah) * fallback_step))
        elif next_marker is not None:
            inferred_time = int(max(0, next_marker.time - ((next_marker.ayah - ayah) * fallback_step)))
        else:
            continue

        if final_time is not None:
            inferred_time = min(inferred_time, final_time)

        marker = Marker(
            time=inferred_time,
            start_time=inferred_time,
            end_time=inferred_time,
            surah=final_surah,
            surah_number=target_surah_number,
            ayah=ayah,
            juz=get_juz_for_ayah(target_surah_number, ayah),
            quality="inferred",
            confidence=0.56,
            reciter=reciter_for_time(inferred_time),
        )
        additions.append(marker)
        best_by_ayah[ayah] = marker
        full_timeline.append(marker)
        full_timeline.sort(key=lambda item: (item.time, item.surah_number or 0, item.ayah))

    previous_tail_added = 0
    if target_surah_number > 1:
        previous_surah_number = target_surah_number - 1
        timeline_with_target = markers + additions
        previous_surah_markers = [
            marker
            for marker in timeline_with_target
            if int(marker.surah_number or 0) == previous_surah_number
        ]
        target_surah_markers = [
            marker
            for marker in timeline_with_target
            if int(marker.surah_number or 0) == target_surah_number
        ]
        previous_total_ayah = 0
        for entry in corpus_entries:
            if int(getattr(entry, "surah_number", 0) or 0) != previous_surah_number:
                continue
            previous_total_ayah = max(previous_total_ayah, int(getattr(entry, "ayah", 0) or 0))

        if previous_surah_markers and target_surah_markers and previous_total_ayah > 0:
            previous_tail = max(previous_surah_markers, key=lambda marker: (int(marker.ayah), int(marker.time)))
            target_start_marker = min(target_surah_markers, key=lambda marker: int(marker.time))
            missing_tail = previous_total_ayah - int(previous_tail.ayah)
            tail_start = int(previous_tail.end_time or previous_tail.time) + 6
            tail_end = int(target_start_marker.start_time or target_start_marker.time) - 6
            if missing_tail > 0 and missing_tail <= 80 and tail_end > tail_start:
                tail_step = (tail_end - tail_start) / float(missing_tail + 1)
                if 2.0 <= tail_step <= 90.0:
                    existing_keys = {
                        (int(marker.surah_number or 0), int(marker.ayah))
                        for marker in timeline_with_target
                    }
                    for offset, ayah in enumerate(
                        range(int(previous_tail.ayah) + 1, previous_total_ayah + 1),
                        start=1,
                    ):
                        key = (previous_surah_number, ayah)
                        if key in existing_keys:
                            continue
                        inferred_time = int(round(tail_start + (tail_step * offset)))
                        inferred_time = max(tail_start, min(tail_end, inferred_time))
                        inferred_marker = Marker(
                            time=inferred_time,
                            start_time=inferred_time,
                            end_time=inferred_time,
                            surah=previous_tail.surah,
                            surah_number=previous_surah_number,
                            ayah=ayah,
                            juz=get_juz_for_ayah(previous_surah_number, ayah),
                            quality="inferred",
                            confidence=0.56,
                            reciter=previous_tail.reciter,
                        )
                        additions.append(inferred_marker)
                        full_timeline.append(inferred_marker)
                        existing_keys.add(key)
                        previous_tail_added += 1

    if not additions:
        return markers, {
            "surah": final_surah,
            "surah_number": target_surah_number,
            "target_final_ayah": final_ayah,
            "added_markers": 0,
            "fallback_step_seconds": fallback_step,
            "previous_surah_tail_added": 0,
        }

    merged = markers + additions
    merged.sort(key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))
    info = {
        "surah": final_surah,
        "surah_number": target_surah_number,
        "target_final_ayah": final_ayah,
        "added_markers": len(additions),
        "fallback_step_seconds": fallback_step,
        "previous_surah_tail_added": previous_tail_added,
    }
    return merged, info


def _apply_marker_time_overrides(
    day: int,
    part: int | None,
    markers: list[Marker],
    overrides_path: Path | None,
    corpus_entries: list | None = None,
) -> tuple[list[Marker], list[dict]]:
    if not markers or overrides_path is None or not overrides_path.exists():
        return markers, []

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return markers, []

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return markers, []

    marker_overrides = day_config.get("marker_overrides", [])
    if not isinstance(marker_overrides, list) or not marker_overrides:
        return markers, []

    applied: list[dict] = []
    entry_lookup: dict[tuple[int, int], object] = {}
    for entry in corpus_entries or []:
        surah_number = getattr(entry, "surah_number", None)
        ayah = getattr(entry, "ayah", None)
        if surah_number is None or ayah is None:
            continue
        entry_lookup[(int(surah_number), int(ayah))] = entry

    for item in marker_overrides:
        if not isinstance(item, dict):
            continue

        item_part = item.get("part")
        if item_part is not None:
            try:
                if int(item_part) != int(part or 0):
                    continue
            except (TypeError, ValueError):
                continue

        surah_number = item.get("surah_number")
        ayah = item.get("ayah")
        start_time = item.get("start_time")
        end_time = item.get("end_time")
        if surah_number is None or ayah is None or start_time is None:
            continue

        try:
            target_surah_number = int(surah_number)
            target_ayah = int(ayah)
            target_start_time = int(start_time)
            target_end_time = int(end_time) if end_time is not None else int(start_time)
        except (TypeError, ValueError):
            continue

        found = False
        for marker in markers:
            if marker.surah_number == target_surah_number and marker.ayah == target_ayah:
                marker.start_time = target_start_time
                marker.time = target_start_time
                marker.end_time = max(target_start_time, target_end_time)
                marker.quality = "manual"
                marker.confidence = 1.0
                found = True
                applied.append(
                    {
                        "surah_number": target_surah_number,
                        "ayah": target_ayah,
                        "part": part,
                        "start_time": target_start_time,
                        "end_time": max(target_start_time, target_end_time),
                    }
                )
                break

        if found:
            continue

        entry = entry_lookup.get((target_surah_number, target_ayah))
        surah_name = str(getattr(entry, "surah", "")) if entry is not None else ""
        markers.append(
            Marker(
                time=target_start_time,
                start_time=target_start_time,
                end_time=max(target_start_time, target_end_time),
                surah=surah_name,
                surah_number=target_surah_number,
                ayah=target_ayah,
                juz=get_juz_for_ayah(target_surah_number, target_ayah),
                quality="manual",
                confidence=1.0,
            )
        )
        applied.append(
            {
                "surah_number": target_surah_number,
                "ayah": target_ayah,
                "part": part,
                "start_time": target_start_time,
                "end_time": max(target_start_time, target_end_time),
                "inserted": True,
            }
        )

    if applied:
        markers.sort(key=lambda marker: (marker.time, marker.surah_number or 0, marker.ayah))
    return markers, applied


def _resolve_day_start_override(
    day: int,
    overrides_path: Path | None,
) -> tuple[int, int] | None:
    if overrides_path is None or not overrides_path.exists():
        return None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return None

    surah_raw = day_config.get("start_surah_number")
    ayah_raw = day_config.get("start_ayah")
    if surah_raw is None or ayah_raw is None:
        return None

    try:
        surah_number = int(surah_raw)
        ayah = int(ayah_raw)
    except (TypeError, ValueError):
        return None
    if surah_number <= 0 or ayah <= 0:
        return None
    return surah_number, ayah


def _resolve_day_final_time_override(
    day: int,
    overrides_path: Path | None,
) -> int | None:
    if overrides_path is None or not overrides_path.exists():
        return None

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return None

    try:
        final_time = int(day_config.get("final_time"))
    except (TypeError, ValueError):
        return None
    return final_time if final_time > 0 else None


def _resolve_day_structured_plan(
    day: int,
    overrides_path: Path | None,
) -> dict:
    empty = {"start": None, "windows": [], "reanchors": [], "resume_anchors": []}
    if overrides_path is None or not overrides_path.exists():
        return empty

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return empty

    start_cfg = day_config.get("taraweeh_start")
    breaks_cfg = day_config.get("breaks", [])
    final_time_raw = day_config.get("final_time")

    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None

    start = None
    reanchors: list[tuple[int, int, int]] = []
    start_time: int | None = None
    if isinstance(start_cfg, dict):
        try:
            start_time = int(start_cfg.get("time"))
            start_surah = int(start_cfg.get("surah_number"))
            start_ayah = int(start_cfg.get("ayah"))
        except (TypeError, ValueError):
            start_time = None
        else:
            if start_time >= 0 and start_surah > 0 and start_ayah > 0:
                start = (start_surah, start_ayah)
                reanchors.append((start_time, start_surah, start_ayah))

    parsed_breaks: list[dict] = []
    resume_anchors: list[tuple[int, int, int]] = []
    if isinstance(breaks_cfg, list):
        for item in breaks_cfg:
            if not isinstance(item, dict):
                continue
            try:
                break_start = int(item.get("start"))
                break_end = int(item.get("end"))
            except (TypeError, ValueError):
                continue
            if break_end <= break_start:
                continue
            resume_surah = item.get("resume_surah_number")
            resume_ayah = item.get("resume_ayah")
            resume_at = item.get("resume_time", break_end)
            parsed_item = {"start": break_start, "end": break_end}
            try:
                resume_surah_i = int(resume_surah) if resume_surah is not None else None
                resume_ayah_i = int(resume_ayah) if resume_ayah is not None else None
                resume_time_i = int(resume_at)
            except (TypeError, ValueError):
                resume_surah_i = None
                resume_ayah_i = None
                resume_time_i = break_end
            if resume_surah_i and resume_ayah_i and resume_surah_i > 0 and resume_ayah_i > 0:
                parsed_item["resume_surah_number"] = resume_surah_i
                parsed_item["resume_ayah"] = resume_ayah_i
                parsed_item["resume_time"] = resume_time_i
                reanchors.append((resume_time_i, resume_surah_i, resume_ayah_i))
                resume_anchors.append((resume_time_i, resume_surah_i, resume_ayah_i))
            parsed_breaks.append(parsed_item)

    windows: list[dict] = []
    if start_time is not None and start_time >= 0:
        cursor = start_time
        for idx, item in enumerate(sorted(parsed_breaks, key=lambda value: int(value["start"]))):
            left = int(item["start"])
            right = int(item["end"])
            if left > cursor:
                windows.append({"start": cursor, "end": left + 20, "label": f"pre-break-{idx + 1}"})
            cursor = max(cursor, right)
        if final_time is not None and final_time > cursor:
            windows.append({"start": max(0, cursor - 20), "end": final_time, "label": "final"})
        elif final_time is None:
            windows.append({"start": max(0, cursor - 20), "end": 999999, "label": "open"})

    reanchors = sorted({(int(t), int(s), int(a)) for t, s, a in reanchors if int(t) >= 0 and int(s) > 0 and int(a) > 0})
    resume_anchors = sorted({(int(t), int(s), int(a)) for t, s, a in resume_anchors if int(t) >= 0 and int(s) > 0 and int(a) > 0})
    return {"start": start, "windows": windows, "reanchors": reanchors, "resume_anchors": resume_anchors}


def _filter_transcript_by_windows(
    transcript_segments: list[TranscriptSegment],
    windows: list[dict],
) -> tuple[list[TranscriptSegment], dict]:
    if not transcript_segments or not windows:
        return transcript_segments, {
            "enabled": False,
            "reason": "no_windows",
            "windows": 0,
            "kept_segments": len(transcript_segments),
            "total_segments": len(transcript_segments),
        }

    normalized_windows: list[tuple[float, float]] = []
    for item in windows:
        try:
            start = float(item.get("start"))
            end = float(item.get("end"))
        except (TypeError, ValueError, AttributeError):
            continue
        if end <= start:
            continue
        normalized_windows.append((start, end))
    if not normalized_windows:
        return transcript_segments, {
            "enabled": False,
            "reason": "invalid_windows",
            "windows": 0,
            "kept_segments": len(transcript_segments),
            "total_segments": len(transcript_segments),
        }

    kept: list[TranscriptSegment] = []
    for segment in transcript_segments:
        seg_start = float(segment.start)
        seg_end = float(segment.end)
        if any(not (seg_end < left or seg_start > right) for left, right in normalized_windows):
            kept.append(segment)

    return kept, {
        "enabled": True,
        "reason": "structured_windows",
        "windows": len(normalized_windows),
        "kept_segments": len(kept),
        "total_segments": len(transcript_segments),
    }


def _build_matching_blocks_from_windows(
    transcript_segments: list[TranscriptSegment],
    windows: list[dict],
) -> list[dict]:
    blocks: list[dict] = []
    if not transcript_segments or not windows:
        return blocks

    for idx, item in enumerate(windows):
        try:
            start = float(item.get("start"))
            end = float(item.get("end"))
        except (TypeError, ValueError, AttributeError):
            continue
        if end <= start:
            continue
        block_segments = [
            segment
            for segment in transcript_segments
            if not (float(segment.end) < start or float(segment.start) > end)
        ]
        if not block_segments:
            continue
        blocks.append(
            {
                "label": str(item.get("label") or f"window-{idx + 1}"),
                "start": start,
                "end": end,
                "segments": block_segments,
            }
        )
    return blocks


def _build_quran_lexicon_index(corpus_entries: list) -> dict[tuple[str, int], set[str]]:
    index: dict[tuple[str, int], set[str]] = {}
    for entry in corpus_entries:
        normalized = normalize_arabic(str(getattr(entry, "text", "")), strict=False)
        if not normalized:
            continue
        for token in [item for item in normalized.split() if len(item) >= 3]:
            key_exact = (token[0], len(token))
            key_wild = ("*", len(token))
            index.setdefault(key_exact, set()).add(token)
            index.setdefault(key_wild, set()).add(token)
    return index


def _best_quran_token(token: str, lexicon_index: dict[tuple[str, int], set[str]]) -> str | None:
    if len(token) < 3:
        return None
    first = token[0]
    length = len(token)
    candidates: set[str] = set()
    for delta in (-1, 0, 1):
        candidates.update(lexicon_index.get((first, length + delta), set()))
    if not candidates:
        for delta in (-1, 0, 1):
            candidates.update(lexicon_index.get(("*", length + delta), set()))
    if not candidates:
        return None

    best_token: str | None = None
    best_score = -1.0
    for candidate in candidates:
        score = max(float(fuzz.ratio(token, candidate)), float(fuzz.partial_ratio(token, candidate)))
        if score > best_score:
            best_score = score
            best_token = candidate

    threshold = 88.0 if len(token) <= 4 else 84.0
    if best_token is None or best_score < threshold:
        return None
    return best_token


def _correct_transcript_with_quran_lexicon(
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list,
) -> tuple[list[TranscriptSegment], dict]:
    if not transcript_segments or not corpus_entries:
        return transcript_segments, {"enabled": False, "changed_words": 0, "total_words": 0}

    lexicon_index = _build_quran_lexicon_index(corpus_entries)
    if not lexicon_index:
        return transcript_segments, {"enabled": False, "changed_words": 0, "total_words": 0}

    changed_words = 0
    total_words = 0
    corrected_segments: list[TranscriptSegment] = []

    for segment in transcript_segments:
        words = list(segment.words or [])
        if not words:
            corrected_segments.append(segment)
            continue

        new_words: list[TranscriptWord] = []
        segment_changed = False
        for word in words:
            original = str(word.text or "").strip()
            normalized = normalize_arabic(original, strict=False)
            replacement = None
            if normalized and len(normalized.split()) == 1 and len(normalized) >= 3:
                total_words += 1
                replacement = _best_quran_token(normalized, lexicon_index)
            if replacement and replacement != normalized:
                segment_changed = True
                changed_words += 1
                new_words.append(
                    TranscriptWord(
                        start=float(word.start),
                        end=float(word.end),
                        text=replacement,
                    )
                )
            else:
                new_words.append(
                    TranscriptWord(
                        start=float(word.start),
                        end=float(word.end),
                        text=original,
                    )
                )

        if segment_changed:
            new_text = " ".join(item.text for item in new_words if str(item.text).strip())
            corrected_segments.append(
                TranscriptSegment(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=new_text or segment.text,
                    words=new_words,
                )
            )
        else:
            corrected_segments.append(segment)

    return corrected_segments, {
        "enabled": True,
        "changed_words": changed_words,
        "total_words": total_words,
        "change_ratio": round((changed_words / max(1, total_words)), 4),
    }


def _merge_ensemble_segments(runs: list[list[TranscriptSegment]]) -> list[TranscriptSegment]:
    if not runs:
        return []
    if len(runs) == 1:
        return runs[0]

    chosen: dict[int, TranscriptSegment] = {}

    def segment_score(segment: TranscriptSegment) -> float:
        normalized = normalize_arabic(str(segment.text or ""), strict=False)
        token_count = len([token for token in normalized.split() if token])
        arabic_chars = sum(1 for ch in str(segment.text or "") if "\u0600" <= ch <= "\u06FF")
        return (token_count * 2.0) + (arabic_chars * 0.05)

    for run in runs:
        for segment in run:
            bucket = int(float(segment.start) / 1.2)
            current = chosen.get(bucket)
            if current is None or segment_score(segment) > segment_score(current):
                chosen[bucket] = segment

    return sorted(chosen.values(), key=lambda item: float(item.start))


def _transcribe_block_ensemble(
    *,
    audio,
    sample_rate: int,
    block_start: float,
    block_end: float,
    cache_dir: Path,
    day: int,
    block_index: int,
) -> list[TranscriptSegment]:
    start_sample = max(0, int(block_start * sample_rate))
    end_sample = min(len(audio), int(block_end * sample_rate))
    if end_sample <= start_sample:
        return []

    block_audio = audio[start_sample:end_sample]
    if len(block_audio) < sample_rate * 10:
        return []

    ensemble_dir = cache_dir / "ensemble"
    ensemble_dir.mkdir(parents=True, exist_ok=True)
    block_wav_path = ensemble_dir / f"day-{day}-block-{block_index + 1}-{int(block_start)}-{int(block_end)}.wav"
    sf.write(block_wav_path, block_audio, sample_rate)

    runs: list[list[TranscriptSegment]] = []
    for model_size in ["small", "medium"]:
        try:
            segments = transcribe_audio(block_wav_path, model_size=model_size, vad_filter=False)
        except Exception:
            continue
        shifted: list[TranscriptSegment] = []
        for segment in segments:
            shifted_words = [
                TranscriptWord(
                    start=float(word.start) + float(block_start),
                    end=float(word.end) + float(block_start),
                    text=str(word.text),
                )
                for word in (segment.words or [])
            ]
            shifted.append(
                TranscriptSegment(
                    start=float(segment.start) + float(block_start),
                    end=float(segment.end) + float(block_start),
                    text=str(segment.text),
                    words=shifted_words,
                )
            )
        if shifted:
            runs.append(shifted)
    return _merge_ensemble_segments(runs)


def _transcribe_window_with_vad_threshold(
    *,
    audio,
    sample_rate: int,
    window_start: float,
    window_end: float,
    cache_dir: Path,
    cache_key: str,
    whisper_model: str,
    threshold: float,
) -> list[TranscriptSegment]:
    start_sample = max(0, int(float(window_start) * sample_rate))
    end_sample = min(len(audio), int(float(window_end) * sample_rate))
    if end_sample <= start_sample:
        return []

    window_audio = audio[start_sample:end_sample]
    if len(window_audio) < sample_rate * 8:
        return []

    tuned_dir = cache_dir / "vad_tuned"
    tuned_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{cache_key}-th-{str(round(float(threshold), 3)).replace('.', '_')}"
    wav_path = tuned_dir / f"{base_name}.wav"
    json_path = tuned_dir / f"{base_name}.json"

    if json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            rows = payload.get("segments", [])
            restored: list[TranscriptSegment] = []
            for row in rows:
                restored.append(
                    TranscriptSegment(
                        start=float(row.get("start", 0.0)),
                        end=float(row.get("end", 0.0)),
                        text=str(row.get("text", "")),
                        words=[
                            TranscriptWord(
                                start=float(word.get("start", 0.0)),
                                end=float(word.get("end", 0.0)),
                                text=str(word.get("text", "")),
                            )
                            for word in row.get("words", [])
                            if str(word.get("text", "")).strip()
                        ],
                    )
                )
            if restored:
                return restored
        except Exception:
            pass

    if not wav_path.exists():
        sf.write(wav_path, window_audio, sample_rate)

    segments = transcribe_audio(
        wav_path,
        model_size=whisper_model,
        vad_filter=True,
        vad_parameters={
            "threshold": float(threshold),
            "min_silence_duration_ms": 700,
            "speech_pad_ms": 400,
        },
    )
    shifted: list[TranscriptSegment] = []
    for segment in segments:
        shifted_words = [
            TranscriptWord(
                start=float(word.start) + float(window_start),
                end=float(word.end) + float(window_start),
                text=str(word.text),
            )
            for word in (segment.words or [])
        ]
        shifted.append(
            TranscriptSegment(
                start=float(segment.start) + float(window_start),
                end=float(segment.end) + float(window_start),
                text=str(segment.text),
                words=shifted_words,
            )
        )

    if shifted:
        write_json(
            json_path,
            {
                "window_start": float(window_start),
                "window_end": float(window_end),
                "threshold": float(threshold),
                "segments": [asdict(item) for item in shifted],
            },
        )
    return shifted


def _score_window_transcript_against_anchor(
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list,
    anchor_surah_number: int,
    anchor_ayah: int,
    lookahead_ayahs: int = 60,
) -> dict:
    corpus_index: dict[tuple[int, int], int] = {
        (int(entry.surah_number), int(entry.ayah)): idx
        for idx, entry in enumerate(corpus_entries)
    }
    start_idx = corpus_index.get((int(anchor_surah_number), int(anchor_ayah)))
    if start_idx is None:
        return {"segments": 0, "avg_score": 0.0, "pct_ge75": 0.0, "pct_ge80": 0.0}

    refs: list[str] = []
    for entry in corpus_entries[start_idx : min(len(corpus_entries), start_idx + max(12, lookahead_ayahs))]:
        refs.append(normalize_arabic(str(entry.text), strict=False))
    refs = [item for item in refs if item]
    if not refs:
        return {"segments": 0, "avg_score": 0.0, "pct_ge75": 0.0, "pct_ge80": 0.0}

    scores: list[float] = []
    ge75 = 0
    ge80 = 0
    for segment in transcript_segments:
        normalized = normalize_arabic(str(segment.text or ""), strict=False)
        if not normalized:
            continue
        best = max(float(fuzz.token_set_ratio(normalized, ref)) for ref in refs)
        scores.append(best)
        ge75 += int(best >= 75.0)
        ge80 += int(best >= 80.0)

    n = len(scores)
    if n == 0:
        return {"segments": 0, "avg_score": 0.0, "pct_ge75": 0.0, "pct_ge80": 0.0}
    return {
        "segments": n,
        "avg_score": round(sum(scores) / n, 2),
        "pct_ge75": round((100.0 * ge75) / n, 1),
        "pct_ge80": round((100.0 * ge80) / n, 1),
    }


def _retune_resume_windows_transcript(
    *,
    transcript_segments: list[TranscriptSegment],
    audio,
    sample_rate: int,
    cache_dir: Path,
    day: int,
    part: int | None,
    whisper_model: str,
    corpus_entries: list,
    windows: list[dict],
    resume_anchors: list[tuple[int, int, int]],
    threshold_candidates: list[float] | None = None,
    calibration_seconds: int = 300,
    fixed_threshold: float | None = None,
    tune_once: bool = True,
) -> tuple[list[TranscriptSegment], dict]:
    if not transcript_segments or not windows or not resume_anchors:
        return transcript_segments, {"enabled": False, "reason": "no_windows_or_resume_anchors", "windows": []}

    candidates = list(threshold_candidates or [0.12, 0.15, 0.18, 0.20, 0.28])
    if not candidates:
        return transcript_segments, {"enabled": False, "reason": "no_threshold_candidates", "windows": []}

    updated_segments = list(transcript_segments)
    window_reports: list[dict] = []
    processed_windows: set[int] = set()
    global_chosen_threshold: float | None = None
    part_suffix = f"-part-{part}" if part is not None and part > 0 else ""
    corpus_index_by_key: dict[tuple[int, int], int] = {
        (int(entry.surah_number), int(entry.ayah)): idx
        for idx, entry in enumerate(corpus_entries)
    }

    sorted_anchors = sorted({(int(t), int(s), int(a)) for t, s, a in resume_anchors}, key=lambda item: item[0])
    normalized_windows: list[dict] = []
    for idx, item in enumerate(windows):
        try:
            start = float(item.get("start"))
            end = float(item.get("end"))
        except (TypeError, ValueError, AttributeError):
            continue
        if end <= start:
            continue
        normalized_windows.append(
            {
                "index": idx,
                "label": str(item.get("label") or f"window-{idx + 1}"),
                "start": start,
                "end": end,
            }
        )

    for resume_time, resume_surah, resume_ayah in sorted_anchors:
        target_window = next(
            (
                item
                for item in normalized_windows
                if float(item["start"]) <= float(resume_time) <= float(item["end"])
            ),
            None,
        )
        if target_window is None:
            continue
        window_index = int(target_window["index"])
        if window_index in processed_windows:
            continue
        processed_windows.add(window_index)

        window_start = float(target_window["start"])
        window_end = float(target_window["end"])
        calibration_start = max(window_start, float(resume_time))
        calibration_end = min(window_end, calibration_start + float(calibration_seconds))
        if calibration_end - calibration_start < 30.0:
            continue

        sweep_rows: list[dict] = []
        chosen_threshold: float | None = None
        selection_mode = "window_sweep"

        if fixed_threshold is not None:
            chosen_threshold = float(fixed_threshold)
            selection_mode = "fixed_threshold"
        elif tune_once and global_chosen_threshold is not None:
            chosen_threshold = float(global_chosen_threshold)
            selection_mode = "reused_threshold"
        else:
            for threshold in candidates:
                clip_key = (
                    f"day-{day}{part_suffix}-resume-{int(resume_time)}-calib-"
                    f"{int(calibration_start)}-{int(calibration_end)}"
                )
                clip_segments = _transcribe_window_with_vad_threshold(
                    audio=audio,
                    sample_rate=sample_rate,
                    window_start=calibration_start,
                    window_end=calibration_end,
                    cache_dir=cache_dir,
                    cache_key=clip_key,
                    whisper_model=whisper_model,
                    threshold=float(threshold),
                )
                clip_segments = clean_transcript_for_matching(clip_segments)
                quality = _score_window_transcript_against_anchor(
                    transcript_segments=clip_segments,
                    corpus_entries=corpus_entries,
                    anchor_surah_number=int(resume_surah),
                    anchor_ayah=int(resume_ayah),
                    lookahead_ayahs=60,
                )
                marker_trial_count = 0
                marker_trial_strong = 0
                marker_trial_non_inferred = 0
                forced_start_index = corpus_index_by_key.get((int(resume_surah), int(resume_ayah)))
                if forced_start_index is not None and clip_segments:
                    trial_resets = [float(item) for item in detect_fatiha_starts(clip_segments)]
                    trial_markers = match_quran_markers(
                        clip_segments,
                        corpus_entries,
                        min_score=74,
                        min_gap_seconds=6,
                        min_overlap=0.14,
                        min_confidence=0.58,
                        require_weak_support_for_inferred=True,
                        forced_start_index=forced_start_index,
                        precomputed_reset_times=trial_resets,
                        reanchor_points=[(int(calibration_start), int(resume_surah), int(resume_ayah))],
                        max_infer_gap_ayahs=0,
                        max_leading_infer_ayahs=0,
                        allow_unverified_leading_infer=False,
                    )
                    marker_trial_count = len(trial_markers)
                    marker_trial_strong = len(
                        [item for item in trial_markers if str(item.quality or "").strip().lower() in {"high", "manual"}]
                    )
                    marker_trial_non_inferred = len(
                        [item for item in trial_markers if str(item.quality or "").strip().lower() in {"high", "manual", "ambiguous"}]
                    )
                segments_count = int(quality.get("segments", 0))
                rank = (
                    (float(marker_trial_strong) * 2.4)
                    + (float(marker_trial_non_inferred) * 1.1)
                    + (float(marker_trial_count) * 0.35)
                    + (float(quality.get("pct_ge75", 0.0)) * 0.55)
                    + (float(quality.get("pct_ge80", 0.0)) * 0.20)
                    + (float(quality.get("avg_score", 0.0)) * 0.20)
                    - (abs(float(segments_count) - 24.0) * 0.35)
                )
                sweep_rows.append(
                    {
                        "threshold": float(threshold),
                        "segments": segments_count,
                        "avg_score": float(quality.get("avg_score", 0.0)),
                        "pct_ge75": float(quality.get("pct_ge75", 0.0)),
                        "pct_ge80": float(quality.get("pct_ge80", 0.0)),
                        "trial_marker_count": int(marker_trial_count),
                        "trial_marker_non_inferred": int(marker_trial_non_inferred),
                        "trial_marker_strong": int(marker_trial_strong),
                        "rank_score": round(rank, 2),
                    }
                )

            if not sweep_rows:
                continue
            best = max(sweep_rows, key=lambda item: float(item.get("rank_score", 0.0)))
            chosen_threshold = float(best["threshold"])
            if tune_once:
                global_chosen_threshold = chosen_threshold

        if chosen_threshold is None:
            continue

        full_key = (
            f"day-{day}{part_suffix}-resume-{int(resume_time)}-full-"
            f"{int(window_start)}-{int(window_end)}"
        )
        full_segments = _transcribe_window_with_vad_threshold(
            audio=audio,
            sample_rate=sample_rate,
            window_start=window_start,
            window_end=window_end,
            cache_dir=cache_dir,
            cache_key=full_key,
            whisper_model=whisper_model,
            threshold=chosen_threshold,
        )
        if not full_segments:
            continue

        # Replace only this resume window transcript so pre-break Hassan data stays unchanged.
        updated_segments = [
            segment
            for segment in updated_segments
            if float(segment.end) < window_start or float(segment.start) > window_end
        ] + full_segments
        updated_segments.sort(key=lambda item: float(item.start))

        window_reports.append(
            {
                "window_label": str(target_window["label"]),
                "window_start": int(round(window_start)),
                "window_end": int(round(window_end)),
                "resume_anchor": [int(resume_time), int(resume_surah), int(resume_ayah)],
                "chosen_threshold": chosen_threshold,
                "selection_mode": selection_mode,
                "benchmarks": sweep_rows,
                "segments_replaced": len(full_segments),
            }
        )

    if not window_reports:
        return transcript_segments, {"enabled": False, "reason": "no_resume_windows_retuned", "windows": []}

    return updated_segments, {"enabled": True, "reason": "resume_window_vad_retune", "windows": window_reports}


def _resolve_day_reanchor_points(
    day: int,
    part: int | None,
    overrides_path: Path | None,
    corpus_entries: list | None = None,
) -> list[tuple[int, int, int]]:
    if overrides_path is None or not overrides_path.exists():
        return []

    try:
        payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return []

    raw_points = day_config.get("reanchor_points", [])
    if not isinstance(raw_points, list):
        return []

    points: list[tuple[int, int, int]] = []
    for item in raw_points:
        if not isinstance(item, dict):
            continue
        item_part = item.get("part")
        if item_part is not None:
            try:
                if int(item_part) != int(part or 0):
                    continue
            except (TypeError, ValueError):
                continue

        try:
            at_time = int(item.get("time"))
            surah_number = int(item.get("surah_number"))
            ayah = int(item.get("ayah"))
        except (TypeError, ValueError):
            continue
        if at_time < 0 or surah_number <= 0 or ayah <= 0:
            continue
        points.append((at_time, surah_number, ayah))

    # Promote manual marker overrides into matching-time reanchors.
    # This lets a confirmed manual ayah advance the matcher pointer forward
    # during reacquire instead of only patching output after matching.
    marker_overrides = day_config.get("marker_overrides", [])
    if isinstance(marker_overrides, list) and marker_overrides:
        corpus_order: dict[tuple[int, int], int] = {}
        for index, entry in enumerate(corpus_entries or []):
            surah_number = getattr(entry, "surah_number", None)
            ayah = getattr(entry, "ayah", None)
            if surah_number is None or ayah is None:
                continue
            corpus_order[(int(surah_number), int(ayah))] = index

        for item in marker_overrides:
            if not isinstance(item, dict):
                continue

            item_part = item.get("part")
            if item_part is not None:
                try:
                    if int(item_part) != int(part or 0):
                        continue
                except (TypeError, ValueError):
                    continue

            try:
                surah_number = int(item.get("surah_number"))
                ayah = int(item.get("ayah"))
            except (TypeError, ValueError):
                continue
            if surah_number <= 0 or ayah <= 0:
                continue

            end_time_raw = item.get("end_time", item.get("start_time"))
            try:
                at_time = int(end_time_raw)
            except (TypeError, ValueError):
                continue
            if at_time < 0:
                continue

            current_index = corpus_order.get((surah_number, ayah))
            if current_index is None:
                continue
            next_index = current_index + 1
            if next_index >= len(corpus_entries or []):
                continue

            next_entry = (corpus_entries or [])[next_index]
            next_surah_number = int(getattr(next_entry, "surah_number", 0) or 0)
            next_ayah = int(getattr(next_entry, "ayah", 0) or 0)
            if next_surah_number <= 0 or next_ayah <= 0:
                continue
            points.append((at_time, next_surah_number, next_ayah))

    points.sort(key=lambda item: item[0])
    return points


def process_day(
    day: int,
    output_path: Path,
    cache_dir: Path,
    corpus_path: Path,
    profiles_path: Path,
    youtube_url: str | None,
    audio_file: Path | None,
    whisper_model: str,
    bootstrap_reciters: bool,
    match_min_score: int = 78,
    match_min_overlap: float = 0.18,
    match_min_confidence: float = 0.62,
    match_min_gap_seconds: int = 8,
    match_require_weak_support_for_inferred: bool = True,
    match_start_surah_number: int | None = None,
    match_start_ayah: int | None = None,
    reuse_transcript_cache: bool = True,
    max_audio_seconds: int | None = None,
    asad_path: Path | None = None,
    day_overrides_path: Path | None = None,
    part: int | None = None,
) -> dict:
    total_stages = 12
    stage_index = 0
    stage_timings: dict[str, float] = {}
    pipeline_start = perf_counter()

    def stage_begin(label: str) -> float:
        nonlocal stage_index
        stage_index += 1
        percent = int((stage_index / total_stages) * 100)
        print(f"[pipeline {stage_index}/{total_stages} {percent:>3}%] {label}...", flush=True)
        return perf_counter()

    def stage_end(label: str, started_at: float) -> None:
        elapsed = perf_counter() - started_at
        stage_timings[label] = round(elapsed, 2)
        print(f"[pipeline] {label} done in {elapsed:.1f}s", flush=True)

    t = stage_begin("prepare audio source")
    normalized_audio_path, source = prepare_audio_source(
        day=day,
        youtube_url=youtube_url,
        audio_file=audio_file,
        cache_dir=cache_dir,
    )
    stage_end("prepare audio source", t)

    t = stage_begin("load normalized audio")
    audio, sample_rate = read_mono_audio(normalized_audio_path)
    transcription_audio_path = normalized_audio_path
    cache_suffix = "full"
    stage_end("load normalized audio", t)

    if max_audio_seconds is not None and max_audio_seconds > 0:
        t = stage_begin(f"trim audio to first {max_audio_seconds}s")
        max_samples = min(len(audio), max_audio_seconds * sample_rate)
        audio = audio[:max_samples]
        cache_suffix = f"{max_audio_seconds}s"
        trimmed_audio_path = normalized_audio_path.parent / f"trimmed-{cache_suffix}.wav"
        sf.write(trimmed_audio_path, audio, sample_rate)
        transcription_audio_path = trimmed_audio_path
        stage_end(f"trim audio to first {max_audio_seconds}s", t)
    else:
        # Keep the progress count stable even when no trim is requested.
        t = stage_begin("trim audio (skipped)")
        stage_end("trim audio (skipped)", t)

    total_seconds = int(len(audio) / sample_rate)

    part_suffix = f"-part-{part}" if part is not None and part > 0 else ""
    transcript_cache_path = Path("data/ai/cache") / f"day-{day}{part_suffix}-transcript-{cache_suffix}.json"
    if (
        reuse_transcript_cache
        and cache_suffix == "full"
        and not transcript_cache_path.exists()
    ):
        final_time_override = _resolve_day_final_time_override(day=day, overrides_path=day_overrides_path)
        if final_time_override is not None:
            fallback_path = Path("data/ai/cache") / f"day-{day}{part_suffix}-transcript-{final_time_override}s.json"
            if fallback_path.exists():
                transcript_cache_path = fallback_path
    transcript_segments: list[TranscriptSegment]
    if reuse_transcript_cache and transcript_cache_path.exists():
        t = stage_begin("load transcript cache")
        import json

        with transcript_cache_path.open("r", encoding="utf-8") as handle:
            cached_payload = json.load(handle)
        transcript_segments = [
            TranscriptSegment(
                start=float(segment.get("start", 0.0)),
                end=float(segment.get("end", 0.0)),
                text=str(segment.get("text", "")).strip(),
                words=[
                    TranscriptWord(
                        start=float(word.get("start", 0.0)),
                        end=float(word.get("end", 0.0)),
                        text=str(word.get("text", "")).strip(),
                    )
                    for word in segment.get("words", [])
                    if str(word.get("text", "")).strip()
                ],
            )
            for segment in cached_payload.get("segments", [])
            if str(segment.get("text", "")).strip()
        ]
        stage_end("load transcript cache", t)
        # Keep stage count stable.
        t = stage_begin("transcribe audio (cache hit, skipped)")
        stage_end("transcribe audio (cache hit, skipped)", t)
    else:
        # Keep stage count stable.
        t = stage_begin("load transcript cache (miss)")
        stage_end("load transcript cache (miss)", t)

        t = stage_begin(f"transcribe audio (model={whisper_model})")
        transcript_segments = transcribe_audio(transcription_audio_path, model_size=whisper_model)
        write_json(
            transcript_cache_path,
            {
                "day": day,
                "source": source,
                "segments": [asdict(segment) for segment in transcript_segments],
            },
        )
        stage_end(f"transcribe audio (model={whisper_model})", t)

    t = stage_begin("detect reciter/prayer segment starts")
    audio_segment_starts = detect_prayer_starts(audio, sample_rate, collapse_rakah_pairs=True)
    fatiha_segment_starts = detect_fatiha_starts(transcript_segments)
    reciter_segment_starts = merge_rakah_starts(audio_segment_starts, fatiha_segment_starts, min_gap_seconds=180)
    stage_end("detect reciter/prayer segment starts", t)

    t = stage_begin("assign reciters to segments")
    reciter_segments = build_prayer_segments(reciter_segment_starts, total_seconds)
    reciter_segments = assign_reciters(
        day=day,
        audio=audio,
        sample_rate=sample_rate,
        prayers=reciter_segments,
        profiles_path=profiles_path,
        bootstrap_reciters=bootstrap_reciters,
    )
    stage_end("assign reciters to segments", t)

    t = stage_begin("load Quran corpus and prepare transcript")
    corpus_entries = load_corpus(corpus_path)
    transcript_for_matching = clean_transcript_for_matching(transcript_segments)
    structured_plan = _resolve_day_structured_plan(day=day, overrides_path=day_overrides_path)
    resume_vad_retune_enabled = os.getenv("ENABLE_RESUME_VAD_RETUNE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if resume_vad_retune_enabled:
        fixed_resume_vad_threshold: float | None = None
        raw_fixed_resume_vad_threshold = os.getenv("RESUME_VAD_FIXED_THRESHOLD")
        if raw_fixed_resume_vad_threshold is not None and str(raw_fixed_resume_vad_threshold).strip() != "":
            try:
                fixed_resume_vad_threshold = float(raw_fixed_resume_vad_threshold)
            except (TypeError, ValueError):
                fixed_resume_vad_threshold = None
        resume_vad_tune_once = os.getenv("RESUME_VAD_TUNE_ONCE", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        transcript_segments, samir_vad_tuning_info = _retune_resume_windows_transcript(
            transcript_segments=transcript_segments,
            audio=audio,
            sample_rate=sample_rate,
            cache_dir=Path("data/ai/cache"),
            day=day,
            part=part,
            whisper_model=whisper_model,
            corpus_entries=corpus_entries,
            windows=list(structured_plan.get("windows") or []),
            resume_anchors=list(structured_plan.get("resume_anchors") or []),
            fixed_threshold=fixed_resume_vad_threshold,
            tune_once=resume_vad_tune_once,
        )
        transcript_for_matching = clean_transcript_for_matching(transcript_segments)
    else:
        samir_vad_tuning_info = {
            "enabled": False,
            "reason": "disabled_by_env",
            "windows": [],
        }
    transcript_window_info = {
        "enabled": False,
        "reason": "not_applied",
        "windows": 0,
        "kept_segments": len(transcript_for_matching),
        "total_segments": len(transcript_for_matching),
    }
    if structured_plan.get("windows"):
        transcript_for_matching, transcript_window_info = _filter_transcript_by_windows(
            transcript_segments=transcript_for_matching,
            windows=list(structured_plan.get("windows") or []),
        )
    if structured_plan.get("windows"):
        reciter_filter_info = {
            "enabled": False,
            "reason": "skipped_due_to_structured_windows",
            "kept_segments": len(transcript_for_matching),
            "total_segments": len(transcript_for_matching),
        }
    else:
        transcript_for_matching, reciter_filter_info = _filter_transcript_by_known_reciter(
            transcript_segments=transcript_for_matching,
            prayers=reciter_segments,
        )
    transcript_for_matching, quran_vocab_correction_info = _correct_transcript_with_quran_lexicon(
        transcript_segments=transcript_for_matching,
        corpus_entries=corpus_entries,
    )
    reset_markers = [float(item) for item in fatiha_segment_starts]
    effective_start_surah_number = match_start_surah_number
    effective_start_ayah = match_start_ayah
    if effective_start_surah_number is None or effective_start_ayah is None:
        day_start_override = _resolve_day_start_override(day=day, overrides_path=day_overrides_path)
        if day_start_override is not None:
            effective_start_surah_number, effective_start_ayah = day_start_override
    structured_start = structured_plan.get("start")
    if (
        (effective_start_surah_number is None or effective_start_ayah is None)
        and isinstance(structured_start, tuple)
        and len(structured_start) == 2
    ):
        effective_start_surah_number, effective_start_ayah = int(structured_start[0]), int(structured_start[1])
    reanchor_points = _resolve_day_reanchor_points(
        day=day,
        part=part,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    structured_reanchors = list(structured_plan.get("reanchors") or [])
    structured_resume_anchors = list(structured_plan.get("resume_anchors") or [])
    if structured_reanchors:
        reanchor_points = sorted(
            {
                (int(item[0]), int(item[1]), int(item[2]))
                for item in (reanchor_points + structured_reanchors)
                if int(item[0]) >= 0 and int(item[1]) > 0 and int(item[2]) > 0
            },
            key=lambda item: item[0],
        )

    forced_start_index: int | None = None
    if effective_start_surah_number is not None and effective_start_ayah is not None:
        for index, entry in enumerate(corpus_entries):
            if entry.surah_number == effective_start_surah_number and entry.ayah == effective_start_ayah:
                forced_start_index = index
                break
    stage_end("load Quran corpus and prepare transcript", t)

    t = stage_begin("match ayah markers")
    corpus_index_by_key = {
        (int(entry.surah_number), int(entry.ayah)): idx
        for idx, entry in enumerate(corpus_entries)
    }
    if structured_plan.get("windows"):
        matching_blocks = _build_matching_blocks_from_windows(
            transcript_segments=transcript_for_matching,
            windows=list(structured_plan.get("windows") or []),
        )
    else:
        matching_blocks = _build_matching_blocks(
            transcript_segments=transcript_for_matching,
            prayers=reciter_segments,
            total_seconds=total_seconds,
        )
    debug_trace: list[dict] = []
    block_summaries: list[dict] = []
    block_markers_all: list[Marker] = []
    rolling_forced_start = forced_start_index
    enable_ensemble_fallback = os.getenv("ENABLE_ENSEMBLE_FALLBACK", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    for block_idx, block in enumerate(matching_blocks):
        block_segments = list(block.get("segments") or [])
        if not block_segments:
            continue
        block_start = float(block.get("start", 0.0))
        block_end = float(block.get("end", float(total_seconds)))
        block_resets = [item for item in reset_markers if block_start <= float(item) <= block_end]
        block_reanchors = [
            item for item in reanchor_points
            if block_start <= float(item[0]) <= block_end
        ]
        block_resume_reanchors = [
            item for item in structured_resume_anchors
            if block_start <= float(item[0]) <= block_end
        ]
        block_forced_start = rolling_forced_start
        if block_reanchors:
            first_anchor = min(block_reanchors, key=lambda item: int(item[0]))
            mapped_anchor = corpus_index_by_key.get((int(first_anchor[1]), int(first_anchor[2])))
            if mapped_anchor is not None:
                block_forced_start = mapped_anchor

        block_markers, pass_meta = _run_two_pass_match(
            transcript_segments=block_segments,
            corpus_entries=corpus_entries,
            min_score=match_min_score,
            min_gap_seconds=match_min_gap_seconds,
            min_overlap=match_min_overlap,
            min_confidence=match_min_confidence,
            require_weak_support_for_inferred=match_require_weak_support_for_inferred,
            forced_start_index=block_forced_start,
            precomputed_reset_times=block_resets,
            reanchor_points=block_reanchors,
            resume_chain_reanchors=block_resume_reanchors,
            debug_trace=debug_trace,
        )

        ensemble_used = False
        if enable_ensemble_fallback and structured_plan.get("windows") and len(block_markers) == 0:
            ensemble_segments = _transcribe_block_ensemble(
                audio=audio,
                sample_rate=sample_rate,
                block_start=block_start,
                block_end=block_end,
                cache_dir=Path("data/ai/cache"),
                day=day,
                block_index=block_idx,
            )
            if ensemble_segments:
                ensemble_segments, _ = _correct_transcript_with_quran_lexicon(
                    transcript_segments=ensemble_segments,
                    corpus_entries=corpus_entries,
                )
                block_markers, pass_meta = _run_two_pass_match(
                    transcript_segments=ensemble_segments,
                    corpus_entries=corpus_entries,
                    min_score=match_min_score,
                    min_gap_seconds=match_min_gap_seconds,
                    min_overlap=match_min_overlap,
                    min_confidence=match_min_confidence,
                    require_weak_support_for_inferred=match_require_weak_support_for_inferred,
                    forced_start_index=block_forced_start,
                    precomputed_reset_times=block_resets,
                    reanchor_points=block_reanchors,
                    resume_chain_reanchors=block_resume_reanchors,
                    debug_trace=debug_trace,
                )
                ensemble_used = True

        block_markers_all.extend(block_markers)
        block_summaries.append(
            {
                "block_index": block_idx,
                "label": str(block.get("label", "unknown")),
                "start": int(round(block_start)),
                "end": int(round(block_end)),
                "segments": len(block_segments),
                "ensemble_used": ensemble_used,
                "markers": len(block_markers),
                "pass_meta": pass_meta,
                "ensemble_fallback_enabled": enable_ensemble_fallback,
            }
        )
        if block_markers:
            tail = max(block_markers, key=lambda item: (int(item.time), int(item.surah_number or 0), int(item.ayah)))
            if tail.surah_number is not None:
                mapped = corpus_index_by_key.get((int(tail.surah_number), int(tail.ayah)))
                if mapped is not None:
                    rolling_forced_start = min(len(corpus_entries) - 1, mapped + 1)

    markers = _merge_markers_prefer_strong(block_markers_all)
    markers, postcheck_info = _postcheck_marker_spans(markers)
    stage_end("match ayah markers", t)

    t = stage_begin("apply day overrides")
    markers, override_info = _apply_day_final_ayah_override(
        day=day,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    markers, marker_time_overrides = _apply_marker_time_overrides(
        day=day,
        part=part,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    markers, range_fill_info = _fill_override_surah_range(
        day=day,
        markers=markers,
        overrides_path=day_overrides_path,
        corpus_entries=corpus_entries,
    )
    stage_end("apply day overrides", t)

    t = stage_begin("enrich marker text + reciter mapping")
    asad_lookup = load_asad_translation(asad_path) if asad_path else {}
    markers = enrich_marker_texts(markers, corpus_entries, asad_lookup)
    markers = _map_reciter_to_markers(markers, reciter_segments)
    stage_end("enrich marker text + reciter mapping", t)

    t = stage_begin("write output JSON")
    payload = {
        "day": day,
        "source": source,
        "markers": [asdict(marker) for marker in markers],
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audio_path": str(normalized_audio_path),
            "part": part,
            "whisper_model": whisper_model,
            "markers_detected": len(markers),
            "transcript_segments_raw": len(transcript_segments),
            "transcript_segments_for_matching": len(transcript_for_matching),
            "transcript_reset_markers": len(reset_markers),
            "reciter_segments_detected": len(reciter_segments),
            "corpus_loaded": bool(corpus_entries),
            "asad_loaded": bool(asad_lookup),
            "transcript_path": str(transcript_cache_path),
            "segment_detection": {
                "audio_starts": len(audio_segment_starts),
                "fatiha_starts": len(fatiha_segment_starts),
                "merged_starts": len(reciter_segment_starts),
            },
            "reciter_filter": reciter_filter_info,
            "quran_vocab_correction": quran_vocab_correction_info,
            "structured_plan": structured_plan,
            "transcript_window_filter": transcript_window_info,
            "matching_blocks": block_summaries,
            "match_postcheck": postcheck_info,
            "match_debug_events": len(debug_trace),
            "match_config": {
                "min_score": match_min_score,
                "min_overlap": match_min_overlap,
                "min_confidence": match_min_confidence,
                "min_gap_seconds": match_min_gap_seconds,
                "strict_normalization": STRICT_NORMALIZATION,
                "require_weak_support_for_inferred": match_require_weak_support_for_inferred,
                "start_surah_number": effective_start_surah_number,
                "start_ayah": effective_start_ayah,
                "two_pass_enabled": True,
                "block_matching_enabled": True,
            },
            "manual_override": override_info,
            "marker_time_overrides": marker_time_overrides,
            "override_surah_fill": range_fill_info,
            "pipeline_timings_seconds": stage_timings,
        },
    }

    debug_path = Path(f"data/ai/reports/day-{day}{('-part-' + str(part)) if part else ''}-match-debug.json")
    write_json(
        debug_path,
        {
            "day": day,
            "part": part,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "events": debug_trace,
        },
    )

    write_json(output_path, payload)
    stage_end("write output JSON", t)
    total_elapsed = perf_counter() - pipeline_start
    print(f"[pipeline] complete in {total_elapsed:.1f}s", flush=True)
    return payload
