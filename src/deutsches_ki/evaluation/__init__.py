"""Bewertung: Metriken, Datensätze und Bewertungsläufe."""

from __future__ import annotations

from deutsches_ki.evaluation.answer_quality import (
    JUDGE_PROMPT,
    JudgeResult,
    answer_relevance,
    citation_coverage,
    groundedness,
    judge_answer,
)
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
    "JUDGE_PROMPT",
    "EvaluationCase",
    "EvaluationDataset",
    "EvaluationReport",
    "JudgeResult",
    "answer_relevance",
    "canonical_source",
    "chunk_identity",
    "citation_coverage",
    "dcg",
    "evaluate_rag",
    "evaluate_retriever",
    "groundedness",
    "hit_rate_at_k",
    "judge_answer",
    "matches_source",
    "mean",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
]
