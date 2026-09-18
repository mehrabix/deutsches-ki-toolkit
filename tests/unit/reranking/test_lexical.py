"""Tests für das Reranking über Wortüberdeckung."""

from __future__ import annotations

import pytest

from deutsches_ki.core.models import Chunk, SearchResult
from deutsches_ki.errors import MissingDependencyError
from deutsches_ki.reranking import LexicalReranker, get_reranker


def _result(content: str, section: str, score: float = 0.01) -> SearchResult:
    return SearchResult(
        chunk=Chunk(content=content, metadata={"section": section}),
        score=score,
        vector_rank=1,
        lexical_rank=1,
    )


def _sample() -> list[SearchResult]:
    return [
        _result("Die Kündigungsfrist beträgt drei Monate.", "§ 7 Kündigung"),
        _result("Die Zahlung ist innerhalb von 30 Tagen fällig.", "§ 4 Zahlungsbedingungen"),
        _result("Der Versicherungsbeitrag steigt jährlich.", "§ 2 Vergütung"),
    ]


def test_reranker_prefers_matching_section() -> None:
    reranker = LexicalReranker()
    results = reranker.rerank("Wie lange ist die Zahlungsfrist?", _sample())
    assert results[0].chunk.section == "§ 4 Zahlungsbedingungen"


def test_reranker_keeps_all_results_without_top_k() -> None:
    assert len(LexicalReranker().rerank("Frist", _sample())) == 3


def test_reranker_respects_top_k() -> None:
    assert len(LexicalReranker().rerank("Frist", _sample(), top_k=2)) == 2


def test_reranker_handles_empty_input() -> None:
    assert LexicalReranker().rerank("Frage", []) == []


def test_reranker_handles_empty_query() -> None:
    reranker = LexicalReranker()
    results = reranker.rerank("   ", _sample())
    assert len(results) == 3
    assert all(result.score == 0.0 for result in results)


def test_reranker_keeps_original_order_on_tie() -> None:
    """Bei gleicher Punktzahl bleibt die Reihenfolge stabil."""
    reranker = LexicalReranker(phrase_bonus=0.0)
    results = reranker.rerank("voellig unbekanntes wort xyz", _sample())
    sections = [result.chunk.section for result in results]
    assert sections == ["§ 7 Kündigung", "§ 4 Zahlungsbedingungen", "§ 2 Vergütung"]


def test_reranker_preserves_branch_ranks() -> None:
    results = LexicalReranker().rerank("Zahlungsfrist", _sample())
    assert all(result.vector_rank == 1 for result in results)
    assert all(result.lexical_rank == 1 for result in results)


def test_phrase_bonus_helps_exact_match() -> None:
    reranker = LexicalReranker()
    results = reranker.rerank("innerhalb von 30 Tagen", _sample())
    assert results[0].chunk.section == "§ 4 Zahlungsbedingungen"


def test_get_reranker_returns_lexical() -> None:
    assert isinstance(get_reranker("lexical"), LexicalReranker)


def test_cross_encoder_requires_extra() -> None:
    with pytest.raises(MissingDependencyError, match="embeddings"):
        get_reranker("BAAI/bge-reranker-v2-m3")
