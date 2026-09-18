"""Zerlegen von Klartext in Abschnitte."""

from __future__ import annotations

from deutsches_ki.core.enums import Language
from deutsches_ki.core.models import Document, Section

__all__ = ["parse_plaintext"]


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


def parse_plaintext(
    text: str,
    *,
    source: str = "<text>",
    title: str | None = None,
    language: Language = Language.DE,
) -> Document:
    """Baut ein Dokument mit einem einzelnen Abschnitt aus reinem Text."""
    paragraphs = split_paragraphs(text)
    section = Section(
        title=title,
        level=1,
        content="\n\n".join(paragraphs),
        metadata={"paragraphs": len(paragraphs)},
    )
    return Document(
        source=source,
        title=title,
        language=language,
        content=text,
        sections=[section] if text.strip() else [],
    )
