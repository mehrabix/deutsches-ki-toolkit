"""Tests für den Bewertungslauf."""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki.core.models import Chunk
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.errors import ParseError
from deutsches_ki.evaluation import (
    EvaluationCase,
    EvaluationDataset,
    canonical_source,
    chunk_identity,
    evaluate_rag,
    evaluate_retriever,
    matches_source,
)
from deutsches_ki.rag import DeutschRAG
from deutsches_ki.retrieval import InMemoryRetriever

CHUNKS = [
    Chunk(
        content="Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.",
        metadata={"document": "vertrag.md", "section": "§ 4 Zahlungsbedingungen"},
    ),
    Chunk(
        content="Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
        metadata={"document": "vertrag.md", "section": "§ 7 Kündigung"},
    ),
    Chunk(
        content="Die Wartung erfolgt jährlich.",
        metadata={"document": "handbuch.md", "section": "Wartungsintervalle"},
    ),
]

DATASET = EvaluationDataset(
    name="test",
    cases=[
        EvaluationCase(
            question="Wie lange ist die Zahlungsfrist?",
            expected_sources=["vertrag.md#§ 4 Zahlungsbedingungen"],
        ),
        EvaluationCase(
            question="Wie lange ist die Kündigungsfrist?",
            expected_sources=["vertrag.md#§ 7 Kündigung"],
        ),
        EvaluationCase(
            question="Wie oft erfolgt die Wartung?",
            expected_sources=["handbuch.md#Wartungsintervalle"],
        ),
    ],
)


def _retriever() -> InMemoryRetriever:
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(CHUNKS)
    return retriever


def test_chunk_identity_uses_document_and_section() -> None:
    assert chunk_identity(CHUNKS[0]) == "vertrag.md#§ 4 zahlungsbedingungen"


def test_chunk_identity_without_section_falls_back_to_document_id() -> None:
    chunk = Chunk(content="Text", document_id="doc-1")
    assert chunk_identity(chunk) == "doc-1"


def test_matches_source_exact() -> None:
    assert matches_source(
        "vertrag.md#§ 4 zahlungsbedingungen", "vertrag.md#§ 4 Zahlungsbedingungen"
    )


def test_matches_source_by_document_only() -> None:
    assert matches_source("vertrag.md#§ 7 kündigung", "vertrag.md")
    assert not matches_source("handbuch.md#ersatzteile", "vertrag.md")


def test_canonical_source_maps_to_expected() -> None:
    identity = "vertrag.md#§ 4 zahlungsbedingungen"
    assert canonical_source(identity, ["vertrag.md"]) == "vertrag.md"
    assert canonical_source(identity, ["etwas anderes"]) == identity


def test_evaluate_retriever_reports_metrics() -> None:
    report = evaluate_retriever(_retriever(), DATASET, top_k=3)

    assert report.cases == 3
    assert report.dataset == "test"
    assert report.recall["1"] == 1.0
    assert report.mrr == 1.0
    assert report.unanswered == []
    assert set(report.recall) == {"1", "5", "10"}


def test_evaluate_retriever_lists_unanswered() -> None:
    dataset = EvaluationDataset(
        name="leer",
        cases=[
            EvaluationCase(
                question="Wie hoch ist der Nettobetrag?",
                expected_sources=["rechnung.txt"],
            )
        ],
    )
    report = evaluate_retriever(_retriever(), dataset, top_k=3)

    assert report.recall["1"] == 0.0
    assert report.unanswered == ["Wie hoch ist der Nettobetrag?"]


def test_evaluate_rag_counts_presence() -> None:
    rag = DeutschRAG(_retriever(), candidates=3, top_k=3)
    report = evaluate_rag(rag, DATASET, top_k=3)

    assert report.answer_presence == 1.0
    assert report.citation_validity == 1.0


def test_evaluate_retriever_with_tighter_top_k() -> None:
    report = evaluate_retriever(_retriever(), DATASET, ks=(1,), top_k=1)
    assert set(report.recall) == {"1"}


def test_dataset_loads_from_yaml(tmp_path: Path) -> None:
    config = tmp_path / "datensatz.yaml"
    config.write_text(
        "name: mini\ncases:\n  - question: Wie lange?\n    expected_sources: ['vertrag.md']\n",
        encoding="utf-8",
    )

    dataset = EvaluationDataset.from_file(config)
    assert dataset.name == "mini"
    assert dataset.cases[0].expected_sources == ["vertrag.md"]


def test_dataset_missing_file_raises() -> None:
    with pytest.raises(ParseError):
        EvaluationDataset.from_file("gibt-es-nicht.yaml")


def test_case_requires_expected_sources() -> None:
    with pytest.raises(ValueError, match="expected_sources"):
        EvaluationCase.model_validate({"question": "Frage?"})


def test_repository_benchmark_dataset_is_loadable() -> None:
    path = Path(__file__).resolve().parents[3] / "datasets" / "benchmark" / "deutsch_rag.yaml"
    dataset = EvaluationDataset.from_file(path)
    assert len(dataset.cases) >= 10
    assert "business" in dataset.categories()
