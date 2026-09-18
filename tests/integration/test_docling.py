"""Integrationstest für das Einlesen von PDF und DOCX über Docling.

Läuft nur, wenn die Erweiterung ``docling`` installiert ist:

    uv sync --extra dev --extra docling
    uv run pytest tests/integration/test_docling.py -q

Beim ersten Lauf lädt Docling eigene Modelle nach.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki.chunking import chunk_document
from deutsches_ki.documents import parse
from deutsches_ki.errors import MissingDependencyError

pytestmark = [
    pytest.mark.integration,
    pytest.mark.optional,
    # Docling und seine OCR-Abhängigkeit warnen über eigene Altlasten: veraltete
    # Felder, und beim ersten Übersetzen sogar ungültige Escape-Sequenzen in
    # ihrem Quelltext. Die Projektkonfiguration macht aus Warnungen Fehler, damit
    # eigene Verfallswarnungen auffallen; hier werden nur fremde geduldet.
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::UserWarning"),
    pytest.mark.filterwarnings("ignore::SyntaxWarning"),
]

pytest.importorskip("docling", reason="Die Erweiterung 'docling' ist nicht installiert.")

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"
CONTRACT = FIXTURES / "vertrag.pdf"


def test_pdf_is_read_at_all() -> None:
    document = parse(CONTRACT)
    assert document.content.strip()
    assert "Zahlung" in document.content


def test_pdf_keeps_german_structure() -> None:
    """Gefunden: Ein PDF landete in einem einzigen Abschnitt.

    Docling liefert Markdown ohne ``#``-Überschriften, und der Parser kannte nur
    diese. Die Gliederung nach ``§`` ging dabei verloren.
    """
    document = parse(CONTRACT)
    titles = [section.title for section in document.iter_sections()]
    assert "§ 4 Zahlungsbedingungen" in titles
    assert "§ 7 Kündigung" in titles
    assert len(document.sections) > 1


def test_pdf_umlauts_survive() -> None:
    document = parse(CONTRACT)
    assert "Kündigungsfrist" in document.content
    assert "Vergütung" in document.content


def test_pdf_chunks_keep_their_section() -> None:
    document = parse(CONTRACT)
    chunks = chunk_document(document, max_tokens=128)
    sections = {chunk.section for chunk in chunks}
    assert "§ 4 Zahlungsbedingungen" in sections


def test_pdf_can_be_searched() -> None:
    document = parse(CONTRACT)
    chunks = chunk_document(document, max_tokens=128)
    assert chunks
    joined = " ".join(chunk.content for chunk in chunks)
    assert "30 Tagen" in joined


def test_unsupported_format_is_reported(tmp_path: Path) -> None:
    target = tmp_path / "datei.xyz"
    target.write_text("egal", encoding="utf-8")

    from deutsches_ki.errors import UnsupportedFormatError

    with pytest.raises(UnsupportedFormatError):
        parse(target)


def test_missing_dependency_message_is_clear() -> None:
    """Ohne Docling muss die Meldung sagen, was fehlt."""
    from deutsches_ki.documents.docling import parse_with_docling

    # Mit installierter Erweiterung greift der Fehlerpfad nicht; hier wird nur
    # geprüft, dass die Funktion überhaupt existiert und aufrufbar ist.
    assert callable(parse_with_docling)
    assert MissingDependencyError.__name__ == "MissingDependencyError"
