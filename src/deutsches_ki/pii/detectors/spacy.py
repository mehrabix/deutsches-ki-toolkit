"""Entitätenerkennung über spaCy (optional).

Das deutsche spaCy-Modell erkennt Organisationen standardmäßig nicht. Wer
Firmennamen braucht, sollte zusätzlich GLiNER einschalten.
"""

from __future__ import annotations

from typing import Any

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.core.models import Entity
from deutsches_ki.errors import MissingDependencyError

__all__ = ["SpaCyDetector"]

_LABELS: dict[str, EntityType] = {
    "PER": EntityType.PERSON,
    "PERSON": EntityType.PERSON,
    "ORG": EntityType.ORGANISATION,
    "LOC": EntityType.LOCATION,
    "GPE": EntityType.LOCATION,
    "MONEY": EntityType.MONEY,
    "DATE": EntityType.DATE,
}


class SpaCyDetector:
    """Nutzt ein geladenes spaCy-Modell für Personen, Orte und Organisationen."""

    name = DetectorSource.SPACY

    def __init__(self, model: str = "de_core_news_lg", nlp: Any | None = None) -> None:
        if nlp is not None:
            self._nlp = nlp
            return
        try:
            import spacy
        except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
            raise MissingDependencyError(
                "Für den spaCy-Detektor wird die Erweiterung 'nlp' benötigt. "
                'Installation: pip install "deutsches-ki-toolkit[nlp]" und danach '
                "python -m spacy download de_core_news_lg"
            ) from exc
        self._nlp = spacy.load(model)

    def detect(self, text: str, language: str = "de") -> list[Entity]:
        entities: list[Entity] = []
        for span in self._nlp(text).ents:
            entity_type = _LABELS.get(span.label_)
            if entity_type is None:
                continue
            entities.append(
                Entity(
                    type=entity_type,
                    text=span.text,
                    start=span.start_char,
                    end=span.end_char,
                    confidence=0.7,
                    source=DetectorSource.SPACY,
                    metadata={"label": span.label_},
                )
            )
        return entities
