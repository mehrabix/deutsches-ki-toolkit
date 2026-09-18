"""Bewertung der Antwortqualität.

Zwei Wege, die sich ergänzen.

**Deterministisch.** Überdeckung und Quellenabdeckung lassen sich ohne Modell
berechnen. Sie schwanken nicht und lassen sich in der CI prüfen. Was sie nicht
können: erkennen, ob eine Aussage inhaltlich falsch ist, obwohl sie dieselben
Wörter benutzt.

**Mit Sprachmodell.** Ein Modell bewertet Treue und Relevanz. Das ist
aussagekräftiger, aber schwankend und nicht reproduzierbar. Deshalb nur als
Ergänzung, nie als einzige Grundlage.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.providers.base import ChatMessage, ChatProvider
from deutsches_ki.rag.citations import extract_markers
from deutsches_ki.text.stopwords import content_terms

__all__ = [
    "JUDGE_PROMPT",
    "JudgeResult",
    "answer_relevance",
    "citation_coverage",
    "groundedness",
    "judge_answer",
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)

JUDGE_PROMPT = (
    "Du prüfst die Antwort eines Sprachmodells gegen die mitgelieferten Quellen. "
    "Bewerte zwei Dinge: ob jede Aussage der Antwort durch die Quellen gedeckt ist "
    "(Treue), und ob die Antwort die Frage beantwortet (Relevanz). "
    "Antworte ausschließlich mit einem JSON-Objekt der Form "
    '{"faithfulness": 0.0, "relevance": 0.0, "reason": "kurze Begründung"}. '
    "Die Werte liegen zwischen 0 und 1."
)


class JudgeResult(BaseModel):
    """Urteil eines Sprachmodells über eine Antwort."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    faithfulness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    reason: str | None = None


def groundedness(answer: str, contexts: Sequence[str]) -> float:
    """Anteil der Antwortwörter, die in den Quellen vorkommen.

    Ein grober Wert: Er erkennt erfundene Aussagen, die kein Wort aus den
    Quellen benutzen, aber nicht eine falsche Aussage aus denselben Wörtern.
    """
    answer_terms = set(content_terms(answer))
    if not answer_terms:
        return 0.0
    context_terms: set[str] = set()
    for context in contexts:
        context_terms.update(content_terms(context))
    if not context_terms:
        return 0.0
    return len(answer_terms & context_terms) / len(answer_terms)


def answer_relevance(question: str, answer: str) -> float:
    """Anteil der Fragewörter, die in der Antwort wieder auftauchen."""
    question_terms = set(content_terms(question))
    if not question_terms:
        return 0.0
    answer_terms = set(content_terms(answer))
    return len(question_terms & answer_terms) / len(question_terms)


def citation_coverage(answer: str) -> float:
    """Anteil der Sätze, die eine Quellenangabe tragen."""
    sentences = [part for part in _SENTENCE_SPLIT.split(answer.strip()) if part.strip()]
    if not sentences:
        return 0.0
    with_marker = sum(1 for sentence in sentences if extract_markers(sentence))
    return with_marker / len(sentences)


def judge_answer(
    question: str,
    answer: str,
    contexts: Sequence[str],
    llm: ChatProvider,
) -> JudgeResult:
    """Lässt ein Sprachmodell Treue und Relevanz bewerten.

    Antwortet das Modell nicht im erwarteten Format, wird das als Fehler
    gemeldet statt stillschweigend als gute Bewertung gewertet.
    """
    sources = "\n\n".join(contexts)
    user = f"Quellen:\n\n{sources}\n\nFrage: {question.strip()}\n\nAntwort: {answer.strip()}"
    text = llm.generate(
        [
            ChatMessage(role="system", content=JUDGE_PROMPT),
            ChatMessage(role="user", content=user),
        ]
    )

    match = _JSON_BLOCK.search(text)
    if match is None:
        raise ValueError("Das Urteil enthielt kein JSON-Objekt.")

    try:
        payload = json.loads(match.group())
    except json.JSONDecodeError as error:
        raise ValueError("Das Urteil war kein gültiges JSON.") from error
    if not isinstance(payload, dict):
        raise ValueError("Das Urteil war kein JSON-Objekt.")

    return JudgeResult.model_validate(payload)
