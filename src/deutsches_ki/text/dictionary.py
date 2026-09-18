"""Gebündelte deutsche Wortliste."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

from deutsches_ki.text.folding import fold

__all__ = ["get_dictionary", "get_folded_dictionary", "is_known_word"]


@lru_cache(maxsize=1)
def get_dictionary() -> frozenset[str]:
    """Lädt die gebündelte Wortliste (einmalig, danach zwischengespeichert)."""
    path = resources.files("deutsches_ki.text").joinpath("data", "de_words.txt")
    try:
        raw = path.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):  # pragma: no cover
        return frozenset()
    words = {
        line.strip().lower()
        for line in raw.splitlines()
        if line.strip() and not line.startswith("#")
    }
    return frozenset(words)


@lru_cache(maxsize=1)
def get_folded_dictionary() -> frozenset[str]:
    """Die Wortliste in Vergleichsform (Umlaute und ß aufgelöst)."""
    return frozenset(fold(word) for word in get_dictionary())


def is_known_word(word: str) -> bool:
    """Prüft, ob ein Wort in der gebündelten Liste steht.

    Der Vergleich ist unabhängig von Umlauten und ß: „Kündigung“,
    „Kuendigung“ und „Kundigung“ gelten als dasselbe Wort.
    """
    return fold(word) in get_folded_dictionary()
