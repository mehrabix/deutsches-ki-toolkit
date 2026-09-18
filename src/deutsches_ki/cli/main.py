"""Die Kommandozeile ``deutsches-ki``."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from deutsches_ki import __version__
from deutsches_ki.chunking import chunk_document
from deutsches_ki.config import Settings
from deutsches_ki.core.models import Chunk, Document, Entity
from deutsches_ki.documents.parse import (
    DOCLING_SUFFIXES,
    MARKDOWN_SUFFIXES,
    TEXT_SUFFIXES,
    parse,
)
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.errors import DeutschesKiError
from deutsches_ki.pii import anonymize, detect
from deutsches_ki.retrieval import InMemoryRetriever

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Deutschsprachige KI-Infrastruktur für Dokumente, Datenschutz und Suche.",
)
console = Console()

_SUPPORTED_SUFFIXES = TEXT_SUFFIXES | MARKDOWN_SUFFIXES | DOCLING_SUFFIXES


@app.callback(invoke_without_command=True)
def _callback(
    version: Annotated[
        bool,
        typer.Option("--version", help="Version anzeigen und beenden.", is_eager=True),
    ] = False,
) -> None:
    if version:
        console.print(f"deutsches-ki-toolkit {__version__}")
        raise typer.Exit()


def _load(path: Path) -> Document:
    try:
        return parse(path)
    except DeutschesKiError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error


def _source_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        console.print(f"[red]Pfad nicht gefunden: {target}[/red]")
        raise typer.Exit(code=1)
    return sorted(
        path
        for path in target.rglob("*")
        if path.is_file() and path.suffix.lower() in _SUPPORTED_SUFFIXES
    )


def _chunks_for(target: Path, settings: Settings) -> list[Chunk]:
    chunks: list[Chunk] = []
    for file in _source_files(target):
        try:
            document = parse(file)
        except DeutschesKiError as error:
            console.print(f"[yellow]Übersprungen: {file} ({error})[/yellow]")
            continue
        chunks.extend(
            chunk_document(
                document,
                strategy=settings.chunking.strategy,
                max_tokens=settings.chunking.max_tokens,
                overlap=settings.chunking.overlap,
                document_type=settings.document_type,
            )
        )
    return chunks


def _entities_table(entities: list[Entity]) -> Table:
    table = Table(title="Erkannte sensible Stellen")
    table.add_column("Typ")
    table.add_column("Text")
    table.add_column("Position", justify="right")
    table.add_column("Konfidenz", justify="right")
    for entity in entities:
        table.add_row(entity.type.value, entity.text, str(entity.start), f"{entity.confidence:.2f}")
    return table


@app.command("parse")
def parse_cmd(
    path: Annotated[Path, typer.Argument(help="Dokument, das eingelesen wird.")],
) -> None:
    """Zeigt die erkannte Struktur eines Dokuments."""
    document = _load(path)
    console.print(f"[bold]{document.title or path.name}[/bold] ({document.language.value})")

    table = Table(title="Abschnitte")
    table.add_column("Ebene", justify="right")
    table.add_column("Titel")
    table.add_column("Zeichen", justify="right")
    for section in document.iter_sections():
        table.add_row(str(section.level), section.title or "–", str(len(section.content)))
    console.print(table)


@app.command("pii")
def pii_cmd(
    path: Annotated[Path, typer.Argument(help="Dokument, das geprüft wird.")],
    json_output: Annotated[bool, typer.Option("--json", help="Ausgabe als JSON.")] = False,
    min_confidence: Annotated[
        float, typer.Option("--min-confidence", help="Nur Treffer ab dieser Konfidenz.")
    ] = 0.0,
) -> None:
    """Findet sensible Stellen in einem Dokument."""
    document = _load(path)
    entities = detect(document.content, min_confidence=min_confidence)

    if json_output:
        payload = [entity.model_dump(mode="json") for entity in entities]
        console.print_json(json.dumps(payload, ensure_ascii=False))
        return
    if not entities:
        console.print("[green]Keine sensiblen Stellen gefunden.[/green]")
        return
    console.print(_entities_table(entities))


@app.command("anonymize")
def anonymize_cmd(
    path: Annotated[Path, typer.Argument(help="Dokument, das bereinigt wird.")],
    mode: Annotated[
        str, typer.Option("--mode", help="redact, replace, mask, hash oder pseudonymize.")
    ] = "redact",
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Zieldatei für den bereinigten Text.")
    ] = None,
) -> None:
    """Entfernt sensible Stellen aus einem Dokument."""
    document = _load(path)
    try:
        result = anonymize(document.content, mode=mode)
    except ValueError as error:
        console.print(f"[red]Unbekannte Betriebsart: {mode}. {error}[/red]")
        raise typer.Exit(code=1) from error

    if output is not None:
        output.write_text(result.text, encoding="utf-8")
        console.print(f"[green]Geschrieben: {output}[/green]")
        return
    console.print(result.text)


@app.command("chunk")
def chunk_cmd(
    path: Annotated[Path, typer.Argument(help="Dokument, das zerlegt wird.")],
    strategy: Annotated[
        str, typer.Option("--strategy", help="structural oder fixed.")
    ] = "structural",
    max_tokens: Annotated[int, typer.Option("--max-tokens", help="Obergrenze je Chunk.")] = 512,
    overlap: Annotated[int, typer.Option("--overlap", help="Überlappung in Token.")] = 64,
) -> None:
    """Zerlegt ein Dokument in Chunks."""
    document = _load(path)
    try:
        chunks = chunk_document(document, strategy=strategy, max_tokens=max_tokens, overlap=overlap)
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    table = Table(title=f"{len(chunks)} Chunks")
    table.add_column("#", justify="right")
    table.add_column("Abschnitt")
    table.add_column("Zeichen", justify="right")
    table.add_column("Anfang")
    for index, chunk in enumerate(chunks, start=1):
        preview = chunk.content[:60].replace("\n", " ")
        table.add_row(str(index), chunk.section or "–", str(len(chunk.content)), preview)
    console.print(table)


@app.command("embed")
def embed_cmd(
    directory: Annotated[Path, typer.Argument(help="Ordner oder Datei.")],
    model: Annotated[str, typer.Option("--model", help="Embedding-Modell.")] = "hashing",
) -> None:
    """Zerlegt Dokumente und berechnet Embeddings."""
    settings = Settings(embeddings=Settings().embeddings.model_copy(update={"provider": model}))
    chunks = _chunks_for(directory, settings)
    if not chunks:
        console.print("[yellow]Keine passenden Dateien gefunden.[/yellow]")
        raise typer.Exit(code=1)

    embedder = get_embedder(model)
    vectors = embedder.embed_documents([chunk.content for chunk in chunks])
    console.print(
        f"[green]{len(chunks)} Chunks eingebettet "
        f"({len(vectors)} Vektoren à {embedder.dimension} Dimensionen).[/green]"
    )


@app.command("search")
def search_cmd(
    directory: Annotated[Path, typer.Argument(help="Ordner oder Datei.")],
    question: Annotated[str, typer.Argument(help="Frage an die Dokumente.")],
    top_k: Annotated[int, typer.Option("--top-k", help="Anzahl der Treffer.")] = 5,
    model: Annotated[str, typer.Option("--model", help="Embedding-Modell.")] = "hashing",
) -> None:
    """Sucht in Dokumenten und gibt Fundstellen aus."""
    settings = Settings(embeddings=Settings().embeddings.model_copy(update={"provider": model}))
    chunks = _chunks_for(directory, settings)
    if not chunks:
        console.print("[yellow]Keine passenden Dateien gefunden.[/yellow]")
        raise typer.Exit(code=1)

    retriever = InMemoryRetriever(get_embedder(model))
    retriever.add(chunks)
    results = retriever.search(question, top_k=top_k)
    if not results:
        console.print("[yellow]Keine Treffer.[/yellow]")
        raise typer.Exit(code=1)

    console.print(results[0].chunk.content)
    console.print("\n[bold]Quellen:[/bold]")
    for result in results:
        page = result.chunk.metadata.get("page")
        location = f" (Seite {page})" if page else ""
        console.print(f"  {result.chunk.section or '–'}{location}")


@app.command("ingest")
def ingest_cmd(
    directory: Annotated[Path, typer.Argument(help="Ordner mit Dokumenten.")],
) -> None:
    """Nimmt Dokumente in PostgreSQL auf (noch nicht verfügbar)."""
    console.print(
        "[yellow]Noch nicht verfügbar: Die PostgreSQL-Anbindung (pgvector) folgt "
        "im nächsten Schritt. Nutze solange 'search', das im Arbeitsspeicher sucht.[/yellow]"
    )
    raise typer.Exit(code=1)


@app.command("ask")
def ask_cmd(
    question: Annotated[str, typer.Argument(help="Frage an die Dokumente.")],
) -> None:
    """Beantwortet eine Frage mit einem Sprachmodell (noch nicht verfügbar)."""
    console.print(
        "[yellow]Noch nicht verfügbar: Die Anbindung von Ollama und vLLM folgt im "
        "nächsten Schritt. Nutze solange 'search', das belegte Fundstellen liefert.[/yellow]"
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":  # pragma: no cover
    app()
