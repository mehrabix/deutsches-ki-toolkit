"""Zerlegen von Markdown und Klartext in eine Abschnittsstruktur."""

from __future__ import annotations

from deutsches_ki.core.enums import Language
from deutsches_ki.core.models import Document, Section
from deutsches_ki.documents.headings import build_sections

__all__ = ["first_title", "parse_markdown", "parse_plaintext", "split_paragraphs"]


def split_paragraphs(text: str) -> list[str]:
    """Trennt Text an Leerzeilen in Absätze."""
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line.rstrip())
        elif current:
            blocks.append("\n".join(current).strip())
            current = []
    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def first_title(sections: list[Section]) -> str | None:
    """Der Titel des ersten Abschnitts der obersten Ebene."""
    for section in sections:
        if section.title:
            return section.title
    return None


def _document(
    text: str,
    *,
    source: str,
    title: str | None,
    language: Language,
) -> Document:
    sections = build_sections(text)
    return Document(
        source=source,
        title=title or first_title(sections),
        language=language,
        content=text,
        sections=sections,
    )


def parse_markdown(
    text: str,
    *,
    source: str = "<text>",
    title: str | None = None,
    language: Language = Language.DE,
) -> Document:
    """Liest Markdown ein. Deutsche Gliederungsformen zählen ebenfalls."""
    return _document(text, source=source, title=title, language=language)


def parse_plaintext(
    text: str,
    *,
    source: str = "<text>",
    title: str | None = None,
    language: Language = Language.DE,
) -> Document:
    """Liest Klartext ein.

    Auch hier werden Überschriften erkannt, damit ein Vertrag im Textformat
    seine Gliederung behält.
    """
    return _document(text, source=source, title=title, language=language)
