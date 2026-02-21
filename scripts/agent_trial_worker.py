#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _log(message: str) -> None:
    print(f"[{_now_iso()}] {message}", flush=True)


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _resolve_path(repo_root: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def _choose_existing_path(repo_root: Path, primary: str | None, fallbacks: list[str] | None) -> Path | None:
    candidates: list[Path] = []
    if primary:
        resolved_primary = _resolve_path(repo_root, primary)
        if resolved_primary is not None:
            candidates.append(resolved_primary)
    for item in (fallbacks or []):
        resolved = _resolve_path(repo_root, item)
        if resolved is not None:
            candidates.append(resolved)

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0] if candidates else None


def _duration_seconds(dataset: dict, markers: list[dict]) -> int:
    max_audio_seconds = int(dataset.get("max_audio_seconds", 0) or 0)
    if max_audio_seconds > 0:
        return max_audio_seconds

    window_start = dataset.get("window_start_seconds")
    window_end = dataset.get("window_end_seconds")
    if window_start is not None and window_end is not None:
        return max(1, int(window_end) - int(window_start))

    if markers:
        times = [int(marker.get("time", 0)) for marker in markers]
        if times:
            return max(1, max(times) - min(times))
    return 1


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _compute_contract_metrics(markers: list[dict], gates: dict, report_summary: dict) -> dict:
    schema_errors = 0
    contract_errors = 0
    suspicious_missing_ayahs = 0
    suspicious_resets = 0
    high_quality_count = 0

    fast_gap_seconds_per_ayah = _to_float(gates.get("fast_gap_seconds_per_ayah"), 9.0)
    reset_gap_seconds = _to_int(gates.get("reset_gap_seconds"), 180)

    previous_time: int | None = None
    previous_surah_number: int | None = None
    previous_ayah: int | None = None

    for marker in markers:
        surah = str(marker.get("surah", "")).strip()
        ayah = _to_int(marker.get("ayah"), 0)
        surah_number = _to_int(marker.get("surah_number"), 0)
        time = _to_int(marker.get("time"), -1)
        quality = str(marker.get("quality", "")).strip().lower()

        if not surah or ayah <= 0 or time < 0:
            schema_errors += 1
            continue

        if surah_number <= 0:
            contract_errors += 1

        if quality not in {"high", "ambiguous", "inferred", "manual"}:
            contract_errors += 1
        if quality == "high":
            high_quality_count += 1

        start_time = marker.get("start_time")
        end_time = marker.get("end_time")
        if start_time is not None and end_time is not None:
            start_value = _to_int(start_time, time)
            end_value = _to_int(end_time, start_value)
            if end_value < start_value:
                contract_errors += 1

        if previous_time is not None and time < previous_time:
            contract_errors += 1

        if previous_time is not None and previous_ayah is not None and previous_surah_number is not None:
            time_gap = max(0, time - previous_time)
            if surah_number == previous_surah_number:
                ayah_gap = ayah - previous_ayah
                if ayah_gap > 1 and time_gap < int(round((ayah_gap - 1) * fast_gap_seconds_per_ayah)):
                    suspicious_missing_ayahs += ayah_gap - 1
                if ayah_gap < 0 and time_gap < reset_gap_seconds:
                    suspicious_resets += 1
            elif surah_number < previous_surah_number and time_gap < reset_gap_seconds:
                suspicious_resets += 1

        previous_time = time
        previous_surah_number = surah_number if surah_number > 0 else previous_surah_number
        previous_ayah = ayah

    markers_count = len(markers)
    quality_high_ratio = high_quality_count / max(1, markers_count)

    # Reuse core chronology/duplicate checks from transcript validator output.
    chronology_backtracks = _to_int(report_summary.get("chronology_backtracks"), 0)
    duplicates = _to_int(report_summary.get("duplicates"), 0)

    return {
        "schema_errors": schema_errors,
        "contract_errors": contract_errors,
        "suspicious_missing_ayahs": suspicious_missing_ayahs,
        "suspicious_resets": suspicious_resets,
        "quality_high_ratio": round(quality_high_ratio, 4),
        "chronology_backtracks": chronology_backtracks,
        "duplicates": duplicates,
    }


def _score_dataset(
    scoring_spec: dict,
    dataset: dict,
    summary: dict,
    contract: dict,
    markers_count: int,
    duration_seconds: int,
) -> dict:
    weights = scoring_spec.get("weights", {})
    ratios = scoring_spec.get("ratios", {})
    penalties = scoring_spec.get("penalties", {})
    gates = scoring_spec.get("gates", {})

    pass_rate = _to_float(summary.get("pass_rate"), 0.0)
    mean_score = _to_float(summary.get("mean_score"), 0.0) / 100.0
    confidence_spread = _to_float(summary.get("confidence_spread"), 0.0)

    confidence_spread_target = max(0.01, _to_float(ratios.get("confidence_spread_target"), 0.35))
    confidence_spread_ratio = min(1.0, confidence_spread / confidence_spread_target)

    seconds_per_marker_target = max(1.0, _to_float(ratios.get("seconds_per_marker_target"), 20.0))
    target_markers = max(1.0, duration_seconds / seconds_per_marker_target)
    marker_density_ratio = min(1.3, markers_count / target_markers) / 1.3

    base_score = (
        (pass_rate * _to_float(weights.get("pass_rate"), 0.0))
        + (mean_score * _to_float(weights.get("mean_score"), 0.0))
        + (_to_float(contract.get("quality_high_ratio"), 0.0) * _to_float(weights.get("quality_high_ratio"), 0.0))
        + (marker_density_ratio * _to_float(weights.get("marker_density_ratio"), 0.0))
        + (confidence_spread_ratio * _to_float(weights.get("confidence_spread_ratio"), 0.0))
    )

    penalty_score = (
        (_to_int(contract.get("chronology_backtracks"), 0) * _to_float(penalties.get("chronology_backtracks"), 0.0))
        + (_to_int(contract.get("duplicates"), 0) * _to_float(penalties.get("duplicates"), 0.0))
        + (_to_int(contract.get("schema_errors"), 0) * _to_float(penalties.get("schema_errors"), 0.0))
        + (_to_int(contract.get("contract_errors"), 0) * _to_float(penalties.get("contract_errors"), 0.0))
        + (
            _to_int(contract.get("suspicious_missing_ayahs"), 0)
            * _to_float(penalties.get("suspicious_missing_ayahs"), 0.0)
        )
        + (_to_int(contract.get("suspicious_resets"), 0) * _to_float(penalties.get("suspicious_resets"), 0.0))
    )

    minimum_markers = max(_to_int(gates.get("min_markers"), 8), _to_int(dataset.get("min_markers"), 0))
    if markers_count < minimum_markers:
        shortfall = (minimum_markers - markers_count) / max(1.0, float(minimum_markers))
        penalty_score += _to_float(penalties.get("low_marker_floor"), 20.0) * shortfall

    final_score = round(base_score - penalty_score, 4)
    return {
        "score": final_score,
        "base_score": round(base_score, 4),
        "penalty_score": round(penalty_score, 4),
        "marker_density_ratio": round(marker_density_ratio, 4),
        "confidence_spread_ratio": round(confidence_spread_ratio, 4),
        "minimum_markers": minimum_markers,
    }


def _run_stage(spec: dict, strategy: dict, stage_name: str, trial_dir: Path, repo_root: Path) -> dict:
    from ai_pipeline import process_day
    from validate_day import evaluate_day_payload

    paths = spec.get("paths", {})
    scoring_spec = spec.get("scoring", {})
    base_match = spec.get("base_match_config", {})

    quran_corpus_path = _resolve_path(repo_root, paths.get("quran_corpus"))
    quran_asad_path = _resolve_path(repo_root, paths.get("quran_asad"))
    reciter_profiles_path = _resolve_path(repo_root, paths.get("reciter_profiles"))
    day_overrides_path = _resolve_path(repo_root, paths.get("day_overrides"))

    if quran_corpus_path is None or not quran_corpus_path.exists():
        raise SystemExit("Missing quran corpus path in spec or file does not exist")

    stage = next((item for item in spec.get("stages", []) if item.get("name") == stage_name), None)
    if stage is None:
        raise SystemExit(f"Unknown stage '{stage_name}'")

    outputs_dir = trial_dir / "outputs"
    reports_dir = trial_dir / "reports"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    dataset_results: list[dict] = []

    for dataset in stage.get("datasets", []):
        dataset_name = str(dataset.get("name") or f"day-{dataset.get('day')}")
        day = _to_int(dataset.get("day"), 0)
        if day <= 0:
            raise SystemExit(f"Invalid day for dataset '{dataset_name}'")

        transcript_cache_path = _choose_existing_path(
            repo_root=repo_root,
            primary=dataset.get("transcript_cache"),
            fallbacks=dataset.get("transcript_fallbacks") if isinstance(dataset.get("transcript_fallbacks"), list) else None,
        )
        if transcript_cache_path is None:
            raise SystemExit(f"Missing transcript cache path for dataset '{dataset_name}'")

        audio_file = _resolve_path(repo_root, dataset.get("audio_file"))
        if audio_file is None or not audio_file.exists():
            raise SystemExit(f"Audio file not found for dataset '{dataset_name}': {dataset.get('audio_file')}")

        output_path = outputs_dir / f"{stage_name}-{dataset_name}.json"
        report_path = reports_dir / f"{stage_name}-{dataset_name}-validation.json"

        stage_overrides = stage.get("match_overrides") if isinstance(stage.get("match_overrides"), dict) else {}
        dataset_overrides = dataset.get("match_overrides") if isinstance(dataset.get("match_overrides"), dict) else {}
        strategy_overrides = strategy.get("match_overrides") if isinstance(strategy.get("match_overrides"), dict) else {}

        combined_overrides: dict = {}
        combined_overrides.update(stage_overrides)
        combined_overrides.update(dataset_overrides)
        combined_overrides.update(strategy_overrides)

        _log(
            f"stage={stage_name} dataset={dataset_name} day={day} running matcher "
            f"(transcript={transcript_cache_path})"
        )
        payload = process_day(
            day=day,
            part=_to_int(dataset.get("part"), 0) or None,
            output_path=output_path,
            cache_dir=repo_root / "data/audio",
            corpus_path=quran_corpus_path,
            asad_path=quran_asad_path,
            day_overrides_path=day_overrides_path,
            profiles_path=reciter_profiles_path,
            youtube_url=dataset.get("youtube_url"),
            audio_file=audio_file,
            whisper_model=str(dataset.get("whisper_model") or "tiny"),
            bootstrap_reciters=bool(dataset.get("bootstrap_reciters", False)),
            match_min_score=_to_int(base_match.get("min_score"), 78),
            match_min_overlap=_to_float(base_match.get("min_overlap"), 0.18),
            match_min_confidence=_to_float(base_match.get("min_confidence"), 0.62),
            match_min_gap_seconds=_to_int(base_match.get("min_gap_seconds"), 8),
            match_require_weak_support_for_inferred=bool(base_match.get("require_weak_support_for_inferred", True)),
            match_start_surah_number=_to_int(dataset.get("start_surah_number"), 0) or None,
            match_start_ayah=_to_int(dataset.get("start_ayah"), 0) or None,
            reuse_transcript_cache=not bool(dataset.get("force_transcribe", False)),
            max_audio_seconds=_to_int(dataset.get("max_audio_seconds"), 0) or None,
            window_start_seconds=_to_int(dataset.get("window_start_seconds"), 0) if dataset.get("window_start_seconds") is not None else None,
            window_end_seconds=_to_int(dataset.get("window_end_seconds"), 0) if dataset.get("window_end_seconds") is not None else None,
            transcript_cache_override=transcript_cache_path,
            match_overrides=combined_overrides,
        )

        transcript_from_payload = Path(str(payload.get("meta", {}).get("transcript_path", "")))
        if not transcript_from_payload.is_absolute():
            transcript_from_payload = repo_root / transcript_from_payload

        report = evaluate_day_payload(
            day_payload=payload,
            quran_corpus_path=quran_corpus_path,
            transcript_path=transcript_from_payload,
            source_json_path=output_path,
            pass_score=_to_float(dataset.get("pass_score"), 80.0),
        )
        _write_json(report_path, report)

        markers = payload.get("markers", []) if isinstance(payload.get("markers"), list) else []
        summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
        contract = _compute_contract_metrics(markers=markers, gates=scoring_spec.get("gates", {}), report_summary=summary)
        duration_seconds = _duration_seconds(dataset, markers)
        score_rows = _score_dataset(
            scoring_spec=scoring_spec,
            dataset=dataset,
            summary=summary,
            contract=contract,
            markers_count=len(markers),
            duration_seconds=duration_seconds,
        )

        dataset_result = {
            "dataset": dataset_name,
            "day": day,
            "output_path": str(output_path),
            "report_path": str(report_path),
            "transcript_path": str(transcript_from_payload),
            "markers": len(markers),
            "duration_seconds": duration_seconds,
            "summary": summary,
            "contract": contract,
            "score": score_rows,
        }
        dataset_results.append(dataset_result)

        _log(
            f"stage={stage_name} dataset={dataset_name} score={score_rows['score']:.3f} "
            f"markers={len(markers)} pass_rate={_to_float(summary.get('pass_rate'), 0.0):.3f} "
            f"backtracks={_to_int(summary.get('chronology_backtracks'), 0)} duplicates={_to_int(summary.get('duplicates'), 0)}"
        )

    stage_score = round(fmean(item["score"]["score"] for item in dataset_results), 4) if dataset_results else -999.0

    return {
        "stage": stage_name,
        "strategy_id": strategy.get("id"),
        "stage_score": stage_score,
        "datasets": dataset_results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one matcher-agent stage inside a trial worktree.")
    parser.add_argument("--spec-file", type=Path, required=True, help="Path to fixed spec JSON")
    parser.add_argument("--strategy-file", type=Path, required=True, help="Path to strategy JSON")
    parser.add_argument("--stage", type=str, required=True, help="Stage name from spec")
    parser.add_argument("--trial-dir", type=Path, required=True, help="Trial output directory")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repo root to resolve relative paths")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    spec = _load_json(args.spec_file)
    strategy = _load_json(args.strategy_file)

    env_map = strategy.get("env") if isinstance(strategy.get("env"), dict) else {}
    for key, value in env_map.items():
        os.environ[str(key)] = str(value)
        _log(f"env override: {key}={value}")

    result = _run_stage(
        spec=spec,
        strategy=strategy,
        stage_name=args.stage,
        trial_dir=args.trial_dir,
        repo_root=args.repo_root.resolve(),
    )

    output_path = args.trial_dir / f"stage-{args.stage}.json"
    _write_json(output_path, result)
    _log(f"saved stage result: {output_path}")


if __name__ == "__main__":
    main()
