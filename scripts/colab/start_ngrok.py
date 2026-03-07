#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Config file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON config at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Config root must be a JSON object: {path}")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start ngrok tunnel for local transcript webhook.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("local_config.json"),
        help="Path to local config JSON.",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Override webhook/ngrok port from config.",
    )
    parser.add_argument(
        "--binary",
        type=str,
        help="Override ngrok executable path/name.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    payload = _load_config(args.config)

    ngrok_cfg = payload.get("ngrok", {})
    webhook_cfg = payload.get("webhook", {})
    if not isinstance(ngrok_cfg, dict):
        ngrok_cfg = {}
    if not isinstance(webhook_cfg, dict):
        webhook_cfg = {}

    binary = str(args.binary or ngrok_cfg.get("binary") or "ngrok").strip()
    if not binary:
        raise SystemExit("ngrok binary is empty. Set ngrok.binary in config or pass --binary.")

    port = args.port
    if port is None:
        try:
            port = int(ngrok_cfg.get("port") or webhook_cfg.get("port") or 8765)
        except (TypeError, ValueError):
            port = 8765
    if port <= 0:
        raise SystemExit("Port must be a positive integer.")

    domain = str(ngrok_cfg.get("domain") or "").strip()
    cmd = [binary, "http", str(port), "--log=stdout"]
    if domain:
        cmd += ["--url", domain]

    print("[ngrok] starting:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
