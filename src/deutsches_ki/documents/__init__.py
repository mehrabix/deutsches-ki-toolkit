"""Dokumente einlesen und Struktur erhalten."""

from __future__ import annotations

from deutsches_ki.documents.markdown import parse_markdown
from deutsches_ki.documents.parse import parse
from deutsches_ki.documents.plaintext import parse_plaintext

__all__ = ["parse", "parse_markdown", "parse_plaintext"]
