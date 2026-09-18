"""Embeddings über sentence-transformers, zum Beispiel BGE-M3 (optional)."""

from __future__ import annotations

from typing import Any

from deutsches_ki.errors import MissingDependencyError

__all__ = ["SentenceTransformerEmbedder"]


class SentenceTransformerEmbedder:
    """Bindet ein Satz-Embedding-Modell an.

    Ausgangspunkt ist BGE-M3: mehrsprachig, 1024 Dimensionen, lange Eingaben.
    Das Modell ist austauschbar und nicht fest verdrahtet.
    """

    name = "sentence-transformers"

    def __init__(
        self,
        model: str = "BAAI/bge-m3",
        *,
        device: str | None = None,
        engine: Any | None = None,
    ) -> None:
        self.model_name = model
        if engine is not None:
            self._model: Any = engine
        else:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
                raise MissingDependencyError(
                    "Für Embeddings über sentence-transformers wird die Erweiterung "
                    "'embeddings' benötigt. Installation: "
                    'pip install "deutsches-ki-toolkit[embeddings]"'
                ) from exc
            self._model = SentenceTransformer(model, device=device)

        dimension = self._model.get_sentence_embedding_dimension()
        self.dimension = int(dimension) if dimension else 0

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [[float(value) for value in vector] for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        vectors = self._model.encode([text], normalize_embeddings=True)
        return [float(value) for value in vectors[0]]
