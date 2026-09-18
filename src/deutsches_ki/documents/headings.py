"""Überschriften erkennen – auch die deutschen, die kein Markdown sind.

Docling liefert Markdown, aber ein deutscher Vertrag liefert seine Gliederung
selbst: ``§ 4 Zahlungsbedingungen``, ``Anlage 2 Vergütung``, ``Abschnitt 3``.
Ohne diese Erkennung landet ein ganzes PDF in einem einzigen Abschnitt, und die
Struktur, auf der das Chunking aufbaut, ist verloren.
"""

from __future__ import annotations

import re

from deutsches_ki.core.models import Section

__all__ = ["build_sections", "match_heading"]

_MARKDOWN = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

# Deutsche Gliederungsformen. Das Paragraphenzeichen ist eindeutig; die
# nummerierte Form ist es nicht, deshalb gelten dort nur kurze Zeilen.
# Ein führender Aufzählungspunkt ist erlaubt: Docling macht aus manchen
# Überschriften einen Listenpunkt („- § 2 Vergütung“).
_BULLET = r"(?:[-*•]\s+)?"
_GERMAN: tuple[tuple[int, re.Pattern[str]], ...] = (
    (2, re.compile(rf"^{_BULLET}§+\s*\d+[a-zA-Z]?(?:\s+\S.{{0,70}})?$")),
    (
        2,
        re.compile(
            rf"^{_BULLET}(?:Abschnitt|Kapitel|Artikel|Anlage|Anhang|Teil|Punkt)\s+"
            r"[IVXLCDM\d]+(?:[.)])?(?:\s+\S.{0,70})?$",
            re.IGNORECASE,
        ),
    ),
    (3, re.compile(rf"^{_BULLET}\d+\.\d+(?:\.\d+)*\s+\S.{{0,60}}$")),
)

# Zeilen mit Satzzeichen am Ende sind Sätze, keine Überschriften.
_SENTENCE_END = re.compile(r"[.!?:;,]$")


def _clean(title: str) -> str | None:
    stripped = title.strip().strip("*_").strip(" :-–—")
    return stripped or None


def match_heading(line: str) -> tuple[int, str | None] | None:
    """Erkennt eine Überschrift und gibt Ebene und Titel zurück.

    Markdown-Überschriften haben Vorrang. Danach folgen die deutschen Formen.
    Sehr lange Zeilen und Zeilen mit Satzzeichen am Ende gelten nicht als
    Überschrift, sonst würde jeder Aufzählungspunkt eine.
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 90:
        return None

    markdown = _MARKDOWN.match(stripped)
    if markdown is not None:
        return len(markdown.group(1)), _clean(markdown.group(2))

    if _SENTENCE_END.search(stripped):
        return None

    for level, pattern in _GERMAN:
        if pattern.match(stripped):
            return level, _clean(stripped)

    return None


def build_sections(text: str) -> list[Section]:
    """Baut aus Text einen Abschnittsbaum.

    Text vor der ersten Überschrift bekommt einen eigenen Abschnitt ohne Titel,
    damit nichts verloren geht.
    """
    roots: list[Section] = []
    stack: list[Section] = []
    buffer: list[str] = []

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
        heading = match_heading(line)
        if heading is None:
            buffer.append(line)
            continue
        flush()
        level, title = heading
        section = Section(title=title, level=level)
        while stack and stack[-1].level >= level:
            stack.pop()
        if stack:
            stack[-1].children.append(section)
        else:
            roots.append(section)
        stack.append(section)
    flush()

    return roots
