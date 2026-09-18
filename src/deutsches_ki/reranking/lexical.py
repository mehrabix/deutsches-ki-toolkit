"""Reranking über Wortüberdeckung, ohne Modell.

Dieser Reranker braucht kein Netz und kein Modell. Er läuft in den Tests und
ist der Vergleichsmaßstab für den Cross-Encoder: Wenn ein aufwendiges Modell
diesen einfachen Ansatz nicht schlägt, gehört das in den Benchmark.

Gezählt werden Such-Token, also bereits gefaltete Wörter mit zerlegten
Komposita. Ein Abschnittstitel zählt mit, weil er bei deutschen Dokumenten das
Thema trägt.
"""

from __future__ import annotations

from deutsches_ki.core.models import SearchResult
from deutsches_ki.text.tokens import search_tokens

__all__ = ["LexicalReranker"]

_PHRASE_BONUS = 0.5


class LexicalReranker:
    """Bewertet Treffer nach übereinstimmenden Wörtern und wörtlichem Vorkommen."""

    name = "lexical"

    def __init__(self, *, phrase_bonus: float = _PHRASE_BONUS) -> None:
        self._phrase_bonus = phrase_bonus

    def _score(self, query: str, query_terms: set[str], result: SearchResult) -> float:
        text = result.chunk.index_text
        document_terms = set(search_tokens(text))
        if not query_terms:
            return 0.0
        overlap = len(query_terms & document_terms) / len(query_terms)
        phrase = query.strip().lower()
        bonus = self._phrase_bonus if phrase and phrase in text.lower() else 0.0
        return overlap + bonus

    def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Sortiert die Treffer nach Überdeckung, stabil bei Gleichstand."""
        query_terms = set(search_tokens(query))
        scored = [
            (self._score(query, query_terms, result), index, result)
            for index, result in enumerate(results)
        ]
        # Der Index als zweites Kriterium hält die Reihenfolge bei Gleichstand
        # stabil, damit das Ergebnis reproduzierbar bleibt.
        scored.sort(key=lambda item: (-item[0], item[1]))

        reordered = [result.model_copy(update={"score": score}) for score, _, result in scored]
        if top_k is not None:
            return reordered[: max(top_k, 0)]
        return reordered
