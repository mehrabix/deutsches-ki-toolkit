"""Prüfung der Quellenangaben.

Eine Antwort ohne Quelle ist nur eine Behauptung. Hier wird geprüft, ob die im
Text genannten Nummern tatsächlich zu den mitgegebenen Quellen passen.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

__all__ = ["CitationReport", "extract_markers", "validate_citations"]

_MARKER = re.compile(r"\[(\d+)\]")


class CitationReport(BaseModel):
    """Ergebnis der Quellenprüfung."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cited: list[int]
    valid: list[int]
    unknown: list[int]
    source_count: int

    @property
    def has_citations(self) -> bool:
        """Wurde überhaupt eine Quelle genannt?"""
        return bool(self.cited)

    @property
    def all_valid(self) -> bool:
        """Wurden nur Quellen genannt, die es auch gibt?"""
        return bool(self.cited) and not self.unknown

    def as_metadata(self) -> dict[str, object]:
        """Der Bericht als Wörterbuch, mit den abgeleiteten Angaben.

        ``model_dump`` lässt die beiden Eigenschaften weg, weil sie berechnet
        werden. Wer die Antwort weiterreicht, will sie aber gerade sehen.
        """
        return {
            **self.model_dump(mode="json"),
            "has_citations": self.has_citations,
            "all_valid": self.all_valid,
        }


def extract_markers(answer: str) -> list[int]:
    """Alle Nummern in eckigen Klammern, in Reihenfolge des Auftretens."""
    return [int(match.group(1)) for match in _MARKER.finditer(answer)]


def validate_citations(answer: str, source_count: int) -> CitationReport:
    """Prüft die genannten Nummern gegen die vorhandenen Quellen.

    ``source_count`` ist die Anzahl der mitgegebenen Quellen. Nummern oberhalb
    davon gibt es nicht und landen in ``unknown``.
    """
    cited = extract_markers(answer)
    valid = sorted({number for number in cited if 1 <= number <= source_count})
    unknown = sorted({number for number in cited if number not in valid})
    return CitationReport(
        cited=cited,
        valid=valid,
        unknown=unknown,
        source_count=source_count,
    )
