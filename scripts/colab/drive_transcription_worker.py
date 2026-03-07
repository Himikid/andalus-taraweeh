#!/usr/bin/env python3
"""
Google Drive request/response transcription worker for Colab.

Workflow:
1) Poll requests in:   {DRIVE_ROOT}/requests/pending/*.json
2) Download source audio (YouTube) if needed.
3) Normalize audio once (mono 16k wav cache).
4) Transcribe full or window request in chunks.
5) Save transcript to: {DRIVE_ROOT}/transcripts/{request_id}.json
6) Save response to:   {DRIVE_ROOT}/responses/{request_id}.json
7) Move request file to done/failed.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import socket
import ssl
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from faster_whisper import WhisperModel


DRIVE_ROOT = Path(".")
REQUESTS_PENDING = DRIVE_ROOT / "requests" / "pending"
REQUESTS_PROCESSING = DRIVE_ROOT / "requests" / "processing"
REQUESTS_DONE = DRIVE_ROOT / "requests" / "done"
REQUESTS_FAILED = DRIVE_ROOT / "requests" / "failed"
RESPONSES_DIR = DRIVE_ROOT / "responses"
TRANSCRIPTS_DIR = DRIVE_ROOT / "transcripts"

AUDIO_CACHE_DIR = DRIVE_ROOT / "audio-cache"
NORMALIZED_CACHE_DIR = DRIVE_ROOT / "normalized-cache"
CLIP_CACHE_DIR = DRIVE_ROOT / "clip-cache"

POLL_SECONDS = 15
DEFAULT_CHUNK_SECONDS = 600
CALLBACK_CONFIG: dict[str, Any] = {
    "enabled": False,
    "url": "",
    "bearer_token": "",
    "timeout_seconds": 20,
    "retry_attempts": 3,
    "retry_backoff_seconds": 2.0,
    "verify_tls": True,
    "send_on_cache_hit": True,
}
TRANSCRIPTION_CONFIG: dict[str, Any] = {
    "device": "auto",
    "compute_type": "",
}
FIRESTORE_ENABLED = False
FIRESTORE_CLIENT: Any | None = None
FIRESTORE_CONFIG: Any | None = None
WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"
_CUDA_AVAILABLE_CACHE: bool | None = None


def _configure_paths(drive_root: Path) -> None:
    global DRIVE_ROOT
    global REQUESTS_PENDING
    global REQUESTS_PROCESSING
    global REQUESTS_DONE
    global REQUESTS_FAILED
    global RESPONSES_DIR
    global TRANSCRIPTS_DIR
    global AUDIO_CACHE_DIR
    global NORMALIZED_CACHE_DIR
    global CLIP_CACHE_DIR

    DRIVE_ROOT = drive_root
    REQUESTS_PENDING = DRIVE_ROOT / "requests" / "pending"
    REQUESTS_PROCESSING = DRIVE_ROOT / "requests" / "processing"
    REQUESTS_DONE = DRIVE_ROOT / "requests" / "done"
    REQUESTS_FAILED = DRIVE_ROOT / "requests" / "failed"
    RESPONSES_DIR = DRIVE_ROOT / "responses"
    TRANSCRIPTS_DIR = DRIVE_ROOT / "transcripts"
    AUDIO_CACHE_DIR = DRIVE_ROOT / "audio-cache"
    NORMALIZED_CACHE_DIR = DRIVE_ROOT / "normalized-cache"
    CLIP_CACHE_DIR = DRIVE_ROOT / "clip-cache"


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def _load_firestore_module():
    module_path = Path(__file__).with_name("firestore_rest.py")
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("firestore_rest", module_path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:  # noqa: BLE001
        print(f"[worker] firestore module unavailable: {exc}", flush=True)
        return None
    return module


def _configure_firestore(config_path: Path | None) -> None:
    global FIRESTORE_ENABLED
    global FIRESTORE_CLIENT
    global FIRESTORE_CONFIG

    FIRESTORE_ENABLED = False
    FIRESTORE_CLIENT = None
    FIRESTORE_CONFIG = None

    module = _load_firestore_module()
    if module is None:
        print("[worker] firestore disabled: helper module not available", flush=True)
        return
    cfg = module.load_firestore_config(config_path)
    if not bool(getattr(cfg, "enabled", False)):
        return
    FIRESTORE_CLIENT = module.FirestoreRestClient(cfg)
    FIRESTORE_CONFIG = cfg
    FIRESTORE_ENABLED = True


def _load_runtime_config(
    config_path: Path | None,
) -> tuple[Path, int, int, dict[str, Any], dict[str, Any]]:
    payload: dict[str, Any] = {}
    if config_path is not None and config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))

    drive_root_raw = payload.get("drive_root")
    if not drive_root_raw:
        raise RuntimeError(
            "Missing drive_root. Set it in config JSON (key: drive_root)."
        )

    drive_root = Path(str(drive_root_raw)).expanduser()
    poll_seconds = int(payload.get("poll_seconds", 15))
    default_chunk_seconds = int(payload.get("default_chunk_seconds", 600))
    callback_payload = payload.get("callback")
    callback_cfg = dict(CALLBACK_CONFIG)
    if isinstance(callback_payload, dict):
        callback_cfg["enabled"] = _to_bool(callback_payload.get("enabled"), default=False)
        callback_cfg["url"] = str(callback_payload.get("url", "")).strip()
        callback_cfg["bearer_token"] = str(callback_payload.get("bearer_token", "")).strip()
        callback_cfg["timeout_seconds"] = max(3, int(callback_payload.get("timeout_seconds", 20)))
        callback_cfg["retry_attempts"] = max(1, int(callback_payload.get("retry_attempts", 3)))
        callback_cfg["retry_backoff_seconds"] = max(
            0.0,
            float(callback_payload.get("retry_backoff_seconds", 2.0)),
        )
        callback_cfg["verify_tls"] = _to_bool(callback_payload.get("verify_tls"), default=True)
        callback_cfg["send_on_cache_hit"] = _to_bool(callback_payload.get("send_on_cache_hit"), default=True)

    transcription_payload = payload.get("transcription")
    transcription_cfg = dict(TRANSCRIPTION_CONFIG)
    if isinstance(transcription_payload, dict):
        transcription_cfg["device"] = str(transcription_payload.get("device", "auto")).strip().lower() or "auto"
        transcription_cfg["compute_type"] = str(transcription_payload.get("compute_type", "")).strip()

    return (
        drive_root,
        max(1, poll_seconds),
        max(30, default_chunk_seconds),
        callback_cfg,
        transcription_cfg,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Google Drive request/response worker (chunked faster-whisper)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("local_config.json"),
        help="Path to JSON config containing drive_root and optional poll/chunk defaults.",
    )
    return parser.parse_args()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _firestore_request_doc_path(request_id: str) -> str:
    if FIRESTORE_CONFIG is None:
        raise RuntimeError("Firestore config is not initialized")
    return f"{FIRESTORE_CONFIG.requests_collection}/{request_id}"


def _firestore_runtime_doc_path() -> str:
    if FIRESTORE_CONFIG is None:
        raise RuntimeError("Firestore config is not initialized")
    return f"{FIRESTORE_CONFIG.runtime_collection}/{FIRESTORE_CONFIG.session_id}"


def _firestore_patch_request(request_id: str, payload: dict[str, Any]) -> None:
    if not FIRESTORE_ENABLED or FIRESTORE_CLIENT is None:
        return
    FIRESTORE_CLIENT.patch_document(_firestore_request_doc_path(request_id), payload)


def _firestore_get_request(request_id: str) -> dict[str, Any] | None:
    if not FIRESTORE_ENABLED or FIRESTORE_CLIENT is None:
        return None
    return FIRESTORE_CLIENT.get_document(_firestore_request_doc_path(request_id))


def _firestore_get_runtime() -> dict[str, Any] | None:
    if not FIRESTORE_ENABLED or FIRESTORE_CLIENT is None:
        return None
    return FIRESTORE_CLIENT.get_document(_firestore_runtime_doc_path())


def _firestore_claim_next_request() -> tuple[str, dict[str, Any]] | None:
    if not FIRESTORE_ENABLED or FIRESTORE_CLIENT is None or FIRESTORE_CONFIG is None:
        return None
    queued = FIRESTORE_CLIENT.query_requests(status="queued", limit=8, session_id=FIRESTORE_CONFIG.session_id)
    for row in queued:
        request_id = str(row.get("request_id") or "").strip()
        if not request_id:
            continue
        # Best-effort claim (non-transactional). Good enough for single active worker.
        _firestore_patch_request(
            request_id,
            {
                "status": "processing",
                "updated_at": _utc_now(),
                "claimed_at": _utc_now(),
                "worker_id": WORKER_ID,
                "progress": {
                    "chunks_total": 0,
                    "chunks_done": 0,
                    "percent": 0.0,
                    "eta_seconds": None,
                    "message": "claimed",
                },
            },
        )
        claimed = _firestore_get_request(request_id) or {}
        if str(claimed.get("status", "")).strip().lower() != "processing":
            continue
        owner = str(claimed.get("worker_id") or "").strip()
        if owner and owner != WORKER_ID:
            continue
        return request_id, claimed
    return None


def _resolve_callback_from_request(request: dict[str, Any]) -> dict[str, Any]:
    effective = dict(CALLBACK_CONFIG)
    # Primary source: Firestore runtime doc published by local loop.
    runtime_doc = _firestore_get_runtime() if FIRESTORE_ENABLED else None
    if isinstance(runtime_doc, dict):
        runtime_url = str(runtime_doc.get("webhook_public_url", "")).strip()
        runtime_token = str(runtime_doc.get("webhook_token", "")).strip()
        if runtime_url:
            effective["enabled"] = True
            effective["url"] = runtime_url
            if runtime_token:
                effective["bearer_token"] = runtime_token

    # Fallback source: request payload callback block (legacy/compat).
    if not str(effective.get("url", "")).strip():
        callback = request.get("callback")
        if isinstance(callback, dict):
            effective["enabled"] = bool(str(callback.get("url", "")).strip())
            effective["url"] = str(callback.get("url", "")).strip()
            effective["bearer_token"] = str(callback.get("bearer_token", "")).strip()
    return effective


def _post_callback(payload: dict[str, Any], callback_config: dict[str, Any] | None = None) -> bool:
    cfg = callback_config or CALLBACK_CONFIG
    if not _to_bool(cfg.get("enabled"), default=False):
        return False
    callback_url = str(cfg.get("url", "")).strip()
    if not callback_url:
        return False

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = str(cfg.get("bearer_token", "")).strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    timeout_seconds = max(3, int(cfg.get("timeout_seconds", 20)))
    retry_attempts = max(1, int(cfg.get("retry_attempts", 3)))
    retry_backoff = max(0.0, float(cfg.get("retry_backoff_seconds", 2.0)))
    verify_tls = _to_bool(cfg.get("verify_tls"), default=True)
    ssl_context: ssl.SSLContext | None = None
    if callback_url.startswith("https://") and not verify_tls:
        ssl_context = ssl._create_unverified_context()

    for attempt in range(1, retry_attempts + 1):
        req = Request(callback_url, data=body, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=timeout_seconds, context=ssl_context) as response:
                status = int(getattr(response, "status", 200))
                if 200 <= status < 300:
                    print(
                        f"[worker] callback ok request={payload.get('request_id')} status={status} attempt={attempt}",
                        flush=True,
                    )
                    return True
                raise RuntimeError(f"Unexpected callback HTTP status: {status}")
        except (HTTPError, URLError, TimeoutError, RuntimeError, Exception) as exc:
            print(
                f"[worker] callback failed request={payload.get('request_id')} "
                f"attempt={attempt}/{retry_attempts} error={exc}",
                flush=True,
            )
            if attempt < retry_attempts and retry_backoff > 0:
                time.sleep(retry_backoff * attempt)
    return False


def _send_callback_event(
    *,
    request: dict[str, Any],
    request_id: str,
    status: str,
    response_payload: dict[str, Any],
    transcript_payload: dict[str, Any] | None,
    callback_config: dict[str, Any] | None = None,
) -> None:
    callback_payload: dict[str, Any] = {
        "event": "transcription.result",
        "created_at": _utc_now(),
        "request_id": request_id,
        "status": status,
        "request": {
            "day": request.get("day"),
            "kind": request.get("kind"),
            "start_sec": request.get("start_sec"),
            "end_sec": request.get("end_sec"),
            "youtube_url": request.get("youtube_url"),
        },
        "response": response_payload,
    }
    if transcript_payload is not None:
        callback_payload["transcript"] = transcript_payload
    _post_callback(callback_payload, callback_config=callback_config)


def _ensure_dirs() -> None:
    for path in [
        REQUESTS_PENDING,
        REQUESTS_PROCESSING,
        REQUESTS_DONE,
        REQUESTS_FAILED,
        RESPONSES_DIR,
        TRANSCRIPTS_DIR,
        AUDIO_CACHE_DIR,
        NORMALIZED_CACHE_DIR,
        CLIP_CACHE_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def _safe_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value)
    return cleaned.strip("-_") or "source"


def _youtube_video_id(youtube_url: str) -> str | None:
    parsed = urlparse(youtube_url.strip())
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if not path and not parsed.query:
        return None

    if "youtu.be" in host:
        segment = path.split("/", 1)[0].strip()
        return segment or None

    if "youtube.com" in host or "m.youtube.com" in host:
        if path.startswith("watch"):
            q = parse_qs(parsed.query)
            value = q.get("v", [""])[0].strip()
            return value or None
        if path.startswith("live/") or path.startswith("shorts/"):
            segment = path.split("/", 1)[1].split("/", 1)[0].strip()
            return segment or None

    return None


def _audio_cache_index_path() -> Path:
    return AUDIO_CACHE_DIR / "_youtube_cache_index.json"


def _load_audio_cache_index() -> dict[str, Any]:
    path = _audio_cache_index_path()
    if not path.exists():
        return {"by_url": {}, "by_video_id": {}, "updated_at": _utc_now()}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"by_url": {}, "by_video_id": {}, "updated_at": _utc_now()}
    if not isinstance(payload, dict):
        return {"by_url": {}, "by_video_id": {}, "updated_at": _utc_now()}
    payload.setdefault("by_url", {})
    payload.setdefault("by_video_id", {})
    return payload


def _save_audio_cache_index(payload: dict[str, Any]) -> None:
    payload["updated_at"] = _utc_now()
    _write_json(_audio_cache_index_path(), payload)


def _canonical_youtube_url(youtube_url: str) -> str:
    video_id = _youtube_video_id(youtube_url)
    if video_id:
        return f"https://youtube.com/watch?v={video_id}"
    return youtube_url.strip()


def _resolve_cached_audio_path_from_index(
    youtube_url: str,
    video_id: str | None,
) -> Path | None:
    index = _load_audio_cache_index()
    by_url = index.get("by_url", {})
    by_video_id = index.get("by_video_id", {})
    if not isinstance(by_url, dict):
        by_url = {}
    if not isinstance(by_video_id, dict):
        by_video_id = {}

    keys: list[str] = []
    canonical = _canonical_youtube_url(youtube_url)
    if canonical:
        keys.append(canonical)
    if video_id:
        keys.append(video_id)

    for key in keys:
        rel = by_url.get(key) or by_video_id.get(key)
        if not rel:
            continue
        candidate = Path(str(rel))
        if not candidate.is_absolute():
            candidate = DRIVE_ROOT / candidate
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return None


def _remember_cached_audio(
    youtube_url: str,
    video_id: str | None,
    audio_path: Path,
) -> None:
    index = _load_audio_cache_index()
    by_url = index.get("by_url", {})
    by_video_id = index.get("by_video_id", {})
    if not isinstance(by_url, dict):
        by_url = {}
    if not isinstance(by_video_id, dict):
        by_video_id = {}
    relative = str(audio_path.relative_to(DRIVE_ROOT)) if audio_path.is_absolute() else str(audio_path)
    canonical = _canonical_youtube_url(youtube_url)
    if canonical:
        by_url[canonical] = relative
    if video_id:
        by_video_id[video_id] = relative
    index["by_url"] = by_url
    index["by_video_id"] = by_video_id
    _save_audio_cache_index(index)


def _download_youtube_audio(youtube_url: str, key: str) -> Path:
    target_pattern = str(AUDIO_CACHE_DIR / f"{_safe_name(key)}.*")
    existing = sorted(glob.glob(target_pattern))
    if existing:
        return Path(existing[-1])

    outtmpl = str(AUDIO_CACHE_DIR / f"{_safe_name(key)}.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f",
        "bestaudio/best",
        "--no-playlist",
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "-o",
        outtmpl,
        youtube_url,
    ]
    subprocess.run(cmd, check=True)
    produced = sorted(glob.glob(target_pattern))
    if not produced:
        raise RuntimeError(f"yt-dlp completed but no audio file was created for {key}")
    return Path(produced[-1])


def _fallback_cached_audio_for_day(day_value: Any) -> Path | None:
    try:
        day_int = int(day_value)
    except (TypeError, ValueError):
        return None
    candidates = sorted(glob.glob(str(AUDIO_CACHE_DIR / f"day{day_int}-*.*")))
    if not candidates:
        return None
    candidate = Path(candidates[-1])
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate
    return None


def _fallback_cached_audio_for_day_video(day_value: Any, video_id: str | None) -> Path | None:
    try:
        day_int = int(day_value)
    except (TypeError, ValueError):
        return None
    if not video_id:
        return None
    candidates = sorted(glob.glob(str(AUDIO_CACHE_DIR / f"day{day_int}-*{video_id}*.*")))
    if not candidates:
        return None
    candidate = Path(candidates[-1])
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate
    return None


def _normalize_audio(source_audio: Path, key: str) -> Path:
    normalized = NORMALIZED_CACHE_DIR / f"{_safe_name(key)}.wav"
    if normalized.exists() and normalized.stat().st_size > 0:
        return normalized
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_audio),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(normalized),
    ]
    subprocess.run(cmd, check=True)
    return normalized


def _clip_audio(source_wav: Path, request_id: str, start_sec: float, end_sec: float) -> Path:
    clip_path = CLIP_CACHE_DIR / f"{_safe_name(request_id)}-{int(start_sec)}-{int(end_sec)}.wav"
    if clip_path.exists() and clip_path.stat().st_size > 0:
        return clip_path
    duration = max(0.1, float(end_sec) - float(start_sec))
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{float(start_sec):.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(source_wav),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(clip_path),
    ]
    subprocess.run(cmd, check=True)
    return clip_path


def _probe_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    output = subprocess.check_output(cmd).decode("utf-8").strip()
    return float(output)


def _normalize_device(raw: Any, *, default: str = "auto") -> str:
    value = str(raw or "").strip().lower()
    if value in {"gpu", "cuda"}:
        return "cuda"
    if value == "cpu":
        return "cpu"
    if value == "auto":
        return "auto"
    return default


def _cuda_available() -> bool:
    global _CUDA_AVAILABLE_CACHE
    if _CUDA_AVAILABLE_CACHE is not None:
        return _CUDA_AVAILABLE_CACHE
    try:
        subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        _CUDA_AVAILABLE_CACHE = True
    except Exception:  # noqa: BLE001
        _CUDA_AVAILABLE_CACHE = False
    return _CUDA_AVAILABLE_CACHE


def _resolve_transcription_runtime(
    request: dict[str, Any],
) -> tuple[str, str]:
    requested_device = _normalize_device(request.get("device"), default="")
    config_device = _normalize_device(TRANSCRIPTION_CONFIG.get("device"), default="auto")
    selected_device = requested_device or config_device
    if selected_device == "auto":
        selected_device = "cuda" if _cuda_available() else "cpu"

    requested_compute = str(request.get("compute_type", "")).strip()
    config_compute = str(TRANSCRIPTION_CONFIG.get("compute_type", "")).strip()
    selected_compute = requested_compute or config_compute
    if not selected_compute:
        selected_compute = "float16" if selected_device == "cuda" else "int8"
    if selected_device == "cpu" and selected_compute.lower() == "float16":
        selected_compute = "int8"

    return selected_device, selected_compute


def _load_model(
    model_cache: dict[tuple[str, str, str], WhisperModel],
    *,
    model: str,
    device: str,
    compute_type: str,
) -> tuple[WhisperModel, str, str, str | None]:
    key = (model, device, compute_type)
    if key in model_cache:
        return model_cache[key], device, compute_type, None

    try:
        model_cache[key] = WhisperModel(model, device=device, compute_type=compute_type)
        return model_cache[key], device, compute_type, None
    except Exception as exc:  # noqa: BLE001
        error_text = str(exc)
        if device != "cuda":
            raise
        fallback_device = "cpu"
        fallback_compute = "int8"
        fallback_key = (model, fallback_device, fallback_compute)
        try:
            if fallback_key not in model_cache:
                model_cache[fallback_key] = WhisperModel(
                    model,
                    device=fallback_device,
                    compute_type=fallback_compute,
                )
        except Exception:  # noqa: BLE001
            raise RuntimeError(
                f"Failed to load model on cuda ({error_text}) and cpu fallback failed."
            ) from exc
        warning = (
            "CUDA model init failed; switched to CPU automatically "
            f"(compute_type={fallback_compute}). Original error: {error_text}"
        )
        print(f"[worker] {warning}", flush=True)
        return model_cache[fallback_key], fallback_device, fallback_compute, warning


def _load_cached_chunk_segments(path: Path) -> list[dict[str, Any]] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    segments = payload.get("segments")
    if not isinstance(segments, list):
        return None

    output: list[dict[str, Any]] = []
    for item in segments:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        row = {
            "start": float(item.get("start", 0.0)),
            "end": float(item.get("end", 0.0)),
            "text": text,
            "words": [],
        }
        for word in item.get("words", []):
            if not isinstance(word, dict):
                continue
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


def _transcript_segments_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    segments = payload.get("segments")
    if not isinstance(segments, list):
        return 0
    return len(segments)


def _format_elapsed(seconds: float) -> str:
    whole = max(0, int(seconds))
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _transcribe_with_chunks(
    model: WhisperModel,
    audio_path: Path,
    *,
    request_id: str,
    language: str,
    beam_size: int,
    vad_filter: bool,
    vad_parameters: dict[str, Any] | None,
    chunk_seconds: int,
    offset_seconds: float,
    progress_hook: Any | None = None,
) -> list[dict[str, Any]]:
    total_duration = _probe_duration_seconds(audio_path)
    chunks: list[tuple[float, float]] = []
    cursor = 0.0
    while cursor < total_duration:
        end = min(total_duration, cursor + max(30, int(chunk_seconds)))
        chunks.append((cursor, end))
        cursor = end

    request_chunk_dir = TRANSCRIPTS_DIR / "_chunks" / _safe_name(request_id)
    request_chunk_dir.mkdir(parents=True, exist_ok=True)
    job_started = time.time()
    all_segments: list[dict[str, Any]] = []
    total_chunks = len(chunks)
    for index, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        chunk_wall_started = time.time()
        chunk_duration = max(0.1, chunk_end - chunk_start)
        chunk_file = CLIP_CACHE_DIR / f"{_safe_name(request_id)}-chunk-{index:03d}.wav"
        chunk_cache_path = request_chunk_dir / f"chunk-{index:03d}.json"
        cached = _load_cached_chunk_segments(chunk_cache_path)
        elapsed = time.time() - job_started
        completed_before = max(0, index - 1)
        if completed_before > 0:
            avg_per_chunk = elapsed / completed_before
            remaining = max(0, total_chunks - completed_before)
            eta = avg_per_chunk * remaining
            eta_label = _format_elapsed(eta)
        else:
            eta_label = "estimating"
        progress_prefix = (
            f"[worker] request={request_id} chunk={index}/{total_chunks} "
            f"start={chunk_start:.1f}s end={chunk_end:.1f}s "
            f"elapsed={_format_elapsed(elapsed)} eta={eta_label}"
        )
        if callable(progress_hook):
            try:
                progress_hook(
                    chunk_index=index,
                    chunks_total=total_chunks,
                    chunk_start=chunk_start,
                    chunk_end=chunk_end,
                    chunks_done=max(0, index - 1),
                    eta_seconds=(0 if eta_label == "estimating" else None),
                    status="processing",
                    source="cache" if cached is not None else "transcribe",
                    message=f"chunk {index}/{total_chunks}",
                )
            except Exception:  # noqa: BLE001
                pass
        if cached is not None:
            print(f"{progress_prefix} source=cache", flush=True)
            all_segments.extend(cached)
            elapsed_total = time.time() - job_started
            completed = index
            avg_chunk_wall = elapsed_total / max(1, completed)
            remaining_chunks = max(0, total_chunks - completed)
            eta_after = avg_chunk_wall * remaining_chunks
            if callable(progress_hook):
                try:
                    progress_hook(
                        chunk_index=index,
                        chunks_total=total_chunks,
                        chunk_start=chunk_start,
                        chunk_end=chunk_end,
                        chunks_done=completed,
                        eta_seconds=max(0, int(eta_after)),
                        status="processing",
                        source="cache",
                        message=f"chunk {index}/{total_chunks} cached",
                    )
                except Exception:  # noqa: BLE001
                    pass
            print(
                f"[worker] request={request_id} chunk-done={index}/{total_chunks} "
                f"wall={_format_elapsed(time.time() - chunk_wall_started)} "
                f"elapsed={_format_elapsed(elapsed_total)} "
                f"eta_after={_format_elapsed(eta_after)}",
                flush=True,
            )
            continue

        if not chunk_file.exists():
            cmd = [
                "ffmpeg",
                "-y",
                "-ss",
                f"{chunk_start:.3f}",
                "-t",
                f"{chunk_duration:.3f}",
                "-i",
                str(audio_path),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(chunk_file),
            ]
            subprocess.run(cmd, check=True)

        print(f"{progress_prefix} source=transcribe", flush=True)
        segment_iter, _ = model.transcribe(
            str(chunk_file),
            language=language,
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=vad_filter,
            vad_parameters=vad_parameters if vad_filter else None,
        )

        global_shift = offset_seconds + chunk_start
        chunk_segments: list[dict[str, Any]] = []
        for segment in segment_iter:
            text = str(segment.text or "").strip()
            if not text:
                continue
            row = {
                "start": float(segment.start) + global_shift,
                "end": float(segment.end) + global_shift,
                "text": text,
                "words": [],
            }
            for word in segment.words or []:
                if word.start is None or word.end is None:
                    continue
                word_text = str(word.word or "").strip()
                if not word_text:
                    continue
                row["words"].append(
                    {
                        "start": float(word.start) + global_shift,
                        "end": float(word.end) + global_shift,
                        "text": word_text,
                    }
                )
            chunk_segments.append(row)

        _write_json(
            chunk_cache_path,
            {
                "request_id": request_id,
                "chunk_index": index,
                "chunk_start": chunk_start,
                "chunk_end": chunk_end,
                "segments": chunk_segments,
                "created_at": _utc_now(),
            },
        )
        all_segments.extend(chunk_segments)
        elapsed_total = time.time() - job_started
        completed = index
        avg_chunk_wall = elapsed_total / max(1, completed)
        remaining_chunks = max(0, total_chunks - completed)
        eta_after = avg_chunk_wall * remaining_chunks
        if callable(progress_hook):
            try:
                progress_hook(
                    chunk_index=index,
                    chunks_total=total_chunks,
                    chunk_start=chunk_start,
                    chunk_end=chunk_end,
                    chunks_done=completed,
                    eta_seconds=max(0, int(eta_after)),
                    status="processing",
                    source="transcribe",
                    message=f"chunk {index}/{total_chunks} complete",
                )
            except Exception:  # noqa: BLE001
                pass
        print(
            f"[worker] request={request_id} chunk-done={index}/{total_chunks} "
            f"wall={_format_elapsed(time.time() - chunk_wall_started)} "
            f"elapsed={_format_elapsed(elapsed_total)} "
            f"eta_after={_format_elapsed(eta_after)}",
            flush=True,
        )

    all_segments.sort(key=lambda item: (float(item["start"]), float(item["end"])))
    return all_segments


def _resolve_source_audio(request: dict[str, Any]) -> Path:
    source_hint = request.get("source_audio_path")
    if source_hint:
        source_path = Path(str(source_hint))
        if not source_path.is_absolute():
            source_path = DRIVE_ROOT / source_path
        if source_path.exists():
            return source_path

    youtube_url = str(request.get("youtube_url", "")).strip()
    if youtube_url:
        video_id = _youtube_video_id(youtube_url)

        cached = _resolve_cached_audio_path_from_index(youtube_url=youtube_url, video_id=video_id)
        if cached is not None:
            return cached

        # Fallback for older runs before cache index existed.
        # IMPORTANT: only accept fallback files that also match the requested video id.
        day_video_fallback = _fallback_cached_audio_for_day_video(request.get("day"), video_id)
        if day_video_fallback is not None:
            _remember_cached_audio(youtube_url=youtube_url, video_id=video_id, audio_path=day_video_fallback)
            print(
                f"[worker] using fallback cached audio for day/video {request.get('day')}:{video_id}: "
                f"{day_video_fallback}",
                flush=True,
            )
            return day_video_fallback

        # Last-resort fallback for non-standard URLs where a video id cannot be extracted.
        if video_id is None:
            day_fallback = _fallback_cached_audio_for_day(request.get("day"))
            if day_fallback is not None:
                _remember_cached_audio(youtube_url=youtube_url, video_id=video_id, audio_path=day_fallback)
                print(f"[worker] using day fallback cached audio for day {request.get('day')}: {day_fallback}", flush=True)
                return day_fallback

        day_part = f"day{request.get('day', 'x')}"
        if video_id:
            key = f"{day_part}-{video_id}"
        else:
            digest = hashlib.sha1(youtube_url.encode("utf-8")).hexdigest()[:10]
            key = f"{day_part}-url-{digest}"
        downloaded = _download_youtube_audio(youtube_url, key=key)
        _remember_cached_audio(youtube_url=youtube_url, video_id=video_id, audio_path=downloaded)
        return downloaded

    raise RuntimeError("Request must include either source_audio_path or youtube_url")


def _process_request(request_input: Path | dict[str, Any], model_cache: dict[tuple[str, str, str], WhisperModel]) -> None:
    processing_path: Path | None = None
    if isinstance(request_input, Path):
        request = json.loads(request_input.read_text(encoding="utf-8"))
        request_id = str(request.get("request_id", request_input.stem))
        processing_path = REQUESTS_PROCESSING / request_input.name
        if request_input.parent == REQUESTS_PENDING:
            request_input.replace(processing_path)
        else:
            processing_path = request_input
    else:
        request = dict(request_input)
        request_id = str(request.get("request_id", "")).strip()
        if not request_id:
            raise RuntimeError("Firestore request payload missing request_id")

    response_path = RESPONSES_DIR / f"{request_id}.json"
    output_path_ref = str(request.get("output_transcript_path", "")).strip()
    transcript_path = Path(output_path_ref) if output_path_ref else (TRANSCRIPTS_DIR / f"{request_id}.json")
    if not transcript_path.is_absolute():
        transcript_path = DRIVE_ROOT / transcript_path
    callback_cfg = _resolve_callback_from_request(request)

    if FIRESTORE_ENABLED:
        _firestore_patch_request(
            request_id,
            {
                "status": "processing",
                "updated_at": _utc_now(),
                "worker_id": WORKER_ID,
                "started_at": _utc_now(),
                "progress": {
                    "chunks_total": 0,
                    "chunks_done": 0,
                    "percent": 0.0,
                    "eta_seconds": None,
                    "message": "starting",
                },
            },
        )

    try:
        existing_segments = _transcript_segments_count(transcript_path)
        if existing_segments > 0:
            cached_response = {
                "request_id": request_id,
                "status": "done",
                "created_at": _utc_now(),
                "transcript_path": str(transcript_path),
                "segments_count": existing_segments,
                "cached": True,
            }
            _write_json(response_path, cached_response)
            if _to_bool(callback_cfg.get("send_on_cache_hit"), default=True):
                transcript_payload: dict[str, Any] | None = None
                try:
                    transcript_payload = json.loads(transcript_path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    transcript_payload = None
                if transcript_payload is not None:
                    _send_callback_event(
                        request=request,
                        request_id=request_id,
                        status="done",
                        response_payload=cached_response,
                        transcript_payload=transcript_payload,
                        callback_config=callback_cfg,
                    )
                else:
                    print(
                        f"[worker] callback skipped for cache hit {request_id}: transcript payload unavailable",
                        flush=True,
                    )
            if FIRESTORE_ENABLED:
                _firestore_patch_request(
                    request_id,
                    {
                        "status": "done",
                        "updated_at": _utc_now(),
                        "completed_at": _utc_now(),
                        "transcript_path": str(transcript_path),
                        "segments_count": existing_segments,
                        "cached": True,
                        "progress": {
                            "chunks_total": 1,
                            "chunks_done": 1,
                            "percent": 100.0,
                            "eta_seconds": 0,
                            "message": "cache hit",
                        },
                    },
                )
            if processing_path is not None and processing_path.exists():
                processing_path.replace(REQUESTS_DONE / processing_path.name)
            print(f"[worker] cache hit {request_id} -> {transcript_path}", flush=True)
            return

        source_audio = _resolve_source_audio(request)
        normalized = _normalize_audio(source_audio, key=f"day{request.get('day', 'x')}-{source_audio.stem}")

        start_sec_raw = request.get("start_sec")
        end_sec_raw = request.get("end_sec")
        start_sec = float(start_sec_raw) if start_sec_raw is not None else 0.0
        if end_sec_raw is not None:
            end_sec = float(end_sec_raw)
        else:
            end_sec = _probe_duration_seconds(normalized)
        if end_sec <= start_sec:
            raise RuntimeError(f"Invalid request window start={start_sec}, end={end_sec}")

        window_wav = _clip_audio(normalized, request_id=request_id, start_sec=start_sec, end_sec=end_sec)
        model_name = str(request.get("model", "large-v3"))
        requested_device = _normalize_device(request.get("device"), default="auto")
        device, compute_type = _resolve_transcription_runtime(request)
        language = str(request.get("language", "ar"))
        beam_size = int(request.get("beam_size", 5))
        chunk_seconds = int(request.get("chunk_seconds", DEFAULT_CHUNK_SECONDS))
        vad_filter = bool(request.get("vad_filter", True))
        vad_parameters = request.get("vad_parameters")
        if not isinstance(vad_parameters, dict):
            vad_parameters = None

        model, effective_device, effective_compute_type, runtime_warning = _load_model(
            model_cache,
            model=model_name,
            device=device,
            compute_type=compute_type,
        )
        if FIRESTORE_ENABLED:
            _firestore_patch_request(
                request_id,
                {
                    "updated_at": _utc_now(),
                    "requested_device": requested_device,
                    "effective_device": effective_device,
                    "effective_compute_type": effective_compute_type,
                    **({"runtime_warning": runtime_warning} if runtime_warning else {}),
                },
            )

        def _progress_hook(
            *,
            chunk_index: int,
            chunks_total: int,
            chunk_start: float,
            chunk_end: float,
            chunks_done: int,
            eta_seconds: int | None,
            status: str,
            source: str,
            message: str,
        ) -> None:
            if not FIRESTORE_ENABLED:
                return
            percent = 0.0
            if chunks_total > 0:
                percent = round((float(chunks_done) / float(chunks_total)) * 100.0, 2)
            _firestore_patch_request(
                request_id,
                {
                    "status": str(status),
                    "updated_at": _utc_now(),
                    "worker_id": WORKER_ID,
                    "progress": {
                        "chunks_total": int(chunks_total),
                        "chunks_done": int(chunks_done),
                        "percent": percent,
                        "eta_seconds": int(eta_seconds) if eta_seconds is not None else None,
                        "last_chunk_index": int(chunk_index),
                        "last_chunk_start": float(chunk_start),
                        "last_chunk_end": float(chunk_end),
                        "source": str(source),
                        "message": str(message),
                    },
                },
            )

        segments = _transcribe_with_chunks(
            model,
            window_wav,
            request_id=request_id,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=vad_parameters,
            chunk_seconds=chunk_seconds,
            offset_seconds=start_sec,
            progress_hook=_progress_hook,
        )

        payload = {
            "request_id": request_id,
            "day": request.get("day"),
            "created_at": _utc_now(),
            "source_audio": str(source_audio),
            "normalized_wav": str(normalized),
            "window_start": start_sec,
            "window_end": end_sec,
            "model": model_name,
            "requested_device": requested_device,
            "effective_device": effective_device,
            "compute_type": effective_compute_type,
            "language": language,
            "beam_size": beam_size,
            "vad_filter": vad_filter,
            "segments": segments,
            "meta": {
                "segments_count": len(segments),
                "request_kind": request.get("kind", "unknown"),
                **({"runtime_warning": runtime_warning} if runtime_warning else {}),
            },
        }
        _write_json(transcript_path, payload)

        done_response = {
            "request_id": request_id,
            "status": "done",
            "created_at": _utc_now(),
            "transcript_path": str(transcript_path),
            "segments_count": len(segments),
        }
        _write_json(response_path, done_response)
        _send_callback_event(
            request=request,
            request_id=request_id,
            status="done",
            response_payload=done_response,
            transcript_payload=payload,
            callback_config=callback_cfg,
        )
        if FIRESTORE_ENABLED:
            _firestore_patch_request(
                request_id,
                {
                    "status": "done",
                    "updated_at": _utc_now(),
                    "completed_at": _utc_now(),
                    "transcript_path": str(transcript_path),
                    "segments_count": len(segments),
                    "response_path": str(response_path),
                    "progress": {
                        "chunks_total": 1,
                        "chunks_done": 1,
                        "percent": 100.0,
                        "eta_seconds": 0,
                        "message": "completed",
                    },
                },
            )
        if processing_path is not None:
            processing_path.replace(REQUESTS_DONE / processing_path.name)
        print(f"[worker] done {request_id} -> {transcript_path}", flush=True)

    except Exception as exc:  # noqa: BLE001
        failed_response = {
            "request_id": request_id,
            "status": "failed",
            "created_at": _utc_now(),
            "error": str(exc),
        }
        _write_json(response_path, failed_response)
        _send_callback_event(
            request=request,
            request_id=request_id,
            status="failed",
            response_payload=failed_response,
            transcript_payload=None,
            callback_config=callback_cfg,
        )
        if FIRESTORE_ENABLED:
            _firestore_patch_request(
                request_id,
                {
                    "status": "failed",
                    "updated_at": _utc_now(),
                    "failed_at": _utc_now(),
                    "error": str(exc),
                },
            )
        if processing_path is not None and processing_path.exists():
            processing_path.replace(REQUESTS_FAILED / processing_path.name)
        print(f"[worker] failed {request_id}: {exc}", flush=True)


def main() -> None:
    global POLL_SECONDS
    global DEFAULT_CHUNK_SECONDS
    global CALLBACK_CONFIG
    global TRANSCRIPTION_CONFIG

    args = _parse_args()
    drive_root, poll_seconds, default_chunk_seconds, callback_cfg, transcription_cfg = _load_runtime_config(args.config)
    _configure_firestore(args.config)
    _configure_paths(drive_root)
    POLL_SECONDS = poll_seconds
    DEFAULT_CHUNK_SECONDS = default_chunk_seconds
    CALLBACK_CONFIG = callback_cfg
    TRANSCRIPTION_CONFIG = transcription_cfg

    _ensure_dirs()
    model_cache: dict[tuple[str, str, str], WhisperModel] = {}
    print(
        "[worker] started "
        f"drive_root={DRIVE_ROOT} "
        f"poll={POLL_SECONDS}s "
        f"chunk_default={DEFAULT_CHUNK_SECONDS}s "
        f"device_default={_normalize_device(TRANSCRIPTION_CONFIG.get('device'), default='auto')} "
        f"compute_default={str(TRANSCRIPTION_CONFIG.get('compute_type') or '').strip() or 'auto'} "
        f"callback_enabled={_to_bool(CALLBACK_CONFIG.get('enabled'), default=False)} "
        f"firestore_enabled={FIRESTORE_ENABLED} "
        f"worker_id={WORKER_ID}",
        flush=True,
    )
    while True:
        processed_any = False

        if FIRESTORE_ENABLED:
            claimed = _firestore_claim_next_request()
            if claimed is not None:
                _request_id, request_payload = claimed
                _process_request(request_payload, model_cache=model_cache)
                processed_any = True

        queued = sorted(REQUESTS_PENDING.glob("*.json")) + sorted(REQUESTS_PROCESSING.glob("*.json"))
        if queued:
            for request_path in queued:
                _process_request(request_path, model_cache=model_cache)
                processed_any = True

        if not processed_any:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
