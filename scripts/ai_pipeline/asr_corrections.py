from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .quran import normalize_arabic
from .types import TranscriptSegment, TranscriptWord


@dataclass(frozen=True)
class CorrectionEntry:
    source: str
    target: str
    source_norm: str
    target_norm: str
    is_phrase: bool


def _parse_replacements_payload(payload: object) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []

    def visit(node: object, depth: int = 0) -> None:
        if depth > 8:
            return

        if isinstance(node, list):
            for item in node:
                visit(item, depth + 1)
            return

        if not isinstance(node, dict):
            return

        if "replacements" in node and isinstance(node["replacements"], (dict, list)):
            visit(node["replacements"], depth + 1)
            return

        from_value = node.get("from") or node.get("source") or node.get("raw")
        to_value = node.get("to") or node.get("target") or node.get("normalized")
        if from_value is not None and to_value is not None:
            left = str(from_value).strip()
            right = str(to_value).strip()
            if left and right:
                parsed.append((left, right))

        # Dict-mapping case (including nested buckets like high_confidence/medium_confidence).
        for key, value in node.items():
            if key in {"from", "source", "raw", "to", "target", "normalized", "replacements"}:
                continue
            if isinstance(value, str):
                left = str(key or "").strip()
                right = value.strip()
                if left and right:
                    parsed.append((left, right))
            elif isinstance(value, (dict, list)):
                visit(value, depth + 1)

    visit(payload, depth=0)
    return parsed


def load_asr_corrections(path: Path | None) -> tuple[list[CorrectionEntry], dict]:
    if path is None:
        return [], {"enabled": False, "reason": "no_path"}
    if not path.exists():
        return [], {"enabled": False, "reason": "file_not_found", "path": str(path)}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], {"enabled": False, "reason": "invalid_json", "path": str(path), "error": str(exc)}

    pairs = _parse_replacements_payload(payload)
    # Keep first-seen mapping for each normalized source token/phrase.
    deduped_pairs: list[tuple[str, str]] = []
    seen_sources: set[str] = set()
    entries: list[CorrectionEntry] = []
    for source, target in pairs:
        source_norm = normalize_arabic(source, strict=False)
        target_norm = normalize_arabic(target, strict=False)
        if not source_norm or not target_norm:
            continue
        if source_norm in seen_sources:
            continue
        seen_sources.add(source_norm)
        deduped_pairs.append((source, target))
        entries.append(
            CorrectionEntry(
                source=source,
                target=target,
                source_norm=source_norm,
                target_norm=target_norm,
                is_phrase=(" " in source_norm),
            )
        )

    return entries, {
        "enabled": bool(entries),
        "path": str(path),
        "entries_total": len(entries),
        "entries_raw": len(pairs),
        "entries_deduped": len(deduped_pairs),
    }


def _apply_phrase_replacements(text: str, entries: list[CorrectionEntry]) -> tuple[str, int]:
    if not text or not entries:
        return text, 0

    phrase_entries = [entry for entry in entries if entry.is_phrase]
    if not phrase_entries:
        return text, 0

    # Longest phrase first to avoid smaller phrases clobbering larger rules.
    phrase_entries.sort(key=lambda entry: len(entry.source_norm.split()), reverse=True)

    tokens = text.split()
    replaced = 0
    index = 0
    output: list[str] = []
    while index < len(tokens):
        match_found = False
        for entry in phrase_entries:
            source_tokens = entry.source_norm.split()
            width = len(source_tokens)
            if width <= 0 or index + width > len(tokens):
                continue
            if tokens[index : index + width] == source_tokens:
                output.extend(entry.target_norm.split())
                replaced += 1
                index += width
                match_found = True
                break
        if match_found:
            continue
        output.append(tokens[index])
        index += 1

    return " ".join(output), replaced


def apply_asr_corrections(
    transcript_segments: list[TranscriptSegment],
    corrections_path: Path | None,
) -> tuple[list[TranscriptSegment], dict]:
    entries, load_info = load_asr_corrections(corrections_path)
    if not entries:
        return transcript_segments, load_info

    single_word_map: dict[str, str] = {}
    for entry in entries:
        if not entry.is_phrase:
            single_word_map[entry.source_norm] = entry.target_norm

    updated_segments: list[TranscriptSegment] = []
    changed_segments = 0
    changed_words = 0
    phrase_replacements = 0

    for segment in transcript_segments:
        updated_words: list[TranscriptWord] = []
        segment_word_changed = False

        for word in segment.words:
            normalized = normalize_arabic(word.text, strict=False)
            replacement = single_word_map.get(normalized)
            if replacement and replacement != normalized:
                changed_words += 1
                segment_word_changed = True
                updated_words.append(TranscriptWord(start=word.start, end=word.end, text=replacement))
            else:
                updated_words.append(TranscriptWord(start=word.start, end=word.end, text=normalized or word.text))

        if updated_words:
            normalized_segment_text = " ".join(item.text for item in updated_words if item.text.strip())
        else:
            normalized_segment_text = normalize_arabic(segment.text, strict=False)

        normalized_segment_text, phrase_hits = _apply_phrase_replacements(normalized_segment_text, entries)
        phrase_replacements += phrase_hits
        if phrase_hits > 0:
            segment_word_changed = True

        if segment_word_changed:
            changed_segments += 1

        updated_segments.append(
            TranscriptSegment(
                start=float(segment.start),
                end=float(segment.end),
                text=normalized_segment_text,
                words=updated_words,
            )
        )

    info = {
        **load_info,
        "segments_total": len(transcript_segments),
        "segments_changed": changed_segments,
        "words_changed": changed_words,
        "phrase_replacements": phrase_replacements,
    }
    return updated_segments, info
