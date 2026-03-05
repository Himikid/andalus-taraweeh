#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz, process
from rapidfuzz.distance import Levenshtein

ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
ARABIC_PUNCT = re.compile(r"[^\u0621-\u063A\u0641-\u064A\s]")
MULTI_SPACE = re.compile(r"\s+")
LEADING_SEGMENT_NUMBER = re.compile(r"^\s*\d+[.\-:]\s*")
ARABIC_CHAR_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
        "ـ": "",
    }
)

COMMON_PHRASE_REPLACEMENTS: list[tuple[str, str]] = [
    (r"\bالمستكين\b", "المستقيم"),
    (r"\bالمستقين\b", "المستقيم"),
    (r"\bالمرضوب\b", "المغضوب"),
    (r"\bوللضا\b", "ولا الضالين"),
    (r"\bوللضى\b", "ولا الضالين"),
    (r"\bان عمت\b", "انعمت"),
]

TOKEN_DIRECT_MAP: dict[str, str] = {
    "المستكين": "المستقيم",
    "المستقين": "المستقيم",
    "المرضوب": "المغضوب",
    "وللضا": "الضالين",
    "وللضى": "الضالين",
    "انعنت": "انعمت",
}


@dataclass
class Correction:
    from_token: str
    to_token: str
    score: float
    edit_distance: int


@dataclass
class SegmentNormalizationResult:
    text: str
    changed_tokens: int
    total_tokens: int
    phrase_hits: int
    corrections: list[Correction]


def normalize_arabic(text: str) -> str:
    value = text or ""
    value = LEADING_SEGMENT_NUMBER.sub("", value)
    value = ARABIC_DIACRITICS.sub("", value)
    value = value.translate(ARABIC_CHAR_MAP)
    value = ARABIC_PUNCT.sub(" ", value)
    value = MULTI_SPACE.sub(" ", value).strip().lower()
    if value:
        tokens = value.split()
        deduped: list[str] = []
        for token in tokens:
            if not deduped or token != deduped[-1]:
                deduped.append(token)
        value = " ".join(deduped)
    return value


def build_quran_vocab(corpus_path: Path) -> tuple[set[str], dict[tuple[str, int], list[str]], dict[int, list[str]]]:
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    surahs = payload.get("surahs", [])

    vocab: set[str] = set()
    for surah in surahs if isinstance(surahs, list) else []:
        ayahs = surah.get("ayahs", [])
        for ayah in ayahs if isinstance(ayahs, list) else []:
            normalized = normalize_arabic(str(ayah.get("text", "") or ""))
            if not normalized:
                continue
            vocab.update(token for token in normalized.split() if token)

    by_first_len: dict[tuple[str, int], list[str]] = {}
    by_len: dict[int, list[str]] = {}
    for token in sorted(vocab):
        if not token:
            continue
        by_first_len.setdefault((token[0], len(token)), []).append(token)
        by_len.setdefault(len(token), []).append(token)
    return vocab, by_first_len, by_len


def apply_phrase_replacements(text: str) -> tuple[str, int]:
    out = text
    hits = 0
    for pattern, replacement in COMMON_PHRASE_REPLACEMENTS:
        updated, count = re.subn(pattern, replacement, out)
        if count > 0:
            out = updated
            hits += count
    return out, hits


def nearest_quran_token(
    token: str,
    vocab: set[str],
    by_first_len: dict[tuple[str, int], list[str]],
    by_len: dict[int, list[str]],
    min_score: float,
    max_edit_distance: int,
) -> tuple[str | None, float, int]:
    if token in vocab:
        return None, 0.0, 0

    if token in TOKEN_DIRECT_MAP:
        mapped = TOKEN_DIRECT_MAP[token]
        edit_distance = Levenshtein.distance(token, mapped)
        return mapped, 99.0, edit_distance

    if len(token) < 4:
        return None, 0.0, 0

    candidates: list[str] = []
    first_char = token[0]
    length = len(token)
    for size in range(max(2, length - 1), length + 2):
        candidates.extend(by_first_len.get((first_char, size), []))
    if not candidates:
        return None, 0.0, 0

    hit = process.extractOne(token, candidates, scorer=fuzz.ratio, score_cutoff=min_score)
    if not hit:
        return None, 0.0, 0
    best_token, score, _ = hit
    edit_distance = Levenshtein.distance(token, best_token)
    if edit_distance > max_edit_distance:
        return None, 0.0, 0
    return best_token, float(score), edit_distance


def quran_token_ratio(tokens: list[str], vocab: set[str]) -> float:
    if not tokens:
        return 0.0
    exact_hits = sum(1 for token in tokens if token in vocab)
    return exact_hits / max(1, len(tokens))


def normalize_segment_text(
    text: str,
    vocab: set[str],
    by_first_len: dict[tuple[str, int], list[str]],
    by_len: dict[int, list[str]],
    min_score: float,
    max_edit_distance: int,
    min_quran_ratio_for_fuzzy: float,
) -> SegmentNormalizationResult:
    normalized = normalize_arabic(text)
    normalized, phrase_hits = apply_phrase_replacements(normalized)
    tokens = [token for token in normalized.split() if token]
    segment_quran_ratio = quran_token_ratio(tokens, vocab)

    corrected: list[str] = []
    changes: list[Correction] = []
    changed_count = 0
    for token in tokens:
        replacement, score, edit_distance = (None, 0.0, 0)
        if segment_quran_ratio >= min_quran_ratio_for_fuzzy or token in TOKEN_DIRECT_MAP:
            replacement, score, edit_distance = nearest_quran_token(
                token=token,
                vocab=vocab,
                by_first_len=by_first_len,
                by_len=by_len,
                min_score=min_score,
                max_edit_distance=max_edit_distance,
            )
        if replacement and replacement != token:
            corrected.append(replacement)
            changed_count += 1
            changes.append(
                Correction(
                    from_token=token,
                    to_token=replacement,
                    score=round(score, 2),
                    edit_distance=edit_distance,
                )
            )
        else:
            corrected.append(token)

    return SegmentNormalizationResult(
        text=" ".join(corrected).strip(),
        changed_tokens=changed_count,
        total_tokens=len(tokens),
        phrase_hits=phrase_hits,
        corrections=changes,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize transcript text against Quran vocabulary.")
    parser.add_argument("--input", type=Path, required=True, help="Input transcript JSON")
    parser.add_argument("--output", type=Path, required=True, help="Output normalized transcript JSON")
    parser.add_argument(
        "--quran-corpus",
        type=Path,
        default=Path("data/quran/quran_arabic.json"),
        help="Quran Arabic corpus JSON path",
    )
    parser.add_argument("--min-score", type=float, default=94.0, help="Minimum fuzzy score to replace a token")
    parser.add_argument("--max-edit-distance", type=int, default=1, help="Max edit distance for token replacement")
    parser.add_argument(
        "--min-quran-ratio-for-fuzzy",
        type=float,
        default=0.45,
        help="Only run fuzzy token replacement when this portion of segment tokens already exists in Quran vocab",
    )
    parser.add_argument(
        "--replace-text",
        action="store_true",
        help="Replace segment text with normalized text (default: keep original and add text_quran_norm)",
    )
    parser.add_argument(
        "--replace-words",
        action="store_true",
        help="Replace each word text with normalized form (default: keep original and add text_quran_norm)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    segments = payload.get("segments", [])
    if not isinstance(segments, list):
        raise SystemExit(f"Invalid transcript: missing segments in {args.input}")

    vocab, by_first_len, by_len = build_quran_vocab(args.quran_corpus)

    total_segments = 0
    changed_segments = 0
    total_tokens = 0
    changed_tokens = 0
    phrase_replacements = 0
    sample_corrections: list[dict[str, Any]] = []

    output_segments: list[dict[str, Any]] = []
    for segment_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            continue
        total_segments += 1
        raw_text = str(segment.get("text", "") or "")
        norm = normalize_segment_text(
            text=raw_text,
            vocab=vocab,
            by_first_len=by_first_len,
            by_len=by_len,
            min_score=args.min_score,
            max_edit_distance=args.max_edit_distance,
            min_quran_ratio_for_fuzzy=args.min_quran_ratio_for_fuzzy,
        )
        total_tokens += norm.total_tokens
        changed_tokens += norm.changed_tokens
        phrase_replacements += norm.phrase_hits
        if norm.changed_tokens > 0 or norm.phrase_hits > 0:
            changed_segments += 1
            if len(sample_corrections) < 80:
                sample_corrections.append(
                    {
                        "segment_index": segment_index,
                        "start": segment.get("start"),
                        "start_global": segment.get("start_global", segment.get("start")),
                        "raw_text": raw_text,
                        "normalized_text": norm.text,
                        "changes": [
                            {
                                "from": change.from_token,
                                "to": change.to_token,
                                "score": change.score,
                                "edit_distance": change.edit_distance,
                            }
                            for change in norm.corrections[:10]
                        ],
                    }
                )

        out_segment = dict(segment)
        out_segment["text_raw"] = raw_text
        out_segment["text_quran_norm"] = norm.text
        if args.replace_text:
            out_segment["text"] = norm.text

        words = out_segment.get("words")
        if isinstance(words, list):
            new_words: list[dict[str, Any]] = []
            for word in words:
                if not isinstance(word, dict):
                    continue
                raw_word = str(word.get("text", "") or "")
                normalized_word = normalize_arabic(raw_word)
                replacement, score, edit_distance = nearest_quran_token(
                    token=normalized_word,
                    vocab=vocab,
                    by_first_len=by_first_len,
                    by_len=by_len,
                    min_score=args.min_score,
                    max_edit_distance=args.max_edit_distance,
                )
                out_word = dict(word)
                out_word["text_raw"] = raw_word
                out_word["text_quran_norm"] = replacement if replacement else normalized_word
                if replacement and replacement != normalized_word:
                    out_word["quran_vocab_fix_score"] = round(score, 2)
                    out_word["quran_vocab_fix_edit_distance"] = edit_distance
                if args.replace_words:
                    out_word["text"] = out_word["text_quran_norm"]
                new_words.append(out_word)
            out_segment["words"] = new_words

        output_segments.append(out_segment)

    output_payload = dict(payload)
    output_payload["segments"] = output_segments
    output_payload["normalization_meta"] = {
        "source_transcript": str(args.input),
        "quran_corpus": str(args.quran_corpus),
        "replace_text": bool(args.replace_text),
        "replace_words": bool(args.replace_words),
        "min_score": args.min_score,
        "max_edit_distance": args.max_edit_distance,
        "min_quran_ratio_for_fuzzy": args.min_quran_ratio_for_fuzzy,
        "segments_total": total_segments,
        "segments_changed": changed_segments,
        "tokens_total": total_tokens,
        "tokens_changed": changed_tokens,
        "phrase_replacements": phrase_replacements,
        "sample_corrections": sample_corrections,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {args.output}")
    print(f"Segments changed: {changed_segments}/{total_segments}")
    print(f"Tokens changed: {changed_tokens}/{total_tokens}")
    print(f"Phrase replacements: {phrase_replacements}")


if __name__ == "__main__":
    main()
