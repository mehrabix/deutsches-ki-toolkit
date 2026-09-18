"""Regressionstests für gefundene deutsche Sprachfälle.

Jeder Fehler, der einmal gefunden wurde, bekommt hier einen Test. Die Fälle
stammen aus echten Problemen und bleiben dauerhaft abgesichert.
"""

from __future__ import annotations

from deutsches_ki.core.models import Chunk
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.retrieval import InMemoryRetriever
from deutsches_ki.text.compounds import analyze_compound
from deutsches_ki.text.tokens import search_tokens


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
