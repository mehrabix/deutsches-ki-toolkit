"""Integrationstest für den Presidio-Detektor.

Läuft nur, wenn die Erweiterungen ``presidio`` und ``nlp`` installiert sind:

    uv sync --extra dev --extra nlp --extra presidio
    uv run python -m spacy download de_core_news_sm
    uv run pytest tests/integration/test_presidio_detector.py -q
"""

from __future__ import annotations

import pytest

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.pii import detect
from deutsches_ki.pii.detectors.presidio import PresidioDetector
from deutsches_ki.pii.detectors.regex import RegexDetector

pytestmark = [pytest.mark.integration, pytest.mark.optional]

pytest.importorskip("presidio_analyzer", reason="Die Erweiterung 'presidio' fehlt.")
spacy = pytest.importorskip("spacy", reason="Die Erweiterung 'nlp' fehlt.")

MODEL = "de_core_news_sm"

TEXT = "Max Mustermann erreicht man unter max.mustermann@example.de."


@pytest.fixture(scope="module")
def detector() -> PresidioDetector:
    try:
        return PresidioDetector(MODEL)
    except OSError:  # pragma: no cover - Modell nicht geladen
        pytest.skip(f"Das Modell {MODEL} ist nicht installiert.")


def test_detects_email(detector: PresidioDetector) -> None:
    entities = detector.detect(TEXT)
    types = {entity.type for entity in entities}
    assert EntityType.EMAIL in types


def test_spans_map_back_to_text(detector: PresidioDetector) -> None:
    for entity in detector.detect(TEXT):
        assert TEXT[entity.start : entity.end] == entity.text
        assert entity.source is DetectorSource.PRESIDIO
        assert 0.0 <= entity.confidence <= 1.0


def test_confidence_is_reported(detector: PresidioDetector) -> None:
    entities = detector.detect(TEXT)
    assert entities
    assert all(entity.confidence > 0.0 for entity in entities)


def test_empty_text_gives_nothing(detector: PresidioDetector) -> None:
    assert detector.detect("") == []


def test_presidio_does_not_know_german_tax_numbers() -> None:
    """Der Grund, warum es die eigenen Muster gibt.

    Presidio bringt vor allem US-Muster mit. Eine deutsche Steuernummer und
    eine Handelsregisternummer erkennt es nicht; das Regex-Detektor schon.
    """
    text = "Steuernummer: 12/345/67890, eingetragen unter HRB 12345."

    presidio_only = detect(text, detectors=[_presidio()])
    with_regex = detect(text, detectors=[_presidio(), RegexDetector()])

    assert not any(
        entity.type in {EntityType.DE_TAX_NUMBER, EntityType.DE_HR_NUMBER}
        for entity in presidio_only
    )
    assert any(entity.type is EntityType.DE_HR_NUMBER for entity in with_regex)


def _presidio() -> PresidioDetector:
    try:
        return PresidioDetector(MODEL)
    except OSError:  # pragma: no cover
        pytest.skip(f"Das Modell {MODEL} ist nicht installiert.")
