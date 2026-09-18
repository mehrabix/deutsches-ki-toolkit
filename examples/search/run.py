"""Mehrere Dokumente durchsuchen.

Aufruf aus dem Projektordner:

    python examples/search/run.py
"""

from pathlib import Path

from deutsches_ki.chunking import chunk_document
from deutsches_ki.documents import parse
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.retrieval import InMemoryRetriever

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"
QUESTIONS = (
    "Wie lange ist die Zahlungsfrist?",
    "Was passiert bei verspäteter Zahlung?",
    "Wie lange ist die Kündigungsfrist?",
    "Wann muss die Arbeitsunfähigkeitsbescheinigung vorliegen?",
)


def main() -> None:
    chunks = []
    for file in sorted(FIXTURES.glob("*")):
        if file.suffix.lower() not in {".md", ".txt"}:
            continue
        chunks.extend(chunk_document(parse(file), max_tokens=64))

    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(chunks)
    print(f"{len(chunks)} Chunks aus {FIXTURES}\n")

    for question in QUESTIONS:
        results = retriever.search(question, top_k=2)
        print(f"Frage: {question}")
        for rank, result in enumerate(results, start=1):
            section = result.chunk.section or "–"
            preview = result.chunk.content[:80].replace("\n", " ")
            print(f"  {rank}. [{section}] {preview}")
        print()


if __name__ == "__main__":
    main()
