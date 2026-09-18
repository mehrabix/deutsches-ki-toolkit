"""Die RAG-Engine.

Ohne Sprachmodell entsteht eine belegte Auswahl: die Antwort ist der
bestpassende Abschnitt, dazu die Fundstellen. Mit Sprachmodell wird daraus eine
formulierte Antwort, deren Quellenangaben geprüft werden.
"""

from __future__ import annotations

from collections.abc import Sequence

from deutsches_ki.core.models import Answer, Chunk, Citation, SearchResult
from deutsches_ki.providers.base import ChatProvider
from deutsches_ki.rag.citations import validate_citations
from deutsches_ki.rag.prompt import build_messages
from deutsches_ki.reranking.base import Reranker
from deutsches_ki.retrieval.base import Retriever

__all__ = ["DeutschRAG"]

_BRANCH_CONFIDENCE = {0: 0.5, 1: 0.7, 2: 0.9}


def _confidence(results: Sequence[SearchResult]) -> float:
    """Grobe Zuversicht: Wurde der beste Treffer in beiden Zweigen gefunden?"""
    if not results:
        return 0.0
    top = results[0]
    matched = sum(1 for rank in (top.vector_rank, top.lexical_rank) if rank is not None)
    return _BRANCH_CONFIDENCE.get(matched, 0.5)


def _document_name(chunk: Chunk) -> str:
    for key in ("document", "source"):
        value = chunk.metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return chunk.document_id


class DeutschRAG:
    """Beantwortet Fragen aus einem Bestand, mit Quellenangabe."""

    def __init__(
        self,
        retriever: Retriever,
        *,
        reranker: Reranker | None = None,
        llm: ChatProvider | None = None,
        candidates: int = 20,
        top_k: int = 5,
    ) -> None:
        if top_k <= 0:
            raise ValueError("top_k muss größer als 0 sein.")
        if candidates < top_k:
            raise ValueError("candidates darf nicht kleiner als top_k sein.")
        self._retriever = retriever
        self._reranker = reranker
        self._llm = llm
        self._candidates = candidates
        self._top_k = top_k

    def ask(self, question: str, *, top_k: int | None = None) -> Answer:
        """Beantwortet eine Frage und liefert die Fundstellen mit."""
        limit = top_k if top_k is not None else self._top_k
        results = self._retriever.search(question, top_k=max(self._candidates, limit))

        if self._reranker is not None:
            results = self._reranker.rerank(question, results, top_k=limit)
        else:
            results = results[:limit]

        if not results:
            return Answer(answer="", citations=[], retrieved_chunks=[], confidence=0.0)

        citations = [
            Citation(
                document=_document_name(result.chunk),
                page=result.chunk.metadata.get("page"),
                section=result.chunk.section,
                chunk_id=result.chunk.id,
                score=result.score,
            )
            for result in results
        ]
        chunks = [result.chunk for result in results]

        if self._llm is None:
            return Answer(
                answer=results[0].chunk.content,
                citations=citations,
                retrieved_chunks=chunks,
                confidence=_confidence(results),
                metadata={"mode": "extractive"},
            )

        sources = list(enumerate(chunks, start=1))
        text = self._llm.generate(build_messages(question, sources))
        report = validate_citations(text, len(chunks))
        return Answer(
            answer=text,
            citations=citations,
            retrieved_chunks=chunks,
            confidence=_confidence(results),
            metadata={"mode": "llm", "citations": report.model_dump(mode="json")},
        )
