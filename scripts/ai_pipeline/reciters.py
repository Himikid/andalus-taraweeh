from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .types import PrayerSegment


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _load_profiles(profiles_path: Path) -> dict[str, np.ndarray]:
    if not profiles_path.exists():
        return {}

    with profiles_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    reciters = payload.get("reciters", {})
    loaded: dict[str, np.ndarray] = {}

    for name, vector in reciters.items():
        loaded[name] = np.asarray(vector, dtype=np.float32)

    return loaded


def _save_profiles(profiles_path: Path, reciters: dict[str, np.ndarray]) -> None:
    profiles_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "reciters": {name: vector.tolist() for name, vector in reciters.items()},
    }

    with profiles_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _bootstrap_day1_profiles(
    embeddings: list[np.ndarray],
    prayers: list[PrayerSegment],
    profiles_path: Path,
) -> dict[str, np.ndarray]:
    hasan_until = 47 * 60
    samir_from = 55 * 60

    hasan_vectors = [
        embeddings[index]
        for index, prayer in enumerate(prayers)
        if prayer.start < hasan_until and np.linalg.norm(embeddings[index]) > 0
    ]
    samir_vectors = [
        embeddings[index]
        for index, prayer in enumerate(prayers)
        if prayer.start >= samir_from and np.linalg.norm(embeddings[index]) > 0
    ]

    if not hasan_vectors or not samir_vectors:
        return _load_profiles(profiles_path)

    profiles = {
        "Hasan": np.mean(np.stack(hasan_vectors), axis=0),
        "Samir": np.mean(np.stack(samir_vectors), axis=0),
    }
    _save_profiles(profiles_path, profiles)
    return profiles


def _slice_segment(audio: np.ndarray, sample_rate: int, start_second: int, end_second: int, cap_seconds: int = 90) -> np.ndarray:
    start_index = max(0, start_second * sample_rate)
    end_index = min(len(audio), end_second * sample_rate)

    max_end_index = min(end_index, start_index + cap_seconds * sample_rate)
    segment = audio[start_index:max_end_index]
    return segment.astype(np.float32)


def _try_build_embeddings(audio: np.ndarray, sample_rate: int, prayers: list[PrayerSegment]) -> list[np.ndarray] | None:
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
    except ImportError:
        return None

    encoder = VoiceEncoder()
    embeddings: list[np.ndarray] = []

    for prayer in prayers:
        segment = _slice_segment(audio, sample_rate, prayer.start, prayer.end)
        if len(segment) < sample_rate * 8:
            embeddings.append(np.zeros(256, dtype=np.float32))
            continue

        processed = preprocess_wav(segment, source_sr=sample_rate)
        embedding = encoder.embed_utterance(processed).astype(np.float32)
        embeddings.append(embedding)

    return embeddings


def assign_reciters(
    day: int,
    audio: np.ndarray,
    sample_rate: int,
    prayers: list[PrayerSegment],
    profiles_path: Path,
    bootstrap_reciters: bool,
) -> list[PrayerSegment]:
    if not prayers:
        return prayers

    embeddings = _try_build_embeddings(audio, sample_rate, prayers)

    if embeddings is None:
        for prayer in prayers:
            prayer.reciter = prayer.reciter or "Unknown"
        return prayers

    profiles = _load_profiles(profiles_path)
    if day == 1 and bootstrap_reciters:
        profiles = _bootstrap_day1_profiles(embeddings=embeddings, prayers=prayers, profiles_path=profiles_path)

    if not profiles:
        for prayer in prayers:
            prayer.reciter = prayer.reciter or "Unknown"
        return prayers

    labels: list[str] = []
    confidences: list[float] = []

    for prayer, embedding in zip(prayers, embeddings):
        if np.linalg.norm(embedding) == 0:
            labels.append("Unknown")
            confidences.append(0.0)
            continue

        best_name = "Unknown"
        best_score = -1.0
        second_best = -1.0

        for name, profile_vector in profiles.items():
            score = _cosine_similarity(embedding, profile_vector)
            if score > best_score:
                second_best = best_score
                best_score = score
                best_name = name
            elif score > second_best:
                second_best = score

        margin = max(0.0, best_score - max(0.0, second_best))
        confident = best_score >= 0.5 and margin >= 0.025
        if not confident:
            labels.append("Talk" if best_score >= 0.4 else "Unknown")
            confidences.append(best_score)
            continue

        labels.append(best_name)
        confidences.append(best_score)

    # Smooth out single-segment flips caused by noisy embeddings.
    for index in range(1, len(labels) - 1):
        left = labels[index - 1]
        center = labels[index]
        right = labels[index + 1]
        if left == right and center != left and confidences[index] < 0.62:
            labels[index] = left

    for prayer, label in zip(prayers, labels):
        prayer.reciter = prayer.reciter or label

    return prayers
