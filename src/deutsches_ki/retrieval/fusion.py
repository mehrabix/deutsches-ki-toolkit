"""Reciprocal Rank Fusion.

Führt die Ranglisten mehrerer Suchzweige zusammen, ohne dass Gewichte
abgestimmt werden müssen. Das ist der robuste Ausgangspunkt; später kann eine
gewichtete oder gelernte Zusammenführung daneben treten.
"""

from __future__ import annotations

from collections.abc import Sequence

__all__ = ["reciprocal_rank_fusion"]

DEFAULT_K = 60


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]],
    *,
    k: int = DEFAULT_K,
) -> dict[str, float]:
    """Fasst Ranglisten zu einer Punktzahl je Dokument zusammen.

    Ein Dokument, das in mehreren Ranglisten weit oben steht, gewinnt.
    """
    if k < 1:
        raise ValueError("k muss mindestens 1 sein.")

    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores
