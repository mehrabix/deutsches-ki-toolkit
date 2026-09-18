"""Regressionstests für gefundene deutsche Sprachfälle.

Jeder Fehler, der einmal gefunden wurde, bekommt hier einen Test. Die Fälle
stammen aus echten Problemen und bleiben dauerhaft abgesichert.
"""

from __future__ import annotations

from pathlib import Path

from deutsches_ki.chunking import chunk_document
from deutsches_ki.core.models import Chunk
from deutsches_ki.documents import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.retrieval import InMemoryRetriever
from deutsches_ki.text.compounds import analyze_compound
from deutsches_ki.text.tokens import search_tokens

FIXTURES = Path(__file__).resolve().parents[3] / "datasets" / "fixtures"


def test_umlaut_compound_is_split_after_folding() -> None:
    """Gefunden: „Kündigungsfrist“ wurde nicht zerlegt.

    Die Suchform faltet ü zu ue, die Wortliste enthält aber „Kündigung“ mit
    Umlaut. Der Vergleich läuft deshalb über die gefaltete Form.
    """
    tokens = search_tokens("Kündigungsfrist")
    assert "kuendigungsfrist" in tokens
    assert "kuendigung" in tokens
    assert "frist" in tokens


def test_umlaut_compound_keeps_original_parts() -> None:
    analysis = analyze_compound("Kündigungsfrist")
    assert analysis.is_compound is True
    assert [part.lower() for part in analysis.parts] == ["kündigung", "frist"]


def test_search_finds_umlaut_compound_by_part() -> None:
    """Gefunden: Eine Suche nach „Frist“ fand den Kündigungsabschnitt nicht."""
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(
        [
            Chunk(content="Die Kündigungsfrist beträgt drei Monate."),
            Chunk(content="Das Wetter ist heute freundlich."),
        ]
    )
    results = retriever.search("Frist")
    assert results
    assert results[0].chunk.content.startswith("Die Kündigungsfrist")


def test_sharp_s_compound_matches() -> None:
    """ß und ss dürfen die Zerlegung nicht verhindern."""
    tokens = search_tokens("Geschäftsstraße")
    assert "geschaeftsstrasse" in tokens


def test_section_title_is_indexed() -> None:
    """Gefunden: Der Abschnittstitel wurde nicht indiziert.

    Eine Frage nach der „Zahlungsfrist“ fand den Abschnitt
    „§ 4 Zahlungsbedingungen“ nicht, weil im Text nur von „Zahlung“ die Rede
    ist. Der Titel muss deshalb mit in den Index.
    """
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(
        [
            Chunk(
                content="Die Zahlung ist innerhalb von 30 Tagen fällig.",
                metadata={"section": "§ 4 Zahlungsbedingungen"},
            ),
            Chunk(
                content="Die Kündigungsfrist beträgt drei Monate.",
                metadata={"section": "§ 7 Kündigung"},
            ),
        ]
    )
    results = retriever.search("Wie lange ist die Zahlungsfrist?")
    assert results
    assert results[0].chunk.metadata["section"] == "§ 4 Zahlungsbedingungen"


def test_search_order_is_stable_across_runs() -> None:
    """Gefunden: Das Suchergebnis hing von der zufälligen Chunk-Kennung ab.

    Bei gleicher Punktzahl entschied die per ``uuid4`` erzeugte Kennung, welcher
    Chunk zuerst kam. Dadurch schwankte das Ergebnis zwischen Läufen. Jetzt
    entscheidet die Reihenfolge im Index.
    """
    orders: set[tuple[str | None, ...]] = set()
    for _ in range(8):
        document = parse(FIXTURES / "vertrag.md")
        retriever = InMemoryRetriever(get_embedder("hashing"))
        retriever.add(chunk_document(document, max_tokens=64))
        results = retriever.search("Wie lange ist die Zahlungsfrist?")
        orders.add(tuple(result.chunk.metadata["section"] for result in results))
    assert len(orders) == 1
