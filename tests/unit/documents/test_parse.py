"""Tests für das Einlesen von Dokumenten."""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki.core.models import Document
from deutsches_ki.documents import parse
from deutsches_ki.errors import ParseError, UnsupportedFormatError

CONTRACT = """\
Vertrag

Die Zahlungsfrist beträgt 30 Tage.
Zahlungen sind an die Beispiel GmbH zu leisten.

Die Kündigungsfrist beträgt drei Monate.
"""

MANUAL = """\
# Handbuch

Einleitungstext.

## Zahlungsbedingungen

Die Zahlung ist innerhalb von 30 Tagen fällig.

## Kündigung

Die Kündigungsfrist beträgt drei Monate.
"""


def test_parse_plaintext_sections(tmp_path: Path) -> None:
    file = tmp_path / "vertrag.txt"
    file.write_text(CONTRACT, encoding="utf-8")

    document = parse(file)

    assert document.source == str(file)
    assert document.title == "vertrag"
    assert len(document.sections) == 1
    content = document.sections[0].content
    assert "Zahlungsfrist" in content
    assert "Kündigungsfrist" in content


def test_parse_markdown_builds_tree(tmp_path: Path) -> None:
    file = tmp_path / "handbuch.md"
    file.write_text(MANUAL, encoding="utf-8")

    document = parse(file)

    assert document.title == "Handbuch"
    titles = [section.title for section in document.iter_sections()]
    assert titles == ["Handbuch", "Zahlungsbedingungen", "Kündigung"]
    zahlung = document.sections[0].children[0]
    assert "30 Tagen" in zahlung.content


def test_document_from_file_delegates(tmp_path: Path) -> None:
    file = tmp_path / "vertrag.txt"
    file.write_text(CONTRACT, encoding="utf-8")

    document = Document.from_file(file)
    assert isinstance(document, Document)
    assert "Zahlungsfrist" in document.content


def test_parse_missing_file() -> None:
    with pytest.raises(ParseError):
        parse("gibt-es-nicht.txt")


def test_parse_unsupported_suffix(tmp_path: Path) -> None:
    file = tmp_path / "daten.xyz"
    file.write_text("egal", encoding="utf-8")
    with pytest.raises(UnsupportedFormatError):
        parse(file)


def test_parse_cp1252_fallback(tmp_path: Path) -> None:
    file = tmp_path / "alt.txt"
    file.write_bytes("Straße mit Umlaut: äöü".encode("cp1252"))

    document = parse(file)
    assert "Straße" in document.content
