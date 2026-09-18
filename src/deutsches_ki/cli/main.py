"""Die Kommandozeile ``deutsches-ki``."""

import contextlib
import json
import sys
from pathlib import Path
from typing import Annotated, Any

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
from deutsches_ki.evaluation import EvaluationDataset, evaluate_retriever
from deutsches_ki.pii import anonymize, detect
from deutsches_ki.providers import ChatProvider, get_provider
from deutsches_ki.rag import DeutschRAG
from deutsches_ki.reranking import get_reranker
from deutsches_ki.retrieval import InMemoryRetriever
from deutsches_ki.security import scan_text
from deutsches_ki.storage import PgVectorStore

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Deutschsprachige KI-Infrastruktur für Dokumente, Datenschutz und Suche.",
)
console = Console()

_SUPPORTED_SUFFIXES = TEXT_SUFFIXES | MARKDOWN_SUFFIXES | DOCLING_SUFFIXES


def _ensure_utf8_output() -> None:
    """Sorgt dafür, dass deutsche Zeichen auch unter Windows korrekt ankommen."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is None:  # pragma: no cover - plattformabhängig
        return
    with contextlib.suppress(ValueError, OSError):  # pragma: no cover - plattformabhängig
        reconfigure(encoding="utf-8")


@app.callback(invoke_without_command=True)
def _callback(
    version: Annotated[
        bool,
        typer.Option("--version", help="Version anzeigen und beenden.", is_eager=True),
    ] = False,
) -> None:
    _ensure_utf8_output()
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


@app.command("scan")
def scan_cmd(
    path: Annotated[Path, typer.Argument(help="Dokument, das geprüft wird.")],
    json_output: Annotated[bool, typer.Option("--json", help="Ausgabe als JSON.")] = False,
) -> None:
    """Prüft ein Dokument auf Prompt-Injection und Geheimnisse."""
    document = _load(path)
    report = scan_text(document.content)

    if json_output:
        console.print_json(report.model_dump_json())
        return
    if report.is_clean:
        console.print("[green]Keine Auffälligkeiten gefunden.[/green]")
        return

    table = Table(title="Auffälligkeiten")
    table.add_column("Art")
    table.add_column("Regel")
    table.add_column("Einstufung")
    table.add_column("Fund")
    for finding in report.injections:
        table.add_row("Injection", finding.rule, finding.severity, finding.text[:50])
    for secret in report.secrets:
        table.add_row("Geheimnis", secret.rule, secret.severity, secret.masked)
    console.print(table)


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


def _build_rag(directory: Path, settings: Settings, model: str) -> DeutschRAG:
    chunks = _chunks_for(directory, settings)
    if not chunks:
        console.print("[yellow]Keine passenden Dateien gefunden.[/yellow]")
        raise typer.Exit(code=1)
    retriever = InMemoryRetriever(get_embedder(model))
    retriever.add(chunks)

    reranker = get_reranker(settings.reranking.provider) if settings.reranking.enabled else None
    return DeutschRAG(
        retriever,
        reranker=reranker,
        llm=_llm_from_settings(settings),
        candidates=settings.retrieval.top_k,
        top_k=min(settings.reranking.top_k, settings.retrieval.top_k),
    )


def _llm_from_settings(settings: Settings) -> ChatProvider | None:
    """Baut den Anbieter aus der Konfiguration, falls einer eingetragen ist."""
    provider = settings.llm.provider
    if not provider:
        return None
    kwargs: dict[str, Any] = {}
    if settings.llm.model:
        kwargs["model"] = settings.llm.model
    if provider == "ollama":
        if settings.llm.base_url:
            kwargs["host"] = settings.llm.base_url
    else:
        if settings.llm.base_url:
            kwargs["base_url"] = settings.llm.base_url
        if settings.llm.api_key:
            kwargs["api_key"] = settings.llm.api_key
    return get_provider(provider, **kwargs)


def _print_answer(answer_text: str, citations: list[Any]) -> None:
    console.print(answer_text or "[yellow]Keine Antwort gefunden.[/yellow]")
    if citations:
        console.print("\n[bold]Quellen:[/bold]")
        for citation in citations:
            page = f" (Seite {citation.page})" if citation.page else ""
            console.print(f"  {citation.document} – {citation.section or '–'}{page}")


@app.command("ingest")
def ingest_cmd(
    directory: Annotated[Path, typer.Argument(help="Ordner mit Dokumenten.")],
    dsn: Annotated[
        str | None, typer.Option("--dsn", help="PostgreSQL-DSN. Sonst aus der Konfiguration.")
    ] = None,
    model: Annotated[str, typer.Option("--model", help="Embedding-Modell.")] = "hashing",
    drop: Annotated[bool, typer.Option("--drop", help="Tabellen vorher entfernen.")] = False,
) -> None:
    """Nimmt Dokumente in PostgreSQL mit pgvector auf."""
    settings = Settings.load()
    target = dsn or settings.storage.dsn
    if not target:
        console.print(
            "[yellow]Kein DSN angegeben. Nutze --dsn oder trage storage.dsn in "
            "deutsches-ki.yaml ein.[/yellow]"
        )
        raise typer.Exit(code=1)

    embedder = get_embedder(model)
    store = PgVectorStore(target, embedder=embedder)
    if drop:
        store.drop_schema()
    store.create_schema()

    files = _source_files(directory)
    documents = 0
    chunks_total = 0
    for file in files:
        try:
            document = parse(file)
        except DeutschesKiError as error:
            console.print(f"[yellow]Übersprungen: {file} ({error})[/yellow]")
            continue
        chunks = chunk_document(
            document,
            strategy=settings.chunking.strategy,
            max_tokens=settings.chunking.max_tokens,
            overlap=settings.chunking.overlap,
            document_type=settings.document_type,
        )
        if not chunks:
            continue
        store.add_document(document)
        for chunk in chunks:
            chunk.document_id = document.id
        store.add_chunks(chunks)
        documents += 1
        chunks_total += len(chunks)

    store.close()
    console.print(f"[green]{documents} Dokumente, {chunks_total} Chunks aufgenommen.[/green]")


@app.command("ask")
def ask_cmd(
    question: Annotated[str, typer.Argument(help="Frage an die Dokumente.")],
    directory: Annotated[Path, typer.Option("--corpus", help="Ordner mit Dokumenten.")] = Path("."),
    top_k: Annotated[int, typer.Option("--top-k", help="Anzahl der Quellen.")] = 5,
    model: Annotated[str, typer.Option("--model", help="Embedding-Modell.")] = "hashing",
) -> None:
    """Beantwortet eine Frage mit Quellenangabe.

    Ohne eingetragenes Sprachmodell kommt der bestpassende Abschnitt zurück,
    ausdrücklich als Auswahl und nicht als formulierte Antwort.
    """
    settings = Settings.load()
    if settings.llm.provider is None:
        console.print(
            "[yellow]Kein Sprachmodell eingetragen. Es wird der bestpassende "
            "Abschnitt ausgegeben. Trage llm.provider in deutsches-ki.yaml ein, "
            "zum Beispiel 'ollama'.[/yellow]\n"
        )
    rag = _build_rag(directory, settings, model)
    answer = rag.ask(question, top_k=top_k)
    _print_answer(answer.answer, answer.citations)


@app.command("evaluate")
def evaluate_cmd(
    dataset: Annotated[Path, typer.Argument(help="Datensatz als YAML oder JSON.")],
    corpus: Annotated[Path, typer.Option("--corpus", help="Ordner mit Dokumenten.")] = Path(
        "datasets/fixtures"
    ),
    top_k: Annotated[
        int, typer.Option("--top-k", help="Wie viele Treffer ausgewertet werden.")
    ] = 10,
    model: Annotated[str, typer.Option("--model", help="Embedding-Modell.")] = "hashing",
    json_output: Annotated[bool, typer.Option("--json", help="Bericht als JSON.")] = False,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Bericht als Datei ablegen.")
    ] = None,
) -> None:
    """Bewertet die Suche gegen einen Datensatz mit erwarteten Fundstellen."""
    settings = Settings.load()
    try:
        cases = EvaluationDataset.from_file(dataset)
    except DeutschesKiError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    chunks = _chunks_for(corpus, settings)
    if not chunks:
        console.print("[yellow]Keine passenden Dateien im Korpus gefunden.[/yellow]")
        raise typer.Exit(code=1)

    retriever = InMemoryRetriever(get_embedder(model))
    retriever.add(chunks)
    report = evaluate_retriever(retriever, cases, top_k=top_k)

    payload = report.model_dump(mode="json")
    if output is not None:
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[green]Bericht geschrieben: {output}[/green]")
    if json_output:
        console.print_json(json.dumps(payload, ensure_ascii=False))
        return

    table = Table(title=f"Bewertung: {report.dataset} ({report.cases} Fälle)")
    table.add_column("Metrik")
    table.add_column("Wert", justify="right")
    table.add_row("Recall@1", f"{report.recall.get('1', 0.0):.2f}")
    table.add_row("Recall@5", f"{report.recall.get('5', 0.0):.2f}")
    table.add_row("Recall@10", f"{report.recall.get('10', 0.0):.2f}")
    table.add_row("MRR", f"{report.mrr:.2f}")
    table.add_row("nDCG@5", f"{report.ndcg.get('5', 0.0):.2f}")
    table.add_row("Trefferquote@5", f"{report.hit_rate.get('5', 0.0):.2f}")
    console.print(table)

    if report.unanswered:
        console.print("\n[bold]Ohne Treffer:[/bold]")
        for question in report.unanswered:
            console.print(f"  – {question}")


if __name__ == "__main__":  # pragma: no cover
    app()
