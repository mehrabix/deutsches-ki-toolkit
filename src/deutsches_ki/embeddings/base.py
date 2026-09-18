"""Schnittstelle für Embedding-Anbieter."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["EmbeddingProvider"]


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Ein Anbieter wandelt Texte in Vektoren um."""

    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Vektoren für Dokumente oder Chunks."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Vektor für eine Suchanfrage."""
        ...
