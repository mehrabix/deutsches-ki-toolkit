"""Tests für das strukturbasierte Chunking."""

from __future__ import annotations

import pytest

from deutsches_ki.chunking import chunk_document, chunk_text, estimate_tokens
from deutsches_ki.core.models import Document, Section
from deutsches_ki.documents.markdown import parse_markdown

CONTRACT = """\
# Vertrag

## § 1 Vertragsgegenstand

Der Auftraggeber beauftragt die Beispiel GmbH mit der Lieferung.

## § 4 Zahlungsbedingungen

(1) Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.

(2) Bei verspäteter Zahlung fallen Verzugszinsen an.
"""


def test_short_paragraphs_are_packed_into_one_chunk() -> None:
    chunks = chunk_text("Erster Absatz.\n\nZweiter Absatz.\n\nDritter Absatz.")
    assert len(chunks) == 1
    assert "Erster Absatz." in chunks[0].content
    assert "Dritter Absatz." in chunks[0].content


def test_paragraph_boundary_is_used_when_limit_forces() -> None:
    text = "Erster Absatz mit etwas mehr Text darin.\n\nZweiter Absatz mit etwas mehr Text darin."
    chunks = chunk_text(text, max_tokens=12, overlap=0)
    assert len(chunks) == 2
    assert chunks[0].content == "Erster Absatz mit etwas mehr Text darin."


def test_section_is_kept_whole_when_it_fits() -> None:
    document = parse_markdown(CONTRACT)
    chunks = chunk_document(document, max_tokens=512)

    zahlung = [chunk for chunk in chunks if chunk.section == "§ 4 Zahlungsbedingungen"]
    assert len(zahlung) == 1
    assert "(1)" in zahlung[0].content
    assert "(2)" in zahlung[0].content


def test_chunk_metadata_carries_section_path() -> None:
    document = parse_markdown(CONTRACT)
    chunks = chunk_document(document)

    zahlung = next(chunk for chunk in chunks if chunk.section == "§ 4 Zahlungsbedingungen")
    assert zahlung.metadata["section_path"] == ["Vertrag", "§ 4 Zahlungsbedingungen"]
    assert zahlung.metadata["language"] == "de"


def test_document_type_is_recorded() -> None:
    chunks = chunk_text("Ein Absatz.", document_type="contract")
    assert chunks[0].metadata["document_type"] == "contract"


def test_max_tokens_is_respected() -> None:
    text = " ".join(f"Wort{i}" for i in range(200))
    chunks = chunk_text(text, max_tokens=40, overlap=0)
    assert len(chunks) > 1
    assert all(estimate_tokens(chunk.content) <= 45 for chunk in chunks)


def test_long_paragraph_splits_at_sentence_boundary() -> None:
    sentence = "Die Zahlungsfrist beträgt genau dreißig Tage nach Rechnungsstellung. "
    chunks = chunk_text(sentence * 20, max_tokens=60, overlap=0)
    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.content.rstrip().endswith(".")


def test_overlap_repeats_context() -> None:
    text = "\n\n".join(f"Absatz Nummer {index} mit etwas Text." for index in range(12))
    with_overlap = chunk_text(text, max_tokens=40, overlap=30)
    without_overlap = chunk_text(text, max_tokens=40, overlap=0)
    assert len(with_overlap) >= len(without_overlap)


def test_fixed_strategy_ignores_structure() -> None:
    document = parse_markdown(CONTRACT)
    chunks = chunk_document(document, strategy="fixed", max_tokens=30, overlap=0)
    assert all(chunk.section is None for chunk in chunks)


def test_document_without_sections_still_chunks() -> None:
    document = Document(content="Nur ein Satz.", sections=[])
    chunks = chunk_document(document)
    assert len(chunks) == 1
    assert chunks[0].content == "Nur ein Satz."


def test_section_without_content_is_skipped() -> None:
    document = Document(
        content="Inhalt",
        sections=[
            Section(title="Leer", level=1, content=""),
            Section(title="Voll", level=1, content="Etwas Inhalt."),
        ],
    )
    chunks = chunk_document(document)
    assert [chunk.section for chunk in chunks] == ["Voll"]


def test_invalid_max_tokens_raises() -> None:
    with pytest.raises(ValueError, match="max_tokens"):
        chunk_text("Text", max_tokens=0)


def test_negative_overlap_raises() -> None:
    with pytest.raises(ValueError, match="overlap"):
        chunk_text("Text", overlap=-1)


def test_estimate_tokens() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("vier") == 1
    assert estimate_tokens("x" * 40) == 10
