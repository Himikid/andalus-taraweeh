#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


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


def _starts_with_path(path: str, prefix: str) -> bool:
    normalized_path = path.strip("/")
    normalized_prefix = prefix.strip("/")
    return normalized_path == normalized_prefix or normalized_path.startswith(f"{normalized_prefix}/")


def _sanitize(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "trial"


def _run_capture(cmd: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def _run_stream(cmd: list[str], cwd: Path, prefix: str = "") -> None:
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        line = line.rstrip("\n")
        if line:
            _log(f"{prefix}{line}")
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Command failed ({return_code}): {' '.join(cmd)}")


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    return _run_capture(["git", *args], cwd=repo_root, check=check)


def _collect_overlay_paths(repo_root: Path, runs_dir: Path) -> list[str]:
    runs_dir_rel = str(runs_dir.relative_to(repo_root)).strip("/")
    allow_untracked_prefixes = ("scripts/", "data/", "public/")

    tracked_paths: set[str] = set()
    for command in (["git", "diff", "--name-only"], ["git", "diff", "--cached", "--name-only"]):
        output = _run_capture(command, cwd=repo_root, check=False)
        for line in output.splitlines():
            path = line.strip()
            if not path:
                continue
            if runs_dir_rel and _starts_with_path(path, runs_dir_rel):
                continue
            tracked_paths.add(path)

    untracked_paths: set[str] = set()
    output = _run_capture(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo_root, check=False)
    for line in output.splitlines():
        path = line.strip()
        if not path:
            continue
        if runs_dir_rel and _starts_with_path(path, runs_dir_rel):
            continue
        if path == "README.md" or path.startswith(allow_untracked_prefixes):
            untracked_paths.add(path)

    overlay_paths = sorted(tracked_paths | untracked_paths)
    return overlay_paths


def _sync_overlay_into_worktree(repo_root: Path, worktree: Path, overlay_paths: list[str]) -> None:
    if not overlay_paths:
        return

    copied = 0
    deleted = 0
    for rel_path in overlay_paths:
        source = repo_root / rel_path
        target = worktree / rel_path
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
        elif not source.exists() and target.exists() and target.is_file():
            target.unlink()
            deleted += 1

    _log(f"Overlay sync: copied={copied} deleted={deleted}")


def _sync_required_assets(repo_root: Path, worktree: Path, spec: dict) -> None:
    candidate_paths: set[str] = set()

    paths = spec.get("paths") if isinstance(spec.get("paths"), dict) else {}
    for value in paths.values():
        if isinstance(value, str) and value.strip():
            candidate_paths.add(value.strip())

    stages = spec.get("stages") if isinstance(spec.get("stages"), list) else []
    for stage in stages:
        datasets = stage.get("datasets") if isinstance(stage, dict) else []
        if not isinstance(datasets, list):
            continue
        for dataset in datasets:
            if not isinstance(dataset, dict):
                continue
            for key in ("audio_file", "transcript_cache"):
                value = dataset.get(key)
                if isinstance(value, str) and value.strip():
                    candidate_paths.add(value.strip())
            fallbacks = dataset.get("transcript_fallbacks")
            if isinstance(fallbacks, list):
                for value in fallbacks:
                    if isinstance(value, str) and value.strip():
                        candidate_paths.add(value.strip())

    copied = 0
    for rel_path in sorted(candidate_paths):
        source = repo_root / rel_path
        target = worktree / rel_path
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1

    _log(f"Asset sync: copied={copied}")


def _apply_patch_sets(worktree: Path, spec: dict, strategy: dict) -> tuple[list[str], list[str]]:
    patch_sets = strategy.get("patch_sets")
    if not isinstance(patch_sets, list) or not patch_sets:
        return [], []

    applied: list[str] = []
    touched_paths: set[str] = set()
    all_patch_sets = spec.get("patch_sets") if isinstance(spec.get("patch_sets"), dict) else {}

    for patch_set_name in patch_sets:
        patch_set = all_patch_sets.get(patch_set_name)
        if not isinstance(patch_set, dict):
            raise RuntimeError(f"Unknown patch set: {patch_set_name}")

        operations = patch_set.get("operations") if isinstance(patch_set.get("operations"), list) else []
        if not operations:
            continue

        _log(f"Applying patch set '{patch_set_name}'")
        for operation in operations:
            path_value = operation.get("path")
            regex_value = operation.get("regex")
            replace_value = operation.get("replace")
            count_value = int(operation.get("count", 0) or 0)
            if not path_value or regex_value is None or replace_value is None:
                raise RuntimeError(f"Invalid patch operation in set '{patch_set_name}'")

            file_path = worktree / str(path_value)
            if not file_path.exists():
                raise RuntimeError(f"Patch target does not exist: {file_path}")

            original = file_path.read_text(encoding="utf-8")
            if count_value > 0:
                updated, replaced = re.subn(str(regex_value), str(replace_value), original, count=count_value)
                expected = count_value
            else:
                updated, replaced = re.subn(str(regex_value), str(replace_value), original)
                expected = replaced

            if replaced <= 0:
                raise RuntimeError(
                    f"Patch set '{patch_set_name}' made no changes for regex '{regex_value}' in {file_path}"
                )
            if count_value > 0 and replaced != expected:
                raise RuntimeError(
                    f"Patch set '{patch_set_name}' expected {expected} replacements, got {replaced} in {file_path}"
                )

            file_path.write_text(updated, encoding="utf-8")
            touched_paths.add(str(path_value))

        applied.append(str(patch_set_name))

    return applied, sorted(touched_paths)


def _save_state(run_dir: Path, state: dict) -> None:
    state["updated_at"] = _now_iso()
    _write_json(run_dir / "state.json", state)


def _load_or_init_state(
    run_dir: Path,
    run_id: str,
    repo_root: Path,
    spec_path: Path,
    spec: dict,
    base_ref: str,
) -> dict:
    state_path = run_dir / "state.json"
    if state_path.exists():
        return _load_json(state_path)

    state = {
        "run_id": run_id,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "repo_root": str(repo_root),
        "spec_file": str(spec_path),
        "spec_version": spec.get("spec_version"),
        "base_ref": base_ref,
        "next_strategy_index": 0,
        "stage_best_scores": {},
        "results": [],
        "best": None,
    }
    _save_state(run_dir, state)
    return state


def _resolve_spec_paths(args: argparse.Namespace, repo_root: Path) -> tuple[Path, Path, Path, str, bool]:
    runs_dir = (repo_root / args.runs_dir).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    if args.resume_run_id:
        run_id = args.resume_run_id
        run_dir = runs_dir / run_id
        if not run_dir.exists():
            raise SystemExit(f"Run id not found: {run_id}")
        spec_lock_path = run_dir / "spec.lock.json"
        if not spec_lock_path.exists():
            raise SystemExit(f"Missing locked spec for run: {spec_lock_path}")
        return run_dir, spec_lock_path, runs_dir, run_id, True

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    spec_path = (repo_root / args.spec_file).resolve()
    if not spec_path.exists():
        raise SystemExit(f"Spec file not found: {spec_path}")
    spec_lock_path = run_dir / "spec.lock.json"
    shutil.copy2(spec_path, spec_lock_path)
    return run_dir, spec_lock_path, runs_dir, run_id, False


def _write_leaderboard(run_dir: Path, results: list[dict]) -> None:
    ranked = sorted(results, key=lambda item: float(item.get("terminal_score", -9999.0)), reverse=True)
    _write_json(run_dir / "leaderboard.json", {"updated_at": _now_iso(), "trials": ranked})


def _best_summary(best: dict | None) -> str:
    if not best:
        return "none"
    return (
        f"strategy={best.get('strategy_id')} "
        f"terminal_stage={best.get('terminal_stage')} "
        f"score={best.get('terminal_score')} "
        f"branch={best.get('branch')} "
        f"commit={best.get('commit')}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Autonomous matcher tuner with fixed scoring and trial branches.")
    parser.add_argument("--spec-file", type=Path, default=Path("scripts/agent/spec_v1.json"), help="Spec JSON path")
    parser.add_argument("--run-id", type=str, help="Optional run id (default timestamp)")
    parser.add_argument("--resume-run-id", type=str, help="Resume an existing run id")
    parser.add_argument("--runs-dir", type=Path, default=Path("data/ai/agent/runs"), help="Run output directory")
    parser.add_argument("--base-ref", type=str, default="HEAD", help="Git ref used as trial baseline")
    parser.add_argument("--max-strategies", type=int, default=0, help="Optional cap on strategies to execute")
    parser.add_argument(
        "--python-bin",
        type=str,
        default="",
        help="Python executable for worker stage runs (defaults to .venv/bin/python if present)",
    )
    parser.add_argument("--keep-worktrees", action="store_true", help="Keep per-trial worktrees after completion")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path.cwd().resolve()
    python_bin = args.python_bin.strip()
    if not python_bin:
        venv_python = repo_root / ".venv/bin/python"
        python_bin = str(venv_python) if venv_python.exists() else "python3"

    run_dir, spec_lock_path, _runs_dir, run_id, resuming = _resolve_spec_paths(args, repo_root)
    spec = _load_json(spec_lock_path)

    base_ref = args.base_ref
    if resuming:
        state = _load_json(run_dir / "state.json")
        base_ref = str(state.get("base_ref") or base_ref)
    else:
        state = _load_or_init_state(run_dir, run_id, repo_root, spec_lock_path, spec, base_ref)
        resolved_base_ref = _git(repo_root, "rev-parse", base_ref)
        base_ref = resolved_base_ref
        state["base_ref"] = resolved_base_ref
        _save_state(run_dir, state)

    strategies = spec.get("strategies") if isinstance(spec.get("strategies"), list) else []
    if not strategies:
        raise SystemExit("No strategies in spec")

    _log(f"Run id: {run_id}")
    _log(f"Spec: {spec_lock_path}")
    _log(f"Base ref: {base_ref}")
    _log(f"Python bin: {python_bin}")
    _log(f"Starting at strategy index: {state.get('next_strategy_index', 0)}")
    try:
        _run_capture([python_bin, "-c", "import soundfile, rapidfuzz"], cwd=repo_root, check=True)
    except RuntimeError as exc:
        raise SystemExit(
            "Python dependencies missing for selected interpreter. "
            "Install with: pip install -r scripts/requirements-ai.txt "
            f"or pass --python-bin with the correct environment.\n{exc}"
        ) from exc

    overlay_paths = _collect_overlay_paths(repo_root=repo_root, runs_dir=(repo_root / args.runs_dir).resolve())
    _log(f"Local overlay files to sync into trials: {len(overlay_paths)}")

    processed_this_invocation = 0
    try:
        start_index = int(state.get("next_strategy_index", 0) or 0)
        for strategy_index in range(start_index, len(strategies)):
            if args.max_strategies > 0 and processed_this_invocation >= args.max_strategies:
                _log(f"Reached --max-strategies={args.max_strategies}; stopping")
                break

            strategy = strategies[strategy_index]
            strategy_id = str(strategy.get("id") or f"strategy-{strategy_index + 1}")
            trial_number = strategy_index + 1
            trial_slug = _sanitize(strategy_id)
            trial_dir = run_dir / "trials" / f"trial-{trial_number:03d}-{trial_slug}"
            trial_dir.mkdir(parents=True, exist_ok=True)

            strategy_path = trial_dir / "strategy.json"
            _write_json(strategy_path, strategy)

            worktrees_dir = run_dir / "worktrees"
            worktree_path = worktrees_dir / f"trial-{trial_number:03d}-{trial_slug}"
            if worktree_path.exists():
                shutil.rmtree(worktree_path)
            worktrees_dir.mkdir(parents=True, exist_ok=True)

            branch_name = f"codex/agent-{_sanitize(run_id)}-t{trial_number:03d}-{trial_slug}"
            _log(f"Trial {trial_number}: strategy={strategy_id}")
            _log(f"Creating worktree: {worktree_path}")
            _git(repo_root, "worktree", "add", "--detach", str(worktree_path), base_ref)
            _git(repo_root, "-C", str(worktree_path), "switch", "-c", branch_name)
            _sync_overlay_into_worktree(repo_root=repo_root, worktree=worktree_path, overlay_paths=overlay_paths)
            _sync_required_assets(repo_root=repo_root, worktree=worktree_path, spec=spec)

            applied_patch_sets: list[str] = []
            patched_paths: list[str] = []
            try:
                applied_patch_sets, patched_paths = _apply_patch_sets(worktree_path, spec, strategy)
                if patched_paths:
                    _git(repo_root, "-C", str(worktree_path), "add", *patched_paths)
                    _git(
                        repo_root,
                        "-C",
                        str(worktree_path),
                        "commit",
                        "-m",
                        f"matcher-agent: {strategy_id}",
                    )

                stage_scores: dict[str, float] = {}
                terminal_stage = ""
                stopped_early = False

                stages = spec.get("stages") if isinstance(spec.get("stages"), list) else []
                for stage_pos, stage in enumerate(stages):
                    stage_name = str(stage.get("name") or f"stage-{stage_pos + 1}")
                    prior_best = state.get("stage_best_scores", {}).get(stage_name)
                    _log(f"Trial {trial_number}: running stage '{stage_name}'")

                    worker_cmd = [
                        python_bin,
                        "scripts/agent_trial_worker.py",
                        "--spec-file",
                        str(spec_lock_path),
                        "--strategy-file",
                        str(strategy_path),
                        "--stage",
                        stage_name,
                        "--trial-dir",
                        str(trial_dir),
                        "--repo-root",
                        str(worktree_path),
                    ]
                    _run_stream(worker_cmd, cwd=worktree_path, prefix=f"[trial {trial_number} {stage_name}] ")

                    stage_result_path = trial_dir / f"stage-{stage_name}.json"
                    if not stage_result_path.exists():
                        raise RuntimeError(f"Missing stage result: {stage_result_path}")
                    stage_result = _load_json(stage_result_path)
                    stage_score = float(stage_result.get("stage_score", -9999.0))
                    stage_scores[stage_name] = stage_score
                    terminal_stage = stage_name

                    stage_best_scores = state.get("stage_best_scores", {})
                    stage_best = stage_best_scores.get(stage_name)
                    if stage_best is None or stage_score > float(stage_best):
                        stage_best_scores[stage_name] = stage_score
                        state["stage_best_scores"] = stage_best_scores

                    promote_within = stage.get("promote_within_best")
                    is_last_stage = stage_pos == len(stages) - 1
                    if not is_last_stage and promote_within is not None and prior_best is not None:
                        threshold = float(prior_best) - float(promote_within)
                        if stage_score < threshold:
                            _log(
                                f"Trial {trial_number}: stopping after stage '{stage_name}' "
                                f"(score={stage_score:.3f} below threshold={threshold:.3f})"
                            )
                            stopped_early = True
                            break

                commit_hash = _git(repo_root, "-C", str(worktree_path), "rev-parse", "HEAD")
                terminal_score = float(stage_scores.get(terminal_stage, -9999.0))

                trial_result = {
                    "trial": trial_number,
                    "strategy_index": strategy_index,
                    "strategy_id": strategy_id,
                    "description": strategy.get("description"),
                    "branch": branch_name,
                    "commit": commit_hash,
                    "trial_dir": str(trial_dir),
                    "worktree": str(worktree_path),
                    "applied_patch_sets": applied_patch_sets,
                    "stage_scores": stage_scores,
                    "terminal_stage": terminal_stage,
                    "terminal_score": terminal_score,
                    "stopped_early": stopped_early,
                    "completed_at": _now_iso(),
                }

                results = state.get("results") if isinstance(state.get("results"), list) else []
                results.append(trial_result)
                state["results"] = results

                current_best = state.get("best")
                if current_best is None or terminal_score > float(current_best.get("terminal_score", -9999.0)):
                    state["best"] = trial_result
                    _log(f"Trial {trial_number}: new best -> {_best_summary(state['best'])}")

                    diff_text = _git(
                        repo_root,
                        "-C",
                        str(worktree_path),
                        "diff",
                        f"{base_ref}..HEAD",
                        "--",
                        "scripts/ai_pipeline/quran.py",
                        "scripts/ai_pipeline/pipeline.py",
                        "scripts/process_day.py",
                        "scripts/validate_day.py",
                        check=True,
                    )
                    best_dir = run_dir / "best"
                    best_dir.mkdir(parents=True, exist_ok=True)
                    (best_dir / "best.diff").write_text(diff_text, encoding="utf-8")
                    _write_json(best_dir / "best-trial.json", trial_result)

                state["next_strategy_index"] = strategy_index + 1
                _save_state(run_dir, state)
                _write_leaderboard(run_dir, state.get("results", []))

                processed_this_invocation += 1
                _log(f"Trial {trial_number} complete: terminal_score={terminal_score:.3f}")
                _log(f"Current best: {_best_summary(state.get('best'))}")

            finally:
                if not args.keep_worktrees:
                    try:
                        _git(repo_root, "worktree", "remove", "--force", str(worktree_path), check=False)
                    except Exception as cleanup_exc:  # noqa: BLE001
                        _log(f"Worktree cleanup warning: {cleanup_exc}")

        _log("Run completed")
        _log(f"Best trial: {_best_summary(state.get('best'))}")
        _save_state(run_dir, state)
        _write_leaderboard(run_dir, state.get("results", []))

    except KeyboardInterrupt:
        _log("Interrupted by user; saving state")
        _save_state(run_dir, state)
        _write_leaderboard(run_dir, state.get("results", []))
        best = state.get("best")
        if best:
            _log(
                "Best so far: "
                f"strategy={best.get('strategy_id')} score={best.get('terminal_score')} "
                f"branch={best.get('branch')} commit={best.get('commit')}"
            )
        raise SystemExit(130)


if __name__ == "__main__":
    main()
