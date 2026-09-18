"""Tests für die Suche im Arbeitsspeicher."""

from __future__ import annotations

import pytest

from deutsches_ki.core.models import Chunk
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.retrieval import HybridRetriever, InMemoryRetriever, reciprocal_rank_fusion


def _chunks() -> list[Chunk]:
    return [
        Chunk(
            content="Die Zahlungsfrist beträgt 30 Tage nach Rechnungsstellung.",
            metadata={"section": "§ 4"},
        ),
        Chunk(
            content="Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
            metadata={"section": "§ 5"},
        ),
        Chunk(
            content="Der Versicherungsbeitrag steigt jährlich um zwei Prozent.",
            metadata={"section": "§ 6"},
        ),
        Chunk(
            content="Nach § 37 Abs. 2 VOB/B ist die Abrechnung zu prüfen.",
            metadata={"section": "§ 7"},
        ),
    ]


def _retriever(**kwargs: object) -> InMemoryRetriever:
    retriever = InMemoryRetriever(get_embedder("hashing"), **kwargs)  # type: ignore[arg-type]
    retriever.add(_chunks())
    return retriever


def test_lexical_finds_exact_reference() -> None:
    retriever = _retriever(vector=False, lexical=True)
    results = retriever.search("§ 37 Abs. 2 VOB/B")
    assert results[0].chunk.metadata["section"] == "§ 7"
    assert results[0].lexical_rank == 1
    assert results[0].vector_rank is None


def test_lexical_finds_compound_by_part() -> None:
    retriever = _retriever(vector=False, lexical=True)
    results = retriever.search("Beitrag")
    assert results[0].chunk.metadata["section"] == "§ 6"


def test_vector_finds_paraphrase() -> None:
    retriever = _retriever(vector=True, lexical=False)
    results = retriever.search("Wie lange dauert die Zahlungsfrist?")
    assert results[0].chunk.metadata["section"] == "§ 4"
    assert results[0].vector_rank == 1


def test_hybrid_reports_both_ranks() -> None:
    retriever = HybridRetriever(get_embedder("hashing"))
    retriever.add(_chunks())
    results = retriever.search("Zahlungsfrist Rechnungsstellung")
    top = results[0]
    assert top.chunk.metadata["section"] == "§ 4"
    assert top.vector_rank == 1
    assert top.lexical_rank == 1


def test_scores_are_descending() -> None:
    retriever = _retriever()
    scores = [result.score for result in retriever.search("Frist")]
    assert scores == sorted(scores, reverse=True)


def test_top_k_limits_results() -> None:
    retriever = _retriever()
    assert len(retriever.search("Frist", top_k=2)) == 2


def test_empty_index_returns_nothing() -> None:
    retriever = InMemoryRetriever(get_embedder("hashing"))
    assert retriever.search("irgendwas") == []
    assert retriever.size == 0


def test_top_k_zero_returns_nothing() -> None:
    assert _retriever().search("Frist", top_k=0) == []


def test_add_empty_list_is_a_no_op() -> None:
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add([])
    assert retriever.size == 0


def test_size_counts_chunks() -> None:
    assert _retriever().size == 4


def test_requires_at_least_one_branch() -> None:
    with pytest.raises(ValueError, match="Suchzweig"):
        InMemoryRetriever(get_embedder("hashing"), vector=False, lexical=False)


def test_unknown_fusion_raises() -> None:
    with pytest.raises(ValueError, match="rrf"):
        InMemoryRetriever(get_embedder("hashing"), fusion="magic")


def test_reciprocal_rank_fusion_prefers_agreement() -> None:
    scores = reciprocal_rank_fusion([["a", "b"], ["b", "c"]])
    assert max(scores, key=lambda key: scores[key]) == "b"
    assert scores["a"] > scores["c"]


def test_reciprocal_rank_fusion_rejects_bad_k() -> None:
    with pytest.raises(ValueError, match="k"):
        reciprocal_rank_fusion([["a"]], k=0)
