"""RAG: belegte Antworten aus einem Bestand."""

from __future__ import annotations

from deutsches_ki.rag.citations import CitationReport, extract_markers, validate_citations
from deutsches_ki.rag.engine import DeutschRAG
from deutsches_ki.rag.prompt import SYSTEM_PROMPT, build_messages, format_sources

__all__ = [
    "SYSTEM_PROMPT",
    "CitationReport",
    "DeutschRAG",
    "build_messages",
    "extract_markers",
    "format_sources",
    "validate_citations",
]
