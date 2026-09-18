"""Ein Dokument einlesen und seine Struktur anzeigen.

Aufruf aus dem Projektordner:

    python examples/document/run.py
"""

from pathlib import Path

from deutsches_ki.documents import parse

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"


def main() -> None:
    document = parse(FIXTURES / "vertrag.md")

    print(f"Quelle:  {document.source}")
    print(f"Titel:   {document.title}")
    print(f"Sprache: {document.language.value}")
    print("\nStruktur:")
    for section in document.iter_sections():
        indent = "  " * max(0, section.level - 1)
        title = section.title or "(ohne Titel)"
        print(f"{indent}- {title} [{len(section.content)} Zeichen]")


if __name__ == "__main__":
    main()
