"""SQL-Schema für PostgreSQL mit pgvector.

Zwei Dinge sind hier bewusst anders als in vielen Beispielen.

**Kein ``unaccent``-Trick.** PostgreSQL löst Umlaute von Haus aus nicht so auf,
wie man denkt: „Schnösel“ und „Schnoesel“ finden sich mit der
Standardkonfiguration nicht gegenseitig, und ``default_text_search_config =
'german'`` ändert daran nichts. Statt die ``unaccent``-Regeln zu verbiegen
(was Schreibrechte im Serververzeichnis verlangt), speichern wir neben dem
Originaltext eine Suchform, die bereits in Python gefaltet wurde. Damit ist die
Volltextsuche in der Datenbank exakt dieselbe wie die lexikalische Suche im
Arbeitsspeicher, inklusive Komposita-Zerlegung.

**Der Originaltext bleibt.** ``content`` enthält den Text unverändert,
``content_search`` nur die zusätzliche Suchform.
"""

from __future__ import annotations

__all__ = ["SCHEMA_VERSION", "create_schema_statements", "drop_schema_statements"]

SCHEMA_VERSION = 1


def create_schema_statements(dimension: int) -> list[str]:
    """Alle Anweisungen, um das Schema anzulegen.

    ``dimension`` ist die Dimension des Embedding-Modells, zum Beispiel 1024
    für BGE-M3 oder 256 für das Hashing-Modell.
    """
    if dimension <= 0:
        raise ValueError("dimension muss größer als 0 sein.")

    return [
        "CREATE EXTENSION IF NOT EXISTS vector",
        """
        CREATE TABLE IF NOT EXISTS documents (
            id          TEXT PRIMARY KEY,
            source      TEXT NOT NULL,
            title       TEXT,
            language    TEXT NOT NULL DEFAULT 'de',
            metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS chunks (
            id              TEXT PRIMARY KEY,
            document_id     TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            ordinal         INTEGER NOT NULL DEFAULT 0,
            content         TEXT NOT NULL,
            content_search  TEXT NOT NULL,
            search_vector   TSVECTOR GENERATED ALWAYS AS (
                                to_tsvector('simple'::regconfig, content_search)
                            ) STORED,
            section         TEXT,
            section_path    TEXT[],
            page            INTEGER,
            metadata        JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            embedding       vector({dimension})
        )
        """,
        "CREATE INDEX IF NOT EXISTS chunks_search_idx ON chunks USING gin (search_vector)",
        """
        CREATE INDEX IF NOT EXISTS chunks_embedding_idx
            ON chunks USING hnsw (embedding vector_cosine_ops)
        """,
        "CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks (document_id)",
        """
        CREATE TABLE IF NOT EXISTS entities (
            id          BIGSERIAL PRIMARY KEY,
            chunk_id    TEXT REFERENCES chunks(id) ON DELETE CASCADE,
            entity_type TEXT NOT NULL,
            text        TEXT NOT NULL,
            start_offset INTEGER,
            end_offset   INTEGER,
            confidence  REAL,
            source      TEXT,
            metadata    JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """,
        "CREATE INDEX IF NOT EXISTS entities_chunk_idx ON entities (chunk_id)",
        "CREATE INDEX IF NOT EXISTS entities_type_idx ON entities (entity_type)",
    ]


def drop_schema_statements() -> list[str]:
    """Alle Anweisungen, um die Tabellen wieder zu entfernen."""
    return [
        "DROP TABLE IF EXISTS entities",
        "DROP TABLE IF EXISTS chunks",
        "DROP TABLE IF EXISTS documents",
    ]
