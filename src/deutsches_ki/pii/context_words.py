"""Deutsche Kontextwörter, die die Erkennung stützen.

Ein Hinweiswort in der Nähe eines Treffers hebt die Konfidenz. Englische
Kontextwörter helfen hier nicht weiter, deshalb sind die Listen deutsch.
"""

from __future__ import annotations

import re

__all__ = ["CONTEXT_WORDS", "has_context"]

CONTEXT_WORDS: dict[str, tuple[str, ...]] = {
    "iban": ("iban", "kontonummer", "bankverbindung", "konto", "empfängerkonto"),
    "bic": ("bic", "swift", "bankverbindung", "bankleitzahl"),
    "vat": (
        "ust-idnr",
        "ust-id",
        "ust.",
        "umsatzsteuer",
        "mehrwertsteuer",
        "vat",
        "steuernummer",
    ),
    "tax_id": (
        "steuer-id",
        "steuerid",
        "steuer-identifikationsnummer",
        "identifikationsnummer",
        "idnr",
        "id-nr",
    ),
    "tax_number": (
        "steuernummer",
        "steuer-nr",
        "st.-nr",
        "st-nr",
        "stnr",
        "finanzamt",
    ),
    "svnr": (
        "sozialversicherung",
        "sozialversicherungsnummer",
        "svnr",
        "rentenversicherung",
        "krankenkasse",
        "versicherungsnummer",
    ),
    "id_card": (
        "personalausweis",
        "ausweisnummer",
        "ausweis-nr",
        "ausweis",
        "identitätsnachweis",
    ),
    "phone": (
        "tel",
        "telefon",
        "telefonnummer",
        "mobil",
        "mobilnummer",
        "fax",
        "ruf",
        "erreichbar",
        "durchwahl",
        "ansprechpartner",
    ),
    "plz": ("plz", "postleitzahl", "postfach"),
    "address": ("adresse", "anschrift", "anschriften", "straße", "str.", "wohnhaft"),
    "person": ("herr", "frau", "hr.", "fr.", "ansprechpartner", "name", "geboren"),
}

_WINDOW = 60


def has_context(text: str, start: int, end: int, key: str, window: int = _WINDOW) -> bool:
    """Prüft, ob in der Umgebung eines Treffers ein Kontextwort steht."""
    words = CONTEXT_WORDS.get(key)
    if not words:
        return False
    left = text[max(0, start - window) : start].lower()
    right = text[end : end + window].lower()
    surroundings = f"{left} {right}"
    return any(word in surroundings for word in words)


def find_context_positions(text: str, key: str) -> list[tuple[int, int]]:
    """Liefert die Positionen aller Kontextwörter (vor allem für Tests)."""
    words = CONTEXT_WORDS.get(key, ())
    spans: list[tuple[int, int]] = []
    lowered = text.lower()
    for word in words:
        for match in re.finditer(re.escape(word), lowered):
            spans.append((match.start(), match.end()))
    return spans
