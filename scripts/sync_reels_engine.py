#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DATA = ROOT / "public" / "data"
DAY_HIGHLIGHTS_TS = ROOT / "data" / "dayHighlights.ts"
VIDEOS_TS = ROOT / "data" / "taraweehVideos.ts"


def extract_day_corpus_summaries(ts_path: Path) -> dict[int, dict]:
    node_script = r"""
const fs = require('fs');
const vm = require('vm');
const file = process.argv[1];
const text = fs.readFileSync(file, 'utf8');
const marker = 'export const dayCorpusSummaries';
const start = text.indexOf(marker);
if (start < 0) throw new Error('dayCorpusSummaries not found');
const braceStart = text.indexOf('{', start);
let depth = 0, inString = false, quote = '', escaped = false, braceEnd = -1;
for (let i = braceStart; i < text.length; i += 1) {
  const ch = text[i];
  if (inString) {
    if (escaped) { escaped = false; continue; }
    if (ch === '\\') { escaped = true; continue; }
    if (ch === quote) { inString = false; quote = ''; }
    continue;
  }
  if (ch === '\'' || ch === '"' || ch === '`') { inString = true; quote = ch; continue; }
  if (ch === '{') { depth += 1; continue; }
  if (ch === '}') {
    depth -= 1;
    if (depth === 0) { braceEnd = i; break; }
  }
}
if (braceEnd < 0) throw new Error('Could not parse dayCorpusSummaries block');
const literal = text.slice(braceStart, braceEnd + 1);
const parsed = vm.runInNewContext('(' + literal + ')');
process.stdout.write(JSON.stringify(parsed));
"""
    out = subprocess.run(["node", "-e", node_script, str(ts_path)], check=True, capture_output=True, text=True)
    raw = json.loads(out.stdout)
    return {int(k): v for k, v in raw.items()}


def extract_video_urls(ts_path: Path) -> dict[int, dict[str, str]]:
    node_script = r"""
const fs = require('fs');
const vm = require('vm');
const file = process.argv[1];
const text = fs.readFileSync(file, 'utf8');
const marker = 'export const taraweehVideos';
const start = text.indexOf(marker);
if (start < 0) throw new Error('taraweehVideos not found');
const braceStart = text.indexOf('{', start);
let depth = 0, inString = false, quote = '', escaped = false, braceEnd = -1;
for (let i = braceStart; i < text.length; i += 1) {
  const ch = text[i];
  if (inString) {
    if (escaped) { escaped = false; continue; }
    if (ch === '\\\\') { escaped = true; continue; }
    if (ch === quote) { inString = false; quote = ''; }
    continue;
  }
  if (ch === "'" || ch === '"' || ch === '`') { inString = true; quote = ch; continue; }
  if (ch === '{') { depth += 1; continue; }
  if (ch === '}') { depth -= 1; if (depth === 0) { braceEnd = i; break; } }
}
if (braceEnd < 0) throw new Error('Could not parse taraweehVideos');
const literal = text.slice(braceStart, braceEnd + 1);
const obj = vm.runInNewContext('(' + literal + ')');
process.stdout.write(JSON.stringify(obj));
"""
    out = subprocess.run(["node", "-e", node_script, str(ts_path)], check=True, capture_output=True, text=True)
    raw = json.loads(out.stdout)
    mapping: dict[int, dict[str, str]] = {}
    for day_str, value in raw.items():
        try:
            day = int(day_str)
        except (TypeError, ValueError):
            continue
        if isinstance(value, str) and value:
            mapping[day] = {"main": f"https://www.youtube.com/watch?v={value}"}
            continue
        if isinstance(value, list):
            item_map: dict[str, str] = {}
            for index, part in enumerate(value, start=1):
                if not isinstance(part, dict):
                    continue
                video_id = str(part.get("videoId", "")).strip()
                if not video_id:
                    continue
                key = f"part-{part.get('id', index)}"
                item_map[key] = f"https://www.youtube.com/watch?v={video_id}"
            if item_map:
                first_url = next(iter(item_map.values()))
                item_map.setdefault("main", first_url)
                mapping[day] = item_map
    return mapping


def day_marker_files(day: int) -> list[Path]:
    exact = PUBLIC_DATA / f"day-{day}.json"
    if exact.exists():
        return [exact]

    pattern = re.compile(rf"^day-{day}-part-(\d+)\.json$")
    parts = [p for p in PUBLIC_DATA.iterdir() if p.is_file() and pattern.match(p.name)]
    parts.sort(key=lambda p: int(pattern.match(p.name).group(1)))
    return parts


def load_markers_for_day(day: int, day_video_map: dict[str, str] | None = None) -> tuple[list[dict], str | None]:
    files = day_marker_files(day)
    if not files:
        return [], None

    merged: list[dict] = []
    day_source = None

    for idx, path in enumerate(files, start=1):
        payload = json.loads(path.read_text(encoding="utf-8"))
        source_url = payload.get("source") if isinstance(payload, dict) else None
        markers = payload.get("markers", []) if isinstance(payload, dict) else []
        if not isinstance(markers, list):
            continue

        source_id = "main" if len(files) == 1 else f"part-{idx}"
        if day_video_map:
            source_url = day_video_map.get(source_id) or day_video_map.get("main") or source_url
        if source_url and not day_source:
            day_source = source_url
        for marker in markers:
            if not isinstance(marker, dict):
                continue
            item = dict(marker)
            item["source_id"] = source_id
            if source_url:
                item["source_url"] = source_url
            merged.append(item)

    merged.sort(key=lambda m: (float(m.get("time", 0)), int(m.get("surah_number", 0)), int(m.get("ayah", 0))))
    return merged, day_source


def sync_day(engine_url: str, day: int, video_map: dict[int, dict[str, str]]) -> dict:
    markers, source_url = load_markers_for_day(day, day_video_map=video_map.get(day))
    if not markers:
        return {"day": day, "status": "skipped", "reason": "no marker files"}

    payload = {
        "day": day,
        "source_url": source_url,
        "full_refresh": True,
        "markers": markers,
    }
    response = post_json(f"{engine_url}/markers/sync", payload)
    return {"day": day, "status": "ok", "markers": len(markers), "response": response}


def sync_summaries(engine_url: str, days: list[int]) -> dict:
    corpus = extract_day_corpus_summaries(DAY_HIGHLIGHTS_TS)
    summaries = []
    for day in days:
        item = corpus.get(day)
        if not item:
            continue
        summaries.append(
            {
                "day": day,
                "title": item.get("title", f"Day {day} Summary"),
                "summary": item.get("summary", ""),
                "themes": item.get("themes", []),
            }
        )

    if not summaries:
        return {"status": "skipped", "reason": "no summaries found"}

    response = post_json(f"{engine_url}/summaries/sync", {"summaries": summaries})
    return {"status": "ok", "count": len(summaries), "response": response}


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=120) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} on {url}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync day markers + corpus summaries to andalus-reels-engine")
    parser.add_argument("--engine-url", default="http://localhost:8090", help="Reels engine base URL")
    parser.add_argument("--days", nargs="+", type=int, default=[2, 3, 4], help="Days to sync")
    args = parser.parse_args()

    engine_url = args.engine_url.rstrip("/")

    results = []
    video_map = extract_video_urls(VIDEOS_TS)
    for day in args.days:
        results.append(sync_day(engine_url, day, video_map=video_map))

    summaries_result = sync_summaries(engine_url, args.days)

    print(json.dumps({"days": results, "summaries": summaries_result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
