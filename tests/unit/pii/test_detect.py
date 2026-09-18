"""Tests für das Zusammenführen der Detektoren."""

from __future__ import annotations

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.core.models import Entity
from deutsches_ki.pii import detect, resolve_entities


def _entity(start: int, end: int, *, source: DetectorSource, confidence: float) -> Entity:
    return Entity(
        type=EntityType.PERSON,
        text="x" * (end - start),
        start=start,
        end=end,
        confidence=confidence,
        source=source,
    )


def test_results_are_sorted_by_position() -> None:
    text = "Erst BIC: DEUTDEFF, dann PLZ 10115."
    entities = detect(text)
    assert [entity.start for entity in entities] == sorted(entity.start for entity in entities)


def test_overlapping_entities_are_resolved() -> None:
    regex = _entity(0, 5, source=DetectorSource.REGEX, confidence=0.9)
    spacy = _entity(2, 8, source=DetectorSource.SPACY, confidence=0.99)
    resolved = resolve_entities([spacy, regex])
    assert resolved == [regex]


def test_non_overlapping_entities_survive() -> None:
    first = _entity(0, 5, source=DetectorSource.REGEX, confidence=0.9)
    second = _entity(6, 10, source=DetectorSource.SPACY, confidence=0.9)
    assert len(resolve_entities([first, second])) == 2


def test_min_confidence_filters() -> None:
    low = _entity(0, 5, source=DetectorSource.SPACY, confidence=0.4)
    assert resolve_entities([low], min_confidence=0.5) == []


def test_detect_accepts_custom_detectors() -> None:
    class AlwaysFound:
        name = DetectorSource.TRANSFORMER

        def detect(self, text: str, language: str = "de") -> list[Entity]:
            return [
                Entity(
                    type=EntityType.PERSON,
                    text="Max",
                    start=0,
                    end=3,
                    source=DetectorSource.TRANSFORMER,
                )
            ]

    entities = detect("Max arbeitet hier.", detectors=[AlwaysFound()])
    assert [entity.text for entity in entities] == ["Max"]
    assert entities[0].source is DetectorSource.TRANSFORMER


def test_detect_without_detectors_returns_empty_for_plain_text() -> None:
    assert detect("Ein ganz gewöhnlicher Satz ohne sensible Daten.") == []
