"""Ende-zu-Ende über die synthetischen Testdateien."""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki import GermanDocument
from deutsches_ki.chunking import chunk_document
from deutsches_ki.core.enums import EntityType
from deutsches_ki.documents import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.retrieval import InMemoryRetriever

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"


def _fixture_files() -> list[Path]:
    return sorted(
        path
        for path in FIXTURES.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}
    )


def test_fixtures_exist() -> None:
    assert _fixture_files(), "Es sollten synthetische Testdateien vorhanden sein."


def test_all_fixtures_parse_and_chunk() -> None:
    for file in _fixture_files():
        document = parse(file)
        chunks = chunk_document(document)
        assert chunks, f"Keine Chunks für {file.name}"
        assert all(chunk.content.strip() for chunk in chunks)


def test_invoice_pii_is_found_and_removed() -> None:
    document = GermanDocument.from_file(FIXTURES / "rechnung.txt")
    found = {entity.type for entity in document.detect_pii()}

    expected = {
        EntityType.DE_IBAN,
        EntityType.DE_BIC,
        EntityType.EMAIL,
        EntityType.PHONE,
        EntityType.DE_INVOICE_NUMBER,
        EntityType.DE_CUSTOMER_NUMBER,
        EntityType.DE_ADDRESS,
    }
    assert expected <= found

    anonymized = document.anonymize(mode="redact")
    assert "DE89" not in anonymized
    assert "max.mustermann@example.de" not in anonymized


def test_contract_question_is_answered_with_source() -> None:
    document = GermanDocument.from_file(FIXTURES / "vertrag.md")
    answer = document.search("Wie lange ist die Zahlungsfrist?")

    assert "30 Tagen" in answer.answer
    assert answer.citations
    assert answer.citations[0].section == "§ 4 Zahlungsbedingungen"


def test_search_spans_several_documents() -> None:
    chunks = []
    for file in _fixture_files():
        chunks.extend(chunk_document(parse(file), max_tokens=64))

    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(chunks)

    results = retriever.search("Arbeitsunfähigkeitsbescheinigung")
    assert results
    assert "Bescheinigung" in results[0].chunk.content


def test_compound_question_finds_invoice_section() -> None:
    chunks = []
    for file in _fixture_files():
        chunks.extend(chunk_document(parse(file), max_tokens=64))

    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(chunks)

    results = retriever.search("Versicherungsbeitrag")
    assert results
