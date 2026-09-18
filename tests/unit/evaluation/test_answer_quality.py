"""Tests für die Bewertung der Antwortqualität."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from deutsches_ki.evaluation import (
    answer_relevance,
    citation_coverage,
    groundedness,
    judge_answer,
)
from deutsches_ki.providers.base import ChatMessage

CONTEXT = (
    "Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig. "
    "Bei verspäteter Zahlung fallen Verzugszinsen an."
)


class _FakeLlm:
    name = "fake"

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.messages: list[ChatMessage] = []

    def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        self.messages = list(messages)
        return self.answer


def test_groundedness_high_for_supported_answer() -> None:
    answer = "Die Zahlung ist innerhalb von 30 Tagen fällig."
    assert groundedness(answer, [CONTEXT]) > 0.8


def test_groundedness_low_for_invented_answer() -> None:
    answer = "Die Kündigungsfrist beträgt fünfzehn Jahre bei Nachtarbeit."
    assert groundedness(answer, [CONTEXT]) < 0.5


def test_groundedness_ignores_stopwords() -> None:
    """Ohne Stoppwort-Filter wäre jede deutsche Antwort zu neunzig Prozent gedeckt."""
    answer = "Der die das und oder aber ist sind war werden."
    assert groundedness(answer, [CONTEXT]) < 0.4


def test_groundedness_without_context_or_answer() -> None:
    assert groundedness("", [CONTEXT]) == 0.0
    assert groundedness("Eine Antwort.", []) == 0.0


def test_answer_relevance() -> None:
    assert (
        answer_relevance("Wie lange ist die Zahlungsfrist?", "Die Zahlungsfrist beträgt 30 Tage.")
        > 0.4
    )
    assert answer_relevance("Wie lange ist die Zahlungsfrist?", "Das Wetter ist schön.") < 0.3


def test_citation_coverage_counts_sentences_with_markers() -> None:
    answer = "Die Frist beträgt 30 Tage [1]. Verzugszinsen fallen an [2]. Ohne Beleg."
    assert citation_coverage(answer) == pytest.approx(2 / 3)


def test_citation_coverage_without_markers() -> None:
    assert citation_coverage("Ein Satz ohne Quellenangabe.") == 0.0


def test_citation_coverage_on_empty_answer() -> None:
    assert citation_coverage("") == 0.0


def test_judge_parses_json() -> None:
    llm = _FakeLlm('{"faithfulness": 0.9, "relevance": 0.8, "reason": "gedeckt"}')
    result = judge_answer("Wie lange ist die Zahlungsfrist?", "30 Tage [1].", [CONTEXT], llm)

    assert result.faithfulness == pytest.approx(0.9)
    assert result.relevance == pytest.approx(0.8)
    assert result.reason == "gedeckt"
    assert "Quellen" in llm.messages[-1].content
    assert "Antwort:" in llm.messages[-1].content


def test_judge_accepts_json_inside_prose() -> None:
    llm = _FakeLlm('Hier das Urteil: {"faithfulness": 1, "relevance": 1} — fertig.')
    result = judge_answer("Frage?", "Antwort.", [CONTEXT], llm)
    assert result.faithfulness == 1.0


def test_judge_rejects_answer_without_json() -> None:
    llm = _FakeLlm("Die Antwort sieht gut aus.")
    with pytest.raises(ValueError, match="JSON"):
        judge_answer("Frage?", "Antwort.", [CONTEXT], llm)


def test_judge_rejects_out_of_range_values() -> None:
    llm = _FakeLlm('{"faithfulness": 2.0, "relevance": 0.5}')
    with pytest.raises(ValueError):
        judge_answer("Frage?", "Antwort.", [CONTEXT], llm)
