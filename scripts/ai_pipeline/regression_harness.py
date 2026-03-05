#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


def _quality_counts(markers: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for marker in markers:
        key = str(marker.get("quality", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _longest_inferred_run(markers: list[dict]) -> int:
    ordered = sorted(markers, key=lambda item: (int(item.get("surah_number") or 0), int(item.get("ayah") or 0)))
    longest = 0
    current = 0
    for marker in ordered:
        if str(marker.get("quality", "")).lower() == "inferred":
            current += 1
            if current > longest:
                longest = current
        else:
            current = 0
    return longest


def compare(baseline_path: Path, candidate_path: Path) -> dict:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))

    baseline_markers = list(baseline.get("markers", []))
    candidate_markers = list(candidate.get("markers", []))
    key = lambda marker: (int(marker.get("surah_number") or 0), int(marker.get("ayah") or 0))
    baseline_map = {key(marker): marker for marker in baseline_markers}
    candidate_map = {key(marker): marker for marker in candidate_markers}

    baseline_keys = set(baseline_map)
    candidate_keys = set(candidate_map)
    common_keys = sorted(baseline_keys & candidate_keys)
    missing_keys = sorted(baseline_keys - candidate_keys)
    new_keys = sorted(candidate_keys - baseline_keys)

    time_abs: list[int] = []
    quality_changed = 0
    for marker_key in common_keys:
        baseline_marker = baseline_map[marker_key]
        candidate_marker = candidate_map[marker_key]
        time_abs.append(abs(int(candidate_marker.get("time") or 0) - int(baseline_marker.get("time") or 0)))
        if str(candidate_marker.get("quality")) != str(baseline_marker.get("quality")):
            quality_changed += 1

    p90 = 0
    if time_abs:
        sorted_abs = sorted(time_abs)
        p90 = int(sorted_abs[int(0.9 * (len(sorted_abs) - 1))])

    return {
        "baseline": str(baseline_path),
        "candidate": str(candidate_path),
        "baseline_markers": len(baseline_markers),
        "candidate_markers": len(candidate_markers),
        "baseline_quality": _quality_counts(baseline_markers),
        "candidate_quality": _quality_counts(candidate_markers),
        "missing_keys": len(missing_keys),
        "new_keys": len(new_keys),
        "common_keys": len(common_keys),
        "quality_changed": quality_changed,
        "time_abs_median": float(median(time_abs)) if time_abs else 0.0,
        "time_abs_p90": p90,
        "time_abs_max": int(max(time_abs)) if time_abs else 0,
        "baseline_longest_inferred_run": _longest_inferred_run(baseline_markers),
        "candidate_longest_inferred_run": _longest_inferred_run(candidate_markers),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare candidate marker JSONs against baseline outputs.")
    parser.add_argument("--baseline", type=Path, required=True, help="Baseline JSON path.")
    parser.add_argument("--candidate", type=Path, required=True, help="Candidate JSON path.")
    args = parser.parse_args()

    report = compare(args.baseline, args.candidate)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
