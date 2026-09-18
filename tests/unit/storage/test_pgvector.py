"""Tests für den PostgreSQL-Speicher.

Die Datenbank wird durch eine Attrappe ersetzt. Damit lässt sich prüfen, welche
Anweisungen abgesetzt werden und wie Zeilen zurückgelesen werden, ohne dass ein
laufender Server nötig ist.
"""

from __future__ import annotations

from typing import Any

import pytest

from deutsches_ki.core.enums import EntityType
from deutsches_ki.core.models import Chunk, Document, Entity
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.embeddings.hashing import HashingEmbedder
from deutsches_ki.storage import (
    SCHEMA_VERSION,
    PgVectorStore,
    create_schema_statements,
    drop_schema_statements,
    row_to_chunk,
    vector_to_literal,
)


class _Cursor:
    def __init__(self, connection: _FakeConnection) -> None:
        self._connection = connection
        self._rows: list[dict[str, Any]] = []

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        self._connection.executed.append((sql, params))
        self._rows = self._connection.rows_for(sql)

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def close(self) -> None:
        return None


class _FakeConnection:
    """Minimale Attrappe: zeichnet Anweisungen auf und liefert feste Zeilen."""

    def __init__(self, rows: dict[str, list[dict[str, Any]]] | None = None) -> None:
        self.executed: list[tuple[str, tuple[Any, ...] | None]] = []
        self.commits = 0
        self.closed = False
        self._rows = rows or {}

    def cursor(self) -> _Cursor:
        return _Cursor(self)

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        self.closed = True

    def rows_for(self, sql: str) -> list[dict[str, Any]]:
        for marker, rows in self._rows.items():
            if marker in sql:
                return rows
        return []


@pytest.fixture
def embedder() -> HashingEmbedder:
    return HashingEmbedder(dimension=32)


def test_vector_to_literal() -> None:
    assert vector_to_literal([1.0, 0.5, -0.25]) == "[1,0.5,-0.25]"


def test_create_schema_contains_dimension_and_indexes() -> None:
    statements = create_schema_statements(1024)
    joined = "\n".join(statements)
    assert "vector(1024)" in joined
    assert "USING gin (search_vector)" in joined
    assert "USING hnsw (embedding vector_cosine_ops)" in joined
    assert "CREATE EXTENSION IF NOT EXISTS vector" in joined
    assert SCHEMA_VERSION == 1


def test_create_schema_rejects_bad_dimension() -> None:
    with pytest.raises(ValueError, match="dimension"):
        create_schema_statements(0)


def test_drop_schema_drops_tables() -> None:
    statements = drop_schema_statements()
    assert any("DROP TABLE IF EXISTS entities" in statement for statement in statements)
    assert len(statements) == 3


def test_store_requires_dsn_or_connection() -> None:
    with pytest.raises(ValueError, match="DSN"):
        PgVectorStore()


def test_dimension_needs_embedder() -> None:
    store = PgVectorStore(connection=_FakeConnection())
    with pytest.raises(ValueError, match="Embedding"):
        _ = store.dimension


def test_create_schema_executes_and_commits(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection()
    store = PgVectorStore(connection=connection, embedder=embedder)

    store.create_schema()

    statements = [sql for sql, _ in connection.executed]
    assert any("chunks" in sql for sql in statements)
    assert any("vector(32)" in sql for sql in statements)
    assert connection.commits == 1


def test_add_document_writes_metadata(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection()
    store = PgVectorStore(connection=connection, embedder=embedder)

    store.add_document(Document.from_text("Inhalt", title="Vertrag"))

    sql, params = connection.executed[0]
    assert "INSERT INTO documents" in sql
    assert params is not None
    assert params[2] == "Vertrag"
    assert params[3] == "de"


def test_add_chunks_stores_folded_search_form(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection()
    store = PgVectorStore(connection=connection, embedder=embedder)
    chunk = Chunk(
        content="Die Kündigungsfrist beträgt drei Monate.",
        metadata={"section": "§ 7 Kündigung"},
    )

    store.add_chunks([chunk])

    sql, params = connection.executed[0]
    assert "INSERT INTO chunks" in sql
    assert params is not None
    content_search = params[4]
    # Umlaute und ß sind aufgelöst, Komposita sind zerlegt.
    assert "kuendigungsfrist" in content_search
    assert "frist" in content_search
    assert "Kündigungsfrist" not in content_search
    # Der Abschnittstitel steckt mit im Index.
    assert "kuendigung" in content_search
    # Der Originaltext bleibt unangetastet.
    assert params[3] == "Die Kündigungsfrist beträgt drei Monate."
    assert params[5] == "§ 7 Kündigung"


def test_add_chunks_requires_vectors_without_embedder() -> None:
    store = PgVectorStore(connection=_FakeConnection())
    with pytest.raises(ValueError, match="Vektoren"):
        store.add_chunks([Chunk(content="Text")])


def test_add_chunks_rejects_mismatched_vectors(embedder: HashingEmbedder) -> None:
    store = PgVectorStore(connection=_FakeConnection(), embedder=embedder)
    with pytest.raises(ValueError, match="gleich viele"):
        store.add_chunks([Chunk(content="a"), Chunk(content="b")], embeddings=[[0.1, 0.2]])


def test_add_chunks_accepts_given_vectors() -> None:
    connection = _FakeConnection()
    store = PgVectorStore(connection=connection)
    store.add_chunks([Chunk(content="Text")], embeddings=[[1.0, 0.0]])
    assert "INSERT INTO chunks" in connection.executed[0][0]


def test_add_entities_writes_values(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection()
    store = PgVectorStore(connection=connection, embedder=embedder)
    entity = Entity(type=EntityType.DE_IBAN, text="DE89 3704 0044 0532 0130 00", start=0, end=27)

    store.add_entities("chk-1", [entity])

    sql, params = connection.executed[0]
    assert "INSERT INTO entities" in sql
    assert params is not None
    assert params[0] == "chk-1"
    assert params[1] == "DE_IBAN"


def test_row_to_chunk_maps_columns() -> None:
    chunk = row_to_chunk(
        {
            "id": "chk-1",
            "document_id": "doc-1",
            "content": "Text",
            "section": "§ 4 Zahlungsbedingungen",
            "section_path": ["Vertrag", "§ 4 Zahlungsbedingungen"],
            "page": 12,
            "metadata": {"language": "de"},
        }
    )
    assert chunk.id == "chk-1"
    assert chunk.section == "§ 4 Zahlungsbedingungen"
    assert chunk.metadata["page"] == 12
    assert chunk.metadata["section_path"] == ["Vertrag", "§ 4 Zahlungsbedingungen"]
    assert chunk.metadata["language"] == "de"


def test_search_combines_both_branches(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection(
        rows={
            "ORDER BY embedding <=>": [{"id": "a"}, {"id": "b"}],
            "plainto_tsquery": [{"id": "b"}, {"id": "c"}],
            "WHERE id = ANY": [
                {
                    "id": "b",
                    "document_id": "doc",
                    "content": "Die Zahlung ist innerhalb von 30 Tagen fällig.",
                    "section": "§ 4 Zahlungsbedingungen",
                    "section_path": None,
                    "page": None,
                    "metadata": {},
                }
            ],
        }
    )
    store = PgVectorStore(connection=connection, embedder=embedder)

    results = store.search("Zahlungsfrist", top_k=1)

    assert len(results) == 1
    assert results[0].chunk.id == "b"
    # In beiden Zweigen gefunden, deshalb der beste Rang.
    assert results[0].vector_rank == 2
    assert results[0].lexical_rank == 1


def test_search_without_hits_returns_empty(embedder: HashingEmbedder) -> None:
    store = PgVectorStore(connection=_FakeConnection(), embedder=embedder)
    assert store.search("nichts") == []


def test_search_respects_top_k_zero(embedder: HashingEmbedder) -> None:
    store = PgVectorStore(connection=_FakeConnection(), embedder=embedder)
    assert store.search("egal", top_k=0) == []


def test_lexical_branch_can_be_disabled(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection(rows={"ORDER BY embedding <=>": [{"id": "a"}]})
    store = PgVectorStore(connection=connection, embedder=embedder)

    store.search("Frage", lexical=False)

    assert not any("plainto_tsquery" in sql for sql, _ in connection.executed)


def test_vector_branch_can_be_disabled(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection(rows={"plainto_tsquery": [{"id": "a"}]})
    store = PgVectorStore(connection=connection, embedder=embedder)

    store.search("Frage", vector=False)

    assert not any("ORDER BY embedding <=>" in sql for sql, _ in connection.executed)


def test_close_closes_connection(embedder: HashingEmbedder) -> None:
    connection = _FakeConnection()
    store = PgVectorStore(connection=connection, embedder=embedder)
    store.close()
    assert connection.closed is True


def test_get_embedder_default_is_hashing() -> None:
    assert isinstance(get_embedder("hashing"), HashingEmbedder)
