"""Tests für die Messungen."""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki.benchmarking import (
    benchmark_pipeline,
    compare_embeddings,
    percentile,
)
from deutsches_ki.chunking import chunk_document
from deutsches_ki.documents import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.evaluation import EvaluationCase, EvaluationDataset

FIXTURES = Path(__file__).resolve().parents[3] / "datasets" / "fixtures"

DATASET = EvaluationDataset(
    name="mini",
    cases=[
        EvaluationCase(
            question="Wie lange ist die Zahlungsfrist?",
            expected_sources=["vertrag.md#§ 4 Zahlungsbedingungen"],
        )
    ],
)


def _chunks() -> list:
    chunks = []
    for file in sorted(FIXTURES.iterdir()):
        if file.suffix.lower() in {".md", ".txt"}:
            chunks.extend(chunk_document(parse(file), max_tokens=64))
    return chunks


def test_percentile_on_empty_list() -> None:
    assert percentile([], 0.5) == 0.0


def test_percentile_on_single_value() -> None:
    assert percentile([7.0], 0.95) == 7.0


def test_percentile_interpolates() -> None:
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == pytest.approx(2.5)
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.95) == pytest.approx(3.85)
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.0) == pytest.approx(1.0)
    assert percentile([1.0, 2.0, 3.0, 4.0], 1.0) == pytest.approx(4.0)


def test_percentile_rejects_bad_share() -> None:
    with pytest.raises(ValueError, match="share"):
        percentile([1.0], 1.5)


def test_benchmark_pipeline_counts_documents_and_chunks() -> None:
    report = benchmark_pipeline(
        [FIXTURES / "vertrag.md", FIXTURES / "rechnung.txt"],
        embedder=get_embedder("hashing"),
        queries=["Wie lange ist die Zahlungsfrist?"],
    )

    assert report.documents == 2
    assert report.chunks > 0
    assert report.parse_seconds >= 0.0
    assert report.chunk_seconds >= 0.0
    assert report.embed_seconds >= 0.0
    assert report.index_seconds >= 0.0
    assert report.peak_memory_mb >= 0.0
    assert report.query_count == 1
    assert report.query_p95_ms >= report.query_p50_ms


def test_benchmark_skips_unreadable_files(tmp_path: Path) -> None:
    broken = tmp_path / "kaputt.xyz"
    broken.write_text("egal", encoding="utf-8")

    report = benchmark_pipeline([broken], embedder=get_embedder("hashing"))
    assert report.documents == 0
    assert report.skipped == [str(broken)]


def test_benchmark_without_queries() -> None:
    report = benchmark_pipeline([FIXTURES / "vertrag.md"], embedder=get_embedder("hashing"))
    assert report.query_count == 0
    assert report.query_p50_ms == 0.0


def test_compare_embeddings_reports_metrics() -> None:
    results = compare_embeddings(_chunks(), DATASET, ["hashing"], top_k=3)

    assert len(results) == 1
    result = results[0]
    assert result.model == "hashing"
    assert result.dimension == 256
    assert result.error is None
    assert result.recall["1"] == pytest.approx(1.0)
    assert result.mrr == pytest.approx(1.0)
    assert result.chunks_per_second > 0


def test_compare_embeddings_reports_failure_per_model() -> None:
    """Ein Modell, das sich nicht laden lässt, bricht den Lauf nicht ab."""
    results = compare_embeddings(_chunks(), DATASET, ["hashing", "gibt-es-nicht"], top_k=3)

    assert len(results) == 2
    assert results[0].error is None
    assert results[1].model == "gibt-es-nicht"
    assert results[1].error is not None
    assert results[1].dimension == 0
