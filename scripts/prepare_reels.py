#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HIGHLIGHTS_TS = ROOT / "data/dayHighlights.ts"
DEFAULT_REELS_DIR = ROOT / "data/reels"
DEFAULT_DAY_JSON_DIR = ROOT / "public/data"
MAKE_REEL_SCRIPT = ROOT / "scripts/make_reel.py"


@dataclass
class AyahRange:
    surah_number: int
    ayah_start: int
    ayah_end: int


def _extract_day_highlights_from_ts(ts_path: Path) -> dict[str, Any]:
    node_script = r"""
const fs = require("fs");
const vm = require("vm");

const file = process.argv[1];
const text = fs.readFileSync(file, "utf8");
const marker = "export const dayHighlights";
const start = text.indexOf(marker);
if (start < 0) {
  throw new Error("Could not find dayHighlights export in " + file);
}
const braceStart = text.indexOf("{", start);
if (braceStart < 0) {
  throw new Error("Could not find opening brace for dayHighlights");
}

let depth = 0;
let inString = false;
let quote = "";
let escaped = false;
let braceEnd = -1;

for (let i = braceStart; i < text.length; i += 1) {
  const ch = text[i];
  if (inString) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      continue;
    }
    if (ch === quote) {
      inString = false;
      quote = "";
    }
    continue;
  }

  if (ch === "'" || ch === '"' || ch === "`") {
    inString = true;
    quote = ch;
    continue;
  }

  if (ch === "{") {
    depth += 1;
    continue;
  }
  if (ch === "}") {
    depth -= 1;
    if (depth === 0) {
      braceEnd = i;
      break;
    }
  }
}

if (braceEnd < 0) {
  throw new Error("Could not find closing brace for dayHighlights");
}

const literal = text.slice(braceStart, braceEnd + 1);
const parsed = vm.runInNewContext("(" + literal + ")");
process.stdout.write(JSON.stringify(parsed));
"""
    result = subprocess.run(
        ["node", "-e", node_script, str(ts_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("Parsed dayHighlights payload is not an object.")
    return payload


def _parse_ayah_ref(ayah_ref: str) -> AyahRange:
    ref = ayah_ref.strip()
    if ":" not in ref:
        raise ValueError(f"Invalid ayahRef '{ayah_ref}'")
    surah_raw, ayah_raw = ref.split(":", 1)
    surah_number = int(surah_raw)
    if "-" in ayah_raw:
        start_raw, end_raw = ayah_raw.split("-", 1)
        ayah_start = int(start_raw)
        ayah_end = int(end_raw)
    else:
        ayah_start = int(ayah_raw)
        ayah_end = ayah_start
    if ayah_end < ayah_start:
        ayah_end = ayah_start
    return AyahRange(surah_number=surah_number, ayah_start=ayah_start, ayah_end=ayah_end)


def _format_ts(seconds: int) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    return f"{hours}:{minutes:02d}:{secs:02d}"


def _parse_ts(value: str) -> int:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Empty timestamp")
    if re.fullmatch(r"\d+", raw):
        return int(raw)
    parts = raw.split(":")
    if len(parts) == 2:
        return (int(parts[0]) * 60) + int(parts[1])
    if len(parts) == 3:
        return (int(parts[0]) * 3600) + (int(parts[1]) * 60) + int(parts[2])
    raise ValueError(f"Invalid timestamp '{value}'")


def _load_day_payload(day: int, explicit_day_json: str | None) -> tuple[dict[str, Any], list[Path]]:
    if explicit_day_json:
        path = Path(explicit_day_json)
        if not path.exists():
            raise RuntimeError(f"Day JSON not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid JSON payload in {path}")
        markers = payload.get("markers", [])
        if not isinstance(markers, list):
            payload["markers"] = []
        return payload, [path]

    primary = DEFAULT_DAY_JSON_DIR / f"day-{day}.json"
    if primary.exists():
        payload = json.loads(primary.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"Invalid JSON payload in {primary}")
        markers = payload.get("markers", [])
        if not isinstance(markers, list):
            payload["markers"] = []
        return payload, [primary]

    part_files = sorted(DEFAULT_DAY_JSON_DIR.glob(f"day-{day}-part-*.json"))
    if not part_files:
        raise RuntimeError(f"No day JSON found for day {day} (expected {primary} or day-{day}-part-*.json).")

    merged_markers: list[Any] = []
    source = ""
    for part in part_files:
        part_payload = json.loads(part.read_text(encoding="utf-8"))
        if not isinstance(part_payload, dict):
            continue
        if not source:
            source = str(part_payload.get("source", "")).strip()
        markers = part_payload.get("markers", [])
        if isinstance(markers, list):
            merged_markers.extend(markers)

    deduped_markers: list[Any] = []
    seen_marker_keys: set[tuple[int, int, int]] = set()
    for marker in merged_markers:
        if not isinstance(marker, dict):
            continue
        try:
            key = (
                int(marker.get("surah_number", 0) or 0),
                int(marker.get("ayah", 0) or 0),
                int(marker.get("time", 0) or 0),
            )
        except (TypeError, ValueError):
            deduped_markers.append(marker)
            continue
        if key in seen_marker_keys:
            continue
        seen_marker_keys.add(key)
        deduped_markers.append(marker)

    merged = {
        "day": day,
        "source": source,
        "markers": deduped_markers,
        "meta": {"merged_from_parts": [str(path) for path in part_files]},
    }
    return merged, part_files


def _marker_for_ayah(markers: list[dict[str, Any]], surah_number: int, ayah: int) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for marker in markers:
        if int(marker.get("surah_number", -1)) != surah_number:
            continue
        if int(marker.get("ayah", -1)) != ayah:
            continue
        if best is None:
            best = marker
            continue
        if int(marker.get("time", 0)) < int(best.get("time", 0)):
            best = marker
    return best


def _suggest_duration(start_marker: dict[str, Any] | None, end_marker: dict[str, Any] | None) -> int:
    if start_marker and end_marker:
        start_time = int(start_marker.get("time", 0))
        end_time = int(end_marker.get("time", 0))
        if end_time > start_time:
            return max(14, min(45, (end_time - start_time) + 8))
    return 22


def command_prepare(args: argparse.Namespace) -> int:
    highlights = _extract_day_highlights_from_ts(Path(args.highlights_ts))
    day_key = str(int(args.day))
    day_items = highlights.get(day_key)
    if not isinstance(day_items, list) or not day_items:
        raise RuntimeError(f"No dayHighlights found for day {args.day}.")

    day_payload, day_sources = _load_day_payload(int(args.day), args.day_json)
    markers = [m for m in day_payload.get("markers", []) if isinstance(m, dict)]
    source_text = str(day_payload.get("source", "")).strip()
    default_youtube = source_text if source_text.startswith("http") else ""

    clips: list[dict[str, Any]] = []
    for idx, item in enumerate(day_items, start=1):
        if not isinstance(item, dict):
            continue
        ayah_ref = str(item.get("ayahRef", "")).strip()
        if not ayah_ref:
            continue
        parsed = _parse_ayah_ref(ayah_ref)
        start_marker = _marker_for_ayah(markers, parsed.surah_number, parsed.ayah_start)
        end_marker = _marker_for_ayah(markers, parsed.surah_number, parsed.ayah_end)
        if start_marker is None and end_marker is not None:
            start_marker = end_marker
        if end_marker is None and start_marker is not None:
            end_marker = start_marker

        start_seconds = int((start_marker or {}).get("time", 0)) if start_marker else None
        end_seconds_hint = None
        if end_marker is not None:
            raw_end = (end_marker or {}).get("end_time")
            if raw_end is None:
                raw_end = (end_marker or {}).get("time")
            if raw_end is not None:
                end_seconds_hint = int(raw_end)
        sheikh = str((start_marker or {}).get("reciter", "")).strip() or "TBD"
        suggested_duration = _suggest_duration(start_marker, end_marker)
        if start_seconds is not None:
            fallback_end = start_seconds + suggested_duration
            end_seconds = max(fallback_end, int(end_seconds_hint)) if end_seconds_hint is not None else fallback_end
        else:
            end_seconds = None

        clip = {
            "id": f"d{args.day}-h{idx}",
            "enabled": True,
            "theme_type": str(item.get("themeType", "")).strip(),
            "title": str(item.get("shortTitle", "")).strip(),
            "ayah_ref": ayah_ref,
            "surah_number": parsed.surah_number,
            "ayah_start": parsed.ayah_start,
            "ayah_end": parsed.ayah_end,
            "summary": str(item.get("summary", "")).strip(),
            "key_takeaway": str(item.get("keyTakeaway", "")).strip(),
            "references": item.get("references", []),
            "timestamp_edit_required": True,
            "start_timestamp": _format_ts(start_seconds) if start_seconds is not None else "",
            "end_timestamp": _format_ts(end_seconds) if end_seconds is not None else "",
            "duration_seconds": suggested_duration,
            "sheikh": sheikh,
            "notes": "Review start_timestamp and duration_seconds manually before generate.",
            "marker_match": {
                "start_marker_quality": (start_marker or {}).get("quality"),
                "end_marker_quality": (end_marker or {}).get("quality"),
                "start_marker_time_hms": _format_ts(int((start_marker or {}).get("time", 0))) if start_marker else "",
                "end_marker_time_hms": _format_ts(int((end_marker or {}).get("time", 0))) if end_marker else "",
            },
            "make_reel_overrides": {
                "variants": "clean,focus,context",
                "style": "fit",
                "size": "1080x1920",
            },
        }
        clips.append(clip)

    output_path = Path(args.output) if args.output else (DEFAULT_REELS_DIR / f"day-{args.day}-reel-draft.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    out_payload = {
        "workflow": "reel-draft-v1",
        "day": int(args.day),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "confirmed": False,
        "instructions": "Edit start_timestamp/duration/sheikh per clip, then set confirmed=true and run generate.",
        "reel_defaults": {
            "youtube_url": args.youtube_url or default_youtube,
            "video_file": args.video_file or "",
            "align_subtitles": bool(args.align_subtitles),
            "prefer_marker_english": True,
            "subtitle_model": "medium",
        },
        "day_sources": [str(path) for path in day_sources],
        "clips": clips,
    }
    output_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote draft reel input: {output_path}")
    print("Next:")
    print("1) Edit that file and tune start_timestamp/duration_seconds.")
    print("2) Set confirmed to true in the file when ready.")
    print(f"3) Run: python scripts/prepare_reels.py generate --input {output_path} --confirm")
    return 0


def _append_arg(cmd: list[str], flag: str, value: Any) -> None:
    if value is None:
        return
    text = str(value).strip()
    if not text:
        return
    cmd.extend([flag, text])


def command_generate(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    if not input_path.exists():
        raise RuntimeError(f"Input file not found: {input_path}")

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid reel draft payload.")

    if not args.confirm:
        raise RuntimeError("Generation requires --confirm.")
    if not bool(payload.get("confirmed", False)):
        raise RuntimeError('Draft is not confirmed. Set "confirmed": true in the input JSON first.')

    day = int(payload.get("day"))
    defaults = payload.get("reel_defaults", {}) if isinstance(payload.get("reel_defaults"), dict) else {}
    clips = payload.get("clips", [])
    if not isinstance(clips, list) or not clips:
        raise RuntimeError("No clips found in draft.")

    ran = 0
    skipped = 0
    for clip in clips:
        if not isinstance(clip, dict):
            skipped += 1
            continue
        if not bool(clip.get("enabled", True)):
            skipped += 1
            continue

        start_timestamp = str(clip.get("start_timestamp", "")).strip()
        sheikh = str(clip.get("sheikh", "")).strip()
        if not start_timestamp or not sheikh:
            print(f"Skipping {clip.get('id', 'unknown')}: missing start_timestamp or sheikh.")
            skipped += 1
            continue

        surah_number = int(clip.get("surah_number"))
        ayah_start = int(clip.get("ayah_start"))
        ayah_end = int(clip.get("ayah_end", ayah_start))
        duration_seconds = float(clip.get("duration_seconds", 22))
        end_timestamp = str(clip.get("end_timestamp", "")).strip()
        if end_timestamp:
            try:
                start_sec = _parse_ts(start_timestamp)
                end_sec = _parse_ts(end_timestamp)
                if end_sec > start_sec:
                    duration_seconds = max(5.0, float(end_sec - start_sec))
            except ValueError:
                pass
        overrides = clip.get("make_reel_overrides", {}) if isinstance(clip.get("make_reel_overrides"), dict) else {}

        cmd = [
            "python3",
            str(MAKE_REEL_SCRIPT),
            "--day",
            str(day),
            "--surah-number",
            str(surah_number),
            "--ayah",
            str(ayah_start),
            "--start",
            start_timestamp,
            "--duration",
            str(duration_seconds),
            "--sheikh",
            sheikh,
            "--subtitle-model",
            str(defaults.get("subtitle_model", "medium")),
        ]
        if ayah_end > ayah_start:
            cmd.extend(["--ayah-end", str(ayah_end)])
        _append_arg(cmd, "--youtube-url", defaults.get("youtube_url", ""))
        _append_arg(cmd, "--video-file", defaults.get("video_file", ""))
        if bool(defaults.get("align_subtitles", False)):
            cmd.append("--align-subtitles")
        if bool(defaults.get("prefer_marker_english", True)):
            cmd.append("--prefer-marker-english")
        _append_arg(cmd, "--variants", overrides.get("variants"))
        _append_arg(cmd, "--style", overrides.get("style"))
        _append_arg(cmd, "--size", overrides.get("size"))

        if args.dry_run:
            print("DRY RUN:", " ".join(cmd))
        else:
            subprocess.run(cmd, check=True, cwd=str(ROOT))
        ran += 1

    print(f"Done. generated={ran} skipped={skipped} dry_run={args.dry_run}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare editable reel metadata from day highlights, then generate clips via make_reel.py.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Generate editable draft JSON for a day.")
    prepare.add_argument("--day", type=int, required=True, help="Ramadan day number.")
    prepare.add_argument("--day-json", type=str, help="Optional explicit day JSON path.")
    prepare.add_argument("--highlights-ts", type=str, default=str(DEFAULT_HIGHLIGHTS_TS), help="Path to dayHighlights.ts.")
    prepare.add_argument("--output", type=str, help="Output draft JSON path.")
    prepare.add_argument("--youtube-url", type=str, help="Override default YouTube URL in reel_defaults.")
    prepare.add_argument("--video-file", type=str, help="Optional local video file in reel_defaults.")
    prepare.add_argument("--align-subtitles", action="store_true", help="Enable align_subtitles in reel_defaults.")
    prepare.set_defaults(func=command_prepare)

    generate = subparsers.add_parser("generate", help="Generate reels from an edited draft JSON.")
    generate.add_argument("--input", type=str, required=True, help="Draft JSON path produced by prepare.")
    generate.add_argument("--confirm", action="store_true", help="Required guard before generation.")
    generate.add_argument("--dry-run", action="store_true", help="Print make_reel commands instead of running.")
    generate.set_defaults(func=command_generate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
