"""Entitätenerkennung über Microsoft Presidio (optional).

Presidio bringt von Haus aus vor allem US-Muster mit. Hier wird es um die
deutsche Sprachunterstützung ergänzt; die strukturierten deutschen Kennungen
liefert weiterhin der Regex-Detektor.
"""

from __future__ import annotations

from typing import Any

from deutsches_ki.core.enums import DetectorSource, EntityType
from deutsches_ki.core.models import Entity
from deutsches_ki.errors import MissingDependencyError

__all__ = ["PresidioDetector"]

_ENTITIES: dict[str, EntityType] = {
    "PERSON": EntityType.PERSON,
    "ORGANIZATION": EntityType.ORGANISATION,
    "LOCATION": EntityType.LOCATION,
    "EMAIL_ADDRESS": EntityType.EMAIL,
    "PHONE_NUMBER": EntityType.PHONE,
    "IBAN_CODE": EntityType.DE_IBAN,
    "DATE_TIME": EntityType.DATE,
}


class PresidioDetector:
    """Bindet den Presidio-Analyzer für Deutsch an."""

    name = DetectorSource.PRESIDIO

    def __init__(
        self,
        model: str = "de_core_news_lg",
        analyzer: Any | None = None,
    ) -> None:
        self._language = "de"
        if analyzer is not None:
            self._analyzer = analyzer
            return
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
        except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
            raise MissingDependencyError(
                "Für den Presidio-Detektor wird die Erweiterung 'presidio' benötigt. "
                'Installation: pip install "deutsches-ki-toolkit[presidio]"'
            ) from exc

        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "de", "model_name": model}],
            }
        )
        self._analyzer = AnalyzerEngine(
            nlp_engine=provider.create_engine(),
            supported_languages=["de"],
        )

    def detect(self, text: str, language: str = "de") -> list[Entity]:
        results = self._analyzer.analyze(text=text, language=language or self._language)
        entities: list[Entity] = []
        for result in results:
            entity_type = _ENTITIES.get(result.entity_type)
            if entity_type is None:
                continue
            entities.append(
                Entity(
                    type=entity_type,
                    text=text[result.start : result.end],
                    start=result.start,
                    end=result.end,
                    confidence=float(result.score),
                    source=DetectorSource.PRESIDIO,
                    metadata={"entity_type": result.entity_type},
                )
            )
        return entities
