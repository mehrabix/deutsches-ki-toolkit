"""Absätze innerhalb eines Abschnitts.

Ein Paragraph gliedert sich in Absätze: „(1)“, „(2)“. Die Marke ist keine
Satzgrenze, sondern eine eigene Ebene zwischen Abschnitt und Satz. Ohne sie
lässt sich „§ 4 Abs. 2“ nicht als Einheit adressieren, und ein Chunk mitten in
einem Paragraphen kann nicht sagen, zu welchem Absatz er gehört.
"""

from __future__ import annotations

import re

from deutsches_ki.core.models import Absatz

__all__ = ["ABSATZ_MARKER", "split_absaetze"]

# „(1)“, „(2)“, „(12)“ und Zwischenformen wie „(2a)“. Die Marke beginnt eine
# Zeile; Text davor gehört zu einem Absatz ohne Marke.
ABSATZ_MARKER = re.compile(r"^\((\d{1,3}[a-z]?)\)[ \t]*")


def split_absaetze(text: str) -> list[Absatz]:
    """Zerlegt den Inhalt eines Abschnitts in Absätze.

    ``text`` bleibt der Absatz wie im Dokument, die Marke eingeschlossen. Sie
    ist Teil des Textes und darf nicht verloren gehen: ein Chunk, der „(2) Die
    Vergütung …“ enthält, zeigt die Gliederung mit an. ``marker`` trägt dieselbe
    Angabe zum Adressieren.

    Text vor der ersten Marke bildet einen Absatz ohne Marke. Ein Abschnitt ohne
    Marken ergibt genau einen Absatz, damit die Ebene überall vorhanden ist und
    nicht als Sonderfall behandelt werden muss.
    """
    absaetze: list[Absatz] = []
    marker: str | None = None
    lines: list[str] = []

    def flush() -> None:
        nonlocal marker, lines
        body = "\n".join(lines).strip()
        if body or marker is not None:
            absaetze.append(Absatz(marker=marker, text=body))
        marker, lines = None, []

    for line in text.splitlines():
        match = ABSATZ_MARKER.match(line)
        if match is None:
            lines.append(line)
            continue
        flush()
        marker = match.group(0).strip()
        lines = [line]

    flush()
    return absaetze
