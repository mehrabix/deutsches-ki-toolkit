"""Die Werkzeuge, die der MCP-Server anbietet.

Bewusst als reine Funktionen ohne MCP-Abhängigkeit. So lassen sie sich ohne
installierte Erweiterung prüfen, und der Server ist nur eine dünne Hülle.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deutsches_ki.chunking import chunk_document
from deutsches_ki.documents.parse import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.errors import DeutschesKiError
from deutsches_ki.evaluation import EvaluationDataset, evaluate_retriever
from deutsches_ki.pii import anonymize, detect
from deutsches_ki.retrieval import InMemoryRetriever
from deutsches_ki.security import scan_text
from deutsches_ki.text import (
    analyze_compound,
    normalize_german,
    split_sentences,
)

__all__ = ["ToolSpec", "call_tool", "list_tools"]

_SUFFIXES = {".txt", ".text", ".log", ".md", ".markdown"}


@dataclass(frozen=True)
class ToolSpec:
    """Ein Werkzeug mit Name, Beschreibung und Funktion."""

    name: str
    description: str
    handler: Callable[..., dict[str, Any]]


def _entities(text: str) -> list[dict[str, Any]]:
    return [entity.model_dump(mode="json") for entity in detect(text)]


def parse_german_document(path: str) -> dict[str, Any]:
    """Liest ein Dokument ein und gibt seine Abschnittsstruktur zurück."""
    document = parse(Path(path))
    return {
        "source": document.source,
        "title": document.title,
        "language": document.language.value,
        "sections": [
            {
                "level": section.level,
                "title": section.title,
                "page": section.page,
                "characters": len(section.content),
            }
            for section in document.iter_sections()
        ],
    }


def detect_german_pii(path: str) -> dict[str, Any]:
    """Findet sensible Stellen in einem Dokument."""
    document = parse(Path(path))
    entities = _entities(document.content)
    return {"source": document.source, "count": len(entities), "entities": entities}


def anonymize_german_document(
    text: str,
    mode: str = "redact",
    key: str | None = None,
) -> dict[str, Any]:
    """Ersetzt sensible Stellen in übergebenem Text."""
    try:
        result = anonymize(text, mode=mode, key=key)
    except ValueError as error:
        return {"error": f"Unbekannte Betriebsart: {mode}", "detail": str(error)}
    return {
        "text": result.text,
        "mapping": result.mapping,
        "count": len(result.entities),
    }


def scan_german_document(path: str) -> dict[str, Any]:
    """Prüft ein Dokument auf Prompt-Injection und Geheimnisse."""
    document = parse(Path(path))
    return scan_text(document.content).model_dump(mode="json")


def analyze_german_text(text: str) -> dict[str, Any]:
    """Zerlegt deutschen Text: Sätze, Suchform, Komposita."""
    sentences = split_sentences(text)
    words = [word for sentence in sentences for word in sentence.text.split()]
    compounds = []
    for word in words:
        cleaned = word.strip(".,;:()[]\"'").strip()
        analysis = analyze_compound(cleaned)
        if analysis.is_compound:
            compounds.append({"word": cleaned, "parts": analysis.parts})
    return {
        "sentences": [sentence.text for sentence in sentences],
        "sentence_count": len(sentences),
        "search_form": normalize_german(text, mode="search"),
        "compounds": compounds,
    }


def _chunks_from(directory: str) -> list[Any]:
    target = Path(directory)
    files = [target] if target.is_file() else sorted(target.rglob("*"))
    chunks = []
    for file in files:
        if not file.is_file() or file.suffix.lower() not in _SUFFIXES:
            continue
        try:
            document = parse(file)
        except DeutschesKiError:
            continue
        chunks.extend(chunk_document(document, max_tokens=512))
    return chunks


def search_german_documents(
    directory: str,
    question: str,
    top_k: int = 5,
) -> dict[str, Any]:
    """Sucht in einem Ordner und gibt belegte Fundstellen zurück."""
    chunks = _chunks_from(directory)
    if not chunks:
        return {"question": question, "count": 0, "results": []}

    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(chunks)
    results = retriever.search(question, top_k=top_k)
    return {
        "question": question,
        "count": len(results),
        "results": [
            {
                "document": result.chunk.metadata.get("document"),
                "section": result.chunk.section,
                "page": result.chunk.metadata.get("page"),
                "content": result.chunk.content,
                "score": result.score,
            }
            for result in results
        ],
    }


def evaluate_german_rag(
    dataset: str,
    corpus: str,
    top_k: int = 10,
) -> dict[str, Any]:
    """Bewertet die Suche gegen einen Datensatz."""
    cases = EvaluationDataset.from_file(dataset)
    chunks = _chunks_from(corpus)
    if not chunks:
        return {"error": "Keine passenden Dateien im Korpus gefunden."}
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(chunks)
    return evaluate_retriever(retriever, cases, top_k=top_k).model_dump(mode="json")


_TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="parse_german_document",
        description="Liest ein Dokument ein und gibt seine Abschnittsstruktur zurück.",
        handler=parse_german_document,
    ),
    ToolSpec(
        name="detect_german_pii",
        description=(
            "Findet deutsche sensible Daten in einem Dokument: IBAN, Steuer-ID, "
            "Steuernummer, Adresse, Telefon und weitere."
        ),
        handler=detect_german_pii,
    ),
    ToolSpec(
        name="anonymize_german_document",
        description="Ersetzt sensible Stellen: redact, replace, mask, hash oder pseudonymize.",
        handler=anonymize_german_document,
    ),
    ToolSpec(
        name="scan_german_document",
        description="Prüft ein Dokument auf Prompt-Injection und Geheimnisse.",
        handler=scan_german_document,
    ),
    ToolSpec(
        name="analyze_german_text",
        description="Zerlegt deutschen Text in Sätze und Komposita.",
        handler=analyze_german_text,
    ),
    ToolSpec(
        name="search_german_documents",
        description="Sucht in einem Ordner mit deutschen Dokumenten und liefert Fundstellen.",
        handler=search_german_documents,
    ),
    ToolSpec(
        name="evaluate_german_rag",
        description="Bewertet die Suche gegen einen Datensatz mit erwarteten Fundstellen.",
        handler=evaluate_german_rag,
    ),
)


def list_tools() -> list[ToolSpec]:
    """Alle angebotenen Werkzeuge."""
    return list(_TOOLS)


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Ruft ein Werkzeug beim Namen auf."""
    for spec in _TOOLS:
        if spec.name == name:
            try:
                return spec.handler(**arguments)
            except DeutschesKiError as error:
                return {"error": str(error)}
    raise KeyError(f"Unbekanntes Werkzeug: {name}")


def tools_as_json() -> str:
    """Die Werkzeugliste als JSON, für Protokolle und Tests."""
    return json.dumps(
        [{"name": spec.name, "description": spec.description} for spec in _TOOLS],
        ensure_ascii=False,
        indent=2,
    )
