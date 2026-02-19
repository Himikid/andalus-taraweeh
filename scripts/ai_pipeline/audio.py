from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .io import run_command


def require_binary(name: str) -> None:
    if shutil.which(name):
        return
    raise RuntimeError(f"Required binary '{name}' not found. Install it before running the pipeline.")


def download_youtube_audio(youtube_url: str, working_dir: Path) -> Path:
    require_binary("yt-dlp")
    working_dir.mkdir(parents=True, exist_ok=True)

    output_template = working_dir / "source.%(ext)s"

    run_command(
        [
            "yt-dlp",
            "-x",
            "--audio-format",
            "wav",
            "--audio-quality",
            "0",
            "-o",
            str(output_template),
            youtube_url,
        ]
    )

    candidates = sorted(working_dir.glob("source.*"))
    if not candidates:
        raise RuntimeError("yt-dlp completed but no audio file was created.")

    return candidates[-1]


def normalize_audio(input_audio: Path, normalized_wav: Path) -> Path:
    require_binary("ffmpeg")
    normalized_wav.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_audio),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(normalized_wav),
    ]

    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return normalized_wav


def prepare_audio_source(
    day: int,
    youtube_url: str | None,
    audio_file: Path | None,
    cache_dir: Path,
) -> tuple[Path, str]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    day_dir = cache_dir / f"day-{day}"
    day_dir.mkdir(parents=True, exist_ok=True)

    if youtube_url:
        raw_audio = download_youtube_audio(youtube_url, day_dir)
        source = youtube_url
    elif audio_file:
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        raw_audio = audio_file
        source = str(audio_file)
    else:
        raise ValueError("Provide either --youtube-url or --audio-file.")

    normalized = day_dir / "normalized.wav"
    return normalize_audio(raw_audio, normalized), source
