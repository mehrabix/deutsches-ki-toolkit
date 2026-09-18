"""Integrationstest für den GLiNER-Detektor.

Läuft nur, wenn die Erweiterung ``gliner`` installiert ist:

    uv sync --extra dev --extra gliner
    uv run pytest tests/integration/test_gliner_detector.py -q

Beim ersten Lauf wird ein Modell geladen. Mit
``DEUTSCHES_KI_TEST_GLINER_MODEL`` lässt sich ein anderes wählen.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.pii import detect
from deutsches_ki.pii.detectors.gliner import GliNERDetector
from deutsches_ki.pii.detectors.regex import RegexDetector

pytestmark = [
    pytest.mark.integration,
    pytest.mark.optional,
    # Fremdbibliotheken warnen beim Laden von Modellen. Die Projektkonfiguration
    # macht aus Warnungen Fehler; hier werden nur fremde geduldet.
    pytest.mark.filterwarnings("ignore::UserWarning"),
    pytest.mark.filterwarnings("ignore::FutureWarning"),
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
]

pytest.importorskip("gliner", reason="Die Erweiterung 'gliner' ist nicht installiert.")

MODEL = os.environ.get("DEUTSCHES_KI_TEST_GLINER_MODEL", "urchade/gliner_multi-v2.1")

SENTENCE = "Max Mustermann arbeitet bei der Beispiel GmbH in Hamburg."


@pytest.fixture(scope="module")
def detector() -> GliNERDetector:
    try:
        return GliNERDetector(MODEL)
    except Exception as error:
        pytest.skip(f"Modell {MODEL} nicht ladbar: {error}")


def test_provider_can_be_given_an_engine() -> None:
    """Ohne Modell lässt sich ein fertiges Objekt einsetzen."""
    assert GliNERDetector(engine=object()).name is DetectorSource.GLINER


def test_detects_person(detector: GliNERDetector) -> None:
    types = {entity.type for entity in detector.detect(SENTENCE)}
    assert EntityType.PERSON in types


def test_detects_organisation(detector: GliNERDetector) -> None:
    types = {entity.type for entity in detector.detect(SENTENCE)}
    assert EntityType.ORGANISATION in types


def test_detects_location(detector: GliNERDetector) -> None:
    types = {entity.type for entity in detector.detect(SENTENCE)}
    assert EntityType.LOCATION in types


def test_spans_map_back_to_the_text(detector: GliNERDetector) -> None:
    for entity in detector.detect(SENTENCE):
        assert SENTENCE[entity.start : entity.end] == entity.text
        assert entity.source is DetectorSource.GLINER
        assert 0.0 <= entity.confidence <= 1.0


def test_empty_text_gives_nothing(detector: GliNERDetector) -> None:
    assert detector.detect("") == []


def test_combined_with_the_regex_detector(detector: GliNERDetector) -> None:
    text = "Max Mustermann, Beispiel GmbH, IBAN DE89 3704 0044 0532 0130 00."
    entities = detect(text, detectors=[RegexDetector(), detector])

    types = {entity.type for entity in entities}
    assert EntityType.PERSON in types
    assert EntityType.ORGANISATION in types
    assert EntityType.DE_IBAN in types


@pytest.mark.skipif(
    importlib.util.find_spec("spacy") is None,
    reason="Ohne spaCy ist der Vergleich nicht möglich.",
)
def test_finds_organisations_that_spacy_skips(detector: GliNERDetector) -> None:
    """Der Grund, warum es diesen Detektor gibt.

    Das deutsche spaCy-Modell lässt Organisationen bewusst aus, weil zu viele
    Fehlalarme entstehen. Genau diese Lücke füllt GLiNER.
    """
    spacy = pytest.importorskip("spacy")
    try:
        nlp = spacy.load("de_core_news_sm")
    except OSError:  # pragma: no cover - Modell nicht installiert
        pytest.skip("Das deutsche spaCy-Modell ist nicht installiert.")

    spacy_labels = {span.label_ for span in nlp(SENTENCE).ents}
    gliner_types = {entity.type for entity in detector.detect(SENTENCE)}

    assert "ORG" not in spacy_labels, "Erwartet: spaCy erkennt hier keine Organisation"
    assert EntityType.ORGANISATION in gliner_types, "GLiNER sollte sie finden"
