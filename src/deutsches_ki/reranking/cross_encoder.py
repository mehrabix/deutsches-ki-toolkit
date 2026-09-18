"""Reranking über ein Cross-Encoder-Modell (optional)."""

from __future__ import annotations

from typing import Any

from deutsches_ki.core.models import SearchResult
from deutsches_ki.errors import MissingDependencyError

__all__ = ["CrossEncoderReranker"]


class CrossEncoderReranker:
    """Bewertet Frage und Treffer gemeinsam mit einem Cross-Encoder.

    Das ist genauer als ein Embedding-Vergleich, aber deutlich langsamer.
    Deshalb nur auf der Kandidatenmenge einsetzen, nicht auf dem ganzen Bestand.
    """

    name = "cross-encoder"

    def __init__(
        self,
        model: str = "BAAI/bge-reranker-v2-m3",
        *,
        device: str | None = None,
        engine: Any | None = None,
    ) -> None:
        self.model_name = model
        if engine is not None:
            self._model: Any = engine
            return
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
            raise MissingDependencyError(
                "Für das Reranking über einen Cross-Encoder wird die Erweiterung "
                "'embeddings' benötigt. Installation: "
                'pip install "deutsches-ki-toolkit[embeddings]"'
            ) from exc
        self._model = CrossEncoder(model, device=device)

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Bewertet alle Paare und sortiert absteigend."""
        if not results:
            return []

        pairs = [(query, result.chunk.index_text) for result in results]
        scores = [float(score) for score in self._model.predict(pairs)]

        scored = list(zip(scores, range(len(results)), results, strict=True))
        scored.sort(key=lambda item: (-item[0], item[1]))

        reordered = [result.model_copy(update={"score": score}) for score, _, result in scored]
        if top_k is not None:
            return reordered[: max(top_k, 0)]
        return reordered
