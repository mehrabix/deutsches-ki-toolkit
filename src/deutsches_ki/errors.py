"""Fehlertypen des Toolkits."""

from __future__ import annotations

__all__ = [
    "DeutschesKiError",
    "MissingDependencyError",
    "ParseError",
    "ProviderError",
    "UnsupportedFormatError",
]


class DeutschesKiError(Exception):
    """Basisklasse aller Fehler des Toolkits."""


class MissingDependencyError(DeutschesKiError):
    """Eine optionale Erweiterung wird gebraucht, ist aber nicht installiert."""


class ParseError(DeutschesKiError):
    """Ein Dokument konnte nicht gelesen werden."""


class UnsupportedFormatError(DeutschesKiError):
    """Für diese Dateiendung gibt es keinen Leser."""


class ProviderError(DeutschesKiError):
    """Ein Sprachmodell war nicht erreichbar oder hat unerwartet geantwortet."""
