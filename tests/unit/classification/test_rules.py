"""Tests für die Dokumentklassifikation."""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki.classification import DocumentType, classify_document

FIXTURES = Path(__file__).resolve().parents[3] / "datasets" / "fixtures"

INVOICE = (
    "Rechnung\nRechnungsnummer: RE-2024-001\nNettobetrag: 1.250,00 EUR\n"
    "Umsatzsteuer: 19 Prozent\nZahlbar innerhalb von 30 Tagen."
)
CONTRACT = (
    "§ 1 Vertragsgegenstand\nDer Auftraggeber beauftragt den Auftragnehmer.\n"
    "§ 2 Vergütung\n§ 3 Zahlungsbedingungen\nDie Kündigungsfrist beträgt drei Monate."
)
MANUAL = (
    "Handbuch Instandhaltung\nDie Wartung erfolgt jährlich. "
    "Das Wartungsintervall beträgt sechs Monate."
)
EMAIL = (
    "Von: max@example.de\nAn: erika@example.de\nBetreff: Anfrage\n"
    "Sehr geehrte Damen und Herren,\nmit freundlichen Grüßen"
)
HR = (
    "Arbeitsvertrag\nPersonalnummer: 4711\n"
    "Der Urlaubsantrag ist zu stellen. Elternzeit nach Absprache."
)


def test_invoice() -> None:
    assert classify_document(INVOICE).document_type is DocumentType.INVOICE


def test_contract() -> None:
    assert classify_document(CONTRACT).document_type is DocumentType.CONTRACT


def test_manual() -> None:
    assert classify_document(MANUAL).document_type is DocumentType.MANUAL


def test_email() -> None:
    assert classify_document(EMAIL).document_type is DocumentType.EMAIL


def test_hr_document() -> None:
    assert classify_document(HR).document_type is DocumentType.HR_DOCUMENT


def test_unknown_for_plain_text() -> None:
    result = classify_document("Ein beliebiger Satz ohne Fachbegriffe.")
    assert result.document_type is DocumentType.UNKNOWN
    assert result.confidence == 0.0


def test_evidence_names_the_cues() -> None:
    result = classify_document(INVOICE)
    assert "rechnungsnummer" in result.evidence
    assert result.evidence == sorted(result.evidence)


def test_scores_are_reported() -> None:
    result = classify_document(CONTRACT)
    assert "contract" in result.scores
    assert all(value > 0 for value in result.scores.values())


def test_confidence_is_a_share() -> None:
    result = classify_document(INVOICE)
    assert 0.0 < result.confidence <= 1.0


def test_min_score_can_force_unknown() -> None:
    result = classify_document(INVOICE, min_score=1000.0)
    assert result.document_type is DocumentType.UNKNOWN


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("rechnung.txt", DocumentType.INVOICE),
        ("vertrag.md", DocumentType.CONTRACT),
        ("handbuch.md", DocumentType.MANUAL),
    ],
)
def test_fixtures_are_classified(filename: str, expected: DocumentType) -> None:
    text = (FIXTURES / filename).read_text(encoding="utf-8")
    assert classify_document(text).document_type is expected


def test_paragraph_structure_counts_toward_legal() -> None:
    text = "§ 1 Allgemeines\n§ 2 Geltungsbereich\n§ 3 Ausnahmen\n§ 4 Schlussbestimmungen"
    result = classify_document(text)
    assert result.scores.get("legal_document", 0.0) > 0
