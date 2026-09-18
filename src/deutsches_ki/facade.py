"""Die Fassade ``GermanDocument``.

Sie führt die Kette zusammen: einlesen, sensible Stellen finden, anonymisieren,
zerlegen, suchen. Wer nur schnell von einem Dokument zu einer belegten Antwort
will, braucht nichts anderes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deutsches_ki.chunking import chunk_document
from deutsches_ki.config import Settings
from deutsches_ki.core.enums import AnonymizeMode, ChunkStrategy
from deutsches_ki.core.models import Answer, Chunk, Citation, Document, Entity, SearchResult
from deutsches_ki.documents.parse import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.pii import Pseudonymizer, anonymize, detect
from deutsches_ki.retrieval import InMemoryRetriever

__all__ = ["GermanDocument"]

_BRANCH_CONFIDENCE = {0: 0.5, 1: 0.7, 2: 0.9}


class GermanDocument:
    """Ein deutsches Dokument mit allem, was dazugehört."""

    def __init__(self, document: Document, *, settings: Settings | None = None) -> None:
        self.document = document
        self.settings = settings if settings is not None else Settings()
        self._session = Pseudonymizer()
        self._entities: list[Entity] | None = None
        self._chunks: list[Chunk] | None = None

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        settings: Settings | None = None,
        **kwargs: Any,
    ) -> GermanDocument:
        """Liest ein Dokument aus einer Datei."""
        return cls(parse(path, **kwargs), settings=settings)

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        title: str | None = None,
        settings: Settings | None = None,
        **metadata: Any,
    ) -> GermanDocument:
        """Baut ein Dokument aus reinem Text."""
        return cls(Document.from_text(text, title=title, **metadata), settings=settings)

    @property
    def text(self) -> str:
        """Der aktuelle Text (nach einer Anonymisierung der bereinigte)."""
        return self.document.content

    @property
    def title(self) -> str | None:
        """Der Titel des Dokuments."""
        return self.document.title

    def detect_pii(self, *, min_confidence: float | None = None) -> list[Entity]:
        """Findet sensible Stellen im Dokument."""
        threshold = min_confidence if min_confidence is not None else 0.0
        self._entities = detect(self.document.content, min_confidence=threshold)
        return self._entities

    def anonymize(
        self,
        mode: AnonymizeMode | str | None = None,
        *,
        key: str | None = None,
    ) -> str:
        """Ersetzt sensible Stellen und schreibt den Text fort.

        Die Erkennung läuft automatisch, wenn sie noch nicht gelaufen ist.
        """
        resolved = mode if mode is not None else self.settings.pii.mode
        result = anonymize(
            self.document.content,
            self._entities,
            resolved,
            key=key,
            session=self._session,
        )
        self.document.content = result.text
        self._entities = None
        self._chunks = None
        return result.text

    def chunk(
        self,
        *,
        strategy: ChunkStrategy | str | None = None,
        max_tokens: int | None = None,
        overlap: int | None = None,
    ) -> list[Chunk]:
        """Zerlegt das Dokument in Chunks."""
        chunks = chunk_document(
            self.document,
            strategy=strategy if strategy is not None else self.settings.chunking.strategy,
            max_tokens=max_tokens if max_tokens is not None else self.settings.chunking.max_tokens,
            overlap=overlap if overlap is not None else self.settings.chunking.overlap,
            document_type=self.settings.document_type,
        )
        self._chunks = chunks
        return chunks

    def build_retriever(self) -> InMemoryRetriever:
        """Baut eine Suche über die Chunks des Dokuments."""
        chunks = self._chunks if self._chunks is not None else self.chunk()
        embedder = get_embedder(
            self.settings.embeddings.provider,
            **(
                {"device": self.settings.embeddings.device}
                if self.settings.embeddings.device
                else {}
            ),
        )
        retriever = InMemoryRetriever(
            embedder,
            vector=self.settings.retrieval.vector,
            lexical=self.settings.retrieval.lexical,
            fusion=self.settings.retrieval.fusion,
        )
        retriever.add(chunks)
        return retriever

    def search(self, question: str, *, top_k: int | None = None) -> Answer:
        """Beantwortet eine Frage aus dem Dokument, mit Quellenangabe.

        Ohne Sprachmodell entsteht eine belegte Auswahl: die Antwort ist der
        bestpassende Abschnitt, dazu die Fundstellen.
        """
        retriever = self.build_retriever()
        limit = top_k if top_k is not None else self.settings.retrieval.top_k
        results = retriever.search(question, top_k=limit)
        return self._to_answer(results)

    def _to_answer(self, results: list[SearchResult]) -> Answer:
        citations = [
            Citation(
                document=self.document.source or self.document.title or "",
                page=result.chunk.metadata.get("page"),
                section=result.chunk.section,
                chunk_id=result.chunk.id,
                score=result.score,
            )
            for result in results
        ]
        if not results:
            return Answer(answer="", citations=[], retrieved_chunks=[], confidence=0.0)

        top = results[0]
        matched = sum(1 for rank in (top.vector_rank, top.lexical_rank) if rank is not None)
        return Answer(
            answer=top.chunk.content,
            citations=citations,
            retrieved_chunks=[result.chunk for result in results],
            confidence=_BRANCH_CONFIDENCE.get(matched, 0.5),
            metadata={"question_chunks": len(results)},
        )
