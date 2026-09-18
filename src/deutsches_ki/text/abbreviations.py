"""Deutsche Abkürzungen für die Satzsegmentierung."""

from __future__ import annotations

__all__ = [
    "ABBREVIATIONS",
    "SENTENCE_END_ABBREVIATIONS",
    "is_abbreviation",
]

# Abkürzungen, nach denen ein Punkt keinen Satz beendet.
ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "z. b.",
        "z.b.",
        "zb.",
        "d. h.",
        "d.h.",
        "u. a.",
        "u.a.",
        "u. ä.",
        "o. ä.",
        "o. g.",
        "s. o.",
        "s. u.",
        "vgl.",
        "bzw.",
        "usw.",
        "etc.",
        "evtl.",
        "ggf.",
        "inkl.",
        "exkl.",
        "zzgl.",
        "abzgl.",
        "ca.",
        "etwa",
        "dr.",
        "prof.",
        "prof. dr.",
        "dipl.-ing.",
        "dipl.",
        "ing.",
        "hr.",
        "hrn.",
        "fr.",
        "frn.",
        "gmbh",
        "mbh",
        "ag",
        "kg",
        "gbr",
        "e. v.",
        "e.v.",
        "e. k.",
        "ohg",
        "nr.",
        "nrn.",
        "art.",
        "abs.",
        "s.",
        "satz",
        "bd.",
        "kap.",
        "anl.",
        "anh.",
        "az.",
        "tel.",
        "fax",
        "mobil",
        "geb.",
        "gest.",
        "jh.",
        "jhd.",
        "mrd.",
        "mio.",
        "tsd.",
        "std.",
        "min.",
        "max.",
        "mwst.",
        "ust.",
        "ustg.",
        "ao.",
        "stgb.",
        "bgb.",
        "hgb.",
        "zpo.",
        "vob",
        "vob/b",
        "gmbhg",
        "gg",
        "ewr",
        "eu",
        "ezb",
        "bzgl.",
        "inkl",
        "zzgl",
    }
)

# Abkürzungen, die am Satzende stehen können und dann einen Satz beenden.
SENTENCE_END_ABBREVIATIONS: frozenset[str] = frozenset({"usw.", "etc.", "u. a.", "u.a."})


def is_abbreviation(token: str) -> bool:
    """Prüft, ob ein Token eine bekannte Abkürzung ist.

    Groß- und Kleinschreibung spielen keine Rolle.
    """
    return token.strip().lower() in ABBREVIATIONS
