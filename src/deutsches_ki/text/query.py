"""Erweiterung deutscher Suchanfragen.

Die Erweiterung entsteht aus mehreren Quellen und nicht allein aus einem
Sprachmodell: die Wörter der Anfrage, die Bestandteile von Komposita und ein
Fachglossar. Das Glossar kann mitgegeben werden; ansonsten gilt die gebündelte
Synonymliste.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from functools import lru_cache
from importlib import resources

import yaml

from deutsches_ki.text.compounds import analyze_compound
from deutsches_ki.text.dictionary import get_dictionary
from deutsches_ki.text.segment import tokenize_words

__all__ = ["default_glossary", "expand_query"]

Glossary = Mapping[str, Sequence[str]]


@lru_cache(maxsize=1)
def default_glossary() -> dict[str, tuple[str, ...]]:
    """Lädt die gebündelte Synonymliste (einmalig, danach zwischengespeichert)."""
    path = resources.files("deutsches_ki.text").joinpath("data", "de_synonyms.yaml")
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):  # pragma: no cover
        return {}
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):  # pragma: no cover - defensiv
        return {}
    glossary: dict[str, tuple[str, ...]] = {}
    for key, values in data.items():
        if isinstance(values, list):
            glossary[str(key).lower()] = tuple(str(value) for value in values)
    return glossary


def expand_query(
    query: str,
    *,
    glossary: Glossary | None = None,
    dictionary: Collection[str] | None = None,
    max_terms: int = 12,
) -> list[str]:
    """Erweitert eine Suchanfrage um Komposita-Bestandteile und Synonyme.

    Die Reihenfolge zählt: zuerst die ursprünglichen Wörter, dann die
    Bestandteile zusammengesetzter Wörter, dann die Synonyme. Doppelte Einträge
    werden entfernt.
    """
    merged = dict(default_glossary())
    if glossary is not None:
        merged.update({key.lower(): tuple(values) for key, values in glossary.items()})

    lexicon = dictionary if dictionary is not None else get_dictionary()
    terms: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        cleaned = value.strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            terms.append(cleaned)

    tokens = tokenize_words(query)
    for token in tokens:
        add(token.text)
    for token in tokens:
        for part in analyze_compound(token.text, dictionary=lexicon).parts:
            add(part)
    for token in tokens:
        for synonym in merged.get(token.text.lower(), ()):
            add(synonym)

    return terms[:max_terms]
