"""Schnittstelle für Suchen."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from deutsches_ki.core.models import Chunk, SearchResult

__all__ = ["Retriever"]


@runtime_checkable
class Retriever(Protocol):
    """Eine Suche nimmt Chunks auf und findet sie zu einer Anfrage wieder."""

    def add(self, chunks: list[Chunk]) -> None:
        """Nimmt Chunks in den Index auf."""
        ...

    def search(self, query: str, top_k: int = 20) -> list[SearchResult]:
        """Findet die passendsten Chunks zu einer Anfrage."""
        ...
