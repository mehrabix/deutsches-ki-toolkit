"""Tests für die Bewertungsmetriken."""

from __future__ import annotations

import pytest

from deutsches_ki.evaluation.metrics import (
    dcg,
    hit_rate_at_k,
    mean,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

RETRIEVED = ["c", "a", "b", "d"]
RELEVANT = ["a", "b"]


def test_recall_at_k() -> None:
    assert recall_at_k(RETRIEVED, RELEVANT, 1) == 0.0
    assert recall_at_k(RETRIEVED, RELEVANT, 2) == 0.5
    assert recall_at_k(RETRIEVED, RELEVANT, 3) == 1.0


def test_precision_at_k() -> None:
    assert precision_at_k(RETRIEVED, RELEVANT, 2) == 0.5
    assert precision_at_k(RETRIEVED, RELEVANT, 4) == 0.5


def test_hit_rate() -> None:
    assert hit_rate_at_k(RETRIEVED, RELEVANT, 1) == 0.0
    assert hit_rate_at_k(RETRIEVED, RELEVANT, 2) == 1.0


def test_reciprocal_rank() -> None:
    assert reciprocal_rank(["x", "a", "b"], RELEVANT) == 0.5
    assert reciprocal_rank(["a"], RELEVANT) == 1.0
    assert reciprocal_rank(["x"], RELEVANT) == 0.0


def test_ndcg_is_one_for_ideal_order() -> None:
    assert ndcg_at_k(["a", "b", "c"], RELEVANT, 3) == pytest.approx(1.0)


def test_ndcg_is_lower_when_relevant_items_come_late() -> None:
    late = ndcg_at_k(["c", "d", "a", "b"], RELEVANT, 4)
    assert 0.0 < late < 1.0


def test_dcg_discounts_lower_ranks() -> None:
    assert dcg([1.0, 1.0]) > dcg([1.0, 0.0])
    assert dcg([]) == 0.0


def test_metrics_handle_degenerate_input() -> None:
    assert recall_at_k(RETRIEVED, RELEVANT, 0) == 0.0
    assert precision_at_k([], RELEVANT, 3) == 0.0
    assert recall_at_k(RETRIEVED, [], 3) == 0.0
    assert ndcg_at_k(RETRIEVED, [], 3) == 0.0
    assert hit_rate_at_k(RETRIEVED, RELEVANT, 0) == 0.0


def test_mean_of_empty_list() -> None:
    assert mean([]) == 0.0
    assert mean([1.0, 0.0]) == 0.5
