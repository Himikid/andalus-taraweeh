#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    # Google Drive/iCloud-backed files can briefly fail with Errno 89 ("Operation canceled")
    # while the file is being synced. Retry a few times before failing hard.
    last_error: Exception | None = None
    for attempt in range(8):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt == 7:
                break
            time.sleep(0.35 + (attempt * 0.1))
    assert last_error is not None
    raise last_error


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_label(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip())
    return cleaned.strip("-_") or "job"


def _request_id_for(
    *,
    day: int,
    kind: str,
    youtube_url: str,
    start_sec: int | None,
    end_sec: int | None,
    model: str,
    device: str,
    compute_type: str,
    beam_size: int,
    language: str,
    chunk_seconds: int,
    vad_filter: bool,
    vad_threshold: float,
    min_silence_ms: int,
    speech_pad_ms: int,
) -> str:
    payload = {
        "day": day,
        "kind": kind,
        "youtube_url": youtube_url.strip(),
        "start_sec": start_sec,
        "end_sec": end_sec,
        "model": model,
        "device": device,
        "compute_type": compute_type,
        "beam_size": beam_size,
        "language": language,
        "chunk_seconds": chunk_seconds,
        "vad_filter": vad_filter,
        "vad_threshold": vad_threshold,
        "min_silence_ms": min_silence_ms,
        "speech_pad_ms": speech_pad_ms,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return _safe_label(f"day{day}-{kind}-{start_sec or 0}-{end_sec or 0}-{digest}")


def _parse_float_list(raw: str, fallback: list[float]) -> list[float]:
    values: list[float] = []
    for token in str(raw or "").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            values.append(float(token))
        except ValueError:
            continue
    if not values:
        return list(fallback)
    # keep order, drop duplicates by rounded string key
    seen: set[str] = set()
    unique: list[float] = []
    for value in values:
        key = f"{value:.6f}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique


def _normalize_request_device(raw: str) -> str:
    value = str(raw or "").strip().lower()
    if value in {"cuda", "gpu"}:
        return "cuda"
    if value == "cpu":
        return "cpu"
    return "auto"


def _load_transcript_segments(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    segments = payload.get("segments", [])
    output: list[dict[str, Any]] = []
    for segment in segments:
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        row = {
            "start": float(segment.get("start", 0.0)),
            "end": float(segment.get("end", 0.0)),
            "text": text,
            "words": [],
        }
        for word in segment.get("words", []):
            wtxt = str(word.get("text", "")).strip()
            if not wtxt:
                continue
            row["words"].append(
                {
                    "start": float(word.get("start", row["start"])),
                    "end": float(word.get("end", row["end"])),
                    "text": wtxt,
                }
            )
        output.append(row)
    output.sort(key=lambda item: (float(item["start"]), float(item["end"])))
    return output


def _merge_transcripts(input_paths: list[Path], output_path: Path) -> Path:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for path in input_paths:
        for segment in _load_transcript_segments(path):
            key = (
                int(round(float(segment["start"]) * 100)),
                int(round(float(segment["end"]) * 100)),
                str(segment["text"]),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(segment)

    merged.sort(key=lambda item: (float(item["start"]), float(item["end"])))
    _write_json(
        output_path,
        {
            "segments": merged,
            "meta": {
                "sources": [str(path) for path in input_paths],
                "segments_count": len(merged),
                "generated_at": _utc_now(),
            },
        },
    )
    return output_path


def _marker_signature_rows(markers: list[dict[str, Any]]) -> list[tuple[int, int, int, str]]:
    rows: list[tuple[int, int, int, str]] = []
    for marker in markers:
        try:
            surah_number = int(marker.get("surah_number") or 0)
            ayah = int(marker.get("ayah") or 0)
            t = int(marker.get("time") or marker.get("start_time") or 0)
        except (TypeError, ValueError):
            continue
        quality = str(marker.get("quality") or "").strip().lower()
        rows.append((surah_number, ayah, t, quality))
    rows.sort()
    return rows


def _marker_signature(payload: dict[str, Any]) -> str:
    markers = [marker for marker in payload.get("markers", []) if isinstance(marker, dict)]
    direct = [marker for marker in markers if _is_direct_marker_row(marker)]
    non_override = [marker for marker in markers if not _is_override_fill_marker_row(marker)]

    rows = _marker_signature_rows(direct)
    if not rows:
        rows = _marker_signature_rows(non_override)
    if not rows:
        rows = _marker_signature_rows(markers)
    raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _marker_quality_counts(payload: dict[str, Any], *, exclude_override_fill: bool = False) -> dict[str, int]:
    counts: dict[str, int] = {
        "manual": 0,
        "high": 0,
        "ambiguous": 0,
        "inferred": 0,
        "other": 0,
    }
    for marker in payload.get("markers", []):
        if not isinstance(marker, dict):
            continue
        if exclude_override_fill and str(marker.get("origin") or "").strip().lower() == "override_surah_fill":
            continue
        quality = str(marker.get("quality") or "").strip().lower()
        if quality in counts:
            counts[quality] += 1
        else:
            counts["other"] += 1
    return counts


def _quality_counts_direct_total(counts: dict[str, Any] | None) -> int:
    if not isinstance(counts, dict):
        return 0
    total = 0
    for key in ("manual", "high", "ambiguous"):
        try:
            total += int(counts.get(key, 0))
        except (TypeError, ValueError):
            continue
    return total


def _resolve_day_window(day: int, overrides_path: Path | None) -> tuple[int | None, int | None]:
    if overrides_path is None or not overrides_path.exists():
        return None, None
    payload = _read_json(overrides_path)
    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return None, None
    start_raw = day_config.get("start_time")
    end_raw = day_config.get("final_time")
    try:
        start = int(start_raw) if start_raw is not None else None
    except (TypeError, ValueError):
        start = None
    try:
        end = int(end_raw) if end_raw is not None else None
    except (TypeError, ValueError):
        end = None
    return start, end


def _resolve_day_target(day: int, overrides_path: Path | None) -> dict[str, Any]:
    target: dict[str, Any] = {
        "final_time": None,
        "final_surah": None,
        "final_ayah": None,
    }
    if overrides_path is None or not overrides_path.exists():
        return target
    payload = _read_json(overrides_path)
    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return target

    final_surah = day_config.get("final_surah")
    if isinstance(final_surah, str) and final_surah.strip():
        target["final_surah"] = final_surah.strip()
    final_ayah_raw = day_config.get("final_ayah")
    try:
        final_ayah = int(final_ayah_raw) if final_ayah_raw is not None else None
    except (TypeError, ValueError):
        final_ayah = None
    if final_ayah is not None and final_ayah > 0:
        target["final_ayah"] = final_ayah
    final_time_raw = day_config.get("final_time")
    try:
        final_time = int(final_time_raw) if final_time_raw is not None else None
    except (TypeError, ValueError):
        final_time = None
    if final_time is not None and final_time >= 0:
        target["final_time"] = final_time
    return target


def _resolve_day_duplicate_markers(day: int, overrides_path: Path | None) -> list[dict[str, Any]]:
    if overrides_path is None or not overrides_path.exists():
        return []
    payload = _read_json(overrides_path)
    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return []
    rows = day_config.get("duplicate_markers", [])
    if not isinstance(rows, list):
        return []
    output: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            surah_number = int(row.get("surah_number"))
            ayah = int(row.get("ayah"))
            time_value = int(row.get("time", row.get("start_time")))
        except (TypeError, ValueError):
            continue
        if surah_number <= 0 or ayah <= 0 or time_value < 0:
            continue
        reciter = str(row.get("reciter", "")).strip() or None
        output.append(
            {
                "surah_number": surah_number,
                "ayah": ayah,
                "time": time_value,
                "reciter": reciter,
            }
        )
    output.sort(key=lambda item: int(item["time"]))
    return output


def _resolve_day_enforce_match_blocks(day: int, part: int | None, overrides_path: Path | None) -> bool:
    if overrides_path is None or not overrides_path.exists():
        return False
    payload = _read_json(overrides_path)
    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return False

    raw = day_config.get("enforce_match_blocks")
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_day_match_block_ranges(
    day: int,
    part: int | None,
    overrides_path: Path | None,
) -> list[tuple[int, int, tuple[int, int] | None, tuple[int, int] | None]]:
    if overrides_path is None or not overrides_path.exists():
        return []
    payload = _read_json(overrides_path)
    overrides = payload.get("day_overrides", payload)
    day_config = overrides.get(str(day)) if isinstance(overrides, dict) else None
    if not isinstance(day_config, dict):
        return []
    rows = day_config.get("match_blocks", [])
    if not isinstance(rows, list):
        return []

    blocks: list[tuple[int, int, tuple[int, int] | None, tuple[int, int] | None]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item_part = row.get("part")
        if item_part is not None:
            try:
                if int(item_part) != int(part or 0):
                    continue
            except (TypeError, ValueError):
                continue
        try:
            start_time = int(float(row.get("start_time")))
        except (TypeError, ValueError):
            continue
        end_raw = row.get("end_time", day_config.get("final_time"))
        try:
            end_time = int(float(end_raw))
        except (TypeError, ValueError):
            continue
        if end_time < start_time:
            continue

        lower_surah_raw = row.get("min_surah_number", row.get("start_surah_number"))
        lower_ayah_raw = row.get("min_ayah", row.get("start_ayah"))
        upper_surah_raw = row.get("max_surah_number", row.get("end_surah_number"))
        upper_ayah_raw = row.get("max_ayah", row.get("end_ayah"))

        lower_key: tuple[int, int] | None = None
        upper_key: tuple[int, int] | None = None
        try:
            if lower_surah_raw is not None and lower_ayah_raw is not None:
                lower_key = (int(lower_surah_raw), int(lower_ayah_raw))
        except (TypeError, ValueError):
            lower_key = None
        try:
            if upper_surah_raw is not None and upper_ayah_raw is not None:
                upper_key = (int(upper_surah_raw), int(upper_ayah_raw))
        except (TypeError, ValueError):
            upper_key = None
        if lower_key is not None and upper_key is not None and upper_key < lower_key:
            lower_key, upper_key = upper_key, lower_key

        blocks.append((start_time, end_time, lower_key, upper_key))

    blocks.sort(key=lambda item: (item[0], item[1]))
    return blocks


def _resolve_drive_root(
    explicit_drive_root: Path | None,
    config_path: Path | None,
) -> Path:
    if explicit_drive_root is not None:
        return explicit_drive_root.expanduser().resolve()
    if config_path is None or not config_path.exists():
        raise FileNotFoundError(
            f"Drive root not provided and config missing: {config_path}"
        )
    payload = _read_json(config_path)
    drive_root_raw = payload.get("drive_root")
    if not drive_root_raw:
        raise RuntimeError(
            f"Config {config_path} is missing required key: drive_root"
        )
    return Path(str(drive_root_raw)).expanduser().resolve()


def _resolve_callback_token(config_path: Path | None) -> str:
    if config_path is None or not config_path.exists():
        return ""
    try:
        payload = _read_json(config_path)
    except Exception:
        return ""
    callback = payload.get("callback")
    if not isinstance(callback, dict):
        return ""
    token = callback.get("bearer_token")
    if token is None:
        return ""
    return str(token).strip()


def _resolve_callback_url(config_path: Path | None) -> str:
    if config_path is None or not config_path.exists():
        return ""
    try:
        payload = _read_json(config_path)
    except Exception:
        return ""
    callback = payload.get("callback")
    if not isinstance(callback, dict):
        return ""
    value = callback.get("url")
    if value is None:
        return ""
    return str(value).strip()


def _load_webhook_module():
    module_path = Path(__file__).resolve().parent / "colab" / "local_transcript_webhook.py"
    spec = importlib.util.spec_from_file_location("local_transcript_webhook", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load webhook module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _load_firestore_module():
    module_path = Path(__file__).resolve().parent / "colab" / "firestore_rest.py"
    spec = importlib.util.spec_from_file_location("firestore_rest", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load firestore module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to load firestore module: {exc}") from exc
    return module


def _resolve_response_transcript_path(transcript_ref: str, drive_root: Path) -> Path:
    raw = str(transcript_ref).strip()
    candidate = Path(raw)
    if not candidate.is_absolute():
        return (drive_root / candidate).resolve()

    # Colab absolute paths are not directly valid on local macOS.
    # Map /content/drive/MyDrive/... into the local synced drive root.
    colab_prefix = "/content/drive/MyDrive/"
    if raw.startswith(colab_prefix):
        relative = raw[len(colab_prefix):].strip("/")
        parts = [part for part in relative.split("/") if part]
        known_subdirs = {
            "requests",
            "responses",
            "transcripts",
            "audio-cache",
            "normalized-cache",
            "clip-cache",
            "incoming_audio",
            "jobs",
        }
        if parts:
            if parts[0] == drive_root.name:
                parts = parts[1:]
            elif parts[0] not in known_subdirs and len(parts) >= 2:
                parts = parts[1:]
        return drive_root.joinpath(*parts).resolve()

    return candidate


def _marker_quality_rank(value: str | None) -> int:
    quality = str(value or "").strip().lower()
    if quality == "manual":
        return 4
    if quality == "high":
        return 3
    if quality == "ambiguous":
        return 2
    if quality == "inferred":
        return 1
    return 0


def _marker_confidence(marker: dict[str, Any]) -> float:
    value = marker.get("confidence")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _is_strong_marker_row(marker: dict[str, Any]) -> bool:
    quality = str(marker.get("quality", "")).strip().lower()
    if quality in {"manual", "high"}:
        return True
    if quality == "ambiguous" and _marker_confidence(marker) >= 0.72:
        return True
    return False


def _is_direct_marker_row(marker: dict[str, Any]) -> bool:
    quality = str(marker.get("quality", "")).strip().lower()
    return quality in {"manual", "high", "ambiguous"}


def _is_override_fill_marker_row(marker: dict[str, Any]) -> bool:
    origin = str(marker.get("origin") or "").strip().lower()
    return origin == "override_surah_fill"


def _extract_marker_rows(
    payload: dict[str, Any],
    window_start: int | None,
    window_end: int | None,
    strong_only: bool = False,
    direct_only: bool = False,
    exclude_override_fill: bool = False,
) -> list[dict[str, Any]]:
    markers = payload.get("markers", [])
    rows: list[dict[str, Any]] = []
    for marker in markers:
        if not isinstance(marker, dict):
            continue
        if exclude_override_fill and _is_override_fill_marker_row(marker):
            continue
        if strong_only and not _is_strong_marker_row(marker):
            continue
        if direct_only and not _is_direct_marker_row(marker):
            continue
        t = int(marker.get("time") or marker.get("start_time") or 0)
        if window_start is not None and t < window_start:
            continue
        if window_end is not None and t > window_end:
            continue
        rows.append(marker)
    rows.sort(key=lambda item: int(item.get("time") or item.get("start_time") or 0))
    return rows


def _extract_marker_times(
    payload: dict[str, Any],
    window_start: int | None,
    window_end: int | None,
    strong_only: bool = False,
    direct_only: bool = False,
    exclude_override_fill: bool = False,
) -> list[int]:
    rows = _extract_marker_rows(
        payload=payload,
        window_start=window_start,
        window_end=window_end,
        strong_only=strong_only,
        direct_only=direct_only,
        exclude_override_fill=exclude_override_fill,
    )
    values = sorted({int(item.get("time") or item.get("start_time") or 0) for item in rows})
    return values


def _propose_recovery_windows(
    payload: dict[str, Any],
    window_start: int | None,
    window_end: int | None,
    max_gap_seconds: int,
    max_windows: int,
    max_window_seconds: int,
    overlap_seconds: int,
    pad_seconds: int,
    target_final_time: int | None = None,
    force_tail: bool = False,
) -> list[tuple[int, int]]:
    strong_marker_times = _extract_marker_times(
        payload,
        window_start=window_start,
        window_end=window_end,
        strong_only=True,
        exclude_override_fill=True,
    )
    direct_marker_times = _extract_marker_times(
        payload,
        window_start=window_start,
        window_end=window_end,
        direct_only=True,
        exclude_override_fill=True,
    )
    non_override_times = _extract_marker_times(
        payload,
        window_start=window_start,
        window_end=window_end,
        exclude_override_fill=True,
    )
    marker_times = strong_marker_times or direct_marker_times or non_override_times or _extract_marker_times(
        payload,
        window_start=window_start,
        window_end=window_end,
        strong_only=False,
    )
    if not marker_times:
        if window_start is not None and window_end is not None and window_end > window_start:
            return [(window_start, window_end)]
        return []

    gaps: list[tuple[int, int]] = []
    if window_start is not None and marker_times[0] - window_start > max_gap_seconds:
        gaps.append((window_start, marker_times[0]))
    for left, right in zip(marker_times, marker_times[1:]):
        if right - left > max_gap_seconds:
            gaps.append((left, right))
    if window_end is not None and window_end - marker_times[-1] > max_gap_seconds:
        gaps.append((marker_times[-1], window_end))
    if force_tail and window_end is not None:
        tail_end = int(window_end)
        if target_final_time is not None:
            tail_end = min(tail_end, int(target_final_time))
        if tail_end > marker_times[-1]:
            # Force a tail reacquire window so dense inferred chains do not mask missing late recitation.
            gaps.append((marker_times[-1], tail_end))

    prioritized_gaps: list[tuple[bool, int, int, int]] = []
    for left, right in gaps:
        span = max(0, int(right - left))
        is_tail_gap = False
        if window_end is not None and int(right) >= int(window_end) - max(60, int(pad_seconds)):
            is_tail_gap = True
        if target_final_time is not None and int(right) >= int(target_final_time) - max(45, int(pad_seconds)):
            is_tail_gap = True
        prioritized_gaps.append((is_tail_gap, span, int(left), int(right)))
    prioritized_gaps.sort(key=lambda item: (1 if item[0] else 0, item[1]), reverse=True)

    windows: list[tuple[int, int]] = []
    exhausted = False
    for is_tail_gap, _span, left, right in prioritized_gaps:
        start = max(window_start or left, left - pad_seconds)
        end = min(window_end or right, right + pad_seconds)
        if end - start < 30:
            continue
        per_gap_limit = 3 if is_tail_gap else 2
        per_gap_count = 0
        if is_tail_gap:
            cursor_end = end
            while cursor_end > start:
                chunk_start = max(start, cursor_end - max_window_seconds)
                windows.append((int(chunk_start), int(cursor_end)))
                per_gap_count += 1
                if len(windows) >= max_windows:
                    exhausted = True
                    break
                if per_gap_count >= per_gap_limit:
                    break
                if chunk_start <= start:
                    break
                cursor_end = max(start + 1, chunk_start + overlap_seconds)
        else:
            cursor = start
            while cursor < end:
                chunk_end = min(end, cursor + max_window_seconds)
                windows.append((int(cursor), int(chunk_end)))
                per_gap_count += 1
                if len(windows) >= max_windows:
                    exhausted = True
                    break
                if per_gap_count >= per_gap_limit:
                    break
                if chunk_end >= end:
                    break
                cursor = max(cursor + 1, chunk_end - overlap_seconds)
        if exhausted:
            break

    deduped: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for start, end in windows:
        key = (int(start), int(end))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped[:max_windows]


class RemoteJobLoop:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.vad_probe_thresholds = _parse_float_list(
            args.vad_probe_thresholds,
            fallback=[float(args.request_vad_threshold)],
        )
        if float(args.request_vad_threshold) not in self.vad_probe_thresholds:
            self.vad_probe_thresholds.append(float(args.request_vad_threshold))
        self._probe_corpus_entries = None
        self._probe_index_lookup: dict[tuple[int, int], int] = {}
        self.drive_root = args.drive_root
        self.requests_pending = self.drive_root / "requests" / "pending"
        self.responses_dir = self.drive_root / "responses"
        self.transcripts_dir = self.drive_root / "transcripts"
        self.requests_processing = self.drive_root / "requests" / "processing"
        self.requests_done = self.drive_root / "requests" / "done"
        self.requests_failed = self.drive_root / "requests" / "failed"
        for path in [
            self.requests_pending,
            self.responses_dir,
            self.transcripts_dir,
            self.requests_processing,
            self.requests_done,
            self.requests_failed,
        ]:
            path.mkdir(parents=True, exist_ok=True)

        self.local_root = Path(f"data/ai/remote_jobs/day-{args.day}")
        self.local_transcripts = self.local_root / "transcripts"
        self.local_outputs = self.local_root / "outputs"
        self.iteration_report_path = self.local_root / "iteration_report.json"
        self.local_transcripts.mkdir(parents=True, exist_ok=True)
        self.local_outputs.mkdir(parents=True, exist_ok=True)
        self.state_path = args.state_path or (self.local_root / "state.json")
        self.state = self._load_or_init_state()
        self.day_target = _resolve_day_target(args.day, args.day_overrides)
        self.day_duplicate_markers = _resolve_day_duplicate_markers(args.day, args.day_overrides)
        self.enforce_day_match_blocks = _resolve_day_enforce_match_blocks(
            args.day,
            args.part,
            args.day_overrides,
        )
        self.day_match_block_ranges = _resolve_day_match_block_ranges(
            args.day,
            args.part,
            args.day_overrides,
        )
        self.firestore_enabled = bool(args.firestore)
        self.firestore = args.firestore_client if self.firestore_enabled else None
        self.firestore_session_id = str(args.firestore_session_id or f"day-{args.day}").strip()
        self.firestore_requests_collection = str(args.firestore_requests_collection).strip()
        self.firestore_runtime_collection = str(args.firestore_runtime_collection).strip()
        if not bool(self.args.recovery_vad_filter):
            # Keep the loop simple by default: VAD on full pass, no-VAD on recovery windows.
            self.args.vad_probe = False
        self._write_iteration_report()

    def _firestore_request_document_path(self, request_id: str) -> str:
        return f"{self.firestore_requests_collection}/{request_id}"

    def _firestore_runtime_document_path(self) -> str:
        return f"{self.firestore_runtime_collection}/{self.firestore_session_id}"

    def publish_runtime_endpoint(self) -> None:
        if not self.firestore_enabled or self.firestore is None:
            return
        payload = {
            "session_id": self.firestore_session_id,
            "day": int(self.args.day),
            "updated_at": _utc_now(),
            "source": "run_day_remote_loop",
            "webhook_public_url": str(self.args.webhook_public_url or "").strip(),
            "webhook_token": str(self.args.webhook_token or "").strip(),
            "webhook_local_health": str(self.args.webhook_health_url or "").strip(),
            "webhook_local_ingest": str(self.args.webhook_ingest_url or "").strip(),
        }
        self.firestore.patch_document(self._firestore_runtime_document_path(), payload)

    def _firestore_get_request(self, request_id: str) -> dict[str, Any] | None:
        if not self.firestore_enabled or self.firestore is None:
            return None
        return self.firestore.get_document(self._firestore_request_document_path(request_id))

    def _firestore_set_request(self, request_id: str, payload: dict[str, Any]) -> None:
        if not self.firestore_enabled or self.firestore is None:
            return
        self.firestore.patch_document(self._firestore_request_document_path(request_id), payload)

    def _ensure_probe_matcher_context(self) -> None:
        if self._probe_corpus_entries is not None:
            return
        from ai_pipeline.quran import load_corpus

        entries = load_corpus(self.args.quran_corpus)
        index_lookup: dict[tuple[int, int], int] = {}
        for idx, entry in enumerate(entries):
            index_lookup[(int(entry.surah_number), int(entry.ayah))] = idx
        self._probe_corpus_entries = entries
        self._probe_index_lookup = index_lookup

    def _load_typed_transcript_segments(self, path: Path):
        from ai_pipeline.types import TranscriptSegment, TranscriptWord

        rows = _load_transcript_segments(path)
        output: list[TranscriptSegment] = []
        for row in rows:
            words = [
                TranscriptWord(
                    start=float(word.get("start", row["start"])),
                    end=float(word.get("end", row["end"])),
                    text=str(word.get("text", "")).strip(),
                )
                for word in row.get("words", [])
                if str(word.get("text", "")).strip()
            ]
            output.append(
                TranscriptSegment(
                    start=float(row["start"]),
                    end=float(row["end"]),
                    text=str(row["text"]),
                    words=words,
                )
            )
        return output

    def _find_anchor_before(self, payload: dict[str, Any], window_start: int) -> tuple[int, int] | None:
        best: tuple[int, int] | None = None
        best_time = -1
        best_rank = -1
        for marker in payload.get("markers", []):
            marker_time = int(marker.get("time") or marker.get("start_time") or 0)
            if marker_time > window_start:
                continue
            surah_number = marker.get("surah_number")
            ayah = marker.get("ayah")
            if surah_number is None or ayah is None:
                continue
            rank = _marker_quality_rank(marker.get("quality"))
            if marker_time > best_time or (marker_time == best_time and rank > best_rank):
                best = (int(surah_number), int(ayah))
                best_time = marker_time
                best_rank = rank
        return best

    def _probe_forced_index_candidates(self, base_index: int | None) -> list[int | None]:
        if base_index is None:
            return [None]
        max_index = max(0, len(self._probe_corpus_entries or []) - 1)
        offsets = [0, -4, 4, -8, 8, -12, 12, -16, 16]
        values: list[int | None] = []
        seen: set[int | None] = set()
        for offset in offsets:
            candidate = base_index + offset
            if candidate < 0 or candidate > max_index:
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            values.append(candidate)
        # Keep an unconstrained fallback as final option.
        if None not in seen:
            values.append(None)
        return values

    def _score_probe_markers(
        self,
        *,
        markers: list[Any],
        probe_start: int,
        probe_end: int,
        forced_start_index: int | None,
    ) -> dict[str, Any]:
        in_window = [
            marker
            for marker in markers
            if probe_start <= int(getattr(marker, "time", 0)) <= probe_end
        ]
        by_quality = {"manual": 0, "high": 0, "ambiguous": 0, "inferred": 0}
        for marker in in_window:
            quality = str(getattr(marker, "quality", "") or "").lower()
            if quality in by_quality:
                by_quality[quality] += 1
        direct = by_quality["manual"] + by_quality["high"] + by_quality["ambiguous"]
        inferred = by_quality["inferred"]
        coverage_seconds = 0.0
        if len(in_window) >= 2:
            coverage_seconds = max(0.0, float(in_window[-1].time) - float(in_window[0].time))
        distinct_direct = {
            (int(marker.surah_number), int(marker.ayah))
            for marker in in_window
            if marker.surah_number is not None
            and str(getattr(marker, "quality", "") or "").lower() in {"manual", "high", "ambiguous"}
        }
        score = (
            (by_quality["high"] * 12.0)
            + (by_quality["ambiguous"] * 8.0)
            + (by_quality["manual"] * 10.0)
            + (len(distinct_direct) * 2.5)
            + min(20.0, coverage_seconds / 15.0)
            - (inferred * 5.0)
        )
        if direct == 0:
            score -= 50.0
        return {
            "score": round(score, 3),
            "high": by_quality["high"],
            "ambiguous": by_quality["ambiguous"],
            "manual": by_quality["manual"],
            "inferred": inferred,
            "direct": direct,
            "markers": len(in_window),
            "coverage_seconds": round(coverage_seconds, 2),
            "distinct_direct_ayat": len(distinct_direct),
            "forced_start_index": forced_start_index,
        }

    def _is_probe_score_better(self, left: dict[str, Any], right: dict[str, Any] | None) -> bool:
        if right is None:
            return True
        left_key = (
            float(left.get("score", -9999.0)),
            int(left.get("direct", 0)),
            int(left.get("high", 0)),
            int(left.get("distinct_direct_ayat", 0)),
            float(left.get("coverage_seconds", 0.0)),
        )
        right_key = (
            float(right.get("score", -9999.0)),
            int(right.get("direct", 0)),
            int(right.get("high", 0)),
            int(right.get("distinct_direct_ayat", 0)),
            float(right.get("coverage_seconds", 0.0)),
        )
        return left_key > right_key

    def _target_reached(self, payload: dict[str, Any]) -> bool:
        target_surah = str(self.day_target.get("final_surah") or "").strip()
        target_ayah = self.day_target.get("final_ayah")
        target_time = self.day_target.get("final_time")
        if not target_surah and target_ayah is None and target_time is None:
            return True
        strong_rows = _extract_marker_rows(
            payload=payload,
            window_start=None,
            window_end=None,
            strong_only=True,
            exclude_override_fill=True,
        )
        if not strong_rows:
            return False
        if target_surah and target_ayah:
            for marker in strong_rows:
                if str(marker.get("surah", "")).strip() == target_surah and int(marker.get("ayah") or 0) == int(target_ayah):
                    return True
        if target_time is not None:
            last_time = int(strong_rows[-1].get("time") or strong_rows[-1].get("start_time") or 0)
            if last_time >= int(target_time) - max(45, int(self.args.max_gap_seconds // 2)):
                return True
        return False

    def _window_has_strong_coverage(self, payload: dict[str, Any], start_sec: int, end_sec: int) -> bool:
        rows = _extract_marker_rows(
            payload=payload,
            window_start=int(start_sec),
            window_end=int(end_sec),
            strong_only=True,
            exclude_override_fill=True,
        )
        return len(rows) >= 2

    def _window_overlaps_failed_request(self, start_sec: int, end_sec: int) -> bool:
        for request in self.state.get("requests", []):
            if str(request.get("kind", "")).strip().lower() != "window":
                continue
            if str(request.get("status", "")).strip().lower() != "failed":
                continue
            req_start = request.get("start_sec")
            req_end = request.get("end_sec")
            try:
                req_start_int = int(req_start)
                req_end_int = int(req_end)
            except (TypeError, ValueError):
                continue
            overlap = not (int(end_sec) < req_start_int or int(start_sec) > req_end_int)
            if overlap:
                return True
        return False

    def _window_needs_probe(self, payload: dict[str, Any], start_sec: int, end_sec: int) -> bool:
        if self._window_overlaps_failed_request(start_sec, end_sec):
            return True
        return not self._window_has_strong_coverage(payload, start_sec, end_sec)

    def _score_probe_transcript(
        self,
        transcript_path: Path,
        probe_start: int,
        probe_end: int,
        current_payload: dict[str, Any],
    ) -> dict[str, Any]:
        from ai_pipeline.matcher import MatcherConfig, run_ayah_matcher
        from ai_pipeline.normalization import prepare_segments_for_matching

        self._ensure_probe_matcher_context()
        transcript_segments = self._load_typed_transcript_segments(transcript_path)
        transcript_segments = [
            segment
            for segment in transcript_segments
            if float(segment.end) >= float(probe_start) and float(segment.start) <= float(probe_end)
        ]
        if not transcript_segments:
            return {
                "score": -999.0,
                "high": 0,
                "ambiguous": 0,
                "manual": 0,
                "inferred": 0,
                "direct": 0,
                "markers": 0,
                "coverage_seconds": 0.0,
                "distinct_direct_ayat": 0,
                "forced_start_index": None,
            }

        cleaned = prepare_segments_for_matching(transcript_segments)
        anchor = self._find_anchor_before(current_payload, probe_start)
        forced_start_index = self._probe_index_lookup.get(anchor) if anchor else None
        candidate_indices = self._probe_forced_index_candidates(forced_start_index)

        best_row: dict[str, Any] | None = None
        for idx, candidate_forced_index in enumerate(candidate_indices):
            # Fast path: evaluate the primary anchor first; only expand if it fails.
            if idx > 0 and best_row is not None and int(best_row.get("direct", 0)) > 0:
                break
            config = MatcherConfig(
                min_score=self.args.match_min_score,
                min_gap_seconds=self.args.match_min_gap_seconds,
                min_overlap=self.args.match_min_overlap,
                min_confidence=self.args.match_min_confidence,
                require_weak_support_for_inferred=not self.args.aggressive_infer_fill,
                forced_start_index=candidate_forced_index,
            )
            markers = run_ayah_matcher(
                transcript_segments=cleaned,
                corpus_entries=self._probe_corpus_entries,
                config=config,
            )
            row = self._score_probe_markers(
                markers=markers,
                probe_start=probe_start,
                probe_end=probe_end,
                forced_start_index=candidate_forced_index,
            )
            if self._is_probe_score_better(row, best_row):
                best_row = row
        assert best_row is not None
        return best_row

    def _select_recovery_vad_threshold(
        self,
        *,
        iteration: int,
        window_index: int,
        window_start: int,
        window_end: int,
        current_payload: dict[str, Any],
    ) -> float:
        default_threshold = float(self.args.request_vad_threshold)
        if not self.args.vad_probe or not self.args.recovery_vad_filter:
            return default_threshold
        if window_index >= self.args.vad_probe_max_windows_per_iteration:
            return default_threshold

        probe_start = int(window_start)
        probe_end = int(min(window_end, probe_start + max(60, int(self.args.vad_probe_seconds))))
        if probe_end <= probe_start:
            return default_threshold

        probe_results: list[dict[str, Any]] = []
        best_threshold = default_threshold
        best_score = -10_000.0

        for threshold in self.vad_probe_thresholds:
            request_id = self.submit_request(
                "probe",
                start_sec=probe_start,
                end_sec=probe_end,
                vad_filter=True,
                vad_threshold=float(threshold),
            )
            transcript_file = self.wait_for_response(request_id)
            score = self._score_probe_transcript(
                transcript_path=transcript_file,
                probe_start=probe_start,
                probe_end=probe_end,
                current_payload=current_payload,
            )
            row = {
                "threshold": float(threshold),
                "request_id": request_id,
                **score,
            }
            probe_results.append(row)
            if score["score"] > best_score:
                best_score = score["score"]
                best_threshold = float(threshold)

        # If probing produced no direct evidence across all thresholds, keep default.
        max_direct = max((int(item.get("direct", 0)) for item in probe_results), default=0)
        if max_direct <= 0:
            best_threshold = float(default_threshold)
        else:
            # On score ties, prefer the default threshold when available.
            tied = [
                item
                for item in probe_results
                if abs(float(item.get("score", -9999.0)) - float(best_score)) <= 1e-6
            ]
            if tied:
                default_row = next(
                    (item for item in tied if abs(float(item.get("threshold", 0.0)) - float(default_threshold)) <= 1e-6),
                    None,
                )
                if default_row is not None:
                    best_threshold = float(default_threshold)

        record = {
            "iteration": int(iteration),
            "window_index": int(window_index),
            "window_start": int(window_start),
            "window_end": int(window_end),
            "probe_start": int(probe_start),
            "probe_end": int(probe_end),
            "selected_threshold": float(best_threshold),
            "default_threshold": float(default_threshold),
            "results": probe_results,
            "created_at": _utc_now(),
        }
        self.state.setdefault("vad_probes", []).append(record)
        self._save_state(status="processing")
        print(
            f"[remote] vad probe window {window_index + 1}: selected threshold={best_threshold:.3f} "
            f"(default={default_threshold:.3f})",
        )
        return best_threshold

    def _load_or_init_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return _read_json(self.state_path)
        state = {
            "day": self.args.day,
            "status": "initialized",
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "iteration": 0,
            "active_transcript": None,
            "requests": [],
            "outputs": [],
        }
        _write_json(self.state_path, state)
        return state

    def _save_state(self, status: str | None = None) -> None:
        self.state["updated_at"] = _utc_now()
        if status is not None:
            self.state["status"] = status
        _write_json(self.state_path, self.state)

    def _record_request(self, request_id: str, kind: str, start_sec: int | None, end_sec: int | None) -> None:
        self.state["requests"].append(
            {
                "request_id": request_id,
                "kind": kind,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "status": "pending",
                "created_at": _utc_now(),
            }
        )
        self._save_state(status="awaiting_transcript")

    def _update_request_status(self, request_id: str, status: str, local_transcript: str | None = None) -> None:
        for request in self.state.get("requests", []):
            if request.get("request_id") == request_id:
                request["status"] = status
                request["updated_at"] = _utc_now()
                if local_transcript:
                    request["local_transcript"] = local_transcript
                break
        self._save_state()

    def _upsert_request_state(
        self,
        *,
        request_id: str,
        kind: str,
        start_sec: int | None,
        end_sec: int | None,
        requested_vad_threshold: float | None,
        status: str,
        local_transcript: str | None = None,
    ) -> None:
        now = _utc_now()
        requests = self.state.setdefault("requests", [])
        for request in requests:
            if str(request.get("request_id")) != request_id:
                continue
            request["kind"] = kind
            request["start_sec"] = start_sec
            request["end_sec"] = end_sec
            request["requested_vad_threshold"] = requested_vad_threshold
            request["status"] = status
            request["updated_at"] = now
            if local_transcript:
                request["local_transcript"] = local_transcript
            self._save_state(status="awaiting_transcript" if status == "pending" else None)
            return

        payload: dict[str, Any] = {
            "request_id": request_id,
            "kind": kind,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "requested_vad_threshold": requested_vad_threshold,
            "status": status,
            "created_at": now,
        }
        if local_transcript:
            payload["local_transcript"] = local_transcript
        requests.append(payload)
        self._save_state(status="awaiting_transcript" if status == "pending" else None)

    def _transcript_has_segments(self, path: Path) -> bool:
        if not path.exists() or not path.is_file():
            return False
        try:
            payload = _read_json(path)
        except Exception:
            return False
        segments = payload.get("segments")
        return isinstance(segments, list) and len(segments) > 0

    def _copy_cached_transcript_local(self, request_id: str, source_path: Path) -> Path:
        local_copy = (self.local_transcripts / f"{request_id}.json").resolve()
        source_resolved = source_path.resolve()
        if source_resolved != local_copy:
            shutil.copy2(source_resolved, local_copy)
        return local_copy

    def _cached_transcript_for_request(self, request_id: str, transcript_rel_path: Path) -> Path | None:
        candidates: list[Path] = []
        local_copy = (self.local_transcripts / f"{request_id}.json").resolve()
        candidates.append(local_copy)

        rel_target = (self.drive_root / transcript_rel_path).resolve()
        if rel_target not in candidates:
            candidates.append(rel_target)

        default_drive = (self.transcripts_dir / f"{request_id}.json").resolve()
        if default_drive not in candidates:
            candidates.append(default_drive)

        for request in self.state.get("requests", []):
            if str(request.get("request_id")) != request_id:
                continue
            local_transcript = str(request.get("local_transcript") or "").strip()
            if local_transcript:
                try:
                    path = Path(local_transcript).expanduser().resolve()
                    if path not in candidates:
                        candidates.append(path)
                except Exception:
                    pass
            break

        response_path = self.responses_dir / f"{request_id}.json"
        if response_path.exists():
            try:
                response_payload = _read_json(response_path)
                status = str(response_payload.get("status", "")).strip().lower()
                if status == "done":
                    transcript_ref = response_payload.get("transcript_path")
                    if transcript_ref:
                        path = _resolve_response_transcript_path(str(transcript_ref), self.drive_root).resolve()
                        if path not in candidates:
                            candidates.append(path)
            except Exception:
                pass

        if self.firestore_enabled:
            try:
                request_payload = self._firestore_get_request(request_id) or {}
                status = str(request_payload.get("status", "")).strip().lower()
                if status == "done":
                    transcript_ref = request_payload.get("transcript_path")
                    if transcript_ref:
                        path = _resolve_response_transcript_path(str(transcript_ref), self.drive_root).resolve()
                        if path not in candidates:
                            candidates.append(path)
            except Exception:
                pass

        for candidate in candidates:
            if not self._transcript_has_segments(candidate):
                continue
            return self._copy_cached_transcript_local(request_id, candidate)
        return None

    def _write_iteration_report(self) -> None:
        outputs = self.state.get("outputs", [])
        entries: list[dict[str, Any]] = []
        previous_non_override_counts: dict[str, int] | None = None
        previous_direct_total: int | None = None
        for row in outputs:
            if not isinstance(row, dict):
                continue
            raw_counts = row.get("marker_counts_non_override_fill")
            if not isinstance(raw_counts, dict):
                raw_counts = {}
            counts_non_override: dict[str, int] = {}
            for key in ("manual", "high", "ambiguous", "inferred", "other"):
                try:
                    counts_non_override[key] = int(raw_counts.get(key, 0))
                except (TypeError, ValueError):
                    counts_non_override[key] = 0
            direct_total = _quality_counts_direct_total(counts_non_override)
            inferred_total = counts_non_override.get("inferred", 0)

            delta_counts: dict[str, int] = {}
            if previous_non_override_counts is None:
                for key, value in counts_non_override.items():
                    delta_counts[key] = value
            else:
                for key in ("manual", "high", "ambiguous", "inferred", "other"):
                    delta_counts[key] = int(counts_non_override.get(key, 0)) - int(previous_non_override_counts.get(key, 0))

            delta_direct = direct_total if previous_direct_total is None else int(direct_total - previous_direct_total)

            entries.append(
                {
                    "iteration": row.get("iteration"),
                    "path": row.get("path"),
                    "markers_detected": int(row.get("markers_detected", 0) or 0),
                    "marker_counts": row.get("marker_counts"),
                    "marker_counts_non_override_fill": counts_non_override,
                    "direct_non_override": direct_total,
                    "inferred_non_override": inferred_total,
                    "delta_non_override_fill": delta_counts,
                    "delta_direct_non_override": delta_direct,
                    "generated_at": row.get("generated_at"),
                }
            )
            previous_non_override_counts = counts_non_override
            previous_direct_total = direct_total

        payload = {
            "day": int(self.args.day),
            "session_id": self.firestore_session_id,
            "generated_at": _utc_now(),
            "outputs_count": len(entries),
            "report_path": str(self.iteration_report_path),
            "entries": entries,
        }
        _write_json(self.iteration_report_path, payload)
        self.state["iteration_report_path"] = str(self.iteration_report_path)
        self.state["iteration_report_generated_at"] = payload["generated_at"]
        self._save_state()

    def submit_request(
        self,
        kind: str,
        *,
        start_sec: int | None,
        end_sec: int | None,
        vad_filter: bool,
        vad_threshold: float | None = None,
    ) -> str:
        effective_vad_threshold = (
            float(vad_threshold)
            if vad_threshold is not None
            else float(self.args.request_vad_threshold)
        )
        request_id = _request_id_for(
            day=self.args.day,
            kind=kind,
            youtube_url=self.args.youtube_url,
            start_sec=start_sec,
            end_sec=end_sec,
            model=self.args.request_model,
            device=self.args.request_device,
            compute_type=self.args.request_compute_type,
            beam_size=self.args.request_beam_size,
            language=self.args.request_language,
            chunk_seconds=self.args.request_chunk_seconds,
            vad_filter=vad_filter,
            vad_threshold=(effective_vad_threshold if vad_filter else 0.0),
            min_silence_ms=self.args.request_min_silence_ms,
            speech_pad_ms=self.args.request_speech_pad_ms,
        )
        request_path = self.requests_pending / f"{request_id}.json"
        transcript_rel_path = Path("transcripts") / f"{request_id}.json"
        processing_path = self.requests_processing / f"{request_id}.json"
        done_path = self.requests_done / f"{request_id}.json"
        failed_path = self.requests_failed / f"{request_id}.json"
        response_path = self.responses_dir / f"{request_id}.json"
        callback_url = str(self.args.webhook_public_url or "").strip()
        callback_token = str(self.args.webhook_token or "").strip()
        payload = {
            "request_id": request_id,
            "session_id": self.firestore_session_id,
            "day": self.args.day,
            "kind": kind,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "status": "queued",
            "youtube_url": self.args.youtube_url,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "model": self.args.request_model,
            "device": self.args.request_device,
            "compute_type": self.args.request_compute_type,
            "beam_size": self.args.request_beam_size,
            "language": self.args.request_language,
            "chunk_seconds": self.args.request_chunk_seconds,
            "vad_filter": vad_filter,
            "requested_vad_threshold": effective_vad_threshold if vad_filter else None,
            "vad_parameters": (
                {
                    "threshold": effective_vad_threshold,
                    "min_silence_duration_ms": self.args.request_min_silence_ms,
                    "speech_pad_ms": self.args.request_speech_pad_ms,
                }
                if vad_filter
                else None
            ),
            # Keep this Drive-relative so Colab can resolve it with its own DRIVE_ROOT.
            "output_transcript_path": str(transcript_rel_path),
            "callback_from_runtime": bool(self.firestore_enabled),
            "progress": {
                "chunks_total": 0,
                "chunks_done": 0,
                "percent": 0.0,
                "eta_seconds": None,
                "message": "queued",
            },
        }
        if not self.firestore_enabled:
            payload["callback"] = {
                "url": callback_url,
                "bearer_token": callback_token,
            }

        if kind == "full" and bool(self.args.skip_full_request_if_cached):
            cached_local = self._cached_transcript_for_request(request_id, transcript_rel_path)
            if cached_local is not None:
                self._upsert_request_state(
                    request_id=request_id,
                    kind=kind,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    requested_vad_threshold=(effective_vad_threshold if vad_filter else None),
                    status="done",
                    local_transcript=str(cached_local),
                )
                print(f"[remote] full request cache hit by request hash {request_id} -> {cached_local}")
                return request_id

        # Reuse existing request lifecycle if an identical request already exists.
        if self.firestore_enabled:
            existing = self._firestore_get_request(request_id)
            if existing is None:
                self._firestore_set_request(request_id, payload)
                print(f"[remote] submitted firestore request {request_id}")
            else:
                print(f"[remote] reusing existing firestore request {request_id}")
        else:
            if not any(path.exists() for path in [request_path, processing_path, done_path, failed_path]):
                _write_json(request_path, payload)
                print(f"[remote] submitted request {request_id} -> {request_path}")
            else:
                print(f"[remote] reusing existing request {request_id}")

        status = "pending"
        local_transcript: str | None = None
        if self.firestore_enabled:
            try:
                request_payload = self._firestore_get_request(request_id) or {}
                response_status = str(request_payload.get("status", "")).strip().lower()
                if response_status in {"done", "failed"}:
                    status = response_status
                transcript_ref = request_payload.get("transcript_path")
                if status == "done" and transcript_ref:
                    transcript_path = _resolve_response_transcript_path(str(transcript_ref), self.drive_root)
                    if self._transcript_has_segments(transcript_path):
                        local_copy = self._copy_cached_transcript_local(request_id, transcript_path)
                        local_transcript = str(local_copy)
                    else:
                        status = "pending"
            except Exception:
                status = "pending"
        elif response_path.exists():
            try:
                response_payload = _read_json(response_path)
                response_status = str(response_payload.get("status", "")).strip().lower()
                if response_status in {"done", "failed"}:
                    status = response_status
                transcript_ref = response_payload.get("transcript_path")
                if status == "done" and transcript_ref:
                    transcript_path = _resolve_response_transcript_path(
                        str(transcript_ref),
                        self.drive_root,
                    )
                    if self._transcript_has_segments(transcript_path):
                        local_copy = self._copy_cached_transcript_local(request_id, transcript_path)
                        local_transcript = str(local_copy)
                    else:
                        # Response may be visible before transcript file syncs locally.
                        status = "pending"
            except Exception:
                status = "pending"

        self._upsert_request_state(
            request_id=request_id,
            kind=kind,
            start_sec=start_sec,
            end_sec=end_sec,
            requested_vad_threshold=(effective_vad_threshold if vad_filter else None),
            status=status,
            local_transcript=local_transcript,
        )

        return request_id

    def wait_for_response(self, request_id: str) -> Path:
        response_path = self.responses_dir / f"{request_id}.json"
        response_seen_at: float | None = None
        while True:
            for request in self.state.get("requests", []):
                if str(request.get("request_id")) != request_id:
                    continue
                status = str(request.get("status", "")).strip().lower()
                local_transcript_raw = str(request.get("local_transcript") or "").strip()
                if status == "done" and local_transcript_raw:
                    try:
                        local_transcript = Path(local_transcript_raw).expanduser().resolve()
                        if self._transcript_has_segments(local_transcript):
                            return local_transcript
                    except Exception:
                        pass
                break

            if self.firestore_enabled:
                request_payload = self._firestore_get_request(request_id) or {}
                status = str(request_payload.get("status", "")).strip().lower()
                if status == "processing":
                    progress = request_payload.get("progress")
                    if isinstance(progress, dict):
                        done = progress.get("chunks_done")
                        total = progress.get("chunks_total")
                        eta = progress.get("eta_seconds")
                        msg = str(progress.get("message") or "").strip()
                        if total:
                            print(
                                f"[remote] firestore progress {request_id}: "
                                f"{done}/{total} eta={eta}s {msg}",
                            )
                if status == "done":
                    transcript_ref = request_payload.get("transcript_path")
                    if not transcript_ref:
                        raise RuntimeError(f"Firestore request {request_id} missing transcript_path.")
                    transcript_path = _resolve_response_transcript_path(str(transcript_ref), self.drive_root)
                    if not transcript_path.exists():
                        if response_seen_at is None:
                            response_seen_at = time.time()
                        waited = time.time() - response_seen_at
                        if waited > max(10, int(self.args.transcript_sync_timeout_seconds)):
                            raise FileNotFoundError(
                                f"Transcript from firestore request not found: {transcript_path}"
                            )
                        print(f"[remote] waiting for transcript sync ({int(waited)}s): {transcript_path}")
                        time.sleep(max(2, self.args.poll_seconds))
                        continue

                    local_copy = self.local_transcripts / f"{request_id}.json"
                    shutil.copy2(transcript_path, local_copy)
                    self._update_request_status(request_id, status="done", local_transcript=str(local_copy))
                    print(f"[remote] firestore response done {request_id} -> {local_copy}")
                    return local_copy

                if status == "failed":
                    error = request_payload.get("error", "unknown error")
                    self._update_request_status(request_id, status="failed")
                    raise RuntimeError(f"Remote firestore request failed for {request_id}: {error}")

            if response_path.exists():
                response = _read_json(response_path)
                status = str(response.get("status", "")).strip().lower()
                if status == "done":
                    if response_seen_at is None:
                        response_seen_at = time.time()
                    transcript_ref = response.get("transcript_path")
                    if not transcript_ref:
                        raise RuntimeError(f"Response {response_path} missing transcript_path.")
                    transcript_path = _resolve_response_transcript_path(
                        str(transcript_ref),
                        self.drive_root,
                    )
                    if not transcript_path.exists():
                        waited = time.time() - response_seen_at
                        if waited > max(10, int(self.args.transcript_sync_timeout_seconds)):
                            raise FileNotFoundError(f"Transcript from response not found: {transcript_path}")
                        print(
                            f"[remote] waiting for transcript sync ({int(waited)}s): {transcript_path}",
                        )
                        time.sleep(max(2, self.args.poll_seconds))
                        continue

                    local_copy = self.local_transcripts / f"{request_id}.json"
                    shutil.copy2(transcript_path, local_copy)
                    self._update_request_status(request_id, status="done", local_transcript=str(local_copy))
                    print(f"[remote] response done {request_id} -> {local_copy}")
                    return local_copy

                if status == "failed":
                    error = response.get("error", "unknown error")
                    self._update_request_status(request_id, status="failed")
                    raise RuntimeError(f"Remote request failed for {request_id}: {error}")

            time.sleep(max(2, self.args.poll_seconds))

    def _run_pipeline_with_transcript(
        self,
        transcript_file: Path,
        output_path: Path,
        *,
        matcher_mode: str | None = None,
        apply_override_surah_fill: bool,
        apply_day_final_ayah_override: bool = True,
        apply_marker_time_overrides: bool = True,
    ) -> dict[str, Any]:
        from ai_pipeline import process_day

        return process_day(
            day=self.args.day,
            output_path=output_path,
            cache_dir=self.args.cache_dir,
            corpus_path=self.args.quran_corpus,
            profiles_path=self.args.reciter_profiles,
            youtube_url=(None if self.args.audio_file is not None else self.args.youtube_url),
            audio_file=self.args.audio_file,
            whisper_model=self.args.local_whisper_model,
            bootstrap_reciters=False,
            match_min_score=self.args.match_min_score,
            match_min_overlap=self.args.match_min_overlap,
            match_min_confidence=self.args.match_min_confidence,
            match_min_gap_seconds=self.args.match_min_gap_seconds,
            match_require_weak_support_for_inferred=not self.args.aggressive_infer_fill,
            matcher_mode=str(matcher_mode or self.args.matcher_mode),
            match_start_surah_number=self.args.start_surah_number,
            match_start_ayah=self.args.start_ayah,
            reuse_transcript_cache=False,
            max_audio_seconds=self.args.max_audio_seconds,
            asad_path=self.args.quran_asad,
            day_overrides_path=self.args.day_overrides,
            asr_corrections_path=self.args.asr_corrections_file,
            transcript_input_path=transcript_file,
            part=self.args.part,
            apply_day_final_ayah_override=bool(apply_day_final_ayah_override),
            apply_marker_time_overrides=bool(apply_marker_time_overrides),
            apply_override_surah_fill=bool(apply_override_surah_fill),
        )

    def run_matcher(self, transcript_file: Path, iteration: int) -> tuple[dict[str, Any], Path]:
        output_path = self.local_outputs / f"day-{self.args.day}-iter-{iteration}.json"
        payload = self._run_pipeline_with_transcript(
            transcript_file=transcript_file,
            output_path=output_path,
            apply_override_surah_fill=bool(self.args.loop_apply_override_surah_fill),
        )
        self.state["outputs"].append(
            {
                "iteration": iteration,
                "path": str(output_path),
                "markers_detected": len(payload.get("markers", [])),
                "marker_counts": _marker_quality_counts(payload),
                "marker_counts_non_override_fill": _marker_quality_counts(
                    payload,
                    exclude_override_fill=True,
                ),
                "generated_at": _utc_now(),
            }
        )
        self._write_iteration_report()
        self._save_state(status="processing")
        return payload, output_path

    def _run_matrix_output(
        self,
        *,
        transcript_label: str,
        transcript_file: Path,
        matcher_mode: str,
    ) -> tuple[dict[str, Any], Path]:
        output_path = self.local_outputs / f"day-{self.args.day}-{transcript_label}-{matcher_mode}.json"
        payload = self._run_pipeline_with_transcript(
            transcript_file=transcript_file,
            output_path=output_path,
            matcher_mode=matcher_mode,
            apply_day_final_ayah_override=True,
            apply_marker_time_overrides=True,
            apply_override_surah_fill=False,
        )
        self.state["outputs"].append(
            {
                "iteration": f"{transcript_label}-{matcher_mode}",
                "path": str(output_path),
                "matcher_mode": matcher_mode,
                "transcript_label": transcript_label,
                "markers_detected": len(payload.get("markers", [])),
                "marker_counts": _marker_quality_counts(payload),
                "marker_counts_non_override_fill": _marker_quality_counts(
                    payload,
                    exclude_override_fill=True,
                ),
                "generated_at": _utc_now(),
            }
        )
        self._write_iteration_report()
        self._save_state(status="processing")
        return payload, output_path

    def _select_best_marker_row(
        self,
        existing: dict[str, Any] | None,
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        if existing is None:
            return candidate
        existing_rank = _marker_quality_rank(existing.get("quality"))
        candidate_rank = _marker_quality_rank(candidate.get("quality"))
        if candidate_rank > existing_rank:
            return candidate
        if candidate_rank < existing_rank:
            return existing
        existing_conf = _marker_confidence(existing)
        candidate_conf = _marker_confidence(candidate)
        if candidate_conf > existing_conf + 0.01:
            return candidate
        if existing_conf > candidate_conf + 0.01:
            return existing
        existing_time = int(existing.get("time") or existing.get("start_time") or 0)
        candidate_time = int(candidate.get("time") or candidate.get("start_time") or 0)
        if candidate_time < existing_time:
            return candidate
        return existing

    def _normalize_marker_row(self, marker: dict[str, Any]) -> dict[str, Any] | None:
        surah_number_raw = marker.get("surah_number")
        ayah_raw = marker.get("ayah")
        try:
            surah_number = int(surah_number_raw)
            ayah = int(ayah_raw)
        except (TypeError, ValueError):
            return None
        if surah_number <= 0 or ayah <= 0:
            return None

        start_time = int(marker.get("start_time") or marker.get("time") or 0)
        end_time = int(marker.get("end_time") or start_time)
        row = dict(marker)
        row["surah_number"] = surah_number
        row["ayah"] = ayah
        row["time"] = start_time
        row["start_time"] = start_time
        row["end_time"] = max(start_time, end_time)
        return row

    def _row_allowed_by_match_blocks(self, row: dict[str, Any]) -> bool:
        if not self.enforce_day_match_blocks or not self.day_match_block_ranges:
            return True
        marker_time = int(row.get("time") or row.get("start_time") or 0)
        marker_key = (int(row.get("surah_number") or 0), int(row.get("ayah") or 0))
        covered = False
        for start_time, end_time, lower_key, upper_key in self.day_match_block_ranges:
            if marker_time < start_time or marker_time > end_time:
                continue
            covered = True
            if lower_key is not None and marker_key < lower_key:
                continue
            if upper_key is not None and marker_key > upper_key:
                continue
            return True
        if not covered:
            return False
        return False

    def _collect_best_by_key(
        self,
        payloads: list[tuple[str, str, dict[str, Any]]],
    ) -> tuple[dict[tuple[int, int], dict[str, Any]], dict[str, int]]:
        best: dict[tuple[int, int], dict[str, Any]] = {}
        skipped = {"non_strong": 0, "invalid": 0, "outside_match_blocks": 0}
        for transcript_label, matcher_mode, payload in payloads:
            rows = _extract_marker_rows(
                payload=payload,
                window_start=None,
                window_end=None,
                strong_only=True,
                exclude_override_fill=True,
            )
            for marker in rows:
                normalized = self._normalize_marker_row(marker)
                if normalized is None:
                    skipped["invalid"] += 1
                    continue
                if not _is_strong_marker_row(normalized):
                    skipped["non_strong"] += 1
                    continue
                if not self._row_allowed_by_match_blocks(normalized):
                    skipped["outside_match_blocks"] += 1
                    continue
                key = (int(normalized["surah_number"]), int(normalized["ayah"]))
                normalized["origin"] = f"matrix_{matcher_mode}_{transcript_label}"
                best[key] = self._select_best_marker_row(best.get(key), normalized)
        return best, skipped

    def _add_bounded_inferred_markers(
        self,
        strong_rows: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        if not strong_rows:
            return [], {"added": 0, "skipped_short_time": 0, "skipped_rate": 0, "skipped_large_gap": 0, "skipped_order": 0}

        from ai_pipeline.quran import load_corpus

        corpus_entries = load_corpus(self.args.quran_corpus)
        corpus_index: dict[tuple[int, int], int] = {}
        for idx, entry in enumerate(corpus_entries):
            corpus_index[(int(entry.surah_number), int(entry.ayah))] = idx

        timeline = sorted(strong_rows, key=lambda row: int(row.get("time") or row.get("start_time") or 0))

        def reciter_at(target_time: int) -> str | None:
            chosen: str | None = None
            for item in timeline:
                t = int(item.get("time") or item.get("start_time") or 0)
                if t <= target_time:
                    chosen = str(item.get("reciter") or "").strip() or None
                else:
                    break
            return chosen

        indexed_rows: list[tuple[int, dict[str, Any]]] = []
        for row in strong_rows:
            key = (int(row.get("surah_number") or 0), int(row.get("ayah") or 0))
            idx = corpus_index.get(key)
            if idx is None:
                continue
            indexed_rows.append((idx, row))
        indexed_rows.sort(key=lambda item: item[0])

        inferred: list[dict[str, Any]] = []
        stats = {
            "added": 0,
            "skipped_short_time": 0,
            "skipped_rate": 0,
            "skipped_large_gap": 0,
            "skipped_order": 0,
            "skipped_outside_match_blocks": 0,
        }
        min_total_gap = max(1, int(self.args.final_infer_min_total_gap_seconds))
        min_sec_per_ayah = float(self.args.final_infer_min_seconds_per_ayah)
        max_sec_per_ayah = float(self.args.final_infer_max_seconds_per_ayah)
        max_gap_ayahs = max(1, int(self.args.final_infer_max_gap_ayahs))
        min_missing_ayahs = max(1, int(self.args.final_infer_min_missing_ayahs))

        for (left_idx, left_row), (right_idx, right_row) in zip(indexed_rows, indexed_rows[1:]):
            if right_idx <= left_idx:
                stats["skipped_order"] += 1
                continue
            left_time = int(left_row.get("time") or left_row.get("start_time") or 0)
            right_time = int(right_row.get("time") or right_row.get("start_time") or 0)
            if right_time <= left_time:
                stats["skipped_order"] += 1
                continue

            missing = int(right_idx - left_idx - 1)
            if missing < min_missing_ayahs:
                continue
            if missing > max_gap_ayahs:
                stats["skipped_large_gap"] += 1
                continue

            total_gap_seconds = int(right_time - left_time)
            if total_gap_seconds < min_total_gap:
                stats["skipped_short_time"] += 1
                continue

            step = float(total_gap_seconds) / float(missing + 1)
            if step < min_sec_per_ayah or step > max_sec_per_ayah:
                stats["skipped_rate"] += 1
                continue

            previous_time = left_time
            for offset in range(1, missing + 1):
                entry = corpus_entries[left_idx + offset]
                inferred_time = int(round(left_time + (step * offset)))
                inferred_time = max(previous_time + 1, inferred_time)
                inferred_time = min(right_time - 1, inferred_time)
                previous_time = inferred_time
                inferred.append(
                    {
                        "time": inferred_time,
                        "start_time": inferred_time,
                        "end_time": inferred_time,
                        "surah": str(entry.surah),
                        "surah_number": int(entry.surah_number),
                        "ayah": int(entry.ayah),
                        "juz": None,
                        "quality": "inferred",
                        "reciter": reciter_at(inferred_time),
                        "confidence": 0.56,
                        "origin": "final_gap_fill_bounded",
                    }
                )
                if not self._row_allowed_by_match_blocks(inferred[-1]):
                    inferred.pop()
                    stats["skipped_outside_match_blocks"] += 1
                    continue
                stats["added"] += 1

        inferred.sort(key=lambda row: (int(row.get("time", 0)), int(row.get("surah_number", 0)), int(row.get("ayah", 0))))
        return inferred, stats

    def _enforce_monotonic_quran_timeline(
        self,
        strong_rows: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if len(strong_rows) <= 2:
            return strong_rows, {"dropped": 0, "total": len(strong_rows), "examples": []}

        ordered = sorted(
            strong_rows,
            key=lambda row: (
                int(row.get("time") or row.get("start_time") or 0),
                int(row.get("surah_number") or 0),
                int(row.get("ayah") or 0),
            ),
        )
        n = len(ordered)
        keys: list[tuple[int, int]] = [
            (int(row.get("surah_number") or 0), int(row.get("ayah") or 0))
            for row in ordered
        ]

        def _weight(row: dict[str, Any]) -> float:
            # Prioritize keeping more markers first, then quality/confidence.
            return 100.0 + (_marker_quality_rank(row.get("quality")) * 10.0) + _marker_confidence(row)

        weights = [_weight(row) for row in ordered]
        dp = list(weights)
        prev = [-1] * n

        for i in range(n):
            si, ai = keys[i]
            for j in range(i):
                sj, aj = keys[j]
                if (sj, aj) > (si, ai):
                    continue
                candidate = dp[j] + weights[i]
                if candidate > dp[i]:
                    dp[i] = candidate
                    prev[i] = j

        best_i = max(range(n), key=lambda idx: dp[idx])
        keep_indices: set[int] = set()
        cursor = best_i
        while cursor >= 0:
            keep_indices.add(cursor)
            cursor = prev[cursor]

        kept = [ordered[idx] for idx in range(n) if idx in keep_indices]
        dropped = [ordered[idx] for idx in range(n) if idx not in keep_indices]
        info = {
            "dropped": len(dropped),
            "total": len(ordered),
            "examples": [
                {
                    "surah_number": int(row.get("surah_number") or 0),
                    "ayah": int(row.get("ayah") or 0),
                    "time": int(row.get("time") or row.get("start_time") or 0),
                    "quality": str(row.get("quality") or ""),
                    "origin": str(row.get("origin") or ""),
                }
                for row in dropped[:20]
            ],
        }
        return kept, info

    def _can_insert_monotonic_marker(
        self,
        timeline: list[dict[str, Any]],
        candidate: dict[str, Any],
    ) -> bool:
        if not timeline:
            return True
        cand_time = int(candidate.get("time") or candidate.get("start_time") or 0)
        cand_key = (int(candidate.get("surah_number") or 0), int(candidate.get("ayah") or 0))
        prev_row: dict[str, Any] | None = None
        next_row: dict[str, Any] | None = None
        for row in timeline:
            row_time = int(row.get("time") or row.get("start_time") or 0)
            if row_time <= cand_time:
                prev_row = row
                continue
            next_row = row
            break
        if prev_row is not None:
            prev_key = (int(prev_row.get("surah_number") or 0), int(prev_row.get("ayah") or 0))
            if prev_key > cand_key:
                return False
        if next_row is not None:
            next_key = (int(next_row.get("surah_number") or 0), int(next_row.get("ayah") or 0))
            if cand_key > next_key:
                return False
        return True

    def _merge_matrix_payloads(self, payload_map: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
        legacy_payloads = [
            ("vad_on", "legacy", payload_map["legacy_vad_on"]),
            ("vad_off", "legacy", payload_map["legacy_vad_off"]),
        ]
        two_stage_payloads = [
            ("vad_on", "two_stage", payload_map["two_stage_vad_on"]),
            ("vad_off", "two_stage", payload_map["two_stage_vad_off"]),
        ]
        legacy_best, legacy_skipped = self._collect_best_by_key(legacy_payloads)
        two_stage_best, two_stage_skipped = self._collect_best_by_key(two_stage_payloads)

        merged_by_key: dict[tuple[int, int], dict[str, Any]] = dict(legacy_best)
        for key, marker in two_stage_best.items():
            if key not in merged_by_key:
                merged_by_key[key] = marker

        strong_rows = list(merged_by_key.values())
        strong_rows.sort(key=lambda row: (int(row.get("time") or row.get("start_time") or 0), int(row.get("surah_number") or 0), int(row.get("ayah") or 0)))
        strong_rows, monotonic_info = self._enforce_monotonic_quran_timeline(strong_rows)
        kept_keys: set[tuple[int, int]] = {
            (int(row.get("surah_number") or 0), int(row.get("ayah") or 0))
            for row in strong_rows
        }
        rescued_from_two_stage = 0
        rescued_examples: list[dict[str, Any]] = []
        for key, candidate in sorted(
            two_stage_best.items(),
            key=lambda item: int(item[1].get("time") or item[1].get("start_time") or 0),
        ):
            if key in kept_keys:
                continue
            if not self._can_insert_monotonic_marker(strong_rows, candidate):
                continue
            strong_rows.append(candidate)
            strong_rows.sort(
                key=lambda row: (
                    int(row.get("time") or row.get("start_time") or 0),
                    int(row.get("surah_number") or 0),
                    int(row.get("ayah") or 0),
                )
            )
            kept_keys.add(key)
            rescued_from_two_stage += 1
            if len(rescued_examples) < 20:
                rescued_examples.append(
                    {
                        "surah_number": int(candidate.get("surah_number") or 0),
                        "ayah": int(candidate.get("ayah") or 0),
                        "time": int(candidate.get("time") or candidate.get("start_time") or 0),
                        "quality": str(candidate.get("quality") or ""),
                        "origin": str(candidate.get("origin") or ""),
                    }
                )
        inferred_rows, infer_stats = self._add_bounded_inferred_markers(strong_rows)

        final_rows = [*strong_rows, *inferred_rows]
        if self.enforce_day_match_blocks and self.day_match_block_ranges:
            final_rows = [row for row in final_rows if self._row_allowed_by_match_blocks(row)]
        final_rows.sort(key=lambda row: (int(row.get("time") or row.get("start_time") or 0), int(row.get("surah_number") or 0), int(row.get("ayah") or 0)))

        if self.day_duplicate_markers:
            by_key: dict[tuple[int, int], dict[str, Any]] = {}
            for row in final_rows:
                key = (int(row.get("surah_number") or 0), int(row.get("ayah") or 0))
                if key not in by_key:
                    by_key[key] = row
            existing_signature = {
                (
                    int(row.get("surah_number") or 0),
                    int(row.get("ayah") or 0),
                    int(row.get("time") or row.get("start_time") or 0),
                    str(row.get("reciter") or "").strip(),
                )
                for row in final_rows
            }
            for item in self.day_duplicate_markers:
                key = (int(item["surah_number"]), int(item["ayah"]))
                base = by_key.get(key)
                if base is None:
                    continue
                row = dict(base)
                row_time = int(item["time"])
                row["time"] = row_time
                row["start_time"] = row_time
                row["end_time"] = max(row_time, int(base.get("end_time") or row_time))
                row["quality"] = "manual"
                row["confidence"] = 1.0
                row["origin"] = "override_duplicate_marker"
                if item.get("reciter"):
                    row["reciter"] = item["reciter"]
                signature = (
                    int(row.get("surah_number") or 0),
                    int(row.get("ayah") or 0),
                    int(row.get("time") or row.get("start_time") or 0),
                    str(row.get("reciter") or "").strip(),
                )
                if signature in existing_signature:
                    continue
                final_rows.append(row)
                existing_signature.add(signature)
            final_rows.sort(
                key=lambda row: (
                    int(row.get("time") or row.get("start_time") or 0),
                    int(row.get("surah_number") or 0),
                    int(row.get("ayah") or 0),
                )
            )

        base_payload = payload_map["two_stage_vad_on"]
        final_payload = dict(base_payload)
        final_payload["markers"] = final_rows
        meta = dict(base_payload.get("meta") or {})
        meta.update(
            {
                "merge_strategy": "legacy_strong_then_two_stage_strong_then_bounded_infer",
                "legacy_commit_ref": "a61c0d3",
                "enforce_match_blocks": bool(self.enforce_day_match_blocks),
                "match_blocks_count": len(self.day_match_block_ranges),
                "matrix_sources": {
                    "legacy_vad_on": f"day-{self.args.day}-vad-on-legacy.json",
                    "legacy_vad_off": f"day-{self.args.day}-vad-off-legacy.json",
                    "two_stage_vad_on": f"day-{self.args.day}-vad-on-two_stage.json",
                    "two_stage_vad_off": f"day-{self.args.day}-vad-off-two_stage.json",
                },
                "merged_strong_count": len(strong_rows),
                "final_inferred_added": int(infer_stats["added"]),
                "legacy_skipped": legacy_skipped,
                "two_stage_skipped": two_stage_skipped,
                "final_infer_constraints": {
                    "min_total_gap_seconds": int(self.args.final_infer_min_total_gap_seconds),
                    "min_seconds_per_ayah": float(self.args.final_infer_min_seconds_per_ayah),
                    "max_seconds_per_ayah": float(self.args.final_infer_max_seconds_per_ayah),
                    "max_gap_ayahs": int(self.args.final_infer_max_gap_ayahs),
                    "min_missing_ayahs": int(self.args.final_infer_min_missing_ayahs),
                },
                "final_infer_stats": infer_stats,
                "monotonic_timeline_filter": monotonic_info,
                "rescued_from_two_stage_after_monotonic": {
                    "count": rescued_from_two_stage,
                    "examples": rescued_examples,
                },
            }
        )
        final_payload["meta"] = meta
        summary = {
            "legacy_strong": len(legacy_best),
            "two_stage_strong": len(two_stage_best),
            "merged_strong": len(strong_rows),
            "inferred_added": int(infer_stats["added"]),
            "final_markers": len(final_rows),
        }
        return final_payload, summary

    def run_dual_vad_matrix(self) -> None:
        window_start, window_end = _resolve_day_window(self.args.day, self.args.day_overrides)
        if self.args.window_start is not None:
            window_start = self.args.window_start
        if self.args.window_end is not None:
            window_end = self.args.window_end

        if self.args.audio_file is None:
            local_audio = Path(f"data/audio/day-{self.args.day}/source.wav")
            if local_audio.exists():
                self.args.audio_file = local_audio
                print(f"[remote] using cached local audio source {local_audio}")

        self._save_state(status="processing")

        transcript_vad_on: Path
        transcript_vad_off: Path
        if self.args.full_vad_on_transcript is not None:
            transcript_vad_on = self.args.full_vad_on_transcript.expanduser().resolve()
        else:
            on_request_id = self.submit_request(
                "full",
                start_sec=window_start,
                end_sec=window_end,
                vad_filter=True,
            )
            transcript_vad_on = self.wait_for_response(on_request_id)

        if self.args.full_vad_off_transcript is not None:
            transcript_vad_off = self.args.full_vad_off_transcript.expanduser().resolve()
        else:
            off_request_id = self.submit_request(
                "full_no_vad",
                start_sec=window_start,
                end_sec=window_end,
                vad_filter=False,
            )
            transcript_vad_off = self.wait_for_response(off_request_id)

        self.state["active_transcript_vad_on"] = str(transcript_vad_on)
        self.state["active_transcript_vad_off"] = str(transcript_vad_off)
        self._save_state(status="processing")

        payload_map: dict[str, dict[str, Any]] = {}
        for transcript_label, transcript_path in [("vad-on", transcript_vad_on), ("vad-off", transcript_vad_off)]:
            for matcher_mode in ("legacy", "two_stage"):
                payload, output_path = self._run_matrix_output(
                    transcript_label=transcript_label,
                    transcript_file=transcript_path,
                    matcher_mode=matcher_mode,
                )
                payload_map[f"{matcher_mode}_{transcript_label.replace('-', '_')}"] = payload
                print(
                    f"[remote] matrix output {transcript_label} + {matcher_mode}: "
                    f"{len(payload.get('markers', []))} markers -> {output_path}"
                )

        final_payload, summary = self._merge_matrix_payloads(payload_map)
        merged_output_path = self.local_outputs / f"day-{self.args.day}-merged-matrix.json"
        _write_json(merged_output_path, final_payload)
        shutil.copy2(merged_output_path, self.args.output)
        self.state["outputs"].append(
            {
                "iteration": "matrix-merged-final",
                "path": str(merged_output_path),
                "markers_detected": len(final_payload.get("markers", [])),
                "marker_counts": _marker_quality_counts(final_payload),
                "marker_counts_non_override_fill": _marker_quality_counts(
                    final_payload,
                    exclude_override_fill=True,
                ),
                "generated_at": _utc_now(),
                "summary": summary,
            }
        )
        self._write_iteration_report()
        self._save_state(status="completed")
        print(
            "[remote] matrix complete "
            f"legacy_strong={summary['legacy_strong']} "
            f"two_stage_strong={summary['two_stage_strong']} "
            f"inferred_added={summary['inferred_added']} "
            f"final_markers={summary['final_markers']} "
            f"-> {self.args.output}"
        )

    def _finalize_output(self, *, active_transcript: Path | None, latest_output: Path | None, status: str) -> None:
        if active_transcript is None:
            if latest_output is not None and latest_output.exists():
                shutil.copy2(latest_output, self.args.output)
            self._save_state(status=status)
            return

        if (
            latest_output is not None
            and latest_output.exists()
            and bool(self.args.final_output_apply_override_surah_fill) == bool(self.args.loop_apply_override_surah_fill)
        ):
            shutil.copy2(latest_output, self.args.output)
            self._save_state(status=status)
            return

        final_mode = "on" if self.args.final_output_apply_override_surah_fill else "off"
        final_output_path = self.local_outputs / f"day-{self.args.day}-final-surah-fill-{final_mode}.json"
        payload = self._run_pipeline_with_transcript(
            transcript_file=active_transcript,
            output_path=final_output_path,
            apply_override_surah_fill=bool(self.args.final_output_apply_override_surah_fill),
        )
        self.state["outputs"].append(
            {
                "iteration": "final",
                "path": str(final_output_path),
                "markers_detected": len(payload.get("markers", [])),
                "marker_counts": _marker_quality_counts(payload),
                "marker_counts_non_override_fill": _marker_quality_counts(
                    payload,
                    exclude_override_fill=True,
                ),
                "generated_at": _utc_now(),
                "final_output_apply_override_surah_fill": bool(self.args.final_output_apply_override_surah_fill),
            }
        )
        self._write_iteration_report()
        shutil.copy2(final_output_path, self.args.output)
        self._save_state(status=status)

    def run(self) -> None:
        if str(self.args.loop_strategy).strip().lower() == "dual_vad_matrix":
            print("[remote] loop strategy: dual_vad_matrix")
            if self.firestore_enabled:
                self.publish_runtime_endpoint()
                print(
                    f"[remote] firestore enabled session={self.firestore_session_id} "
                    f"requests_collection={self.firestore_requests_collection}",
                )
            self.run_dual_vad_matrix()
            return

        window_start, window_end = _resolve_day_window(self.args.day, self.args.day_overrides)
        if self.args.window_start is not None:
            window_start = self.args.window_start
        if self.args.window_end is not None:
            window_end = self.args.window_end
        print(
            "[remote] vad strategy "
            f"full={'on' if self.args.initial_vad_filter else 'off'} "
            f"recovery={'on' if self.args.recovery_vad_filter else 'off'} "
            f"probe={'on' if self.args.vad_probe else 'off'}",
        )

        if self.firestore_enabled:
            self.publish_runtime_endpoint()
            print(
                f"[remote] firestore enabled session={self.firestore_session_id} "
                f"requests_collection={self.firestore_requests_collection}",
            )

        active_transcript = Path(self.state["active_transcript"]) if self.state.get("active_transcript") else None
        resumed_recovery_files: list[Path] = []
        pending_requests = [request for request in self.state.get("requests", []) if request.get("status") == "pending"]
        if pending_requests:
            print(f"[remote] resuming {len(pending_requests)} pending requests from state")
        for request in pending_requests:
            request_id = str(request.get("request_id", ""))
            if not request_id:
                continue
            local_file = self.wait_for_response(request_id)
            if str(request.get("kind")) == "full" and (active_transcript is None or not active_transcript.exists()):
                active_transcript = local_file
            else:
                resumed_recovery_files.append(local_file)

        if active_transcript is not None and resumed_recovery_files:
            resumed_merged = self.local_transcripts / f"day-{self.args.day}-merged-resume.json"
            active_transcript = _merge_transcripts([active_transcript, *resumed_recovery_files], resumed_merged)
            self.state["active_transcript"] = str(active_transcript)
            self._save_state(status="processing")

        if active_transcript is None or not active_transcript.exists():
            request_id = self.submit_request(
                "full",
                start_sec=window_start,
                end_sec=window_end,
                vad_filter=self.args.initial_vad_filter,
            )
            active_transcript = self.wait_for_response(request_id)
            self.state["active_transcript"] = str(active_transcript)
            self._save_state(status="processing")

        for iteration in range(int(self.state.get("iteration", 0)) + 1, self.args.max_iterations + 1):
            self.state["iteration"] = iteration
            self._save_state(status="processing")
            payload, output_path = self.run_matcher(active_transcript, iteration)
            marker_sig = _marker_signature(payload)
            previous_sig = str(self.state.get("last_marker_signature") or "")
            self.state["last_marker_signature"] = marker_sig
            self._save_state(status="processing")
            if (
                self.args.stop_on_stalled_iterations
                and previous_sig
                and marker_sig == previous_sig
            ):
                self.state["active_transcript"] = str(active_transcript)
                self._finalize_output(
                    active_transcript=active_transcript,
                    latest_output=output_path,
                    status="stalled_completed",
                )
                print(
                    f"[remote] stalled marker signature detected at iteration {iteration}; "
                    f"stopping early -> {self.args.output}"
                )
                return

            strong_times = _extract_marker_times(
                payload=payload,
                window_start=window_start,
                window_end=window_end,
                strong_only=True,
            )
            force_tail = False
            if window_end is not None:
                if not strong_times:
                    force_tail = True
                else:
                    if int(window_end) - int(strong_times[-1]) > max(90, int(self.args.max_gap_seconds)):
                        force_tail = True
            if not self._target_reached(payload):
                force_tail = True

            windows = _propose_recovery_windows(
                payload=payload,
                window_start=window_start,
                window_end=window_end,
                max_gap_seconds=self.args.max_gap_seconds,
                max_windows=self.args.max_recovery_windows,
                max_window_seconds=self.args.max_recovery_window_seconds,
                overlap_seconds=self.args.recovery_overlap_seconds,
                pad_seconds=self.args.recovery_pad_seconds,
                target_final_time=self.day_target.get("final_time"),
                force_tail=force_tail,
            )

            if not windows:
                self.state["active_transcript"] = str(active_transcript)
                self._finalize_output(
                    active_transcript=active_transcript,
                    latest_output=output_path,
                    status="completed",
                )
                print(f"[remote] completed, output -> {self.args.output}")
                return

            print(f"[remote] iteration {iteration}: requesting {len(windows)} recovery windows")
            recovery_files: list[Path] = []
            for window_index, (start_sec, end_sec) in enumerate(windows):
                selected_vad_threshold = None
                if self.args.recovery_vad_filter:
                    if self._window_needs_probe(payload, int(start_sec), int(end_sec)):
                        selected_vad_threshold = self._select_recovery_vad_threshold(
                            iteration=iteration,
                            window_index=window_index,
                            window_start=int(start_sec),
                            window_end=int(end_sec),
                            current_payload=payload,
                        )
                    else:
                        selected_vad_threshold = float(self.args.request_vad_threshold)
                        print(
                            f"[remote] skip vad probe for window {window_index + 1}: "
                            f"strong coverage present ({int(start_sec)}-{int(end_sec)})",
                        )
                request_id = self.submit_request(
                    "window",
                    start_sec=int(start_sec),
                    end_sec=int(end_sec),
                    vad_filter=self.args.recovery_vad_filter,
                    vad_threshold=selected_vad_threshold,
                )
                recovery_files.append(self.wait_for_response(request_id))

            merged_path = self.local_transcripts / f"day-{self.args.day}-merged-iter-{iteration}.json"
            active_transcript = _merge_transcripts([active_transcript, *recovery_files], merged_path)
            self.state["active_transcript"] = str(active_transcript)
            self._save_state(status="processing")

        # last fallback
        latest_output_raw = self.state.get("outputs", [])[-1]["path"] if self.state.get("outputs") else None
        latest_output = Path(latest_output_raw) if latest_output_raw else None
        self._finalize_output(
            active_transcript=active_transcript,
            latest_output=latest_output,
            status="max_iterations_reached",
        )
        print(f"[remote] max iterations reached, last output -> {self.args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stateful local loop: request transcript jobs via Google Drive, wait for responses, run matcher, and request targeted recovery windows."
    )
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--youtube-url", type=str, required=True)
    parser.add_argument("--drive-root", type=Path, help="Local Google Drive sync path used as request/response bridge.")
    parser.add_argument(
        "--drive-config",
        type=Path,
        default=Path("scripts/colab/local_config.json"),
        help="Optional config JSON containing drive_root when --drive-root is not passed.",
    )
    parser.add_argument("--audio-file", type=Path, help="Optional local audio file for process_day.")
    parser.add_argument("--output", type=Path, default=Path("public/data/day-12.json"))
    parser.add_argument("--state-path", type=Path, help="Optional explicit state JSON path.")
    parser.add_argument("--poll-seconds", type=int, default=15)
    parser.add_argument("--transcript-sync-timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--loop-strategy",
        type=str,
        default="dual_vad_matrix",
        choices=["dual_vad_matrix", "iterative"],
        help="Loop behavior: dual_vad_matrix (4 outputs + merge) or iterative (legacy gap-recovery loop).",
    )
    parser.add_argument(
        "--full-vad-on-transcript",
        type=Path,
        help="Optional local transcript path for the full VAD-on pass (skips remote request).",
    )
    parser.add_argument(
        "--full-vad-off-transcript",
        type=Path,
        help="Optional local transcript path for the full VAD-off pass (skips remote request).",
    )
    parser.add_argument(
        "--skip-full-request-if-cached",
        dest="skip_full_request_if_cached",
        action="store_true",
        default=True,
        help="Do not enqueue a new full request if transcript for the same request hash already exists.",
    )
    parser.add_argument(
        "--no-skip-full-request-if-cached",
        dest="skip_full_request_if_cached",
        action="store_false",
    )
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--stop-on-stalled-iterations", dest="stop_on_stalled_iterations", action="store_true", default=True)
    parser.add_argument("--no-stop-on-stalled-iterations", dest="stop_on_stalled_iterations", action="store_false")
    parser.add_argument("--window-start", type=int)
    parser.add_argument("--window-end", type=int)

    parser.add_argument("--webhook", dest="webhook", action="store_true", default=True)
    parser.add_argument("--no-webhook", dest="webhook", action="store_false")
    parser.add_argument("--webhook-host", type=str, default="127.0.0.1")
    parser.add_argument("--webhook-port", type=int, default=8765)
    parser.add_argument(
        "--webhook-public-url",
        type=str,
        help="Public callback URL used by Colab worker (usually ngrok URL ending with /ingest/transcript).",
    )
    parser.add_argument(
        "--webhook-token",
        type=str,
        help="Bearer token expected by local webhook. Defaults to callback.bearer_token from --drive-config.",
    )
    parser.add_argument(
        "--webhook-mirror-dir",
        type=Path,
        help="Optional debug mirror dir for raw webhook payload snapshots.",
    )
    parser.add_argument("--firestore", dest="firestore", action="store_true", default=False)
    parser.add_argument("--no-firestore", dest="firestore", action="store_false")
    parser.add_argument(
        "--firestore-session-id",
        type=str,
        help="Logical Firestore session id. Defaults to day-{day}.",
    )
    parser.add_argument(
        "--firestore-requests-collection",
        type=str,
        default="andalus_transcription_requests",
    )
    parser.add_argument(
        "--firestore-runtime-collection",
        type=str,
        default="andalus_transcription_runtime",
    )

    parser.add_argument("--max-gap-seconds", type=int, default=180)
    parser.add_argument("--max-recovery-windows", type=int, default=4)
    parser.add_argument("--max-recovery-window-seconds", type=int, default=420)
    parser.add_argument("--recovery-overlap-seconds", type=int, default=25)
    parser.add_argument("--recovery-pad-seconds", type=int, default=20)

    parser.add_argument("--request-model", type=str, default="large-v3")
    parser.add_argument(
        "--request-device",
        type=str,
        default="auto",
        help="Preferred worker device for transcription requests: auto|cpu|cuda.",
    )
    parser.add_argument("--request-compute-type", type=str, default="float16")
    parser.add_argument("--request-beam-size", type=int, default=5)
    parser.add_argument("--request-language", type=str, default="ar")
    parser.add_argument("--request-chunk-seconds", type=int, default=600)
    parser.add_argument("--request-vad-threshold", type=float, default=0.18)
    parser.add_argument("--request-min-silence-ms", type=int, default=350)
    parser.add_argument("--request-speech-pad-ms", type=int, default=200)
    parser.add_argument("--initial-vad-filter", action="store_true", default=True)
    parser.add_argument("--no-initial-vad-filter", dest="initial_vad_filter", action="store_false")
    parser.add_argument("--recovery-vad-filter", action="store_true", default=False)
    parser.add_argument("--no-recovery-vad-filter", dest="recovery_vad_filter", action="store_false")
    parser.add_argument("--vad-probe", dest="vad_probe", action="store_true", default=False)
    parser.add_argument("--no-vad-probe", dest="vad_probe", action="store_false")
    parser.add_argument("--vad-probe-thresholds", type=str, default="0.08,0.12,0.16,0.18,0.22")
    parser.add_argument("--vad-probe-seconds", type=int, default=300)
    parser.add_argument("--vad-probe-max-windows-per-iteration", type=int, default=2)

    parser.add_argument("--local-whisper-model", type=str, default="small")
    parser.add_argument("--cache-dir", type=Path, default=Path("data/audio"))
    parser.add_argument("--quran-corpus", type=Path, default=Path("data/quran/quran_arabic.json"))
    parser.add_argument("--quran-asad", type=Path, default=Path("data/quran/quran_asad_en.json"))
    parser.add_argument("--reciter-profiles", type=Path, default=Path("data/ai/reciter_profiles.json"))
    parser.add_argument("--day-overrides", type=Path, default=Path("data/ai/day_overrides.json"))
    parser.add_argument("--asr-corrections-file", type=Path)
    parser.add_argument("--part", type=int)

    parser.add_argument("--start-surah-number", type=int)
    parser.add_argument("--start-ayah", type=int)
    parser.add_argument("--match-min-score", type=int, default=78)
    parser.add_argument("--match-min-overlap", type=float, default=0.18)
    parser.add_argument("--match-min-confidence", type=float, default=0.62)
    parser.add_argument("--match-min-gap-seconds", type=int, default=8)
    parser.add_argument(
        "--matcher-mode",
        type=str,
        default="legacy",
        choices=["legacy", "two_stage"],
        help="Matcher strategy used by local process_day runs.",
    )
    parser.add_argument("--max-audio-seconds", type=int)
    parser.add_argument("--aggressive-infer-fill", action="store_true")
    parser.add_argument(
        "--final-infer-min-total-gap-seconds",
        type=int,
        default=12,
        help="Only infer missing ayahs when time between surrounding anchors is at least this many seconds.",
    )
    parser.add_argument(
        "--final-infer-min-seconds-per-ayah",
        type=float,
        default=2.5,
        help="Lower bound on inferred timing density (avoid unrealistic many ayahs in very short audio).",
    )
    parser.add_argument(
        "--final-infer-max-seconds-per-ayah",
        type=float,
        default=30.0,
        help="Upper bound on inferred timing density.",
    )
    parser.add_argument(
        "--final-infer-max-gap-ayahs",
        type=int,
        default=40,
        help="Skip inference for extremely large ayah gaps.",
    )
    parser.add_argument(
        "--final-infer-min-missing-ayahs",
        type=int,
        default=1,
        help="Minimum missing ayah count required before bounded inference runs.",
    )
    parser.add_argument(
        "--loop-apply-override-surah-fill",
        dest="loop_apply_override_surah_fill",
        action="store_true",
        default=False,
        help="Apply override surah fill during each loop iteration (default: disabled to avoid masking gaps).",
    )
    parser.add_argument(
        "--no-loop-apply-override-surah-fill",
        dest="loop_apply_override_surah_fill",
        action="store_false",
    )
    parser.add_argument(
        "--final-output-apply-override-surah-fill",
        dest="final_output_apply_override_surah_fill",
        action="store_true",
        default=True,
        help="Apply override surah fill on the final exported output.",
    )
    parser.add_argument(
        "--no-final-output-apply-override-surah-fill",
        dest="final_output_apply_override_surah_fill",
        action="store_false",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.day < 1 or args.day > 30:
        raise SystemExit("--day must be between 1 and 30")
    args.drive_root = _resolve_drive_root(args.drive_root, args.drive_config)
    args.request_device = _normalize_request_device(args.request_device)
    default_token = _resolve_callback_token(args.drive_config)
    default_public_url = _resolve_callback_url(args.drive_config)
    args.webhook_token = str(args.webhook_token).strip() if args.webhook_token is not None else default_token
    args.webhook_public_url = str(args.webhook_public_url).strip() if args.webhook_public_url else default_public_url
    args.webhook_health_url = ""
    args.webhook_ingest_url = ""
    args.firestore_client = None
    if args.firestore:
        firestore_mod = _load_firestore_module()
        fs_config = firestore_mod.load_firestore_config(args.drive_config)
        fs_config.enabled = True
        if args.firestore_requests_collection:
            fs_config.requests_collection = str(args.firestore_requests_collection).strip()
        if args.firestore_runtime_collection:
            fs_config.runtime_collection = str(args.firestore_runtime_collection).strip()
        if args.firestore_session_id:
            fs_config.session_id = str(args.firestore_session_id).strip()
        elif not str(fs_config.session_id or "").strip() or str(fs_config.session_id).strip().lower() == "default":
            fs_config.session_id = f"day-{args.day}"
        args.firestore_session_id = fs_config.session_id
        args.firestore_requests_collection = fs_config.requests_collection
        args.firestore_runtime_collection = fs_config.runtime_collection
        args.firestore_client = firestore_mod.FirestoreRestClient(fs_config)
        print(
            "[remote] firestore client ready "
            f"project={fs_config.project_id} "
            f"requests={fs_config.requests_collection} "
            f"runtime={fs_config.runtime_collection} "
            f"session={fs_config.session_id}",
        )
        if not str(args.webhook_public_url or "").strip():
            raise SystemExit(
                "Firestore mode requires --webhook-public-url (or callback.url in --drive-config) "
                "so worker can read callback endpoint from runtime doc."
            )
        if not str(args.webhook_token or "").strip():
            raise SystemExit(
                "Firestore mode requires --webhook-token (or callback.bearer_token in --drive-config) "
                "so worker can read callback credentials from runtime doc."
            )
    webhook_runtime: Any | None = None
    webhook_mod: Any | None = None
    try:
        if args.webhook:
            webhook_mod = _load_webhook_module()
            try:
                webhook_runtime = webhook_mod.start_webhook_server(
                    host=args.webhook_host,
                    port=int(args.webhook_port),
                    drive_root=args.drive_root,
                    token=args.webhook_token,
                    mirror_dir=args.webhook_mirror_dir,
                )
            except OSError as exc:
                raise SystemExit(
                    f"Failed to start local webhook on {args.webhook_host}:{args.webhook_port}: {exc}. "
                    "Use --webhook-port to change port or --no-webhook to disable."
                ) from exc
            print(
                "[remote] webhook ready "
                f"health={webhook_runtime.health_url} "
                f"ingest={webhook_runtime.ingest_url} "
                f"auth={'enabled' if webhook_runtime.auth_enabled else 'disabled'}",
            )
            args.webhook_health_url = webhook_runtime.health_url
            args.webhook_ingest_url = webhook_runtime.ingest_url

        runner = RemoteJobLoop(args)
        runner.run()
    except KeyboardInterrupt:
        print("[remote] interrupted", file=sys.stderr)
        raise SystemExit(130)
    finally:
        if webhook_runtime is not None:
            assert webhook_mod is not None
            webhook_mod.stop_webhook_server(webhook_runtime)


if __name__ == "__main__":
    main()
