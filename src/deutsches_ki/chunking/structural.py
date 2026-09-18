"""Strukturbasiertes Chunking für deutsche Dokumente.

Geschnitten wird in dieser Rangfolge: Dokument, Abschnitt, Absatz, Satz,
Token. Die Token-Grenze kommt zuletzt. Ein Absatz, der eine Ausnahme enthält,
bleibt zusammen; ein Paragraphenabschnitt wird nicht auseinandergerissen.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from deutsches_ki.chunking.tokenize import estimate_tokens, split_tokens
from deutsches_ki.core.enums import ChunkStrategy
from deutsches_ki.core.models import Chunk, Document, Section
from deutsches_ki.documents.plaintext import split_paragraphs
from deutsches_ki.text.segment import split_sentences

__all__ = ["chunk_document", "chunk_text"]


@dataclass
class _Unit:
    text: str
    page: int | None = None
    section_id: str | None = None
    section_title: str | None = None
    section_path: list[str] = field(default_factory=list)


def _iter_sections(
    sections: list[Section], path: list[str] | None = None
) -> list[tuple[Section, list[str]]]:
    result: list[tuple[Section, list[str]]] = []
    current_path = list(path or [])
    for section in sections:
        section_path = [*current_path, section.title] if section.title else list(current_path)
        result.append((section, section_path))
        result.extend(_iter_sections(section.children, section_path))
    return result


def _split_by_tokens(text: str, max_tokens: int) -> list[str]:
    words = split_tokens(text)
    if not words:
        return []
    pieces: list[str] = []
    buffer: list[str] = []
    current = 0
    for word in words:
        cost = estimate_tokens(word)
        if buffer and current + cost > max_tokens:
            pieces.append(" ".join(buffer))
            buffer, current = [], 0
        buffer.append(word)
        current += cost
    if buffer:
        pieces.append(" ".join(buffer))
    return pieces


def _expand(paragraph: str, max_tokens: int) -> list[str]:
    """Zerlegt einen zu langen Absatz an Satzgrenzen, notfalls an Wortgrenzen."""
    if estimate_tokens(paragraph) <= max_tokens:
        return [paragraph]
    pieces: list[str] = []
    for sentence in split_sentences(paragraph):
        if estimate_tokens(sentence.text) <= max_tokens:
            pieces.append(sentence.text)
        else:
            pieces.extend(_split_by_tokens(sentence.text, max_tokens))
    return pieces or [paragraph]


def _overlap_tail(units: list[_Unit], overlap: int) -> tuple[list[_Unit], int]:
    kept: list[_Unit] = []
    total = 0
    for unit in reversed(units):
        cost = estimate_tokens(unit.text)
        if total + cost > overlap:
            break
        kept.insert(0, unit)
        total += cost
    return kept, total


def _pack(units: list[_Unit], max_tokens: int, overlap: int) -> list[list[_Unit]]:
    groups: list[list[_Unit]] = []
    current: list[_Unit] = []
    current_tokens = 0
    for unit in units:
        cost = estimate_tokens(unit.text)
        if current and current_tokens + cost > max_tokens:
            groups.append(current)
            current, current_tokens = _overlap_tail(current, overlap) if overlap else ([], 0)
        current.append(unit)
        current_tokens += cost
    if current:
        groups.append(current)
    return groups


def _make_chunk(document: Document, units: list[_Unit], document_type: str | None) -> Chunk:
    first = units[0]
    return Chunk(
        document_id=document.id,
        content="\n\n".join(unit.text for unit in units),
        section_id=first.section_id,
        metadata={
            "section": first.section_title,
            "section_path": first.section_path,
            "page": first.page,
            "language": document.language.value,
            "document_type": document_type,
            "paragraphs": len(units),
        },
    )


def _chunk_structural(
    document: Document,
    max_tokens: int,
    overlap: int,
    document_type: str | None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section, path in _iter_sections(document.sections):
        if not section.content.strip():
            continue
        units: list[_Unit] = []
        for paragraph in split_paragraphs(section.content):
            for piece in _expand(paragraph, max_tokens):
                units.append(
                    _Unit(
                        text=piece,
                        page=section.page,
                        section_id=section.id,
                        section_title=section.title,
                        section_path=path,
                    )
                )
        chunks.extend(
            _make_chunk(document, group, document_type)
            for group in _pack(units, max_tokens, overlap)
        )
    return chunks


def _chunk_fixed(
    document: Document,
    max_tokens: int,
    overlap: int,
    document_type: str | None,
) -> list[Chunk]:
    units = [
        _Unit(text=piece, page=None, section_title=None, section_path=[])
        for piece in _split_by_tokens(document.content, max_tokens)
    ]
    return [
        _make_chunk(document, group, document_type) for group in _pack(units, max_tokens, overlap)
    ]


def chunk_document(
    document: Document,
    *,
    strategy: ChunkStrategy | str = ChunkStrategy.STRUCTURAL,
    max_tokens: int = 512,
    overlap: int = 64,
    document_type: str | None = None,
) -> list[Chunk]:
    """Zerlegt ein Dokument in Chunks."""
    resolved = ChunkStrategy(strategy)
    if max_tokens <= 0:
        raise ValueError("max_tokens muss größer als 0 sein.")
    if overlap < 0:
        raise ValueError("overlap darf nicht negativ sein.")

    if resolved is ChunkStrategy.FIXED:
        return _chunk_fixed(document, max_tokens, overlap, document_type)
    if not document.sections:
        document = document.model_copy(
            update={"sections": [Section(title=document.title, level=1, content=document.content)]}
        )
    return _chunk_structural(document, max_tokens, overlap, document_type)


def chunk_text(
    text: str,
    *,
    strategy: ChunkStrategy | str = ChunkStrategy.STRUCTURAL,
    max_tokens: int = 512,
    overlap: int = 64,
    document_type: str | None = None,
) -> list[Chunk]:
    """Zerlegt reinen Text in Chunks."""
    document = Document.from_text(text)
    return chunk_document(
        document,
        strategy=strategy,
        max_tokens=max_tokens,
        overlap=overlap,
        document_type=document_type,
    )
