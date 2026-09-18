"""Erzeugt ein kleines synthetisches PDF als Testdatei.

Das PDF wird von Hand geschrieben, damit die Testdatei erzeugbar bleibt und
nicht als undurchsichtiges Binärstück im Repository liegt. Deutsche Zeichen
kommen über ``WinAnsiEncoding``; damit sind Umlaute, ß und § abgedeckt.

Aufruf aus dem Projektordner:

    python scripts/generate_pdf_fixture.py
"""

from __future__ import annotations

from pathlib import Path

TARGET = Path(__file__).resolve().parent.parent / "datasets" / "fixtures" / "vertrag.pdf"

LINES = [
    "Rahmenvertrag",
    "",
    "§ 1 Vertragsgegenstand",
    "Der Auftraggeber beauftragt die Beispiel GmbH mit der Lieferung und",
    "Instandhaltung der Anlagen am Standort Hamburg.",
    "",
    "§ 2 Vergütung",
    "Die Vergütung richtet sich nach dem vereinbarten Arbeitsauftrag.",
    "",
    "§ 4 Zahlungsbedingungen",
    "(1) Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.",
    "(2) Bei verspäteter Zahlung fallen Verzugszinsen an.",
    "",
    "§ 7 Kündigung",
    "Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
    "Kündigungen bedürfen der Schriftform.",
]


def _escape(text: str) -> str:
    """Maskiert die Zeichen, die in einem PDF-String Bedeutung haben."""
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines: list[str]) -> bytes:
    """Baut ein einseitiges PDF mit den angegebenen Zeilen."""
    operations = ["BT", "/F1 11 Tf", "14 TL", "50 800 Td"]
    for line in lines:
        operations.append(f"({_escape(line)}) Tj")
        operations.append("T*")
    operations.append("ET")
    content = "\n".join(operations).encode("cp1252")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii")
    out += f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    return bytes(out)


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(build_pdf(LINES))
    print(f"Geschrieben: {TARGET} ({TARGET.stat().st_size} Bytes)")


if __name__ == "__main__":
    main()
