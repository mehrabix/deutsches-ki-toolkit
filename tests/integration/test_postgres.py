"""Integrationstest gegen ein echtes PostgreSQL mit pgvector.

Läuft nur, wenn ``DEUTSCHES_KI_TEST_DSN`` gesetzt ist und die Erweiterung
installiert wurde:

    set DEUTSCHES_KI_TEST_DSN=postgresql://postgres:postgres@localhost:5432/postgres
    uv sync --extra dev --extra postgres
    uv run pytest tests/integration/test_postgres.py -q
"""

from __future__ import annotations

import os

import pytest

from deutsches_ki.core.models import Chunk, Document
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.storage import PgVectorStore

pytestmark = [pytest.mark.integration, pytest.mark.optional]

_DSN = os.environ.get("DEUTSCHES_KI_TEST_DSN")

pytest.importorskip("psycopg", reason="Die Erweiterung 'postgres' ist nicht installiert.")

pytestmark.append(pytest.mark.skipif(not _DSN, reason="DEUTSCHES_KI_TEST_DSN ist nicht gesetzt."))

CONTRACT = [
    Chunk(
        content="Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.",
        metadata={"section": "§ 4 Zahlungsbedingungen", "page": 12},
    ),
    Chunk(
        content="Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
        metadata={"section": "§ 7 Kündigung"},
    ),
    Chunk(
        content="Der Versicherungsbeitrag steigt jährlich um zwei Prozent.",
        metadata={"section": "§ 2 Vergütung"},
    ),
]


@pytest.fixture
def store() -> object:
    embedder = get_embedder("hashing")
    instance = PgVectorStore(_DSN, embedder=embedder)
    instance.create_schema()
    document = Document.from_text("Vertrag", title="Rahmenvertrag")
    instance.add_document(document)
    for chunk in CONTRACT:
        chunk.document_id = document.id
    instance.add_chunks(CONTRACT)
    yield instance
    instance.drop_schema()
    instance.close()


def test_finds_section_by_topic(store: PgVectorStore) -> None:
    results = store.search("Wie lange ist die Zahlungsfrist?", top_k=3)
    assert results
    assert results[0].chunk.metadata["section"] == "§ 4 Zahlungsbedingungen"


def test_finds_umlaut_compound_by_part(store: PgVectorStore) -> None:
    """Der Kern der deutschen Volltextsuche: „Kündigungsfrist“ über „Frist“."""
    results = store.search("Frist", top_k=3, vector=False)
    assert results
    assert "Kündigungsfrist" in results[0].chunk.content


def test_finds_compound_by_part(store: PgVectorStore) -> None:
    results = store.search("Beitrag", top_k=3, vector=False)
    assert results
    assert "Versicherungsbeitrag" in results[0].chunk.content


def test_page_metadata_survives_round_trip(store: PgVectorStore) -> None:
    results = store.search("Zahlungsfrist", top_k=1)
    assert results[0].chunk.metadata.get("page") == 12
