#!/usr/bin/env python3
"""
Local webhook receiver for Colab transcript callbacks.

Expected payload from scripts/colab/drive_transcription_worker.py:
{
  "event": "transcription.result",
  "request_id": "...",
  "status": "done" | "failed",
  "response": {...},
  "transcript": {... optional ...}
}

Writes:
- {drive_root}/responses/{request_id}.json
- {drive_root}/transcripts/{request_id}.json (when transcript provided)
"""
from __future__ import annotations

import argparse
import hmac
import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


CONFIG_LOCK = threading.Lock()
CONFIG: dict[str, Any] = {
    "drive_root": Path(".").resolve(),
    "token": "",
    "mirror_dir": None,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _resolve_drive_root(explicit: Path | None, config_path: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser().resolve()
    if config_path and config_path.exists():
        payload = _read_json(config_path)
        value = payload.get("drive_root")
        if value:
            return Path(str(value)).expanduser().resolve()
    raise RuntimeError("Missing drive_root. Pass --drive-root or provide it in --drive-config.")


def _resolve_transcript_path(
    transcript_ref: str | None,
    *,
    request_id: str,
    drive_root: Path,
) -> Path:
    drive_root = drive_root.resolve()
    default_target = (drive_root / "transcripts" / f"{request_id}.json").resolve()
    if not transcript_ref:
        return default_target

    raw = str(transcript_ref).strip()
    if not raw:
        return default_target

    candidate = Path(raw)
    if not candidate.is_absolute():
        mapped = (drive_root / candidate).resolve()
        if mapped.is_relative_to(drive_root):
            return mapped
        return default_target

    colab_prefix = "/content/drive/MyDrive/"
    if raw.startswith(colab_prefix):
        relative = raw[len(colab_prefix) :].strip("/")
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
                # Path likely includes the remote Drive folder name at the first segment.
                parts = parts[1:]
        mapped = (drive_root.joinpath(*parts)).resolve()
        if mapped.is_relative_to(drive_root):
            return mapped
        return default_target

    return default_target


def _require_token(headers: Any, expected_token: str) -> bool:
    if not expected_token:
        return True
    auth = str(headers.get("Authorization", "")).strip()
    if not auth.startswith("Bearer "):
        return False
    provided = auth[len("Bearer ") :].strip()
    return hmac.compare_digest(provided, expected_token)


def _status_payload(*, drive_root: Path, token: str) -> dict[str, Any]:
    return {
        "ok": True,
        "service": "local_transcript_webhook",
        "time": _utc_now(),
        "drive_root": str(drive_root),
        "auth": "bearer" if token else "none",
        "endpoints": {
            "health": "/health",
            "ingest_transcript": "/ingest/transcript",
        },
    }


class TranscriptWebhookHandler(BaseHTTPRequestHandler):
    server_version = "LocalTranscriptWebhook/1.0"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") not in {"", "/health", "/healthz"}:
            self._send_json(404, {"ok": False, "error": "not_found"})
            return
        with CONFIG_LOCK:
            drive_root: Path = CONFIG["drive_root"]
            token = str(CONFIG.get("token", ""))
        self._send_json(200, _status_payload(drive_root=drive_root.resolve(), token=token))

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/ingest/transcript":
            self._send_json(404, {"ok": False, "error": "not_found"})
            return

        with CONFIG_LOCK:
            drive_root: Path = CONFIG["drive_root"].resolve()
            expected_token = str(CONFIG.get("token", ""))
            mirror_dir: Path | None = CONFIG.get("mirror_dir")

        if not _require_token(self.headers, expected_token):
            self._send_json(401, {"ok": False, "error": "unauthorized"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"ok": False, "error": "invalid_content_length"})
            return
        if content_length <= 0:
            self._send_json(400, {"ok": False, "error": "empty_body"})
            return

        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001
            self._send_json(400, {"ok": False, "error": "invalid_json"})
            return

        if not isinstance(payload, dict):
            self._send_json(400, {"ok": False, "error": "payload_must_be_object"})
            return

        response_payload = payload.get("response")
        if not isinstance(response_payload, dict):
            response_payload = {}
        request_id = str(payload.get("request_id") or response_payload.get("request_id") or "").strip()
        status = str(payload.get("status") or response_payload.get("status") or "").strip().lower()
        if not request_id:
            self._send_json(400, {"ok": False, "error": "missing_request_id"})
            return
        if status not in {"done", "failed"}:
            self._send_json(400, {"ok": False, "error": "status_must_be_done_or_failed"})
            return

        transcript_payload = payload.get("transcript")
        transcript_ref = response_payload.get("transcript_path")
        transcript_target = _resolve_transcript_path(
            str(transcript_ref) if transcript_ref else None,
            request_id=request_id,
            drive_root=drive_root,
        )
        try:
            transcript_ref_out = str(transcript_target.resolve().relative_to(drive_root.resolve()))
        except ValueError:
            transcript_target = (drive_root / "transcripts" / f"{request_id}.json").resolve()
            transcript_ref_out = str(transcript_target.relative_to(drive_root))

        if status == "done":
            if isinstance(transcript_payload, dict):
                _write_json(transcript_target, transcript_payload)
            elif not transcript_target.exists():
                self._send_json(
                    422,
                    {
                        "ok": False,
                        "error": "missing_transcript_payload",
                        "request_id": request_id,
                    },
                )
                return

        final_response = {
            **response_payload,
            "request_id": request_id,
            "status": status,
            "created_at": response_payload.get("created_at") or _utc_now(),
        }
        if status == "done":
            final_response["transcript_path"] = transcript_ref_out

        response_target = drive_root / "responses" / f"{request_id}.json"
        _write_json(response_target, final_response)

        if mirror_dir is not None:
            mirror_payload = {
                "received_at": _utc_now(),
                "request_id": request_id,
                "status": status,
                "payload": payload,
                "written_response": str(response_target),
                "written_transcript": str(transcript_target) if status == "done" else None,
            }
            mirror_target = mirror_dir / f"{request_id}-{int(datetime.now().timestamp())}.json"
            _write_json(mirror_target, mirror_payload)

        self._send_json(
            200,
            {
                "ok": True,
                "request_id": request_id,
                "status": status,
                "response_path": str(response_target),
                "transcript_path": str(transcript_target) if status == "done" else None,
            },
        )


@dataclass
class RunningWebhook:
    server: ThreadingHTTPServer
    thread: threading.Thread
    host: str
    port: int
    ingest_url: str
    health_url: str
    drive_root: Path
    auth_enabled: bool


def start_webhook_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    drive_root: Path,
    token: str = "",
    mirror_dir: Path | None = None,
) -> RunningWebhook:
    drive_root = drive_root.expanduser().resolve()
    with CONFIG_LOCK:
        CONFIG["drive_root"] = drive_root
        CONFIG["token"] = str(token or "")
        CONFIG["mirror_dir"] = mirror_dir.resolve() if mirror_dir else None
    server = ThreadingHTTPServer((host, int(port)), TranscriptWebhookHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True, name="transcript-webhook")
    thread.start()
    bound_port = int(server.server_port)
    return RunningWebhook(
        server=server,
        thread=thread,
        host=host,
        port=bound_port,
        ingest_url=f"http://{host}:{bound_port}/ingest/transcript",
        health_url=f"http://{host}:{bound_port}/health",
        drive_root=drive_root,
        auth_enabled=bool(token),
    )


def stop_webhook_server(runtime: RunningWebhook) -> None:
    runtime.server.shutdown()
    runtime.server.server_close()
    runtime.thread.join(timeout=3.0)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local transcript webhook receiver for ngrok/Colab callbacks.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765).")
    parser.add_argument("--drive-root", type=Path, help="Local Google Drive bridge root.")
    parser.add_argument(
        "--drive-config",
        type=Path,
        default=Path("scripts/colab/local_config.json"),
        help="Config JSON containing drive_root when --drive-root is omitted.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default="",
        help="Expected bearer token. If empty, auth is disabled (not recommended).",
    )
    parser.add_argument(
        "--mirror-dir",
        type=Path,
        help="Optional local dir to mirror raw webhook payloads for debugging.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    drive_root = _resolve_drive_root(args.drive_root, args.drive_config)

    runtime = start_webhook_server(
        host=args.host,
        port=int(args.port),
        drive_root=drive_root,
        token=str(args.token or ""),
        mirror_dir=args.mirror_dir,
    )
    print(
        "[webhook] listening "
        f"{runtime.ingest_url} "
        f"health={runtime.health_url} "
        f"drive_root={runtime.drive_root} "
        f"auth={'enabled' if args.token else 'disabled'}",
        flush=True,
    )
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        stop_webhook_server(runtime)


if __name__ == "__main__":
    main()
