"""Zusammenführen mehrerer Detektoren zu einem Ergebnis."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from deutsches_ki.core.enums import DetectorSource
from deutsches_ki.core.models import Entity
from deutsches_ki.errors import MissingDependencyError
from deutsches_ki.pii.base import EntityDetector
from deutsches_ki.pii.detectors.regex import RegexDetector

__all__ = ["default_detectors", "detect", "resolve_entities"]

# Strukturierte Kennungen schlagen Namenserkennung, wenn sich Treffer überlappen.
_SOURCE_PRIORITY: dict[DetectorSource, int] = {
    DetectorSource.REGEX: 30,
    DetectorSource.PRESIDIO: 20,
    DetectorSource.GLINER: 20,
    DetectorSource.SPACY: 10,
    DetectorSource.TRANSFORMER: 10,
}

_OPTIONAL = {"spacy", "presidio", "gliner"}


def _optional_detector(name: str) -> EntityDetector:
    if name == "spacy":
        from deutsches_ki.pii.detectors.spacy import SpaCyDetector

        return SpaCyDetector()
    if name == "presidio":
        from deutsches_ki.pii.detectors.presidio import PresidioDetector

        return PresidioDetector()
    if name == "gliner":
        from deutsches_ki.pii.detectors.gliner import GliNERDetector

        return GliNERDetector()
    raise MissingDependencyError(f"Unbekannter Detektor: {name}")


def default_detectors(include: Iterable[str] | None = None) -> list[EntityDetector]:
    """Baut die Detektorkette.

    Ohne ``include`` kommt nur die Erkennung über Muster zum Einsatz. Das hält
    die Grundinstallation leicht und die Tests laufen ohne optionale Pakete.
    """
    detectors: list[EntityDetector] = [RegexDetector()]
    for name in include or ():
        if name not in _OPTIONAL:
            raise MissingDependencyError(f"Unbekannter Detektor: {name}")
        detectors.append(_optional_detector(name))
    return detectors


def _overlaps(left: Entity, right: Entity) -> bool:
    return not (left.end <= right.start or left.start >= right.end)


def resolve_entities(
    entities: Iterable[Entity],
    *,
    min_confidence: float = 0.0,
) -> list[Entity]:
    """Entfernt Überlappungen und doppelte Treffer.

    Bei Überlappungen gewinnt der Detektor mit höherer Priorität, danach die
    höhere Konfidenz, danach der längere Treffer.
    """
    candidates = [entity for entity in entities if entity.confidence >= min_confidence]
    candidates.sort(
        key=lambda entity: (
            -_SOURCE_PRIORITY.get(entity.source, 0),
            -entity.confidence,
            -entity.length,
            entity.start,
        )
    )

    accepted: list[Entity] = []
    for entity in candidates:
        if any(_overlaps(entity, chosen) for chosen in accepted):
            continue
        accepted.append(entity)

    return sorted(accepted, key=lambda entity: (entity.start, entity.end))


def detect(
    text: str,
    *,
    detectors: Sequence[EntityDetector] | None = None,
    language: str = "de",
    min_confidence: float = 0.0,
) -> list[Entity]:
    """Findet Entitäten in einem Text."""
    active = list(detectors) if detectors is not None else default_detectors()
    found: list[Entity] = []
    for detector in active:
        found.extend(detector.detect(text, language=language))
    return resolve_entities(found, min_confidence=min_confidence)
