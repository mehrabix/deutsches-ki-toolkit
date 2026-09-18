"""Tests für die RAG-Engine."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from deutsches_ki.core.models import Chunk
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.providers.base import ChatMessage
from deutsches_ki.rag import DeutschRAG, build_messages
from deutsches_ki.reranking import LexicalReranker
from deutsches_ki.retrieval import InMemoryRetriever


class _FakeLlm:
    """Ein Sprachmodell, das eine feste Antwort gibt und die Frage merkt."""

    name = "fake"

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.messages: list[ChatMessage] = []

    def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        self.messages = list(messages)
        return self.answer


CHUNKS = [
    Chunk(
        content="Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.",
        metadata={"section": "§ 4 Zahlungsbedingungen", "document": "vertrag.md"},
    ),
    Chunk(
        content="Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
        metadata={"section": "§ 7 Kündigung", "document": "vertrag.md"},
    ),
]


def _retriever() -> InMemoryRetriever:
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(CHUNKS)
    return retriever


def test_extractive_answer_without_llm() -> None:
    rag = DeutschRAG(_retriever())
    answer = rag.ask("Wie lange ist die Zahlungsfrist?")
    assert "30 Tagen" in answer.answer
    assert answer.metadata["mode"] == "extractive"
    assert answer.citations


def test_citations_carry_document_and_section() -> None:
    rag = DeutschRAG(_retriever())
    answer = rag.ask("Wie lange ist die Zahlungsfrist?")
    top = answer.citations[0]
    assert top.document == "vertrag.md"
    assert top.section == "§ 4 Zahlungsbedingungen"
    assert top.chunk_id


def test_llm_answer_is_citation_checked() -> None:
    llm = _FakeLlm("Die Zahlungsfrist beträgt 30 Tage [1].")
    rag = DeutschRAG(_retriever(), llm=llm)

    answer = rag.ask("Wie lange ist die Zahlungsfrist?")

    assert answer.metadata["mode"] == "llm"
    assert answer.answer.startswith("Die Zahlungsfrist")
    report = answer.metadata["citations"]
    assert report["valid"] == [1]
    assert report["unknown"] == []


def test_invented_citation_is_reported() -> None:
    llm = _FakeLlm("Laut [9] gilt etwas anderes.")
    rag = DeutschRAG(_retriever(), llm=llm)

    answer = rag.ask("Wie lange ist die Zahlungsfrist?")
    assert answer.metadata["citations"]["unknown"] == [9]


def test_prompt_contains_numbered_sources() -> None:
    llm = _FakeLlm("Antwort [1].")
    rag = DeutschRAG(_retriever(), llm=llm)
    rag.ask("Wie lange ist die Zahlungsfrist?")

    user_message = llm.messages[-1].content
    assert "[1]" in user_message
    assert "§ 4 Zahlungsbedingungen" in user_message
    assert "Frage:" in user_message
    assert llm.messages[0].role == "system"
    assert "erfinde nichts" in llm.messages[0].content.lower()


def test_empty_result_gives_empty_answer() -> None:
    rag = DeutschRAG(_retriever())
    answer = rag.ask("")
    assert answer.answer == ""
    assert answer.confidence == 0.0


def test_reranker_is_applied() -> None:
    rag = DeutschRAG(_retriever(), reranker=LexicalReranker(), candidates=2, top_k=1)
    answer = rag.ask("Wie lange ist die Zahlungsfrist?")
    assert answer.citations[0].section == "§ 4 Zahlungsbedingungen"
    assert len(answer.retrieved_chunks) == 1


def test_candidates_must_cover_top_k() -> None:
    with pytest.raises(ValueError, match="candidates"):
        DeutschRAG(_retriever(), candidates=2, top_k=5)


def test_top_k_must_be_positive() -> None:
    with pytest.raises(ValueError, match="top_k"):
        DeutschRAG(_retriever(), top_k=0)


def test_build_messages_formats_sources() -> None:
    messages = build_messages("Frage?", [(1, CHUNKS[0])])
    assert len(messages) == 2
    assert "[1] § 4 Zahlungsbedingungen" in messages[1].content
    assert "30 Tagen" in messages[1].content
