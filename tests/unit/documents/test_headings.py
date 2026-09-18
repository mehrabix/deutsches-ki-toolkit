"""Tests für Überschriften, Spracherkennung und deutsche Metadaten."""

from __future__ import annotations

from pathlib import Path

from deutsches_ki.core.enums import Language
from deutsches_ki.documents import (
    build_sections,
    detect_language,
    extract_metadata,
    match_heading,
    parse,
)

# --- Überschriften ---------------------------------------------------------


def test_markdown_heading() -> None:
    assert match_heading("# Vertrag") == (1, "Vertrag")
    assert match_heading("### Unterpunkt") == (3, "Unterpunkt")


def test_paragraph_sign_is_a_heading() -> None:
    assert match_heading("§ 4 Zahlungsbedingungen") == (2, "§ 4 Zahlungsbedingungen")
    assert match_heading("§ 1") == (2, "§ 1")


def test_bulleted_paragraph_sign_is_a_heading() -> None:
    """Gefunden: Docling machte aus „§ 2 Vergütung“ einen Listenpunkt."""
    assert match_heading("- § 2 Vergütung") == (2, "§ 2 Vergütung")
    assert match_heading("* § 3 Haftung") == (2, "§ 3 Haftung")


def test_named_german_headings() -> None:
    assert match_heading("Anlage 2 Vergütung") == (2, "Anlage 2 Vergütung")
    assert match_heading("Abschnitt 3") == (2, "Abschnitt 3")
    assert match_heading("Kapitel IV Haftung") == (2, "Kapitel IV Haftung")


def test_numbered_subheading() -> None:
    assert match_heading("3.1 Zahlungsbedingungen") == (3, "3.1 Zahlungsbedingungen")


def test_plain_sentence_is_not_a_heading() -> None:
    assert match_heading("Die Zahlung ist innerhalb von 30 Tagen fällig.") is None
    assert match_heading("Das ist ein ganz normaler Satz") is None


def test_long_line_is_not_a_heading() -> None:
    assert match_heading("§ 4 " + "x" * 100) is None


def test_build_sections_from_german_headings() -> None:
    text = (
        "§ 1 Vertragsgegenstand\nDer Auftraggeber beauftragt die GmbH.\n\n"
        "§ 2 Vergütung\nNach Aufwand."
    )
    sections = build_sections(text)
    assert [section.title for section in sections] == ["§ 1 Vertragsgegenstand", "§ 2 Vergütung"]
    assert "beauftragt" in sections[0].content
    assert "Aufwand" in sections[1].content


def test_preamble_becomes_its_own_section() -> None:
    text = "Rahmenvertrag\n\n§ 1 Beginn\nText."
    sections = build_sections(text)
    assert sections[0].title is None
    assert "Rahmenvertrag" in sections[0].content


# --- Sprache ---------------------------------------------------------------


def test_detects_german() -> None:
    assert detect_language("Die Zahlung ist innerhalb von 30 Tagen fällig.") is Language.DE


def test_detects_english() -> None:
    text = "The payment is due within 30 days and the contract will be reviewed by the team."
    assert detect_language(text) is Language.EN


def test_detects_mixed_text() -> None:
    text = (
        "Die Zahlung ist fällig und der Vertrag wird geprüft. "
        "The payment is due and the contract will be reviewed by the team."
    )
    assert detect_language(text) is Language.MIXED


def test_empty_text_defaults_to_german() -> None:
    assert detect_language("") is Language.DE


# --- Metadaten -------------------------------------------------------------


def test_extracts_invoice_metadata() -> None:
    metadata = extract_metadata(
        "Rechnungsnummer: RE-2024-001\nRechnungsdatum: 03.02.2024\n"
        "Kundennummer: 4711\nUSt-IdNr.: DE123456789"
    )
    assert metadata["invoice_number"] == "RE-2024-001"
    assert metadata["customer_number"] == "4711"
    assert metadata["vat_id"] == "DE123456789"
    assert metadata["date"] == "03.02.2024"


def test_metadata_on_plain_text() -> None:
    assert extract_metadata("Ein Satz ohne Angaben.") == {}


def test_parse_fills_metadata_and_language(tmp_path: Path) -> None:
    file = tmp_path / "rechnung.txt"
    file.write_text("Rechnungsnummer: RE-1\nRechnungsdatum: 01.03.2024", encoding="utf-8")

    document = parse(file)
    assert document.metadata["invoice_number"] == "RE-1"
    assert document.language is Language.DE


def test_explicit_language_wins(tmp_path: Path) -> None:
    file = tmp_path / "text.txt"
    file.write_text("The payment is due and the contract will be reviewed.", encoding="utf-8")

    assert parse(file).language is Language.EN
    assert parse(file, language=Language.DE).language is Language.DE
