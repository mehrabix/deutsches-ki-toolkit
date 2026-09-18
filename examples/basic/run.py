"""Grundbeispiel: von einem Dokument zur belegten Antwort.

Aufruf aus dem Projektordner:

    python examples/basic/run.py
"""

from pathlib import Path

from deutsches_ki import GermanDocument

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"


def main() -> None:
    document = GermanDocument.from_file(FIXTURES / "vertrag.md")

    print(f"Titel: {document.title}")
    print(f"Abschnitte: {len(document.document.iter_sections())}")

    entities = document.detect_pii()
    print(f"Sensible Stellen: {[entity.type.value for entity in entities]}")

    chunks = document.chunk(max_tokens=64)
    print(f"Chunks: {len(chunks)}")

    answer = document.search("Wie lange ist die Zahlungsfrist?")
    print("\nAntwort:")
    print(answer.answer)
    print("\nQuellen:")
    for citation in answer.citations[:3]:
        print(f"  {citation.section} (Konfidenz {answer.confidence:.2f})")


if __name__ == "__main__":
    main()
