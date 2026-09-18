"""Vergleich von Embedding-Modellen auf demselben Bewertungssatz.

Der Sinn ist nicht, ein Modell zu küren, sondern die Frage zu beantworten, ob
sich der Aufwand lohnt. Wenn ein deutsches Modell BGE-M3 nicht schlägt, gehört
das hier hin und nicht in eine Produktbeschreibung.
"""

from __future__ import annotations

import time
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.core.models import Chunk
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.evaluation import EvaluationDataset, evaluate_retriever
from deutsches_ki.retrieval import InMemoryRetriever

__all__ = ["EmbeddingComparison", "compare_embeddings"]


class EmbeddingComparison(BaseModel):
    """Ergebnis eines Modells im Vergleich."""

    model_config = ConfigDict(extra="forbid")

    model: str
    dimension: int
    recall: dict[str, float] = Field(default_factory=dict)
    mrr: float = 0.0
    ndcg: dict[str, float] = Field(default_factory=dict)
    index_seconds: float = 0.0
    query_ms: float = 0.0
    chunks_per_second: float = 0.0
    error: str | None = None


def compare_embeddings(
    chunks: Sequence[Chunk],
    dataset: EvaluationDataset,
    models: Sequence[str],
    *,
    top_k: int = 10,
) -> list[EmbeddingComparison]:
    """Bewertet mehrere Embedding-Modelle auf demselben Bestand.

    Ein Modell, das sich nicht laden lässt (fehlende Erweiterung, kein Netz),
    bekommt einen Eintrag mit ``error`` statt den ganzen Lauf abzubrechen.
    """
    results: list[EmbeddingComparison] = []

    for name in models:
        try:
            embedder = get_embedder(name)
        except Exception as error:
            results.append(
                EmbeddingComparison(
                    model=name, dimension=0, error=f"{type(error).__name__}: {error}"
                )
            )
            continue

        retriever = InMemoryRetriever(embedder)
        started = time.perf_counter()
        retriever.add(list(chunks))
        index_seconds = time.perf_counter() - started

        questions = [case.question for case in dataset.cases]
        started = time.perf_counter()
        for question in questions:
            retriever.search(question, top_k=top_k)
        query_seconds = time.perf_counter() - started

        report = evaluate_retriever(retriever, dataset, top_k=top_k)
        results.append(
            EmbeddingComparison(
                model=name,
                dimension=embedder.dimension,
                recall=report.recall,
                mrr=report.mrr,
                ndcg=report.ndcg,
                index_seconds=round(index_seconds, 4),
                query_ms=round((query_seconds / len(questions)) * 1000.0, 3) if questions else 0.0,
                chunks_per_second=round(len(chunks) / index_seconds, 2)
                if index_seconds > 0
                else 0.0,
            )
        )

    return results
