"""Satz- und Wortsegmentierung für deutsche Texte."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from deutsches_ki.core.models import Sentence
from deutsches_ki.text.abbreviations import ABBREVIATIONS, SENTENCE_END_ABBREVIATIONS

__all__ = ["split_sentences", "tokenize_words"]

_BOUNDARY = re.compile(r"([.!?…]+)(?=\s|$)")
_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
_WORD = re.compile(r"[\wÄÖÜäöüß]+(?:[-\u2013][\wÄÖÜäöüß]+)*", flags=re.UNICODE)
_FIRST_WORD = re.compile(r"\w+", flags=re.UNICODE)

# Datum mit Leerzeichen: „am 30. 09. 2024“. Der Punkt zwischen den Zahlen
# trennt keinen Satz.
_SPACED_DATE = re.compile(r"^\d{1,2}\s*\.\s*\d{1,2}")

_MONTHS = frozenset(
    {
        "januar",
        "februar",
        "märz",
        "april",
        "mai",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "dezember",
    }
)

# Abkürzungen, die eine Fundstelle einleiten. Nach ihnen steht oft eine Nummer,
# mit der der Satz endet: „Siehe Rn. 45. Die Norm ist einschlägig.“
_REFERENCE_ABBREVIATIONS = frozenset(
    {
        "rn.",
        "rz.",
        "randnr.",
        "nr.",
        "nrn.",
        "no.",
        "nos.",
        "abs.",
        "s.",
        "ziff.",
        "anm.",
        "az.",
        "aktz.",
        "art.",
        "artt.",
        "bd.",
        "bde.",
        "kap.",
        "bl.",
        "lit.",
        "buchst.",
        "halbs.",
        "var.",
        "tab.",
        "anl.",
        "anh.",
        "fig.",
        "pos.",
        "pkt.",
        "vgl.",
    }
)

# Wörter, mit denen ein deutscher Satz beginnen kann. Sie entscheiden in zwei
# Fällen, ob wirklich ein Satzende vorliegt: nach einer Abkürzung, die am
# Satzende stehen darf, und nach einer Fundstelle. Inhaltswörter fehlen hier
# bewusst, denn „… u. a. Personen“ führt die Aufzählung fort, während
# „… u. a. Ihr Vater“ einen neuen Satz beginnt.
_SENTENCE_OPENERS = frozenset(
    {
        # Artikel und Pronomen
        "der",
        "die",
        "das",
        "den",
        "dem",
        "des",
        "ein",
        "eine",
        "einen",
        "einem",
        "einer",
        "eines",
        "er",
        "sie",
        "es",
        "ihm",
        "ihn",
        "ihnen",
        "ihr",
        "wir",
        "uns",
        "unser",
        "ich",
        "mich",
        "mir",
        "mein",
        "du",
        "dich",
        "dir",
        "euch",
        "wer",
        "wen",
        "wem",
        "man",
        "jede",
        "jeder",
        "jedes",
        "diese",
        "dieser",
        "dieses",
        "diesen",
        "diesem",
        "jene",
        "jener",
        "jenes",
        "alle",
        "beide",
        "solche",
        "welche",
        "welcher",
        "welches",
        "dies",
        # Adverbien und Konnektoren
        "danach",
        "davor",
        "daher",
        "darum",
        "deshalb",
        "deswegen",
        "trotzdem",
        "außerdem",
        "zudem",
        "ferner",
        "weiter",
        "dann",
        "nun",
        "so",
        "auch",
        "nur",
        "nicht",
        "kein",
        "keine",
        "keinen",
        "keiner",
        "hier",
        "dort",
        "heute",
        "morgen",
        "gestern",
        "jetzt",
        "bald",
        "oft",
        "meist",
        "immer",
        "nie",
        "wieder",
        "jedoch",
        "doch",
        "aber",
        "oder",
        "und",
        "denn",
        "also",
        "somit",
        "folglich",
        "schließlich",
        "zuletzt",
        "zunächst",
        "zuerst",
        "anschließend",
        "ebenso",
        "ebenfalls",
        "hingegen",
        "dagegen",
        "vielmehr",
        "allerdings",
        "zwar",
        "jedenfalls",
        "mindestens",
        "höchstens",
        "etwa",
        "rund",
        "insgesamt",
        "damit",
        "dafür",
        "dazu",
        "dabei",
        "dadurch",
        "hiermit",
        "hierbei",
        "hierfür",
        "hiervon",
        "insofern",
        "soweit",
        # Präpositionen am Satzanfang
        "im",
        "in",
        "am",
        "an",
        "auf",
        "aus",
        "bei",
        "für",
        "mit",
        "nach",
        "von",
        "vor",
        "zu",
        "zum",
        "zur",
        "über",
        "unter",
        "zwischen",
        "ohne",
        "gegen",
        "bis",
        "seit",
        "während",
        "laut",
        "gemäß",
        "wegen",
        "trotz",
        "statt",
        "innerhalb",
        "außerhalb",
        "bezüglich",
        "hinsichtlich",
        # Häufige Satzanfänge mit Verb
        "ist",
        "sind",
        "war",
        "waren",
        "wird",
        "werden",
        "wurde",
        "wurden",
        "hat",
        "haben",
        "hatte",
        "hatten",
        "kann",
        "können",
        "konnte",
        "muss",
        "müssen",
        "soll",
        "sollen",
        "darf",
        "dürfen",
        "will",
        "wollen",
        "gibt",
        "geben",
        "gilt",
        "gelten",
        "bleibt",
        "bleiben",
        # Aufforderungen und Hinweise
        "bitte",
        "siehe",
        "beachten",
        "hinweis",
        "hinweise",
        "wichtig",
        "achtung",
        "vorsicht",
    }
)

_OPENING_CHARS = "„“”\"'»«([{"


@lru_cache(maxsize=1)
def _abbreviation_pattern() -> re.Pattern[str]:
    """Baut ein Muster, das alle bekannten Abkürzungen erkennt.

    Mehrteilige Abkürzungen wie „z. B.“ dürfen beliebig viele Leerzeichen
    zwischen ihren Teilen haben.
    """
    parts = sorted(ABBREVIATIONS, key=len, reverse=True)
    alternatives = [re.escape(part).replace(r"\ ", r"\s+") for part in parts]
    return re.compile(r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)", re.IGNORECASE)


def _abbreviation_spans(text: str) -> list[tuple[int, int, str]]:
    """Alle Abkürzungen als (Start, Ende, Text)."""
    return [
        (match.start(), match.end(), match.group().lower())
        for match in _abbreviation_pattern().finditer(text)
    ]


def _abbreviation_at(position: int, spans: list[tuple[int, int, str]]) -> str | None:
    """Die Abkürzung, in der die Position liegt."""
    for start, end, token in spans:
        if start <= position < end:
            return token
    return None


def _first_word(rest: str) -> str | None:
    match = _FIRST_WORD.match(rest)
    return match.group() if match else None


def _starts_sentence(rest: str) -> bool:
    """Beginnt hier ein neuer Satz?

    Nur ein großgeschriebenes Funktionswort zählt. Ein Inhaltswort setzt die
    vorherige Aufzählung fort statt einen Satz zu beginnen.
    """
    word = _first_word(rest)
    return bool(rest[:1].isupper() and word is not None and word.lower() in _SENTENCE_OPENERS)


def _digit_run_start(text: str, start: int) -> int:
    """Anfang der Ziffernfolge, die vor ``start`` endet."""
    position = start - 1
    while position >= 0 and text[position].isdigit():
        position -= 1
    return position + 1


def _preceded_by_reference(text: str, position: int) -> bool:
    """Steht vor der Position eine Fundstelle wie „Rn.“ oder „Nr.“?"""
    davor = text[:position].rstrip().lower()
    return any(davor.endswith(reference) for reference in _REFERENCE_ABBREVIATIONS)


def _is_standalone_ordinal(text: str, start: int) -> bool:
    """Steht vor dem Punkt eine freistehende Ordnungszahl?

    „1.“ und „21.“ sind Ordnungszahlen oder Aufzählungszeichen: „Im 1.
    Quartal“, „Die 2. Auflage“, „1. Der erste Punkt.“ Bei „1.000.“ oder
    „30.09.2024.“ gehört die Zahl dagegen zu einer längeren Zahl oder einem
    Datum, dort kann der Punkt ein Satzende sein.
    """
    beginn = _digit_run_start(text, start)
    ziffern = start - beginn
    if beginn > 0 and text[beginn - 1] in ".,/-":
        return False
    return ziffern <= 3


def _is_boundary(text: str, start: int, end: int, spans: list[tuple[int, int, str]]) -> bool:
    punct = text[start:end]
    rest = text[end:].lstrip()

    if punct[-1] in "!?…":
        return True

    abbreviation = _abbreviation_at(start, spans)
    if abbreviation is not None:
        # Duden D 4: Steht eine Abkürzung mit Punkt am Satzende, ist ihr Punkt
        # zugleich der Schlusspunkt des Satzes. Ob wirklich ein Satzende
        # vorliegt, entscheidet der Satzanfang. Auf „… Schiller u. a.“ folgt
        # mit „Ihr“ ein neuer Satz, „… u. a. Personen“ führt die Aufzählung fort.
        if abbreviation not in SENTENCE_END_ABBREVIATIONS:
            return False
        return _starts_sentence(rest)

    if start > 0 and text[start - 1].isdigit():
        if _SPACED_DATE.match(rest):
            return False
        word = _first_word(rest)
        if word is not None and word.lower() in _MONTHS:
            return False
        if word is not None and word[0].islower():
            return False
        if _is_standalone_ordinal(text, start):
            # Nach einer Fundstelle endet der Satz trotzdem, wenn ein
            # Funktionswort folgt: „Siehe Rn. 45. Die Norm ist einschlägig.“
            # Bei „Art. 3. Absatz 2 regelt“ geht es dagegen weiter.
            if _preceded_by_reference(text, _digit_run_start(text, start)):
                return _starts_sentence(rest)
            return False

    if not rest:
        return True
    # Auch eine Ziffer kann einen Satz beginnen: Aufzählungen wie „… Punkt.
    # 2. Der zweite Punkt.“ Der Punkt zwischen zwei Ziffern ohne Leerzeichen
    # erreicht diese Stelle gar nicht, weil _BOUNDARY ein Leerzeichen verlangt.
    return rest[0].isupper() or rest[0].isdigit() or rest[0] in _OPENING_CHARS


def _split_with_nlp(text: str, nlp: Any) -> list[Sentence]:
    document = nlp(text)
    return [
        Sentence(text=span.text, start=span.start_char, end=span.end_char)
        for span in document.sents
        if span.text.strip()
    ]


def _split_rule_based(text: str) -> list[Sentence]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    spans = _abbreviation_spans(normalized)

    boundaries: set[int] = set()
    for match in _BOUNDARY.finditer(normalized):
        if _is_boundary(normalized, match.start(), match.end(), spans):
            boundaries.add(match.end())
    for match in _PARAGRAPH_BREAK.finditer(normalized):
        boundaries.add(match.end())
    boundaries.add(len(normalized))

    sentences: list[Sentence] = []
    start = 0
    for end in sorted(boundaries):
        if end <= start:
            continue
        segment = normalized[start:end]
        stripped = segment.strip()
        if stripped:
            offset = start + (len(segment) - len(segment.lstrip()))
            sentences.append(Sentence(text=stripped, start=offset, end=offset + len(stripped)))
        start = end
    return sentences


def split_sentences(text: str, nlp: Any | None = None) -> list[Sentence]:
    """Zerlegt Text in Sätze.

    Ohne ``nlp`` arbeitet eine regelbasierte Zerlegung, die deutsche
    Abkürzungen, Ordinalzahlen, Dezimalzahlen und Paragraphenzeichen kennt.
    Wird ein spaCy-Modell übergeben, kommt dessen Segmentierung zum Einsatz.
    """
    if nlp is not None:
        return _split_with_nlp(text, nlp)
    return _split_rule_based(text)


def tokenize_words(text: str) -> list[Sentence]:
    """Zerlegt Text in Wörter und gibt deren Positionen zurück."""
    return [
        Sentence(text=match.group(), start=match.start(), end=match.end())
        for match in _WORD.finditer(text)
    ]
