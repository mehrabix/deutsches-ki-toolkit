"""Dokumente einlesen und Struktur erhalten."""

from __future__ import annotations

from deutsches_ki.documents.headings import build_sections, match_heading
from deutsches_ki.documents.language import detect_language
from deutsches_ki.documents.markdown import parse_markdown, split_paragraphs
from deutsches_ki.documents.metadata_de import extract_metadata
from deutsches_ki.documents.parse import parse
from deutsches_ki.documents.plaintext import parse_plaintext

__all__ = [
    "build_sections",
    "detect_language",
    "extract_metadata",
    "match_heading",
    "parse",
    "parse_markdown",
    "parse_plaintext",
    "split_paragraphs",
]
