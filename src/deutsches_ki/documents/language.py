"""Spracherkennung für deutsche und gemischte Dokumente.

Bewusst einfach gehalten: deutsche Funktionswörter, Umlaute und ß auf der einen
Seite, englische Funktionswörter auf der anderen. Für die Frage „Deutsch,
Englisch oder gemischt?“ reicht das, und es lässt sich nachvollziehen.
"""

from __future__ import annotations

import re

from deutsches_ki.core.enums import Language

__all__ = ["detect_language"]

_WORD = re.compile(r"[a-zäöüß]{2,}")

_GERMAN = frozenset(
    {
        "der",
        "die",
        "das",
        "den",
        "dem",
        "des",
        "und",
        "oder",
        "aber",
        "ist",
        "sind",
        "nicht",
        "mit",
        "von",
        "für",
        "auf",
        "werden",
        "wird",
        "sich",
        "auch",
        "bei",
        "aus",
        "nach",
        "über",
        "eine",
        "einer",
        "einem",
        "einen",
        "dass",
        "wenn",
        "kann",
        "muss",
        "soll",
        "zur",
        "zum",
        "im",
        "am",
    }
)

_ENGLISH = frozenset(
    {
        "the",
        "and",
        "or",
        "but",
        "is",
        "are",
        "not",
        "with",
        "of",
        "for",
        "on",
        "from",
        "by",
        "be",
        "as",
        "it",
        "this",
        "that",
        "these",
        "those",
        "will",
        "shall",
        "must",
        "can",
        "to",
        "in",
        "at",
        "we",
        "you",
        "they",
    }
)

_UMLAUTS = "äöüß"
_MIN_MARKERS = 3


def detect_language(text: str) -> Language:
    """Schätzt die Sprache eines Textes.

    Ohne verwertbare Anhaltspunkte gilt Deutsch als Vorgabe, weil das der Zweck
    des Toolkits ist. Als gemischt gilt ein Text erst, wenn beide Seiten
    genügend Anhaltspunkte haben.
    """
    lowered = text.casefold()
    words = _WORD.findall(lowered)
    if not words:
        return Language.DE

    german = sum(1 for word in words if word in _GERMAN)
    english = sum(1 for word in words if word in _ENGLISH)
    umlauts = sum(lowered.count(char) for char in _UMLAUTS)
    german_score = german + umlauts

    if english < _MIN_MARKERS:
        return Language.DE
    if german_score < _MIN_MARKERS:
        return Language.EN

    share = german_score / (german_score + english)
    if 0.35 <= share <= 0.65:
        return Language.MIXED
    return Language.DE if share > 0.5 else Language.EN
