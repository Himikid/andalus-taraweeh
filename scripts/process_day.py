#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process one Ramadan day audio into UI JSON markers.")
    parser.add_argument("--day", type=int, required=True, help="Ramadan day number (1-30)")
    parser.add_argument("--part", type=int, help="Optional part number for split uploads (e.g. 1, 2)")
    parser.add_argument("--youtube-url", type=str, help="YouTube URL for the day")
    parser.add_argument("--audio-file", type=Path, help="Local audio file path")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path. Defaults to public/data/day-{day}.json",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/audio"),
        help="Directory for downloaded/normalized audio cache",
    )
    parser.add_argument(
        "--quran-corpus",
        type=Path,
        default=Path("data/quran/quran_arabic.json"),
        help="Quran corpus JSON path",
    )
    parser.add_argument(
        "--quran-asad",
        type=Path,
        default=Path("data/quran/quran_asad_en.json"),
        help="Muhammad Asad translation cache JSON path",
    )
    parser.add_argument(
        "--reciter-profiles",
        type=Path,
        default=Path("data/ai/reciter_profiles.json"),
        help="Stored reciter profile embeddings",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="small",
        help="faster-whisper model size (tiny/base/small/medium)",
    )
    parser.add_argument(
        "--bootstrap-reciters",
        action="store_true",
        help="When processing day 1, build Hasan/Samir profiles from first 5 / second 5 prayers.",
    )
    parser.add_argument("--match-min-score", type=int, default=78, help="Minimum fuzzy score for ayah match")
    parser.add_argument("--match-min-overlap", type=float, default=0.18, help="Minimum token overlap for ayah match")
    parser.add_argument(
        "--match-min-confidence",
        type=float,
        default=0.62,
        help="Minimum confidence gate for accepted ayah markers",
    )
    parser.add_argument(
        "--match-min-gap-seconds",
        type=int,
        default=8,
        help="Minimum time gap between consecutive markers",
    )
    parser.add_argument(
        "--no-reuse-transcript-cache",
        action="store_true",
        help="Force fresh transcription instead of using cached transcript segments.",
    )
    parser.add_argument(
        "--transcript-cache-override",
        type=Path,
        help="Optional transcript cache path to force-use (supports window/full reuse and old cache formats).",
    )
    parser.add_argument(
        "--max-audio-seconds",
        type=int,
        help="Optional cap for processing only the first N seconds (useful for tuning).",
    )
    parser.add_argument(
        "--window-start-seconds",
        type=int,
        help="Optional start offset in seconds for processing a windowed portion of the audio.",
    )
    parser.add_argument(
        "--window-end-seconds",
        type=int,
        help="Optional end offset in seconds (exclusive) for processing a windowed portion of the audio.",
    )
    parser.add_argument(
        "--aggressive-infer-fill",
        action="store_true",
        help="Fill missing ayahs between detected anchors more aggressively (less strict local-support gating).",
    )
    parser.add_argument(
        "--start-surah-number",
        type=int,
        help="Optional forced start surah number for constrained matching (e.g. 2 for Al-Baqara).",
    )
    parser.add_argument(
        "--start-ayah",
        type=int,
        help="Optional forced start ayah for constrained matching.",
    )
    parser.add_argument(
        "--day-overrides",
        type=Path,
        default=Path("data/ai/day_overrides.json"),
        help="Optional manual per-day caps (e.g. final ayah/final time).",
    )
    parser.add_argument(
        "--match-overrides-json",
        type=Path,
        help="Optional JSON file containing extra match_quran_markers overrides.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from ai_pipeline import process_day
    except ImportError as exc:
        raise SystemExit(
            "Missing Python dependencies. Install with: pip install -r scripts/requirements-ai.txt"
        ) from exc

    if not args.youtube_url and not args.audio_file:
        raise SystemExit("Provide at least one source: --youtube-url or --audio-file")

    if args.day < 1 or args.day > 30:
        raise SystemExit("--day must be between 1 and 30")

    if args.output:
        output_path = args.output
    elif args.part and args.part > 0:
        output_path = Path(f"public/data/day-{args.day}-part-{args.part}.json")
    else:
        output_path = Path(f"public/data/day-{args.day}.json")

    match_overrides: dict | None = None
    if args.match_overrides_json:
        try:
            payload = json.loads(args.match_overrides_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Unable to load --match-overrides-json: {exc}") from exc

        if isinstance(payload, dict):
            if "match_overrides" in payload and isinstance(payload.get("match_overrides"), dict):
                match_overrides = dict(payload["match_overrides"])
            else:
                match_overrides = dict(payload)
        else:
            raise SystemExit("--match-overrides-json must contain a JSON object")

    payload = process_day(
        day=args.day,
        output_path=output_path,
        cache_dir=(Path(f"data/audio/day-{args.day}-part-{args.part}") if args.part and args.cache_dir == Path("data/audio") else args.cache_dir),
        corpus_path=args.quran_corpus,
        profiles_path=args.reciter_profiles,
        youtube_url=args.youtube_url,
        audio_file=args.audio_file,
        whisper_model=args.whisper_model,
        bootstrap_reciters=args.bootstrap_reciters,
        match_min_score=args.match_min_score,
        match_min_overlap=args.match_min_overlap,
        match_min_confidence=args.match_min_confidence,
        match_min_gap_seconds=args.match_min_gap_seconds,
        match_require_weak_support_for_inferred=not args.aggressive_infer_fill,
        match_start_surah_number=args.start_surah_number,
        match_start_ayah=args.start_ayah,
        reuse_transcript_cache=not args.no_reuse_transcript_cache,
        max_audio_seconds=args.max_audio_seconds,
        window_start_seconds=args.window_start_seconds,
        window_end_seconds=args.window_end_seconds,
        asad_path=args.quran_asad,
        day_overrides_path=args.day_overrides,
        part=args.part,
        transcript_cache_override=args.transcript_cache_override,
        match_overrides=match_overrides,
    )

    print(f"Saved: {output_path}")
    print(f"Reciter segments detected: {payload['meta'].get('reciter_segments_detected', 0)}")
    print(f"Markers detected: {len(payload['markers'])}")
    print(f"Corpus loaded: {payload['meta']['corpus_loaded']}")
    print(f"Asad loaded: {payload['meta']['asad_loaded']}")


if __name__ == "__main__":
    main()
