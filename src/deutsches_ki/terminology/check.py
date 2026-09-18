"""Prüfung eines Textes gegen ein Glossar."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.terminology.glossary import Glossary

__all__ = [
    "Inconsistency",
    "Occurrence",
    "TerminologyReport",
    "check_terminology",
]


class Occurrence(BaseModel):
    """Eine Fundstelle eines Begriffs im Text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    surface: str
    preferred: str
    start: int
    end: int
    is_preferred: bool
    domain: str | None = None


class Inconsistency(BaseModel):
    """Derselbe Begriff in mehr als einer Schreibweise."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    preferred: str
    surfaces: list[str]
    count: int


class TerminologyReport(BaseModel):
    """Ergebnis einer Terminologie-Prüfung."""

    model_config = ConfigDict(extra="forbid")

    glossary: str
    occurrences: list[Occurrence] = Field(default_factory=list)
    inconsistencies: list[Inconsistency] = Field(default_factory=list)

    @property
    def is_consistent(self) -> bool:
        """Wurde durchgehend die bevorzugte Form verwendet?"""
        return not self.inconsistencies

    def deviations(self) -> list[Occurrence]:
        """Alle Stellen, die nicht der bevorzugten Form entsprechen."""
        return [item for item in self.occurrences if not item.is_preferred]

    def count_by_preferred(self) -> dict[str, int]:
        """Wie oft jeder Begriff vorkommt."""
        counts: dict[str, int] = {}
        for item in self.occurrences:
            counts[item.preferred] = counts.get(item.preferred, 0) + 1
        return counts


def check_terminology(text: str, glossary: Glossary) -> TerminologyReport:
    """Sucht Begriffe und meldet abweichende Schreibweisen.

    Verglichen wird ohne Rücksicht auf Groß- und Kleinschreibung. Ein Begriff
    gilt als inkonsistent, sobald er im Text in mehr als einer Form auftaucht,
    auch wenn die bevorzugte Form gar nicht dabei ist.
    """
    pattern = glossary.pattern()

    occurrences: list[Occurrence] = []
    forms: dict[str, set[str]] = {}
    counts: dict[str, int] = {}

    for match in pattern.finditer(text):
        surface = match.group()
        term = glossary.term_for(surface)
        if term is None:  # pragma: no cover - Muster und Glossar passen zusammen
            continue

        is_preferred = (
            " ".join(surface.split()).casefold() == " ".join(term.preferred.split()).casefold()
        )
        occurrences.append(
            Occurrence(
                surface=surface,
                preferred=term.preferred,
                start=match.start(),
                end=match.end(),
                is_preferred=is_preferred,
                domain=term.domain,
            )
        )
        forms.setdefault(term.preferred, set()).add(" ".join(surface.split()).casefold())
        counts[term.preferred] = counts.get(term.preferred, 0) + 1

    inconsistencies = [
        Inconsistency(
            preferred=preferred,
            surfaces=sorted(surface_forms),
            count=counts[preferred],
        )
        for preferred, surface_forms in forms.items()
        if len(surface_forms) > 1
    ]
    inconsistencies.sort(key=lambda item: item.preferred)

    return TerminologyReport(
        glossary=glossary.name,
        occurrences=occurrences,
        inconsistencies=inconsistencies,
    )
