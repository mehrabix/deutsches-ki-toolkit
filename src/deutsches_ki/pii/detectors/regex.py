"""Erkennung über reguläre Ausdrücke und deutsche Prüfsummen."""

from __future__ import annotations

from collections.abc import Iterable

from deutsches_ki.core.enums import DetectorSource
from deutsches_ki.core.models import Entity
from deutsches_ki.pii.context_words import has_context
from deutsches_ki.pii.recognizers.german import Recognizer, default_recognizers

__all__ = ["RegexDetector"]


class RegexDetector:
    """Erkennt strukturierte Kennungen über Muster und Prüfsummen."""

    name = DetectorSource.REGEX

    def __init__(self, recognizers: Iterable[Recognizer] | None = None) -> None:
        self.recognizers: tuple[Recognizer, ...] = (
            tuple(recognizers) if recognizers is not None else default_recognizers()
        )

    def detect(self, text: str, language: str = "de") -> list[Entity]:
        """Findet alle Treffer der hinterlegten Muster."""
        entities: list[Entity] = []
        for recognizer in self.recognizers:
            pattern = recognizer.pattern
            for match in pattern.finditer(text):
                start, end = match.start(recognizer.group), match.end(recognizer.group)
                value = text[start:end]
                if not value.strip():
                    continue
                if recognizer.validate is not None and not recognizer.validate(value):
                    continue

                confidence = recognizer.confidence
                if recognizer.context_key is not None:
                    nearby = has_context(text, start, end, recognizer.context_key)
                    if recognizer.requires_context and not nearby:
                        continue
                    if nearby:
                        confidence = min(1.0, confidence + 0.05)

                entities.append(
                    Entity(
                        type=recognizer.entity_type,
                        text=value,
                        start=start,
                        end=end,
                        confidence=confidence,
                        source=DetectorSource.REGEX,
                        metadata={"recognizer": recognizer.name},
                    )
                )
        return entities
