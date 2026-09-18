"""Bewertungslauf über einen Datensatz.

Ergebnis ist ein Bericht mit Zahlen, der sich als JSON ablegen lässt. Damit
werden Vergleiche zwischen Chunking-Verfahren, Embedding-Modellen oder
Rerankern reproduzierbar statt gefühlt.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.core.models import Chunk
from deutsches_ki.evaluation.dataset import (
    EvaluationDataset,
    canonical_source,
    chunk_identity,
)
from deutsches_ki.evaluation.metrics import (
    hit_rate_at_k,
    mean,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from deutsches_ki.providers.base import ChatProvider
from deutsches_ki.rag import DeutschRAG
from deutsches_ki.retrieval.base import Retriever

__all__ = ["DEFAULT_KS", "EvaluationReport", "evaluate_rag", "evaluate_retriever"]

DEFAULT_KS = (1, 5, 10)


class EvaluationReport(BaseModel):
    """Ergebnis eines Bewertungslaufs."""

    model_config = ConfigDict(extra="forbid")

    dataset: str
    cases: int
    top_k: int
    recall: dict[str, float] = Field(default_factory=dict)
    precision: dict[str, float] = Field(default_factory=dict)
    hit_rate: dict[str, float] = Field(default_factory=dict)
    ndcg: dict[str, float] = Field(default_factory=dict)
    mrr: float = 0.0
    citation_validity: float = 1.0
    answer_presence: float = 0.0
    unanswered: list[str] = Field(default_factory=list)


class _Accumulator:
    """Sammelt die Einzelwerte und mittelt am Ende."""

    def __init__(self, ks: Sequence[int]) -> None:
        self.ks = list(ks)
        self.recall: dict[int, list[float]] = {k: [] for k in self.ks}
        self.precision: dict[int, list[float]] = {k: [] for k in self.ks}
        self.hit_rate: dict[int, list[float]] = {k: [] for k in self.ks}
        self.ndcg: dict[int, list[float]] = {k: [] for k in self.ks}
        self.mrr: list[float] = []
        self.citation_validity: list[float] = []
        self.answer_presence: list[float] = []
        self.unanswered: list[str] = []

    def add(self, retrieved: Sequence[str], expected: list[str]) -> None:
        wanted = [source.strip().lower() for source in expected]
        for k in self.ks:
            self.recall[k].append(recall_at_k(retrieved, wanted, k))
            self.precision[k].append(precision_at_k(retrieved, wanted, k))
            self.hit_rate[k].append(hit_rate_at_k(retrieved, wanted, k))
            self.ndcg[k].append(ndcg_at_k(retrieved, wanted, k))
        self.mrr.append(reciprocal_rank(retrieved, wanted))

    def build(self, dataset: str, top_k: int, cases: int) -> EvaluationReport:
        return EvaluationReport(
            dataset=dataset,
            cases=cases,
            top_k=top_k,
            recall={str(k): mean(self.recall[k]) for k in self.ks},
            precision={str(k): mean(self.precision[k]) for k in self.ks},
            hit_rate={str(k): mean(self.hit_rate[k]) for k in self.ks},
            ndcg={str(k): mean(self.ndcg[k]) for k in self.ks},
            mrr=mean(self.mrr),
            citation_validity=mean(self.citation_validity) if self.citation_validity else 1.0,
            answer_presence=mean(self.answer_presence),
            unanswered=self.unanswered,
        )


def _identities(chunks: Sequence[Chunk], expected: list[str]) -> list[str]:
    return [canonical_source(chunk_identity(chunk), expected) for chunk in chunks]


def evaluate_retriever(
    retriever: Retriever,
    dataset: EvaluationDataset,
    *,
    ks: Sequence[int] = DEFAULT_KS,
    top_k: int = 10,
) -> EvaluationReport:
    """Bewertet nur die Suche."""
    accumulator = _Accumulator(ks)
    for case in dataset.cases:
        results = retriever.search(case.question, top_k=top_k)
        chunks = [result.chunk for result in results]
        identities = _identities(chunks, case.expected_sources)
        accumulator.add(identities, case.expected_sources)

        wanted = [source.strip().lower() for source in case.expected_sources]
        if not set(identities[:top_k]) & set(wanted):
            accumulator.unanswered.append(case.question)

    return accumulator.build(dataset.name, top_k, len(dataset.cases))


def evaluate_rag(
    rag: DeutschRAG,
    dataset: EvaluationDataset,
    *,
    ks: Sequence[int] = DEFAULT_KS,
    top_k: int = 10,
    llm: ChatProvider | None = None,
) -> EvaluationReport:
    """Bewertet Suche und Antwort: Treffer, Quellenangaben, Antwort vorhanden.

    ``citation_validity`` zählt nur Antworten mit Quellenangaben, also solche,
    die ein Sprachmodell formuliert hat.
    """
    accumulator = _Accumulator(ks)
    for case in dataset.cases:
        answer = rag.ask(case.question, top_k=top_k)
        identities = _identities(answer.retrieved_chunks, case.expected_sources)
        accumulator.add(identities, case.expected_sources)

        wanted = [source.strip().lower() for source in case.expected_sources]
        if not set(identities[:top_k]) & set(wanted):
            accumulator.unanswered.append(case.question)

        accumulator.answer_presence.append(1.0 if answer.answer.strip() else 0.0)
        if llm is not None:
            report = answer.metadata.get("citations") or {}
            unknown = report.get("unknown") if isinstance(report, dict) else None
            if isinstance(unknown, list):
                accumulator.citation_validity.append(0.0 if unknown else 1.0)

    return accumulator.build(dataset.name, top_k, len(dataset.cases))
