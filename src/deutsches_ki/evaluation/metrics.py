"""Metriken für die Bewertung von Suche und Antwort.

Alles hier ist deterministisch und braucht kein Sprachmodell. Ein Modell als
Richter ist bequem, aber schwankend; wo ein Ergebnis feststehen kann, wird es
festgeprüft.
"""

from __future__ import annotations

import math
from collections.abc import Collection, Sequence

__all__ = [
    "dcg",
    "hit_rate_at_k",
    "mean",
    "ndcg_at_k",
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
]


def recall_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """Anteil der relevanten Fundstellen, die unter den ersten ``k`` stehen."""
    if k <= 0:
        return 0.0
    expected = set(relevant)
    if not expected:
        return 0.0
    return len(set(retrieved[:k]) & expected) / len(expected)


def precision_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """Anteil der ersten ``k`` Treffer, die relevant sind."""
    if k <= 0:
        return 0.0
    top = retrieved[:k]
    if not top:
        return 0.0
    return len(set(top) & set(relevant)) / len(top)


def hit_rate_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """1, wenn mindestens eine relevante Fundstelle unter den ersten ``k`` steht."""
    if k <= 0:
        return 0.0
    return 1.0 if set(retrieved[:k]) & set(relevant) else 0.0


def reciprocal_rank(retrieved: Sequence[str], relevant: Collection[str]) -> float:
    """Kehrwert des Rangs der ersten relevanten Fundstelle."""
    expected = set(relevant)
    for rank, item in enumerate(retrieved, start=1):
        if item in expected:
            return 1.0 / rank
    return 0.0


def dcg(gains: Sequence[float]) -> float:
    """Discounted Cumulative Gain."""
    return sum(gain / math.log2(rank + 1) for rank, gain in enumerate(gains, start=1))


def ndcg_at_k(retrieved: Sequence[str], relevant: Collection[str], k: int) -> float:
    """Normierter DCG: 1,0 bedeutet ideale Reihenfolge."""
    if k <= 0:
        return 0.0
    expected = set(relevant)
    if not expected:
        return 0.0
    gains = [1.0 if item in expected else 0.0 for item in retrieved[:k]]
    ideal = [1.0] * min(len(expected), k)
    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0.0:
        return 0.0
    return dcg(gains) / ideal_dcg


def mean(values: Sequence[float]) -> float:
    """Mittelwert, 0.0 bei leerer Liste."""
    if not values:
        return 0.0
    return sum(values) / len(values)
