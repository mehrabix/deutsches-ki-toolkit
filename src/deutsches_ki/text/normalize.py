"""Normalisierung deutscher Texte.

Grundsatz: Der Originaltext bleibt erhalten. Der Modus ``display`` räumt nur
typografisch auf, der Modus ``search`` erzeugt zusätzlich eine Suchform, in der
Umlaute und ß aufgelöst, Groß-/Kleinschreibung vereinheitlicht und Satzzeichen
entfernt sind. Die Anzeigeform wird dabei nie überschrieben.
"""

from __future__ import annotations

import re
from collections.abc import Collection
from typing import Literal

from deutsches_ki.text.dictionary import is_known_word

__all__ = [
    "NormalizeMode",
    "normalize_case",
    "normalize_dashes",
    "normalize_ergaenzung",
    "normalize_for_search",
    "normalize_german",
    "normalize_punctuation",
    "normalize_quotes",
    "normalize_ss",
    "normalize_umlauts",
    "normalize_unicode",
    "normalize_whitespace",
]

NormalizeMode = Literal["display", "search"]

_UNICODE_MAP = {
    "\u00a0": " ",  # geschütztes Leerzeichen
    "\u202f": " ",  # schmales geschütztes Leerzeichen
    "\u2009": " ",  # dünnes Leerzeichen
    "\u200a": " ",
    "\u200b": "",  # Nullbreite
    "\u00ad": "",  # weiches Trennzeichen
    "\ufeff": "",  # Byte Order Mark
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\u0132": "IJ",
    "\u0133": "ij",
}

_DASH_MAP = str.maketrans(
    {
        "\u2014": "\u2013",  # Em Dash -> Gedankenstrich
        "\u2015": "\u2013",
        "\u2212": "-",  # Minuszeichen
        "\u2010": "-",  # Bindestrich-Varianten
        "\u2011": "-",
        "\u2012": "-",
    }
)

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

_DOUBLE_QUOTES = frozenset({"„", "“", "”", '"', "«", "»", "‟", "″"})

_ERGAENZUNG = re.compile(r"\b([A-ZÄÖÜ][\wÄÖÜäöüß]{2,})-\s+(und|oder|bzw\.?)\s+(\w[\wÄÖÜäöüß-]*)")

_NON_WORD = re.compile(r"[^\w\s]", flags=re.UNICODE)


def normalize_unicode(text: str) -> str:
    """Vereinheitlicht Leerzeichen, Ligaturen und Zeilenenden."""
    result = text.replace("\r\n", "\n").replace("\r", "\n")
    for source, target in _UNICODE_MAP.items():
        result = result.replace(source, target)
    return result


def normalize_whitespace(text: str) -> str:
    """Räumt Leerzeichen und übermäßige Leerzeilen auf."""
    result = re.sub(r"[ \t]+", " ", text)
    result = re.sub(r" *\n *", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def normalize_quotes(text: str) -> str:
    """Setzt doppelte Anführungszeichen auf deutsche Form („…“)."""
    out: list[str] = []
    opening = True
    for char in text:
        if char in _DOUBLE_QUOTES:
            out.append("„" if opening else "“")
            opening = not opening
        else:
            out.append(char)
    return "".join(out)


def normalize_dashes(text: str) -> str:
    """Vereinheitlicht Gedankenstriche, Minuszeichen und Bindestrich-Varianten."""
    return text.translate(_DASH_MAP)


def _shared_suffix(stem: str, word: str, dictionary: Collection[str] | None) -> str | None:
    known = (lambda value: value in dictionary) if dictionary is not None else is_known_word
    lowered_stem = stem.lower()
    for length in range(len(word) - 2, 2, -1):
        suffix = word[-length:]
        if known(lowered_stem + suffix.lower()):
            return suffix
    return None


def normalize_ergaenzung(text: str, *, dictionary: Collection[str] | None = None) -> str:
    """Löst Ergänzungsstriche auf: „Haupt- und Nebensatz“ -> „Hauptsatz und Nebensatz“.

    Ob der Ergänzungsstrich aufgelöst werden kann, hängt davon ab, ob das
    ergänzte Wort in der Wortliste steht. Ist es unbekannt, bleibt nur ein
    Leerzeichen: „Haupt und Nebensatz“. Die Suche funktioniert in beiden Fällen.
    """

    def replace(match: re.Match[str]) -> str:
        stem, conjunction, word = match.group(1), match.group(2), match.group(3)
        suffix = _shared_suffix(stem, word, dictionary)
        joined = f"{stem}{suffix}" if suffix else stem
        return f"{joined} {conjunction} {word}"

    return _ERGAENZUNG.sub(replace, text)


def normalize_umlauts(text: str) -> str:
    """Löst Umlaute auf (nur für die Suchform gedacht)."""
    return text.translate(_UMLAUT_MAP)


def normalize_ss(text: str) -> str:
    """Wandelt ß in ss um (nur für die Suchform gedacht)."""
    return text.translate(_SS_MAP)


def normalize_case(text: str) -> str:
    """Vereinheitlicht die Groß-/Kleinschreibung (Kleinschreibung)."""
    return text.lower()


def normalize_punctuation(text: str) -> str:
    """Ersetzt Satzzeichen durch Leerzeichen."""
    return _NON_WORD.sub(" ", text)


def normalize_for_search(text: str) -> str:
    """Baut die Suchform: Umlaute und ß aufgelöst, klein, ohne Satzzeichen."""
    result = normalize_unicode(text)
    result = normalize_dashes(result)
    result = normalize_ergaenzung(result)
    result = normalize_ss(result)
    result = normalize_umlauts(result)
    result = normalize_punctuation(result)
    result = normalize_case(result)
    return normalize_whitespace(result)


def normalize_german(text: str, mode: NormalizeMode = "display") -> str:
    """Normalisiert deutschen Text je nach Verwendungszweck."""
    if mode == "search":
        return normalize_for_search(text)
    result = normalize_unicode(text)
    result = normalize_dashes(result)
    result = normalize_quotes(result)
    return normalize_whitespace(result)
