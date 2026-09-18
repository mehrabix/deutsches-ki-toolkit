"""Einlesen strukturierter Formate über Docling (optional)."""

from __future__ import annotations

from pathlib import Path

from deutsches_ki.core.enums import Language
from deutsches_ki.core.models import Document
from deutsches_ki.documents.markdown import parse_markdown
from deutsches_ki.errors import MissingDependencyError, ParseError

__all__ = ["parse_with_docling"]


def parse_with_docling(
    path: Path,
    *,
    language: Language = Language.DE,
    title: str | None = None,
) -> Document:
    """Liest PDF, DOCX und weitere Formate über Docling ein.

    Docling liefert Markdown, das anschließend in die Abschnittsstruktur
    überführt wird. Dadurch bleibt die deutsche Nachbearbeitung an einer Stelle.
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
        raise MissingDependencyError(
            "Zum Einlesen von PDF, DOCX und ähnlichen Formaten wird die optionale "
            "Erweiterung 'docling' benötigt. Installation: "
            'pip install "deutsches-ki-toolkit[docling]"'
        ) from exc

    try:
        result = DocumentConverter().convert(str(path))
        markdown_text = result.document.export_to_markdown()
    except Exception as exc:  # pragma: no cover - hängt vom Dokument ab
        raise ParseError(f"Dokument konnte nicht gelesen werden: {path}") from exc

    return parse_markdown(
        markdown_text,
        source=str(path),
        title=title or path.stem,
        language=language,
    )
