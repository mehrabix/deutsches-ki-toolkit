"""Zerlegung deutscher Komposita.

Deutsche Komposita verstecken Bedeutung in einem Token. „Versicherungsbeitrag“
und „Beitrag zur Versicherung“ meinen dasselbe, treffen sich in der Suche aber
nur, wenn die Bestandteile sichtbar gemacht werden. Die Zerlegung arbeitet
heuristisch über eine Wortliste und behandelt die üblichen Fugenelemente
(``s``, ``n``, ``en``, ``er``, ``e`` …).
"""

from __future__ import annotations

import re
from collections.abc import Collection

from pydantic import BaseModel, ConfigDict

from deutsches_ki.text.dictionary import get_dictionary

__all__ = ["CompoundAnalysis", "analyze_compound", "decompound_for_search"]

_MIN_PART = 3
_MAX_PARTS = 5
_LINKERS = ("", "s", "es", "ns", "n", "en", "er", "e")
_WORD = re.compile(r"[\wÄÖÜäöüß]+", flags=re.UNICODE)


class CompoundAnalysis(BaseModel):
    """Ergebnis der Komposita-Zerlegung."""

    model_config = ConfigDict(frozen=True)

    word: str
    parts: list[str]
    strategy: str
    score: float

    @property
    def is_compound(self) -> bool:
        """Wurde mehr als ein Bestandteil gefunden?"""
        return len(self.parts) > 1


def _known(word: str, dictionary: Collection[str]) -> bool:
    return word.lower() in dictionary


def _decompose(
    word: str,
    dictionary: Collection[str],
    depth: int,
) -> list[str] | None:
    if depth <= 1 or len(word) < 2 * _MIN_PART:
        return [word] if _known(word, dictionary) else None

    for index in range(_MIN_PART, len(word) - _MIN_PART + 1):
        head = word[:index]
        if not _known(head, dictionary):
            continue
        for linker in _LINKERS:
            tail_start = index + len(linker)
            if tail_start > len(word) - _MIN_PART:
                continue
            if linker and word[index:tail_start].lower() != linker:
                continue
            tail = _decompose(word[tail_start:], dictionary, depth - 1)
            if tail is not None:
                return [head, *tail]

    return [word] if _known(word, dictionary) else None


def analyze_compound(
    word: str,
    *,
    dictionary: Collection[str] | None = None,
) -> CompoundAnalysis:
    """Zerlegt ein Wort in seine Bestandteile.

    Ist das Wort kein zusammengesetztes Wort oder nicht zerlegbar, enthält
    ``parts`` nur das Wort selbst und ``is_compound`` ist ``False``.
    """
    lexicon = dictionary if dictionary is not None else get_dictionary()
    stripped = word.strip()
    if not stripped or not _WORD.fullmatch(stripped):
        return CompoundAnalysis(word=word, parts=[word], strategy="none", score=0.0)

    parts = _decompose(stripped, lexicon, _MAX_PARTS)
    if parts is None or len(parts) < 2:
        return CompoundAnalysis(word=word, parts=[stripped], strategy="none", score=0.0)

    return CompoundAnalysis(word=word, parts=parts, strategy="dictionary", score=1.0)


def decompound_for_search(
    text: str,
    *,
    dictionary: Collection[str] | None = None,
) -> str:
    """Ersetzt Komposita durch ihre Bestandteile, damit die Suche sie findet."""
    output: list[str] = []
    position = 0
    for match in _WORD.finditer(text):
        if match.start() > position:
            output.extend(text[position : match.start()].split())
        analysis = analyze_compound(match.group(), dictionary=dictionary)
        output.extend(analysis.parts)
        position = match.end()
    if position < len(text):
        output.extend(text[position:].split())
    return " ".join(output)
