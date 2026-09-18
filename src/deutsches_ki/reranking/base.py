"""Schnittstelle für Reranker.

Die Suche holt großzügig Kandidaten, der Reranker sortiert sie neu. Tausende
Dokumente zu reranken ist weder sinnvoll noch schnell, deshalb bleibt die
Kandidatenmenge begrenzt.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from deutsches_ki.core.models import SearchResult

__all__ = ["Reranker"]


@runtime_checkable
class Reranker(Protocol):
    """Sortiert Suchergebnisse zu einer Anfrage neu."""

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Gibt die Ergebnisse in neuer Reihenfolge zurück."""
        ...
