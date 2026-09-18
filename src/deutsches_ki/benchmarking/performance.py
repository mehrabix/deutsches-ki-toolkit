"""Leistungsmessung der Verarbeitungskette.

Gemessen wird, was tatsächlich durchläuft: einlesen, zerlegen, einbetten,
indizieren und suchen. Die Zahlen sind maschinenlesbar, damit sich Änderungen
über die Zeit vergleichen lassen statt nur gefühlt schneller zu sein.
"""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.chunking import chunk_document
from deutsches_ki.core.models import Chunk
from deutsches_ki.documents.parse import parse
from deutsches_ki.embeddings.base import EmbeddingProvider
from deutsches_ki.errors import DeutschesKiError
from deutsches_ki.retrieval import InMemoryRetriever

__all__ = ["PerformanceReport", "benchmark_pipeline", "percentile"]


class PerformanceReport(BaseModel):
    """Ergebnis einer Leistungsmessung."""

    model_config = ConfigDict(extra="forbid")

    documents: int = 0
    chunks: int = 0
    parse_seconds: float = 0.0
    chunk_seconds: float = 0.0
    embed_seconds: float = 0.0
    index_seconds: float = 0.0
    query_count: int = 0
    query_p50_ms: float = 0.0
    query_p95_ms: float = 0.0
    peak_memory_mb: float = 0.0
    documents_per_second: float = 0.0
    chunks_per_second: float = 0.0
    skipped: list[str] = Field(default_factory=list)


def percentile(values: Sequence[float], share: float) -> float:
    """Perzentil nach der üblichen Näherung über den Rang.

    Bei leerer Liste 0.0. ``share`` liegt zwischen 0 und 1.
    """
    if not values:
        return 0.0
    if not 0.0 <= share <= 1.0:
        raise ValueError("share muss zwischen 0 und 1 liegen.")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = share * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def benchmark_pipeline(
    paths: Sequence[Path],
    *,
    embedder: EmbeddingProvider,
    queries: Sequence[str] = (),
    max_tokens: int = 512,
) -> PerformanceReport:
    """Misst die Kette über die angegebenen Dateien."""
    tracemalloc.start()

    skipped: list[str] = []
    chunks: list[Chunk] = []

    started = time.perf_counter()
    documents = []
    for path in paths:
        try:
            documents.append(parse(path))
        except DeutschesKiError:
            skipped.append(str(path))
    parse_seconds = time.perf_counter() - started

    started = time.perf_counter()
    for document in documents:
        chunks.extend(chunk_document(document, max_tokens=max_tokens))
    chunk_seconds = time.perf_counter() - started

    texts = [chunk.index_text for chunk in chunks]
    started = time.perf_counter()
    if texts:
        embedder.embed_documents(texts)
    embed_seconds = time.perf_counter() - started

    # Das Indizieren rechnet die Vektoren noch einmal; die Zahl enthält also
    # auch das Einbetten und ist deshalb immer größer als ``embed_seconds``.
    retriever = InMemoryRetriever(embedder)
    started = time.perf_counter()
    retriever.add(chunks)
    index_seconds = time.perf_counter() - started

    latencies: list[float] = []
    for query in queries:
        started = time.perf_counter()
        retriever.search(query, top_k=5)
        latencies.append((time.perf_counter() - started) * 1000.0)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total = parse_seconds + chunk_seconds
    return PerformanceReport(
        documents=len(documents),
        chunks=len(chunks),
        parse_seconds=round(parse_seconds, 4),
        chunk_seconds=round(chunk_seconds, 4),
        embed_seconds=round(embed_seconds, 4),
        index_seconds=round(index_seconds, 4),
        query_count=len(latencies),
        query_p50_ms=round(percentile(latencies, 0.5), 3),
        query_p95_ms=round(percentile(latencies, 0.95), 3),
        peak_memory_mb=round(peak / (1024 * 1024), 2),
        documents_per_second=round(len(documents) / total, 2) if total > 0 else 0.0,
        chunks_per_second=round(len(chunks) / (chunk_seconds + embed_seconds), 2)
        if (chunk_seconds + embed_seconds) > 0
        else 0.0,
        skipped=skipped,
    )
