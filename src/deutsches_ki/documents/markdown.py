"""Zerlegen von Markdown in eine Abschnittsstruktur."""

from __future__ import annotations

import re

from deutsches_ki.core.enums import Language
from deutsches_ki.core.models import Document, Section

__all__ = ["parse_markdown"]

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")


def parse_markdown(
    text: str,
    *,
    source: str = "<text>",
    title: str | None = None,
    language: Language = Language.DE,
) -> Document:
    """Baut aus Überschriften einen Abschnittsbaum."""
    roots: list[Section] = []
    stack: list[Section] = []
    buffer: list[str] = []
    document_title = title

    def flush() -> None:
        content = "\n".join(buffer).strip()
        buffer.clear()
        if not content:
            return
        if stack:
            existing = stack[-1].content
            stack[-1].content = f"{existing}\n\n{content}".strip() if existing else content
        else:
            roots.append(Section(title=None, level=0, content=content))

    for line in text.splitlines():
        match = _HEADING.match(line)
        if match is None:
            buffer.append(line)
            continue
        flush()
        level = len(match.group(1))
        heading = match.group(2).strip()
        if document_title is None and level == 1:
            document_title = heading
        section = Section(title=heading, level=level)
        while stack and stack[-1].level >= level:
            stack.pop()
        if stack:
            stack[-1].children.append(section)
        else:
            roots.append(section)
        stack.append(section)
    flush()

    return Document(
        source=source,
        title=document_title,
        language=language,
        content=text,
        sections=roots,
    )
