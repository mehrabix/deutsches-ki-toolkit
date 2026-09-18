"""Bewertungsdatensätze.

Ein Fall besteht aus einer Frage, den erwarteten Fundstellen und optional einer
Referenzantwort. Die Fundstellen werden als ``datei#abschnitt`` angegeben, also
zum Beispiel ``vertrag.md#§ 4 Zahlungsbedingungen``. Nur der Dateiname ohne
Abschnitt ist ebenfalls erlaubt; dann zählt jeder Abschnitt der Datei.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.core.models import Chunk
from deutsches_ki.errors import ParseError

__all__ = [
    "EvaluationCase",
    "EvaluationDataset",
    "canonical_source",
    "chunk_identity",
    "is_relevant",
    "matches_source",
]


class EvaluationCase(BaseModel):
    """Eine Frage mit erwarteten Fundstellen."""

    model_config = ConfigDict(extra="forbid")

    question: str
    expected_sources: list[str] = Field(min_length=1)
    reference_answer: str | None = None
    category: str | None = None
    difficulty: str | None = None


class EvaluationDataset(BaseModel):
    """Eine Sammlung von Fällen."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    cases: list[EvaluationCase] = Field(min_length=1)

    @classmethod
    def from_file(cls, path: str | Path) -> EvaluationDataset:
        """Lädt einen Datensatz aus YAML oder JSON."""
        file = Path(path)
        if not file.exists():
            raise ParseError(f"Datensatz nicht gefunden: {file}")
        raw = yaml.safe_load(file.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ParseError(f"Datensatz hat ein unerwartetes Format: {file}")
        return cls.model_validate(raw)

    def categories(self) -> list[str]:
        """Alle vorkommenden Kategorien, sortiert."""
        return sorted({case.category for case in self.cases if case.category})


def chunk_identity(chunk: Chunk) -> str:
    """Kennung einer Fundstelle, wie sie im Datensatz steht.

    Zum Beispiel ``vertrag.md#§ 4 zahlungsbedingungen``. Kleinschreibung, damit
    der Vergleich nicht an der Schreibweise scheitert.
    """
    document = chunk.metadata.get("document")
    document_name = str(document) if document else chunk.document_id
    section = chunk.section
    identity = f"{document_name}#{section}" if section else document_name
    return identity.strip().lower()


def matches_source(identity: str, expected: str) -> bool:
    """Prüft, ob eine Fundstelle zu einer erwarteten Quelle passt."""
    wanted = expected.strip().lower()
    if not wanted:
        return False
    if identity == wanted:
        return True
    # Nur der Dateiname erwartet: dann zählt jeder Abschnitt der Datei.
    return identity.split("#", 1)[0] == wanted


def is_relevant(identity: str, expected: list[str]) -> bool:
    """Prüft eine Fundstelle gegen alle erwarteten Quellen."""
    return any(matches_source(identity, source) for source in expected)


def canonical_source(identity: str, expected: list[str]) -> str:
    """Bildet eine Fundstelle auf die passende erwartete Quelle ab.

    Dadurch funktionieren die Mengenoperationen der Metriken auch dann, wenn im
    Datensatz nur der Dateiname steht und die Fundstelle den Abschnitt nennt.
    """
    for source in expected:
        if matches_source(identity, source):
            return source.strip().lower()
    return identity
