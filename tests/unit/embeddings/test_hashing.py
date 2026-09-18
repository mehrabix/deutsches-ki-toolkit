"""Tests für den deterministischen Hashing-Embedder."""

from __future__ import annotations

import math

import pytest

from deutsches_ki.embeddings import HashingEmbedder, get_embedder


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def test_dimension_is_configurable() -> None:
    assert HashingEmbedder(dimension=64).dimension == 64


def test_invalid_dimension_raises() -> None:
    with pytest.raises(ValueError, match="dimension"):
        HashingEmbedder(dimension=0)


def test_vectors_are_deterministic() -> None:
    embedder = HashingEmbedder()
    first = embedder.embed_query("Die Zahlungsfrist beträgt 30 Tage.")
    second = embedder.embed_query("Die Zahlungsfrist beträgt 30 Tage.")
    assert first == second


def test_vectors_are_normalized() -> None:
    vector = HashingEmbedder().embed_query("Die Zahlungsfrist beträgt 30 Tage.")
    assert math.isclose(math.sqrt(sum(value * value for value in vector)), 1.0, rel_tol=1e-9)


def test_query_matches_document_embedding() -> None:
    embedder = HashingEmbedder()
    document_vector = embedder.embed_documents(["Die Zahlungsfrist beträgt 30 Tage."])[0]
    query_vector = embedder.embed_query("Die Zahlungsfrist beträgt 30 Tage.")
    assert document_vector == query_vector


def test_similar_texts_are_closer_than_dissimilar() -> None:
    embedder = HashingEmbedder()
    base = embedder.embed_query("Versicherungsbeitrag")
    related = embedder.embed_query("Beitrag zur Versicherung")
    unrelated = embedder.embed_query("Das Wetter ist heute schön")
    assert _cosine(base, related) > _cosine(base, unrelated)


def test_compound_is_split_for_better_matching() -> None:
    embedder = HashingEmbedder()
    separated = _cosine(
        embedder.embed_query("Versicherungsbeitrag"),
        embedder.embed_query("Beitrag"),
    )
    without = HashingEmbedder(expand_compounds=False)
    not_separated = _cosine(
        without.embed_query("Versicherungsbeitrag"),
        without.embed_query("Beitrag"),
    )
    assert separated > not_separated


def test_empty_text_gives_zero_vector() -> None:
    vector = HashingEmbedder().embed_query("")
    assert all(value == 0.0 for value in vector)


def test_get_embedder_returns_hashing() -> None:
    embedder = get_embedder("hashing")
    assert isinstance(embedder, HashingEmbedder)
    assert embedder.dimension == 256
