"""Golden-Datensätze: deutsche Fälle als JSON statt als Python-Code.

Jeder Fall nennt eine Prüfung, eine Eingabe und die Erwartung. Neue Fälle
lassen sich ergänzen, ohne Testcode anzufassen; wer einen Fehler findet, hängt
einen Eintrag an die passende Datei.

Format:

    {
      "name": "german_compounds",
      "cases": [
        {"input": "Versicherungsbeitrag",
         "check": "compound_parts",
         "expected": ["versicherung", "beitrag"]}
      ]
    }
"""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from deutsches_ki.chunking import chunk_document
from deutsches_ki.classification import classify_document
from deutsches_ki.documents import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.pii import anonymize, detect
from deutsches_ki.retrieval import InMemoryRetriever
from deutsches_ki.text import (
    analyze_compound,
    normalize_german,
    search_tokens,
    split_sentences,
)

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parents[2] / "datasets" / "fixtures"
GOLDEN_FILES = sorted(HERE.glob("german_*.json"))


@lru_cache(maxsize=1)
def _retriever() -> InMemoryRetriever:
    """Die Testdateien, einmal indiziert."""
    chunks = []
    for file in sorted(FIXTURES.iterdir()):
        if file.suffix.lower() in {".md", ".txt"}:
            chunks.extend(chunk_document(parse(file), max_tokens=64))
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(chunks)
    return retriever


def _top_result(question: str) -> Any:
    results = _retriever().search(question, top_k=5)
    assert results, f"Keine Treffer für: {question}"
    return results[0].chunk


def _compound_parts(text: str) -> list[str]:
    return [part.lower() for part in analyze_compound(text).parts]


def _pii_types(text: str) -> list[str]:
    return sorted({entity.type.value for entity in detect(text)})


def _pii_texts(text: str) -> list[str]:
    return [entity.text for entity in detect(text)]


def _missing_tokens(text: str) -> list[str]:
    present = set(search_tokens(text))
    return sorted(term for term in text.split() if term not in present)


CHECKS: dict[str, Callable[[str], Any]] = {
    "compound_parts": _compound_parts,
    "pii_types": _pii_types,
    "pii_texts": _pii_texts,
    "sentence_count": lambda text: len(split_sentences(text)),
    "normalize_search": lambda text: normalize_german(text, mode="search"),
    "normalize_display": lambda text: normalize_german(text, mode="display"),
    "classify_type": lambda text: classify_document(text).document_type.value,
    "anonymize_redact": lambda text: anonymize(text, mode="redact").text,
    "search_tokens_contains": lambda text: sorted(set(search_tokens(text))),
    "search_top_section": lambda text: _top_result(text).section,
    "search_finds_text": lambda text: _top_result(text).content,
}


def _all_cases() -> list[Any]:
    params: list[Any] = []
    for path in GOLDEN_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for index, case in enumerate(data["cases"]):
            params.append(pytest.param(case, id=f"{path.stem}-{index:02d}"))
    return params


def test_golden_files_exist() -> None:
    assert GOLDEN_FILES, "Es sollten Golden-Datensätze vorhanden sein."


def test_every_check_is_known() -> None:
    for path in GOLDEN_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "name" in data
        for case in data["cases"]:
            assert case["check"] in CHECKS, f"{path.name}: unbekannte Prüfung {case['check']}"
            assert "input" in case
            assert "expected" in case


@pytest.mark.parametrize("case", _all_cases())
def test_golden_case(case: dict[str, Any]) -> None:
    check = CHECKS[case["check"]]
    actual = check(case["input"])

    if case["check"] == "search_tokens_contains":
        missing = sorted(set(case["expected"]) - set(actual))
        assert not missing, f"Fehlende Such-Token: {missing}"
        return

    if case["check"] == "search_finds_text":
        assert case["expected"] in actual, f"{case['expected']} nicht gefunden in: {actual[:120]}"
        return

    assert actual == case["expected"], f"Erwartet {case['expected']!r}, bekommen {actual!r}"
