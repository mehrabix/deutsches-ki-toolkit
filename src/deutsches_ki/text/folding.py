"""Falten deutscher Sonderzeichen für Vergleiche und Suche.

Falten heißt: Umlaute auflösen und ß zu ss machen. Damit passen gefaltete
Suchformen zu einer Wortliste, die in korrekter Schreibweise vorliegt.
"""

from __future__ import annotations

__all__ = ["fold", "fold_sharp_s", "fold_umlauts"]

_UMLAUT_MAP = str.maketrans(
    {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
    }
)

_SS_MAP = str.maketrans({"ß": "ss"})


def fold_umlauts(text: str) -> str:
    """Löst Umlaute auf (ä zu ae, ö zu oe, ü zu ue)."""
    return text.translate(_UMLAUT_MAP)


def fold_sharp_s(text: str) -> str:
    """Wandelt ß in ss um."""
    return text.translate(_SS_MAP)


def fold(text: str) -> str:
    """Faltet Umlaute und ß und schreibt klein.

    Das ist die Vergleichsform für Wortlisten und Komposita-Zerlegung.
    """
    return fold_umlauts(fold_sharp_s(text)).lower()
