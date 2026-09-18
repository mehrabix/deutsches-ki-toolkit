"""Satz- und Wortsegmentierung für deutsche Texte."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from deutsches_ki.core.models import Sentence
from deutsches_ki.text.abbreviations import ABBREVIATIONS

__all__ = ["split_sentences", "tokenize_words"]

_BOUNDARY = re.compile(r"([.!?…]+)(?=\s|$)")
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
_WORD = re.compile(r"[\wÄÖÜäöüß]+(?:[-\u2013][\wÄÖÜäöüß]+)*", flags=re.UNICODE)
_FIRST_WORD = re.compile(r"\w+", flags=re.UNICODE)

_MONTHS = frozenset(
    {
        "januar",
        "februar",
        "märz",
        "april",
        "mai",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "dezember",
    }
)

_OPENING_CHARS = "„“”\"'»«([{"


@lru_cache(maxsize=1)
def _abbreviation_pattern() -> re.Pattern[str]:
    """Baut ein Muster, das alle bekannten Abkürzungen erkennt.

    Mehrteilige Abkürzungen wie „z. B.“ dürfen beliebig viele Leerzeichen
    zwischen ihren Teilen haben.
    """
    parts = sorted(ABBREVIATIONS, key=len, reverse=True)
    alternatives = [re.escape(part).replace(r"\ ", r"\s+") for part in parts]
    return re.compile(r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)", re.IGNORECASE)


def _abbreviation_spans(text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in _abbreviation_pattern().finditer(text)]


def _inside_abbreviation(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _first_word(rest: str) -> str | None:
    match = _FIRST_WORD.match(rest)
    return match.group() if match else None


def _is_boundary(text: str, start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    punct = text[start:end]
    rest = text[end:].lstrip()

    if punct[-1] in "!?…":
        return True

    if _inside_abbreviation(start, spans):
        return False

    if start > 0 and text[start - 1].isdigit():
        if rest[:1].isdigit():
            return False
        word = _first_word(rest)
        if word is not None and word.lower() in _MONTHS:
            return False
        if word is not None and word[0].islower():
            return False

    if not rest:
        return True
    return rest[0].isupper() or rest[0] in _OPENING_CHARS


def _split_with_nlp(text: str, nlp: Any) -> list[Sentence]:
    document = nlp(text)
    return [
        Sentence(text=span.text, start=span.start_char, end=span.end_char)
        for span in document.sents
        if span.text.strip()
    ]


def _split_rule_based(text: str) -> list[Sentence]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    spans = _abbreviation_spans(normalized)

    boundaries: set[int] = set()
    for match in _BOUNDARY.finditer(normalized):
        if _is_boundary(normalized, match.start(), match.end(), spans):
            boundaries.add(match.end())
    for match in _PARAGRAPH_BREAK.finditer(normalized):
        boundaries.add(match.end())
    boundaries.add(len(normalized))

    sentences: list[Sentence] = []
    start = 0
    for end in sorted(boundaries):
        if end <= start:
            continue
        segment = normalized[start:end]
        stripped = segment.strip()
        if stripped:
            offset = start + (len(segment) - len(segment.lstrip()))
            sentences.append(Sentence(text=stripped, start=offset, end=offset + len(stripped)))
        start = end
    return sentences


def split_sentences(text: str, nlp: Any | None = None) -> list[Sentence]:
    """Zerlegt Text in Sätze.

    Ohne ``nlp`` arbeitet eine regelbasierte Zerlegung, die deutsche
    Abkürzungen, Ordinalzahlen, Dezimalzahlen und Paragraphenzeichen kennt.
    Wird ein spaCy-Modell übergeben, kommt dessen Segmentierung zum Einsatz.
    """
    if nlp is not None:
        return _split_with_nlp(text, nlp)
    return _split_rule_based(text)


def tokenize_words(text: str) -> list[Sentence]:
    """Zerlegt Text in Wörter und gibt deren Positionen zurück."""
    return [
        Sentence(text=match.group(), start=match.start(), end=match.end())
        for match in _WORD.finditer(text)
    ]
