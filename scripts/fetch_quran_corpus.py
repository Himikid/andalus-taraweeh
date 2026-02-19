#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_URL = "https://api.alquran.cloud/v1/quran/quran-uthmani"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Quran corpus and store as local JSON for ayah matching.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Source URL for Quran corpus")
    parser.add_argument("--output", type=Path, default=Path("data/quran/quran_arabic.json"), help="Output file path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        import requests
    except ImportError as exc:
        raise SystemExit(
            "Missing Python dependencies. Install with: pip install -r scripts/requirements-ai.txt"
        ) from exc

    response = requests.get(args.url, timeout=60)
    response.raise_for_status()

    payload = response.json()
    data = payload.get("data", {})
    surahs = data.get("surahs", [])

    transformed = {
        "surahs": [
            {
                "number": surah.get("number"),
                "name": surah.get("englishName", f"Surah {surah.get('number', '')}").strip(),
                "ayahs": [
                    {
                        "number": ayah.get("numberInSurah"),
                        "text": ayah.get("text", ""),
                    }
                    for ayah in surah.get("ayahs", [])
                ],
            }
            for surah in surahs
        ]
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(transformed, handle, ensure_ascii=False, indent=2)

    print(f"Saved Quran corpus to {args.output}")
    print(f"Surahs: {len(transformed['surahs'])}")


if __name__ == "__main__":
    main()
