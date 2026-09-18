"""Begriffe und ihre bevorzugten Schreibweisen.

In Unternehmen schreibt jeder dasselbe anders: mal „Kunde“, mal „Kundin“, mal
„Auftraggeber“, mal „Client“. Ein Glossar legt fest, welche Form gelten soll.
Der Prüflauf findet dann die Stellen, an denen davon abgewichen wird.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.errors import ParseError

__all__ = ["Glossary", "Term"]


class Term(BaseModel):
    """Ein Begriff mit bevorzugter Form und erlaubten Abweichungen."""

    model_config = ConfigDict(extra="forbid")

    preferred: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    note: str | None = None
    domain: str | None = None

    def surfaces(self) -> list[str]:
        """Bevorzugte Form und Abweichungen, längste zuerst.

        Die Reihenfolge zählt beim Suchen: „Erholungsurlaub“ muss vor
        „Urlaub“ geprüft werden, sonst matcht der kürzere Begriff zuerst.
        """
        forms = [self.preferred, *self.aliases]
        return sorted({form for form in forms if form.strip()}, key=len, reverse=True)


class Glossary(BaseModel):
    """Eine Sammlung von Begriffen."""

    model_config = ConfigDict(extra="forbid")

    name: str = "glossar"
    description: str | None = None
    terms: list[Term] = Field(default_factory=list)

    @classmethod
    def from_file(cls, path: str | Path) -> Glossary:
        """Lädt ein Glossar aus YAML oder JSON."""
        file = Path(path)
        if not file.exists():
            raise ParseError(f"Glossar nicht gefunden: {file}")
        raw = yaml.safe_load(file.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ParseError(f"Glossar hat ein unerwartetes Format: {file}")
        return cls.model_validate(raw)

    def to_file(self, path: str | Path) -> None:
        """Schreibt das Glossar als YAML."""
        payload = self.model_dump(mode="json", exclude_none=True)
        Path(path).write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def pattern(self) -> re.Pattern[str]:
        """Ein Muster, das alle Formen aller Begriffe findet.

        Mehrteilige Formen dürfen beliebig viele Leerzeichen enthalten, damit
        „Erholungsurlaub“ und „Erholungs urlaub“ beide passen. Gesucht wird
        ohne Rücksicht auf Groß- und Kleinschreibung.
        """
        alternatives: list[str] = []
        for term in self.terms:
            for surface in term.surfaces():
                escaped = re.escape(surface).replace(r"\ ", r"\s+")
                alternatives.append(escaped)
        if not alternatives:
            return re.compile(r"(?!x)x")  # trifft nie
        joined = "|".join(alternatives)
        return re.compile(rf"(?<![\w-])(?:{joined})(?![\w-])", re.IGNORECASE)

    def term_for(self, surface: str) -> Term | None:
        """Sucht den Begriff zu einer Schreibweise."""
        wanted = " ".join(surface.split()).casefold()
        for term in self.terms:
            if any(" ".join(form.split()).casefold() == wanted for form in term.surfaces()):
                return term
        return None

    def merge(self, other: Glossary) -> Glossary:
        """Fasst zwei Glossare zusammen, ohne Begriffe doppelt zu führen."""
        known = {term.preferred.casefold() for term in self.terms}
        combined = list(self.terms)
        for term in other.terms:
            if term.preferred.casefold() not in known:
                combined.append(term)
                known.add(term.preferred.casefold())
        return Glossary(
            name=f"{self.name}+{other.name}",
            terms=combined,
        )
