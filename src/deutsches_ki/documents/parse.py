"""Einlesen von Dokumenten anhand ihrer Dateiendung."""

from __future__ import annotations

from pathlib import Path

from deutsches_ki.core.enums import Language
from deutsches_ki.core.models import Document
from deutsches_ki.documents.docling import parse_with_docling
from deutsches_ki.documents.language import detect_language
from deutsches_ki.documents.markdown import parse_markdown
from deutsches_ki.documents.metadata_de import extract_metadata
from deutsches_ki.documents.plaintext import parse_plaintext
from deutsches_ki.errors import ParseError, UnsupportedFormatError

__all__ = ["parse", "read_text"]

TEXT_SUFFIXES = frozenset({".txt", ".text", ".log"})
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
DOCLING_SUFFIXES = frozenset(
    {
        ".pdf",
        ".docx",
        ".doc",
        ".pptx",
        ".xlsx",
        ".html",
        ".htm",
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
    }
)
_ENCODINGS = ("utf-8", "cp1252")


def read_text(path: Path) -> str:
    """Liest eine Textdatei als UTF-8, mit Rückfall auf Windows-1252."""
    for encoding in _ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ParseError(f"Datei konnte nicht als Text gelesen werden: {path}")


def _finalize(document: Document, *, language: Language | None) -> Document:
    """Ergänzt Sprache und deutsche Metadaten.

    Die Sprache wird nur geschätzt, wenn sie nicht vorgegeben wurde. Metadaten
    überschreiben nichts, was der Leser selbst gesetzt hat.
    """
    document.language = language or detect_language(document.content)
    for key, value in extract_metadata(document.content).items():
        document.metadata.setdefault(key, value)
    return document


def parse(
    source: str | Path,
    *,
    parser: str | None = None,
    language: Language | None = None,
    title: str | None = None,
) -> Document:
    """Liest ein Dokument ein und gibt die Abschnittsstruktur zurück.

    Die Sprache wird erkannt, wenn keine angegeben ist. Zusätzlich werden
    deutsche Geschäftsangaben wie Rechnungs- und Kundennummer in die Metadaten
    übernommen.
    """
    path = Path(source)
    if not path.exists():
        raise ParseError(f"Datei nicht gefunden: {path}")
    if not path.is_file():
        raise ParseError(f"Keine reguläre Datei: {path}")

    suffix = path.suffix.lower()

    if parser in (None, "plaintext") and suffix in TEXT_SUFFIXES:
        document = parse_plaintext(
            read_text(path),
            source=str(path),
            title=title or path.stem,
        )
    elif parser in (None, "markdown") and suffix in MARKDOWN_SUFFIXES:
        document = parse_markdown(read_text(path), source=str(path), title=title)
    elif parser == "docling" or (parser is None and suffix in DOCLING_SUFFIXES):
        document = parse_with_docling(path, title=title or path.stem)
    else:
        raise UnsupportedFormatError(f"Kein Leser für die Endung '{suffix}'.")

    return _finalize(document, language=language)
