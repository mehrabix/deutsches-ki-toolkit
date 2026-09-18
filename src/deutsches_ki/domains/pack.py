"""Fachpakete: Begriffe und Dokumentarten je Branche.

Ein Paket ist Konfiguration und Daten, kein eigener Code. Es bündelt die
bevorzugten Schreibweisen einer Branche und die Dokumentarten, die dort
typisch sind. Wer eine eigene Branche braucht, legt eine YAML-Datei daneben.
"""

from __future__ import annotations

from functools import cache
from importlib import resources

import yaml
from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.classification.types import DocumentType
from deutsches_ki.errors import ParseError
from deutsches_ki.terminology.glossary import Glossary, Term

__all__ = ["DomainPack", "available_domains", "load_domain"]

_PACKAGE = "deutsches_ki.domains"
_FOLDER = "data"


class DomainPack(BaseModel):
    """Ein Fachpaket für eine Branche."""

    model_config = ConfigDict(extra="forbid")

    name: str
    title: str
    description: str | None = None
    document_types: list[DocumentType] = Field(default_factory=list)
    terminology: list[Term] = Field(default_factory=list)

    @property
    def glossary(self) -> Glossary:
        """Die Begriffe des Pakets als Glossar."""
        return Glossary(name=self.name, description=self.description, terms=self.terminology)

    def merge(self, other: DomainPack) -> DomainPack:
        """Verbindet zwei Pakete zu einem."""
        return DomainPack(
            name=f"{self.name}+{other.name}",
            title=f"{self.title} und {other.title}",
            document_types=sorted({*self.document_types, *other.document_types}),
            terminology=[*self.terminology, *other.terminology],
        )


def available_domains() -> list[str]:
    """Namen der mitgelieferten Fachpakete."""
    folder = resources.files(_PACKAGE).joinpath(_FOLDER)
    try:
        files = list(folder.iterdir())
    except (FileNotFoundError, ModuleNotFoundError):  # pragma: no cover - defensiv
        return []
    return sorted(file.name.removesuffix(".yaml") for file in files if file.name.endswith(".yaml"))


@cache
def load_domain(name: str) -> DomainPack:
    """Lädt ein mitgeliefertes Fachpaket."""
    path = resources.files(_PACKAGE).joinpath(_FOLDER, f"{name}.yaml")
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        vorhanden = ", ".join(available_domains()) or "keine"
        raise ParseError(f"Unbekanntes Fachpaket '{name}'. Verfügbar: {vorhanden}.") from error

    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ParseError(f"Fachpaket '{name}' hat ein unerwartetes Format.")
    return DomainPack.model_validate(data)
