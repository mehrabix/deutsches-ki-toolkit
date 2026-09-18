"""Erkennung der Dokumentart anhand deutscher Merkmale.

Der Ansatz ist bewusst einfach: Eine Tabelle gewichteter deutscher Wendungen
und ein paar strukturelle Merkmale. Das reicht für die üblichen Fälle und lässt
sich im Gegensatz zu einem Modell erklären: Man sieht, welche Wendung den
Ausschlag gegeben hat.

Ein Sprachmodell kann später daneben treten. Die Schnittstelle bleibt dieselbe.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.classification.types import DocumentType

__all__ = ["ClassificationResult", "classify_document"]

# (Dokumentart, Wendung, Gewicht). Längere Wendungen wiegen mehr, weil sie
# weniger zufällig vorkommen.
_CUES: tuple[tuple[DocumentType, str, float], ...] = (
    # Rechnung
    (DocumentType.INVOICE, "rechnungsnummer", 3.0),
    (DocumentType.INVOICE, "rechnungsbetrag", 3.0),
    (DocumentType.INVOICE, "rechnungsdatum", 2.5),
    (DocumentType.INVOICE, "nettobetrag", 3.0),
    (DocumentType.INVOICE, "umsatzsteuer", 2.0),
    (DocumentType.INVOICE, "zahlbar innerhalb", 3.0),
    (DocumentType.INVOICE, "zahlbetrag", 2.0),
    (DocumentType.INVOICE, "rechnung", 1.0),
    # Vertrag
    (DocumentType.CONTRACT, "vertragsparteien", 3.0),
    (DocumentType.CONTRACT, "kündigungsfrist", 3.0),
    (DocumentType.CONTRACT, "vertragsgegenstand", 3.0),
    (DocumentType.CONTRACT, "auftragnehmer", 2.0),
    (DocumentType.CONTRACT, "auftraggeber", 2.0),
    (DocumentType.CONTRACT, "vereinbarung", 1.5),
    (DocumentType.CONTRACT, "rahmenvertrag", 3.0),
    (DocumentType.CONTRACT, "vertrag", 1.0),
    # Angebot
    (DocumentType.OFFER, "angebotsnummer", 3.0),
    (DocumentType.OFFER, "gültig bis", 2.5),
    (DocumentType.OFFER, "wir bieten", 2.5),
    (DocumentType.OFFER, "angebot", 1.5),
    # Bestellung
    (DocumentType.ORDER, "bestellnummer", 3.0),
    (DocumentType.ORDER, "auftragsbestätigung", 3.0),
    (DocumentType.ORDER, "liefertermin", 2.5),
    (DocumentType.ORDER, "bestellung", 1.5),
    # Rechtstext
    (DocumentType.LEGAL_DOCUMENT, "verordnung", 2.5),
    (DocumentType.LEGAL_DOCUMENT, "bundesgesetzblatt", 3.0),
    (DocumentType.LEGAL_DOCUMENT, "urteil", 2.5),
    (DocumentType.LEGAL_DOCUMENT, "gesetz", 1.5),
    (DocumentType.LEGAL_DOCUMENT, "vorschrift", 1.5),
    # Personal
    (DocumentType.HR_DOCUMENT, "arbeitsvertrag", 3.0),
    (DocumentType.HR_DOCUMENT, "urlaubsantrag", 3.0),
    (DocumentType.HR_DOCUMENT, "lohnabrechnung", 3.0),
    (DocumentType.HR_DOCUMENT, "personalnummer", 3.0),
    (DocumentType.HR_DOCUMENT, "elternzeit", 3.0),
    (DocumentType.HR_DOCUMENT, "gehalt", 1.5),
    (DocumentType.HR_DOCUMENT, "mitarbeiter", 1.0),
    # Handbuch
    (DocumentType.MANUAL, "handbuch", 2.5),
    (DocumentType.MANUAL, "anleitung", 2.5),
    (DocumentType.MANUAL, "montage", 2.0),
    (DocumentType.MANUAL, "wartungsintervall", 3.0),
    (DocumentType.MANUAL, "instandhaltung", 2.0),
    (DocumentType.MANUAL, "schritt", 1.0),
    # Spezifikation
    (DocumentType.SPECIFICATION, "spezifikation", 3.0),
    (DocumentType.SPECIFICATION, "anforderung", 2.0),
    (DocumentType.SPECIFICATION, "schnittstelle", 2.0),
    (DocumentType.SPECIFICATION, "norm", 1.5),
    # Technisches Dokument
    (DocumentType.TECHNICAL_DOCUMENT, "baugruppe", 3.0),
    (DocumentType.TECHNICAL_DOCUMENT, "schaltplan", 3.0),
    (DocumentType.TECHNICAL_DOCUMENT, "technische daten", 3.0),
    (DocumentType.TECHNICAL_DOCUMENT, "messung", 1.5),
    (DocumentType.TECHNICAL_DOCUMENT, "betrieb", 1.0),
    # Bericht
    (DocumentType.REPORT, "jahresbericht", 3.0),
    (DocumentType.REPORT, "zwischenbericht", 3.0),
    (DocumentType.REPORT, "zusammenfassung", 2.0),
    (DocumentType.REPORT, "bericht", 2.0),
    (DocumentType.REPORT, "ergebnis", 1.0),
    # E-Mail
    (DocumentType.EMAIL, "sehr geehrte", 3.0),
    (DocumentType.EMAIL, "mit freundlichen grüßen", 3.0),
    (DocumentType.EMAIL, "betreff:", 2.5),
    (DocumentType.EMAIL, "an:", 1.5),
    (DocumentType.EMAIL, "von:", 1.5),
)

# Strukturelle Merkmale, die unabhängig vom Wortlaut zählen.
_PARAGRAPH = re.compile(r"§\s*\d+")
_CLAUSE_NUMBER = re.compile(r"\(\d+\)")
_EMAIL_HEADER = re.compile(r"(?im)^\s*(?:von|an|betreff|cc|bcc)\s*:")

_MAX_PER_CUE = 3


class ClassificationResult(BaseModel):
    """Ergebnis der Dokumentklassifikation."""

    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)


def _score_cues(lowered: str) -> tuple[dict[DocumentType, float], dict[DocumentType, list[str]]]:
    scores: dict[DocumentType, float] = {}
    evidence: dict[DocumentType, list[str]] = {}
    for document_type, phrase, weight in _CUES:
        count = lowered.count(phrase)
        if count == 0:
            continue
        effective = min(count, _MAX_PER_CUE)
        scores[document_type] = scores.get(document_type, 0.0) + weight * effective
        evidence.setdefault(document_type, []).append(phrase)
    return scores, evidence


def _score_structure(text: str, scores: dict[DocumentType, float]) -> None:
    paragraphs = len(_PARAGRAPH.findall(text))
    if paragraphs >= 2:
        scores[DocumentType.LEGAL_DOCUMENT] = (
            scores.get(DocumentType.LEGAL_DOCUMENT, 0.0) + min(paragraphs, 5) * 1.5
        )
        scores[DocumentType.CONTRACT] = (
            scores.get(DocumentType.CONTRACT, 0.0) + min(paragraphs, 5) * 1.0
        )
    if len(_CLAUSE_NUMBER.findall(text)) >= 3:
        scores[DocumentType.CONTRACT] = scores.get(DocumentType.CONTRACT, 0.0) + 2.0
    if _EMAIL_HEADER.search(text):
        scores[DocumentType.EMAIL] = scores.get(DocumentType.EMAIL, 0.0) + 2.0


def classify_document(text: str, *, min_score: float = 3.0) -> ClassificationResult:
    """Erkennt die Dokumentart.

    Liegt keine Art über ``min_score``, ist das Ergebnis ``unknown``. Die
    Konfidenz ist der Anteil der besten Art an allen Punkten; sie sagt also, wie
    eindeutig die Entscheidung war, nicht wie sicher der Text gelesen wurde.
    """
    lowered = text.casefold()
    scores, evidence = _score_cues(lowered)
    _score_structure(text, scores)

    if not scores:
        return ClassificationResult(document_type=DocumentType.UNKNOWN, confidence=0.0)

    total = sum(scores.values())
    best_type, best_score = max(scores.items(), key=lambda item: (item[1], item[0].value))

    if best_score < min_score:
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            scores={kind.value: round(value, 2) for kind, value in scores.items()},
        )

    return ClassificationResult(
        document_type=best_type,
        confidence=round(best_score / total, 4) if total else 0.0,
        evidence=sorted(evidence.get(best_type, [])),
        scores={kind.value: round(value, 2) for kind, value in scores.items()},
    )
