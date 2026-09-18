"""Tests für die Fassade GermanDocument."""

from __future__ import annotations

from pathlib import Path

from deutsches_ki import GermanDocument
from deutsches_ki.core.enums import EntityType

TEXT = (
    "Der Vertrag regelt die Zusammenarbeit.\n\n"
    "Die Zahlungsfrist beträgt 30 Tage nach Rechnungsstellung.\n\n"
    "Die Kündigungsfrist beträgt drei Monate zum Monatsende."
)

WITH_PII = "Bitte an DE89 3704 0044 0532 0130 00 überweisen."


def test_from_text_exposes_text_and_title() -> None:
    document = GermanDocument.from_text("Inhalt", title="Vertrag")
    assert document.text == "Inhalt"
    assert document.title == "Vertrag"


def test_from_file_reads_document(tmp_path: Path) -> None:
    file = tmp_path / "vertrag.txt"
    file.write_text(TEXT, encoding="utf-8")

    document = GermanDocument.from_file(file)
    assert "Zahlungsfrist" in document.text
    assert document.title == "vertrag"


def test_detect_pii_finds_iban() -> None:
    document = GermanDocument.from_text(WITH_PII)
    entities = document.detect_pii()
    assert [entity.type for entity in entities] == [EntityType.DE_IBAN]


def test_anonymize_rewrites_text() -> None:
    document = GermanDocument.from_text(WITH_PII)
    result = document.anonymize()
    assert result == "Bitte an [DE_IBAN] überweisen."
    assert document.text == result


def test_anonymize_pseudonymize_mode() -> None:
    document = GermanDocument.from_text(WITH_PII)
    result = document.anonymize(mode="mask")
    assert "DE89" in result
    assert "****" in result


def test_chunk_returns_chunks() -> None:
    document = GermanDocument.from_text(TEXT)
    chunks = document.chunk()
    assert chunks
    assert all(chunk.document_id == document.document.id for chunk in chunks)


def test_chunk_respects_settings() -> None:
    document = GermanDocument.from_text(TEXT, title="Vertrag")
    chunks = document.chunk(max_tokens=8, overlap=0)
    assert len(chunks) > 1


def test_search_returns_cited_answer() -> None:
    document = GermanDocument.from_text(TEXT, title="Vertrag")
    answer = document.search("Wie lange ist die Zahlungsfrist?")
    assert "30 Tage" in answer.answer
    assert answer.citations
    assert answer.citations[0].chunk_id


def test_search_without_match_returns_empty_answer() -> None:
    document = GermanDocument.from_text("Nur ein einzelner Satz über Wetter.")
    answer = document.search("Quantenphysik in der Raumfahrt")
    assert answer.answer in {"", "Nur ein einzelner Satz über Wetter."}


def test_anonymize_clears_cached_chunks() -> None:
    document = GermanDocument.from_text(WITH_PII)
    first = document.chunk()
    document.anonymize()
    second = document.chunk()
    assert first[0].content != second[0].content
