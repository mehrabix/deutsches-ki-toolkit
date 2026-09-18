"""Schnittstelle für Entitätsdetektoren."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from deutsches_ki.core.enums import DetectorSource
from deutsches_ki.core.models import Entity

__all__ = ["EntityDetector"]


@runtime_checkable
class EntityDetector(Protocol):
    """Ein Detektor findet Entitäten in einem Text."""

    name: DetectorSource

    def detect(self, text: str, language: str = "de") -> list[Entity]:
        """Gibt alle gefundenen Entitäten mit Position und Konfidenz zurück."""
        ...
