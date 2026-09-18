"""Begriffe prüfen: bevorzugte Schreibweisen und Abweichungen."""

from __future__ import annotations

from deutsches_ki.terminology.check import (
    Inconsistency,
    Occurrence,
    TerminologyReport,
    check_terminology,
)
from deutsches_ki.terminology.glossary import Glossary, Term

__all__ = [
    "Glossary",
    "Inconsistency",
    "Occurrence",
    "Term",
    "TerminologyReport",
    "check_terminology",
]
