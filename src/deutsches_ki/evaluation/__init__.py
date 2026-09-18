"""Bewertung: Metriken, Datensätze und Bewertungsläufe."""

from __future__ import annotations

from deutsches_ki.evaluation.dataset import (
    EvaluationCase,
    EvaluationDataset,
    canonical_source,
    chunk_identity,
    matches_source,
)
from deutsches_ki.evaluation.metrics import (
    dcg,
    hit_rate_at_k,
    mean,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from deutsches_ki.evaluation.runner import (
    DEFAULT_KS,
    EvaluationReport,
    evaluate_rag,
    evaluate_retriever,
)

__all__ = [
    "DEFAULT_KS",
    "EvaluationCase",
    "EvaluationDataset",
    "EvaluationReport",
    "canonical_source",
    "chunk_identity",
    "dcg",
    "evaluate_rag",
    "evaluate_retriever",
    "hit_rate_at_k",
    "matches_source",
    "mean",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
]
