from __future__ import annotations

from dataclasses import dataclass

from .matcher_two_stage import match_quran_markers_two_stage
from .quran import AyahEntry, match_quran_markers
from .quran_samir import match_quran_markers as match_quran_markers_legacy
from .types import Marker, TranscriptSegment


@dataclass(frozen=True)
class MatcherConfig:
    min_score: int = 78
    min_gap_seconds: int = 8
    min_overlap: float = 0.18
    min_confidence: float = 0.62
    require_weak_support_for_inferred: bool = True
    forced_start_index: int | None = None
    precomputed_reset_times: list[float] | None = None
    reanchor_points: list[tuple[int, int, int]] | None = None
    segment_constraints: list[tuple[float, float, int | None, int | None]] | None = None
    mode: str = "legacy"
    beam_width: int = 96
    top_k_per_segment: int = 8


def run_ayah_matcher(
    transcript_segments: list[TranscriptSegment],
    corpus_entries: list[AyahEntry],
    config: MatcherConfig,
) -> list[Marker]:
    mode = str(getattr(config, "mode", "legacy") or "legacy").strip().lower()
    if mode == "two_stage":
        return match_quran_markers_two_stage(
            transcript_segments=transcript_segments,
            corpus_entries=corpus_entries,
            min_score=config.min_score,
            min_gap_seconds=config.min_gap_seconds,
            min_overlap=config.min_overlap,
            min_confidence=config.min_confidence,
            forced_start_index=config.forced_start_index,
            reanchor_points=config.reanchor_points,
            segment_constraints=config.segment_constraints,
            beam_width=config.beam_width,
            top_k_per_segment=config.top_k_per_segment,
        )
    if mode == "legacy":
        # Legacy mode keeps the committed Hasan-optimized matcher behavior.
        return match_quran_markers_legacy(
            transcript_segments=transcript_segments,
            corpus_entries=corpus_entries,
            min_score=config.min_score,
            min_gap_seconds=config.min_gap_seconds,
            min_overlap=config.min_overlap,
            min_confidence=config.min_confidence,
            require_weak_support_for_inferred=config.require_weak_support_for_inferred,
            forced_start_index=config.forced_start_index,
            precomputed_reset_times=config.precomputed_reset_times,
            reanchor_points=config.reanchor_points,
        )
    return match_quran_markers(
        transcript_segments=transcript_segments,
        corpus_entries=corpus_entries,
        min_score=config.min_score,
        min_gap_seconds=config.min_gap_seconds,
        min_overlap=config.min_overlap,
        min_confidence=config.min_confidence,
        require_weak_support_for_inferred=config.require_weak_support_for_inferred,
        forced_start_index=config.forced_start_index,
        precomputed_reset_times=config.precomputed_reset_times,
        reanchor_points=config.reanchor_points,
        segment_constraints=config.segment_constraints,
    )


__all__ = ["MatcherConfig", "run_ayah_matcher"]
