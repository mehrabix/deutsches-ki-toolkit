"""Entitätenerkennung über GLiNER (optional).

GLiNER erkennt im Deutschen unter anderem Organisationen, die das spaCy-Modell
bewusst auslässt. Der Detektor ist bewusst schlank gehalten und teilt sein
Ergebnis in dieselbe Entitätsform wie alle anderen.
"""

from __future__ import annotations

from typing import Any

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.core.models import Entity
from deutsches_ki.errors import MissingDependencyError

__all__ = ["GliNERDetector"]

_LABELS: dict[str, EntityType] = {
    "person": EntityType.PERSON,
    "organization": EntityType.ORGANISATION,
    "organisation": EntityType.ORGANISATION,
    "location": EntityType.LOCATION,
}


class GliNERDetector:
    """Nutzt ein GLiNER-Modell für Namen und Organisationen."""

    name = DetectorSource.GLINER

    def __init__(
        self,
        model: str = "urchade/gliner_multi-v2.1",
        labels: list[str] | None = None,
        threshold: float = 0.5,
        engine: Any | None = None,
    ) -> None:
        self._labels = list(labels or _LABELS)
        self._threshold = threshold
        if engine is not None:
            self._model = engine
            return
        try:
            from gliner import GLiNER
        except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
            raise MissingDependencyError(
                "Für den GLiNER-Detektor wird die Erweiterung 'gliner' benötigt. "
                'Installation: pip install "deutsches-ki-toolkit[gliner]"'
            ) from exc
        self._model = GLiNER.from_pretrained(model)

    def detect(self, text: str, language: str = "de") -> list[Entity]:
        predictions = self._model.predict_entities(
            text,
            self._labels,
            threshold=self._threshold,
        )
        entities: list[Entity] = []
        for prediction in predictions:
            entity_type = _LABELS.get(str(prediction["label"]).lower())
            if entity_type is None:
                continue
            entities.append(
                Entity(
                    type=entity_type,
                    text=prediction["text"],
                    start=int(prediction["start"]),
                    end=int(prediction["end"]),
                    confidence=float(prediction.get("score", 0.7)),
                    source=DetectorSource.GLINER,
                    metadata={"label": prediction["label"]},
                )
            )
        return entities
