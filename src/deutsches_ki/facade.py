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
from deutsches_ki.core.models import Answer, Chunk, Document, Entity
from deutsches_ki.documents.parse import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.pii import Pseudonymizer, anonymize, detect
from deutsches_ki.providers.base import ChatProvider
from deutsches_ki.rag import DeutschRAG
from deutsches_ki.reranking import Reranker, get_reranker
from deutsches_ki.retrieval import InMemoryRetriever

__all__ = ["GermanDocument"]


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

    def build_reranker(self) -> Reranker | None:
        """Baut den Reranker, sofern er eingeschaltet ist."""
        if not self.settings.reranking.enabled:
            return None
        return get_reranker(self.settings.reranking.provider)

    def build_rag(self, *, llm: ChatProvider | None = None) -> DeutschRAG:
        """Baut die RAG-Engine über diesem Dokument."""
        return DeutschRAG(
            self.build_retriever(),
            reranker=self.build_reranker(),
            llm=llm,
            candidates=self.settings.retrieval.top_k,
            top_k=min(self.settings.reranking.top_k, self.settings.retrieval.top_k),
        )

    def search(
        self,
        question: str,
        *,
        top_k: int | None = None,
        llm: ChatProvider | None = None,
    ) -> Answer:
        """Beantwortet eine Frage aus dem Dokument, mit Quellenangabe.

        Ohne Sprachmodell entsteht eine belegte Auswahl: die Antwort ist der
        bestpassende Abschnitt, dazu die Fundstellen. Mit ``llm`` wird daraus
        eine formulierte Antwort, deren Quellenangaben geprüft werden.
        """
        limit = top_k if top_k is not None else self.settings.retrieval.top_k
        rag = self.build_rag(llm=llm)
        return rag.ask(question, top_k=limit)
