from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Sequence


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def run_command(command: Sequence[str]) -> None:
    subprocess.run(command, check=True)


def write_json(path: Path, payload: dict) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
