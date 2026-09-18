"""Sensible Stellen finden und auf fünf Weisen ersetzen.

Aufruf aus dem Projektordner:

    python examples/pii/run.py
"""

from pathlib import Path

from deutsches_ki.pii import anonymize, detect

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"

MODES = ("redact", "replace", "mask", "hash", "pseudonymize")


def main() -> None:
    text = (FIXTURES / "rechnung.txt").read_text(encoding="utf-8")

    print("Gefundene Stellen:")
    for entity in detect(text):
        print(f"  {entity.type.value:24} {entity.text[:40]:42} {entity.confidence:.2f}")

    for mode in MODES:
        result = anonymize(text, mode=mode, key="beispiel")
        first_line = next(
            line for line in result.text.splitlines() if "DE" in line or "IBAN" in line
        )
        print(f"\n{mode:14} {first_line.strip()}")


if __name__ == "__main__":
    main()
