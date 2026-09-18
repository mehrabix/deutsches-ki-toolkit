"""Gebündelte deutsche Wortliste."""

from __future__ import annotations

from functools import lru_cache
from importlib import resources

__all__ = ["get_dictionary", "is_known_word"]


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


def is_known_word(word: str) -> bool:
    """Prüft, ob ein Wort in der gebündelten Liste steht."""
    return word.strip().lower() in get_dictionary()
