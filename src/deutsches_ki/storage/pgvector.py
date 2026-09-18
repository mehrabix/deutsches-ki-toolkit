"""Speicher in PostgreSQL mit pgvector.

Die Suche in der Datenbank ist bewusst dieselbe wie im Arbeitsspeicher: Der
Volltextzweig läuft über eine Suchform, die in Python gefaltet und um
Komposita-Bestandteile ergänzt wurde. Dadurch findet „Schnösel“ auch
„Schnoesel“, ohne dass an den ``unaccent``-Regeln des Servers gedreht wird.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from deutsches_ki.core.models import Chunk, Document, Entity, SearchResult
from deutsches_ki.embeddings.base import EmbeddingProvider
from deutsches_ki.errors import MissingDependencyError
from deutsches_ki.retrieval.fusion import reciprocal_rank_fusion
from deutsches_ki.storage.schema import create_schema_statements, drop_schema_statements
from deutsches_ki.text.tokens import search_tokens

__all__ = [
    "FETCH_CHUNKS",
    "INSERT_ENTITY",
    "LEXICAL_SEARCH",
    "UPSERT_CHUNK",
    "UPSERT_DOCUMENT",
    "VECTOR_SEARCH",
    "PgVectorStore",
    "row_to_chunk",
    "vector_to_literal",
]

UPSERT_DOCUMENT = """
INSERT INTO documents (id, source, title, language, metadata)
VALUES (%s, %s, %s, %s, %s::jsonb)
ON CONFLICT (id) DO UPDATE
SET source = EXCLUDED.source,
    title = EXCLUDED.title,
    language = EXCLUDED.language,
    metadata = EXCLUDED.metadata
"""

UPSERT_CHUNK = """
INSERT INTO chunks (id, document_id, ordinal, content, content_search,
                    section, section_path, page, metadata, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector)
ON CONFLICT (id) DO UPDATE
SET content = EXCLUDED.content,
    content_search = EXCLUDED.content_search,
    section = EXCLUDED.section,
    section_path = EXCLUDED.section_path,
    page = EXCLUDED.page,
    metadata = EXCLUDED.metadata,
    embedding = EXCLUDED.embedding
"""

INSERT_ENTITY = """
INSERT INTO entities (chunk_id, entity_type, text, start_offset, end_offset,
                      confidence, source, metadata)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
"""

VECTOR_SEARCH = """
SELECT id, 1 - (embedding <=> %s::vector) AS score
FROM chunks
WHERE embedding IS NOT NULL
ORDER BY embedding <=> %s::vector
LIMIT %s
"""

LEXICAL_SEARCH = """
SELECT id,
       ts_rank_cd(search_vector, plainto_tsquery('simple'::regconfig, %s)) AS score
FROM chunks
WHERE search_vector @@ plainto_tsquery('simple'::regconfig, %s)
ORDER BY score DESC, id
LIMIT %s
"""

FETCH_CHUNKS = """
SELECT id, document_id, content, section, section_path, page, metadata
FROM chunks
WHERE id = ANY(%s)
"""

_DEFAULT_CANDIDATES = 4


def vector_to_literal(vector: Sequence[float]) -> str:
    """pgvector erwartet Vektoren in der Schreibweise ``[0.1,0.2]``."""
    return "[" + ",".join(f"{value:.8g}" for value in vector) + "]"


def row_to_chunk(row: Mapping[str, Any]) -> Chunk:
    """Baut einen Chunk aus einer Datenbankzeile."""
    metadata: dict[str, Any] = dict(row.get("metadata") or {})
    section = row.get("section")
    if section:
        metadata["section"] = section
    if row.get("page") is not None:
        metadata["page"] = row["page"]
    if row.get("section_path"):
        metadata["section_path"] = list(row["section_path"])
    return Chunk(
        id=str(row["id"]),
        document_id=str(row.get("document_id") or ""),
        content=str(row.get("content") or ""),
        metadata=metadata,
    )


class PgVectorStore:
    """Speichert Dokumente, Chunks und Entitäten in PostgreSQL.

    Eine Verbindung kann hereingereicht werden. Dann erwartet der Speicher ein
    Objekt, dessen ``cursor()`` Zeilen als Mapping liefert (``dict_row``).
    """

    def __init__(
        self,
        dsn: str | None = None,
        *,
        connection: Any | None = None,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        if connection is None and not dsn:
            raise ValueError("Entweder eine DSN oder eine bestehende Verbindung angeben.")
        self._dsn = dsn
        self._connection = connection
        self._embedder = embedder

    # ------------------------------------------------------------------ Aufbau

    @property
    def connection(self) -> Any:
        """Die Verbindung, bei Bedarf neu aufgebaut."""
        if self._connection is None:
            try:
                import psycopg
                from psycopg.rows import dict_row
            except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
                raise MissingDependencyError(
                    "Für PostgreSQL wird die Erweiterung 'postgres' benötigt. "
                    'Installation: pip install "deutsches-ki-toolkit[postgres]"'
                ) from exc
            if self._dsn is None:  # pragma: no cover - durch __init__ ausgeschlossen
                raise ValueError("Ohne DSN lässt sich keine Verbindung aufbauen.")
            self._connection = psycopg.connect(self._dsn, row_factory=dict_row)
        return self._connection

    @property
    def dimension(self) -> int:
        """Dimension des Embedding-Modells."""
        if self._embedder is None:
            raise ValueError("Für das Schema wird ein Embedding-Anbieter benötigt.")
        return self._embedder.dimension

    def create_schema(self) -> None:
        """Legt Tabellen und Indexe an."""
        cursor = self.connection.cursor()
        try:
            for statement in create_schema_statements(self.dimension):
                cursor.execute(statement)
            self.connection.commit()
        finally:
            cursor.close()

    def drop_schema(self) -> None:
        """Entfernt die Tabellen wieder."""
        cursor = self.connection.cursor()
        try:
            for statement in drop_schema_statements():
                cursor.execute(statement)
            self.connection.commit()
        finally:
            cursor.close()

    def close(self) -> None:
        """Schließt die Verbindung, wenn sie hier aufgebaut wurde."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    # ------------------------------------------------------------------ Schreiben

    def add_document(self, document: Document) -> None:
        """Legt ein Dokument an oder aktualisiert es."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                UPSERT_DOCUMENT,
                (
                    document.id,
                    document.source,
                    document.title,
                    document.language.value,
                    json.dumps(document.metadata, ensure_ascii=False),
                ),
            )
            self.connection.commit()
        finally:
            cursor.close()

    def add_chunks(
        self,
        chunks: list[Chunk],
        *,
        embeddings: Sequence[Sequence[float]] | None = None,
    ) -> None:
        """Legt Chunks an oder aktualisiert sie."""
        if not chunks:
            return
        vectors = list(embeddings) if embeddings is not None else self._embed(chunks)
        if len(vectors) != len(chunks):
            raise ValueError("Es müssen gleich viele Vektoren wie Chunks vorliegen.")

        cursor = self.connection.cursor()
        try:
            for ordinal, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                cursor.execute(
                    UPSERT_CHUNK,
                    (
                        chunk.id,
                        chunk.document_id,
                        ordinal,
                        chunk.content,
                        " ".join(search_tokens(chunk.index_text)),
                        chunk.section,
                        chunk.metadata.get("section_path"),
                        chunk.metadata.get("page"),
                        json.dumps(chunk.metadata, ensure_ascii=False),
                        vector_to_literal(vector),
                    ),
                )
            self.connection.commit()
        finally:
            cursor.close()

    def add_entities(self, chunk_id: str, entities: Iterable[Entity]) -> None:
        """Speichert die gefundenen Entitäten zu einem Chunk."""
        cursor = self.connection.cursor()
        try:
            for entity in entities:
                cursor.execute(
                    INSERT_ENTITY,
                    (
                        chunk_id,
                        entity.type.value,
                        entity.text,
                        entity.start,
                        entity.end,
                        entity.confidence,
                        entity.source.value,
                        json.dumps(entity.metadata, ensure_ascii=False),
                    ),
                )
            self.connection.commit()
        finally:
            cursor.close()

    def _embed(self, chunks: list[Chunk]) -> list[list[float]]:
        if self._embedder is None:
            raise ValueError("Ohne Embedding-Anbieter müssen die Vektoren mitgegeben werden.")
        return self._embedder.embed_documents([chunk.index_text for chunk in chunks])

    # ------------------------------------------------------------------ Suchen

    def _fetch(self, sql: str, params: tuple[Any, ...]) -> list[Mapping[str, Any]]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
        finally:
            cursor.close()

    def _vector_ranking(self, query: str, candidates: int) -> list[str]:
        if self._embedder is None:
            return []
        literal = vector_to_literal(self._embedder.embed_query(query))
        rows = self._fetch(VECTOR_SEARCH, (literal, literal, candidates))
        return [str(row["id"]) for row in rows]

    def _lexical_ranking(self, query: str, candidates: int) -> list[str]:
        text = " ".join(search_tokens(query))
        if not text.strip():
            return []
        rows = self._fetch(LEXICAL_SEARCH, (text, text, candidates))
        return [str(row["id"]) for row in rows]

    def search(
        self,
        query: str,
        top_k: int = 20,
        *,
        vector: bool = True,
        lexical: bool = True,
        candidates: int | None = None,
    ) -> list[SearchResult]:
        """Sucht hybrid: Vektoren und deutsche Volltextsuche, vereint per RRF."""
        if top_k <= 0:
            return []
        limit = candidates if candidates is not None else max(top_k * _DEFAULT_CANDIDATES, top_k)

        vector_ranking = self._vector_ranking(query, limit) if vector else []
        lexical_ranking = self._lexical_ranking(query, limit) if lexical else []
        rankings = [ranking for ranking in (vector_ranking, lexical_ranking) if ranking]
        if not rankings:
            return []

        fused = reciprocal_rank_fusion(rankings)
        ordered = sorted(fused.items(), key=lambda pair: (-pair[1], pair[0]))
        selected = ordered[:top_k]

        rows = self._fetch(FETCH_CHUNKS, ([doc_id for doc_id, _ in selected],))
        chunks = {str(row["id"]): row_to_chunk(row) for row in rows}

        vector_rank = {doc_id: rank for rank, doc_id in enumerate(vector_ranking, start=1)}
        lexical_rank = {doc_id: rank for rank, doc_id in enumerate(lexical_ranking, start=1)}

        results: list[SearchResult] = []
        for doc_id, score in selected:
            chunk = chunks.get(doc_id)
            if chunk is None:
                continue
            results.append(
                SearchResult(
                    chunk=chunk,
                    score=score,
                    vector_rank=vector_rank.get(doc_id),
                    lexical_rank=lexical_rank.get(doc_id),
                )
            )
        return results
