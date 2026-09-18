"""Such-Token: normalisierte Wörter, Komposita-Bestandteile und Wortstämme.

Damit finden sich „Versicherungsbeitrag“ und „Beitrag“ sowie „Ersatzteile“ und
„Ersatzteilen“. Das ist die unspektakulärste, aber wirksamste Verbesserung für
deutsche Unternehmenssuche.
"""

from __future__ import annotations

from deutsches_ki.text.compounds import analyze_compound
from deutsches_ki.text.normalize import normalize_for_search

__all__ = ["light_stem", "search_tokens"]

# Nur eine Endung wird entfernt. Ein vollständiger Stemmer wäre genauer, würde
# ohne Wörterbuch aber auch mehr kaputt machen; für die Suche reicht das hier.
_STEM_SUFFIXES = ("ungen", "ung", "ern", "em", "er", "en", "es", "e", "n", "s")
_MIN_STEM_LENGTH = 4


def light_stem(token: str) -> str | None:
    """Grober deutscher Wortstamm für die Suche.

    „Ersatzteilen“ wird zu „ersatzteil“, „Ersatzteile“ ebenfalls. Das
    Originalwort bleibt erhalten, der Stamm kommt zusätzlich dazu. Dadurch
    verbessert sich die Trefferquote, ohne dass genaue Treffer verloren gehen.
    """
    for suffix in _STEM_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= _MIN_STEM_LENGTH:
            return token[: -len(suffix)]
    return None


def search_tokens(text: str, *, expand_compounds: bool = True) -> list[str]:
    """Zerlegt Text in Such-Token, optional mit Bestandteilen und Stämmen."""
    tokens = normalize_for_search(text).split()
    if not expand_compounds:
        return tokens

    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        analysis = analyze_compound(token)
        if analysis.is_compound:
            expanded.extend(part.lower() for part in analysis.parts)

    # Stämme kommen zusätzlich dazu, damit Beugungsformen sich finden.
    for token in list(expanded):
        stem = light_stem(token)
        if stem is not None:
            expanded.append(stem)
    return expanded
