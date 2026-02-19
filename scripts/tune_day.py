#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_day import evaluate_day_payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tune ayah matching parameters against validation metrics.")
    parser.add_argument("--day", type=int, required=True, help="Ramadan day number")
    parser.add_argument("--audio-file", type=Path, required=True, help="Normalized day audio WAV path")
    parser.add_argument(
        "--quran-corpus",
        type=Path,
        default=Path("data/quran/quran_arabic.json"),
        help="Quran corpus JSON path",
    )
    parser.add_argument(
        "--tuning-dir",
        type=Path,
        default=Path("data/ai/tuning"),
        help="Directory for candidate outputs and leaderboard",
    )
    parser.add_argument(
        "--max-audio-seconds",
        type=int,
        default=900,
        help="Process only first N seconds during tuning (default: 900).",
    )
    return parser.parse_args()


def _score(summary: dict) -> float:
    pass_rate = float(summary.get("pass_rate", 0.0))
    mean_score = float(summary.get("mean_score", 0.0))
    backtracks = int(summary.get("chronology_backtracks", 0))
    duplicates = int(summary.get("duplicates", 0))
    markers = int(summary.get("markers", 0))
    confidence_spread = float(summary.get("confidence_spread", 0.0))
    if markers == 0:
        return -999.0
    if markers < 5:
        return -500.0 + (markers * 5.0) - (backtracks * 20.0) - (duplicates * 10.0)

    coverage = min(markers, 20) / 20.0
    return (
        (pass_rate * 100.0)
        + (mean_score / 2.0)
        + (confidence_spread * 10.0)
        + (coverage * 40.0)
        - (backtracks * 12.0)
        - (duplicates * 6.0)
    )


def main() -> None:
    args = parse_args()

    try:
        from ai_pipeline import process_day
    except ImportError as exc:
        raise SystemExit(
            "Missing Python dependencies. Install with: pip install -r scripts/requirements-ai.txt"
        ) from exc

    day_dir = args.tuning_dir / f"day-{args.day}"
    day_dir.mkdir(parents=True, exist_ok=True)

    param_grid = [
        {"match_min_score": 78, "match_min_overlap": 0.08, "match_min_confidence": 0.55, "match_min_gap_seconds": 5},
        {"match_min_score": 79, "match_min_overlap": 0.1, "match_min_confidence": 0.58, "match_min_gap_seconds": 6},
        {"match_min_score": 80, "match_min_overlap": 0.12, "match_min_confidence": 0.62, "match_min_gap_seconds": 6},
        {"match_min_score": 82, "match_min_overlap": 0.15, "match_min_confidence": 0.66, "match_min_gap_seconds": 8},
        {"match_min_score": 84, "match_min_overlap": 0.15, "match_min_confidence": 0.68, "match_min_gap_seconds": 8},
        {"match_min_score": 86, "match_min_overlap": 0.18, "match_min_confidence": 0.7, "match_min_gap_seconds": 10},
        {"match_min_score": 88, "match_min_overlap": 0.2, "match_min_confidence": 0.72, "match_min_gap_seconds": 10},
    ]

    leaderboard: list[dict] = []
    best: dict | None = None

    for index, params in enumerate(param_grid, start=1):
        output_path = day_dir / f"candidate-{index}.json"
        payload = process_day(
            day=args.day,
            output_path=output_path,
            cache_dir=Path("data/audio"),
            corpus_path=args.quran_corpus,
            profiles_path=Path("data/ai/reciter_profiles.json"),
            youtube_url=None,
            audio_file=args.audio_file,
            whisper_model="tiny",
            bootstrap_reciters=False,
            reuse_transcript_cache=True,
            max_audio_seconds=args.max_audio_seconds,
            **params,
        )

        cache_suffix = f"{args.max_audio_seconds}s" if args.max_audio_seconds and args.max_audio_seconds > 0 else "full"
        transcript_cache = Path(f"data/ai/cache/day-{args.day}-transcript-{cache_suffix}.json")
        report = evaluate_day_payload(
            day_payload=payload,
            quran_corpus_path=args.quran_corpus,
            transcript_path=transcript_cache,
            pass_score=80.0,
        )
        summary = report["summary"]
        candidate_score = _score(summary)

        candidate = {
            "candidate": index,
            "params": params,
            "score": round(candidate_score, 3),
            "summary": summary,
            "output_path": str(output_path),
        }
        leaderboard.append(candidate)

        if best is None or candidate_score > float(best["score"]):
            best = candidate

    leaderboard.sort(key=lambda item: item["score"], reverse=True)

    leaderboard_path = day_dir / "leaderboard.json"
    with leaderboard_path.open("w", encoding="utf-8") as handle:
        json.dump({"day": args.day, "best": best, "candidates": leaderboard}, handle, ensure_ascii=False, indent=2)

    if best is None:
        raise SystemExit("No candidates were generated")

    best_payload_path = Path(str(best["output_path"]))
    final_path = Path(f"public/data/day-{args.day}.json")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(best_payload_path.read_text(encoding="utf-8"), encoding="utf-8")

    print(f"Saved leaderboard: {leaderboard_path}")
    print(f"Best candidate: {best['candidate']} score={best['score']}")
    print(f"Final output: {final_path}")


if __name__ == "__main__":
    main()
