from __future__ import annotations

from .types import Marker


def interpolate_small_gaps(
    markers: list[Marker],
    *,
    max_gap_ayahs: int = 2,
) -> list[Marker]:
    if len(markers) < 2:
        return markers

    ordered = sorted(markers, key=lambda item: (item.surah_number or 0, item.ayah, item.time))
    out: list[Marker] = []

    for index, current in enumerate(ordered[:-1]):
        out.append(current)
        nxt = ordered[index + 1]
        if current.surah != nxt.surah:
            continue
        missing = nxt.ayah - current.ayah - 1
        if missing <= 0 or missing > max_gap_ayahs:
            continue
        span = max(1, nxt.time - current.time)
        for offset in range(1, missing + 1):
            ratio = offset / (missing + 1)
            inferred_time = int(round(current.time + (span * ratio)))
            out.append(
                Marker(
                    time=inferred_time,
                    start_time=inferred_time,
                    end_time=inferred_time,
                    surah=current.surah,
                    surah_number=current.surah_number,
                    ayah=current.ayah + offset,
                    juz=current.juz,
                    quality="inferred",
                    confidence=0.55,
                    reciter=current.reciter,
                )
            )

    out.append(ordered[-1])
    return sorted(out, key=lambda item: (item.time, item.surah_number or 0, item.ayah))


__all__ = ["interpolate_small_gaps"]

