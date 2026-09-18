"""Strukturbasiertes Chunking im Vergleich zum festen Schnitt.

Aufruf aus dem Projektordner:

    python examples/chunking/run.py
"""

from pathlib import Path

from deutsches_ki.chunking import chunk_document
from deutsches_ki.documents import parse

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"


def main() -> None:
    document = parse(FIXTURES / "vertrag.md")

    for strategy in ("structural", "fixed"):
        chunks = chunk_document(document, strategy=strategy, max_tokens=48, overlap=0)
        print(f"\n=== {strategy} ({len(chunks)} Chunks) ===")
        for index, chunk in enumerate(chunks, start=1):
            section = chunk.section or "–"
            preview = chunk.content[:70].replace("\n", " ")
            print(f"{index:>2}. [{section}] {preview}")


if __name__ == "__main__":
    main()
