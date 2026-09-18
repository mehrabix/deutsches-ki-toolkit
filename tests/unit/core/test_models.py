"""Tests für die Core-Datenmodelle."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deutsches_ki.core.enums import (
    AnonymizeMode,
    ChunkStrategy,
    DetectorSource,
    EntityType,
    Language,
)
from deutsches_ki.core.models import (
    Answer,
    Chunk,
    Citation,
    Document,
    Entity,
    SearchResult,
    Section,
    Sentence,
)


def test_sentence_span() -> None:
    sentence = Sentence(text="Hallo Welt.", start=0, end=11)
    assert sentence.end - sentence.start == 11


def test_sentence_rejects_negative_offset() -> None:
    with pytest.raises(ValidationError):
        Sentence(text="x", start=-1, end=1)


def test_entity_confidence_bounds() -> None:
    entity = Entity(
        type=EntityType.DE_IBAN,
        text="DE89 3704 0044 0532 0130 00",
        start=0,
        end=27,
        confidence=0.99,
        source=DetectorSource.REGEX,
    )
    assert entity.length == 27
    with pytest.raises(ValidationError):
        Entity(type=EntityType.PERSON, text="x", start=0, end=1, confidence=1.5)


def test_entity_is_frozen() -> None:
    entity = Entity(type=EntityType.PERSON, text="Max", start=0, end=3)
    with pytest.raises(ValidationError):
        entity.start = 5


def test_section_tree_iteration() -> None:
    child = Section(title="Zahlungsbedingungen", level=2, content="30 Tage")
    root = Section(title="Vertrag", level=1, content="", children=[child])
    document = Document(content="...", sections=[root])

    titles = [section.title for section in document.iter_sections()]
    assert titles == ["Vertrag", "Zahlungsbedingungen"]


def test_document_from_text() -> None:
    document = Document.from_text("Die Frist beträgt 30 Tage.", title="Vertrag")
    assert document.title == "Vertrag"
    assert document.language is Language.DE
    assert document.content.startswith("Die Frist")


def test_document_round_trip() -> None:
    original = Document.from_text("Hallo", title="T")
    restored = Document.model_validate(original.model_dump())
    assert restored == original


def test_document_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Document.model_validate({"content": "x", "unknown": 1})


def test_chunk_section_property() -> None:
    chunk = Chunk(content="x", metadata={"section": "Zahlungsbedingungen"})
    assert chunk.section == "Zahlungsbedingungen"
    assert Chunk(content="x").section is None


def test_search_result_ranks() -> None:
    result = SearchResult(
        chunk=Chunk(content="x"),
        score=0.5,
        vector_rank=1,
        lexical_rank=None,
    )
    assert result.vector_rank == 1
    assert result.lexical_rank is None


def test_answer_carries_citations() -> None:
    answer = Answer(
        answer="30 Tage.",
        citations=[Citation(document="Vertrag.pdf", page=12, section="§ 4")],
        retrieved_chunks=[Chunk(content="30 Tage")],
        confidence=0.8,
    )
    assert answer.citations[0].page == 12


def test_enums_are_string_valued() -> None:
    assert Language.DE == "de"
    assert AnonymizeMode.PSEUDONYMIZE.value == "pseudonymize"
    assert ChunkStrategy.STRUCTURAL.value == "structural"
    assert EntityType.DE_TAX_ID.value == "DE_TAX_ID"
