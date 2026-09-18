"""Stabile interne Datenmodelle für die gesamte Verarbeitungskette."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.core.enums import (
    DetectorSource,
    EntityType,
    Language,
)
from deutsches_ki.core.ids import new_id

__all__ = [
    "Answer",
    "Chunk",
    "Citation",
    "Document",
    "Entity",
    "SearchResult",
    "Section",
    "Sentence",
]


class _Model(BaseModel):
    """Gemeinsame Basis: keine unerwarteten Felder."""

    model_config = ConfigDict(extra="forbid")


class Sentence(_Model):
    """Ein Satz mit seiner Position im Ausgangstext."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)


class Entity(_Model):
    """Eine erkannte Entität mit Position, Konfidenz und Herkunft."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: EntityType
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: DetectorSource = DetectorSource.REGEX
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def length(self) -> int:
        """Länge des Treffers in Zeichen."""
        return self.end - self.start


class Section(_Model):
    """Ein Abschnitt eines Dokuments, optional mit Unterabschnitten."""

    id: str = Field(default_factory=lambda: new_id("sec"))
    title: str | None = None
    level: int = Field(default=1, ge=0)
    content: str = ""
    page: int | None = None
    children: list[Section] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(_Model):
    """Ein eingelesenes Dokument mit erhaltener Struktur."""

    id: str = Field(default_factory=lambda: new_id("doc"))
    source: str = ""
    title: str | None = None
    language: Language = Language.DE
    content: str = ""
    sections: list[Section] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path, **kwargs: Any) -> Document:
        """Liest ein Dokument anhand seiner Dateiendung ein."""
        from deutsches_ki.documents.parse import parse

        return parse(path, **kwargs)

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        title: str | None = None,
        source: str = "<text>",
        language: Language = Language.DE,
        **metadata: Any,
    ) -> Document:
        """Baut ein Dokument aus reinem Text ohne Datei."""
        return cls(
            source=source,
            title=title,
            language=language,
            content=text,
            metadata=dict(metadata),
        )

    def iter_sections(self) -> list[Section]:
        """Alle Abschnitte, Tiefensuche, Eltern vor Kindern."""
        result: list[Section] = []

        def walk(sections: list[Section]) -> None:
            for section in sections:
                result.append(section)
                walk(section.children)

        walk(self.sections)
        return result


class Chunk(_Model):
    """Ein Abschnitt des Dokuments, klein genug für Embedding und Suche."""

    id: str = Field(default_factory=lambda: new_id("chk"))
    document_id: str = ""
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    start: int | None = None
    end: int | None = None
    section_id: str | None = None

    @property
    def section(self) -> str | None:
        """Titel des Abschnitts, aus dem der Chunk stammt."""
        value = self.metadata.get("section")
        return value if isinstance(value, str) else None

    @property
    def index_text(self) -> str:
        """Der Text, der indiziert wird: Abschnittstitel plus Inhalt.

        Deutsche Abschnittstitel tragen das Thema („§ 4 Zahlungsbedingungen“).
        Ohne den Titel findet eine Frage nach der Zahlungsfrist den Abschnitt
        nicht, in dem nur von „Zahlung“ die Rede ist.
        """
        section = self.section
        return f"{section}\n{self.content}" if section else self.content


class Citation(_Model):
    """Ein Beleg für eine Antwort."""

    document: str
    page: int | None = None
    section: str | None = None
    chunk_id: str | None = None
    score: float = 0.0


class SearchResult(_Model):
    """Ein Treffer mit seinem Rang in den einzelnen Suchzweigen."""

    chunk: Chunk
    score: float = 0.0
    vector_rank: int | None = None
    lexical_rank: int | None = None


class Answer(_Model):
    """Eine Antwort samt Quellen."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunks: list[Chunk] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
