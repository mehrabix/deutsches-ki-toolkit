"""Suche im Arbeitsspeicher: Vektor und lexikalisch, zusammengeführt per RRF.

Diese Suche braucht keine Datenbank und keinen Suchdienst. Sie ist der
Ausgangspunkt und die Vergleichsgrundlage für die PostgreSQL-Anbindung.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from deutsches_ki.core.models import Chunk, SearchResult
from deutsches_ki.embeddings.base import EmbeddingProvider
from deutsches_ki.retrieval.fusion import reciprocal_rank_fusion
from deutsches_ki.text.tokens import search_tokens

__all__ = ["HybridRetriever", "InMemoryRetriever"]


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right, strict=False):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (math.sqrt(left_norm) * math.sqrt(right_norm))


class InMemoryRetriever:
    """Hybride Suche über Vektoren und deutsche Volltext-Token."""

    def __init__(
        self,
        embedder: EmbeddingProvider,
        *,
        vector: bool = True,
        lexical: bool = True,
        fusion: str = "rrf",
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if not vector and not lexical:
            raise ValueError("Mindestens ein Suchzweig (vector oder lexical) muss aktiv sein.")
        if fusion != "rrf":
            raise ValueError("Derzeit wird nur die Zusammenführung 'rrf' unterstützt.")

        self._embedder = embedder
        self._vector = vector
        self._lexical = lexical
        self._fusion = fusion
        self._k1 = k1
        self._b = b
        self._chunks: list[Chunk] = []
        self._vectors: list[list[float]] = []
        self._tokens: list[list[str]] = []
        self._doc_freq: Counter[str] = Counter()
        self._average_length = 0.0

    @property
    def size(self) -> int:
        """Anzahl der aufgenommenen Chunks."""
        return len(self._chunks)

    def add(self, chunks: list[Chunk]) -> None:
        """Nimmt Chunks in den Index auf."""
        if not chunks:
            return
        self._chunks.extend(chunks)

        new_tokens = [search_tokens(chunk.content) for chunk in chunks]
        self._tokens.extend(new_tokens)
        for tokens in new_tokens:
            for term in set(tokens):
                self._doc_freq[term] += 1

        if self._vector:
            self._vectors.extend(
                self._embedder.embed_documents([chunk.content for chunk in chunks])
            )

        total = sum(len(tokens) for tokens in self._tokens)
        self._average_length = total / len(self._tokens) if self._tokens else 0.0

    def _vector_ranking(self, query: str) -> list[str]:
        if not self._vectors:
            return []
        query_vector = self._embedder.embed_query(query)
        scored = [
            (_cosine(query_vector, vector), index) for index, vector in enumerate(self._vectors)
        ]
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [self._chunks[index].id for score, index in scored if score > 0.0]

    def _lexical_ranking(self, query: str) -> list[str]:
        terms = search_tokens(query)
        if not terms:
            return []
        document_count = len(self._chunks)
        scored: list[tuple[float, int]] = []
        for index, tokens in enumerate(self._tokens):
            length = len(tokens)
            counts = Counter(tokens)
            score = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if frequency == 0:
                    continue
                document_frequency = self._doc_freq.get(term, 0)
                idf = math.log(
                    1.0 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
                )
                denominator = frequency + self._k1 * (
                    1.0 - self._b + self._b * (length / self._average_length)
                )
                score += idf * (frequency * (self._k1 + 1.0)) / denominator
            if score > 0.0:
                scored.append((score, index))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [self._chunks[index].id for _, index in scored]

    def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """Findet die passendsten Chunks zu einer Anfrage."""
        if not self._chunks or top_k <= 0:
            return []

        vector_ranking = self._vector_ranking(query) if self._vector else []
        lexical_ranking = self._lexical_ranking(query) if self._lexical else []

        rankings = [ranking for ranking in (vector_ranking, lexical_ranking) if ranking]
        if not rankings:
            return []
        fused = reciprocal_rank_fusion(rankings)
        ordered = sorted(fused.items(), key=lambda pair: (-pair[1], pair[0]))

        position = {chunk.id: index for index, chunk in enumerate(self._chunks)}
        vector_rank = {doc_id: rank for rank, doc_id in enumerate(vector_ranking, start=1)}
        lexical_rank = {doc_id: rank for rank, doc_id in enumerate(lexical_ranking, start=1)}

        return [
            SearchResult(
                chunk=self._chunks[position[doc_id]],
                score=score,
                vector_rank=vector_rank.get(doc_id),
                lexical_rank=lexical_rank.get(doc_id),
            )
            for doc_id, score in ordered[:top_k]
        ]


class HybridRetriever(InMemoryRetriever):
    """Aussagekräftiger Name für die hybride Suche im Arbeitsspeicher."""
