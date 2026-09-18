"""Such-Token: normalisierte Wörter plus Bestandteile von Komposita.

Damit finden sich „Versicherungsbeitrag“ und „Beitrag“ in der lexikalischen
Suche. Das ist die unspektakulärste, aber wirksamste Verbesserung für deutsche
Unternehmenssuche.
"""

from __future__ import annotations

from deutsches_ki.text.compounds import analyze_compound
from deutsches_ki.text.normalize import normalize_for_search

__all__ = ["search_tokens"]


def search_tokens(text: str, *, expand_compounds: bool = True) -> list[str]:
    """Zerlegt Text in Such-Token, optional mit Komposita-Bestandteilen."""
    tokens = normalize_for_search(text).split()
    if not expand_compounds:
        return tokens

    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        analysis = analyze_compound(token)
        if analysis.is_compound:
            expanded.extend(part.lower() for part in analysis.parts)
    return expanded
