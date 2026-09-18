"""Integrationstest für den spaCy-Detektor.

Läuft nur, wenn die Erweiterung ``nlp`` und ein deutsches Modell installiert
sind:

    uv sync --extra dev --extra nlp
    uv run python -m spacy download de_core_news_sm
    uv run pytest tests/integration/test_spacy_detector.py -q
"""

from __future__ import annotations

import pytest

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.pii import detect
from deutsches_ki.pii.detectors.regex import RegexDetector
from deutsches_ki.pii.detectors.spacy import SpaCyDetector

pytestmark = [pytest.mark.integration, pytest.mark.optional]

spacy = pytest.importorskip("spacy", reason="Die Erweiterung 'nlp' ist nicht installiert.")

MODEL = "de_core_news_sm"

SENTENCE = "Max Mustermann arbeitet bei der Beispiel GmbH in Hamburg."


@pytest.fixture(scope="module")
def detector() -> SpaCyDetector:
    try:
        return SpaCyDetector(MODEL)
    except OSError:  # pragma: no cover - Modell nicht geladen
        pytest.skip(f"Das Modell {MODEL} ist nicht installiert.")


def test_detects_person(detector: SpaCyDetector) -> None:
    entities = detector.detect(SENTENCE)
    types = {entity.type for entity in entities}
    assert EntityType.PERSON in types


def test_detects_location(detector: SpaCyDetector) -> None:
    entities = detector.detect(SENTENCE)
    types = {entity.type for entity in entities}
    assert EntityType.LOCATION in types


def test_spans_map_back_to_text(detector: SpaCyDetector) -> None:
    for entity in detector.detect(SENTENCE):
        assert SENTENCE[entity.start : entity.end] == entity.text
        assert entity.source is DetectorSource.SPACY


def test_empty_text_gives_nothing(detector: SpaCyDetector) -> None:
    assert detector.detect("") == []


def test_combined_with_regex_detector(detector: SpaCyDetector) -> None:
    """Beide Detektoren zusammen: Namen und deutsche Kennungen."""
    text = "Max Mustermann, IBAN DE89 3704 0044 0532 0130 00."
    entities = detect(text, detectors=[RegexDetector(), detector])
    types = {entity.type for entity in entities}
    assert EntityType.PERSON in types
    assert EntityType.DE_IBAN in types


def test_regex_wins_on_overlap(detector: SpaCyDetector) -> None:
    """Strukturierte Kennungen schlagen die Namenserkennung."""
    text = "Kennung DE89 3704 0044 0532 0130 00 gehört dazu."
    entities = detect(text, detectors=[detector, RegexDetector()])
    iban = next(entity for entity in entities if entity.type is EntityType.DE_IBAN)
    assert iban.source is DetectorSource.REGEX
