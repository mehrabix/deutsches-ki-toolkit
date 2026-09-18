"""Integrationstest für Embeddings und Cross-Encoder-Reranking.

Läuft nur, wenn die Erweiterung ``embeddings`` installiert ist. Beim ersten Lauf
werden Modelle geladen; die Voreinstellung ist bewusst klein, damit die CI nicht
mehrere Gigabyte zieht. Lokal lässt sich das große Modell erzwingen:

    set DEUTSCHES_KI_TEST_EMBEDDING_MODEL=BAAI/bge-m3
    uv run pytest tests/integration/test_embeddings.py -q
"""

from __future__ import annotations

import os

import pytest

from deutsches_ki.core.models import Chunk, SearchResult
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.reranking.cross_encoder import CrossEncoderReranker

pytestmark = [
    pytest.mark.integration,
    pytest.mark.optional,
    # Beim ersten Laden laden die Bibliotheken Modelle herunter und warnen dabei.
    # Die Projektkonfiguration macht aus Warnungen Fehler, damit eigene
    # Verfallswarnungen auffallen; hier werden nur die bekannten Fremdwarungen
    # geduldet.
    pytest.mark.filterwarnings("ignore:.*cache-system uses symlinks.*:UserWarning"),
    pytest.mark.filterwarnings("ignore:.*unauthenticated requests to the HF Hub.*:UserWarning"),
    pytest.mark.filterwarnings("ignore:.*torch.jit.script is deprecated.*:FutureWarning"),
]

pytest.importorskip("sentence_transformers", reason="Die Erweiterung 'embeddings' fehlt.")

EMBEDDING_MODEL = os.environ.get(
    "DEUTSCHES_KI_TEST_EMBEDDING_MODEL", "intfloat/multilingual-e5-small"
)
RERANKER_MODEL = os.environ.get(
    "DEUTSCHES_KI_TEST_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

SENTENCES = [
    "Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.",
    "Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


@pytest.fixture(scope="module")
def embedder() -> object:
    try:
        return get_embedder(EMBEDDING_MODEL)
    except Exception as error:
        pytest.skip(f"Modell {EMBEDDING_MODEL} nicht ladbar: {error}")


def test_dimension_is_reported(embedder: object) -> None:
    assert embedder.dimension > 0  # type: ignore[attr-defined]


def test_documents_and_query_share_a_shape(embedder: object) -> None:
    vectors = embedder.embed_documents(SENTENCES)  # type: ignore[attr-defined]
    query = embedder.embed_query("Welche Zahlungsfrist gilt?")  # type: ignore[attr-defined]

    assert len(vectors) == len(SENTENCES)
    assert all(len(vector) == embedder.dimension for vector in vectors)  # type: ignore[attr-defined]
    assert len(query) == embedder.dimension  # type: ignore[attr-defined]


def test_vectors_are_usable_for_cosine(embedder: object) -> None:
    vectors = embedder.embed_documents(SENTENCES)  # type: ignore[attr-defined]
    self_similarity = _cosine(vectors[0], vectors[0])
    assert self_similarity == pytest.approx(1.0, abs=1e-3)


def test_matching_sentence_scores_higher(embedder: object) -> None:
    vectors = embedder.embed_documents(SENTENCES)  # type: ignore[attr-defined]
    query = embedder.embed_query("Wie lange ist die Zahlungsfrist?")  # type: ignore[attr-defined]

    payment = _cosine(query, vectors[0])
    cancellation = _cosine(query, vectors[1])
    assert payment > cancellation, "Das passende Satzpaar sollte ähnlicher sein"


@pytest.fixture(scope="module")
def reranker() -> CrossEncoderReranker:
    try:
        return CrossEncoderReranker(RERANKER_MODEL)
    except Exception as error:
        pytest.skip(f"Modell {RERANKER_MODEL} nicht ladbar: {error}")


def test_reranker_scores_and_reorders(reranker: CrossEncoderReranker) -> None:
    results = [
        SearchResult(chunk=Chunk(content=SENTENCES[0], metadata={"section": "§ 4"}), score=0.0),
        SearchResult(chunk=Chunk(content=SENTENCES[1], metadata={"section": "§ 7"}), score=0.0),
    ]

    reordered = reranker.rerank("Wie lange ist die Zahlungsfrist?", results)

    assert len(reordered) == 2
    assert all(result.score != 0.0 for result in reordered)
    assert reordered[0].chunk.metadata["section"] == "§ 4"


def test_reranker_respects_top_k(reranker: CrossEncoderReranker) -> None:
    results = [
        SearchResult(chunk=Chunk(content=text, metadata={"section": text[:8]}))
        for text in SENTENCES
    ]
    assert len(reranker.rerank("Frist", results, top_k=1)) == 1
