# Chunking

Chunking ist der Punkt, an dem deutsche RAG-Anwendungen Qualität verlieren.
Ein Schnitt nach fester Tokenzahl reißt Absatz eins von Absatz zwei weg – und
genau dort steht die Ausnahme.

Geschnitten wird in dieser Rangfolge:

```text
Dokument
  ↓ Abschnitt
  ↓ Absatz
  ↓ Satz
  ↓ Token   (nur wenn nichts anderes mehr geht)
```

Ein Paragraphenabschnitt, der in die Token-Grenze passt, bleibt eine Einheit:

```text
Chunk: § 4 Zahlungsbedingungen

       (1) Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.

       (2) Bei verspäteter Zahlung fallen Verzugszinsen an.
```

## Metadaten

Jeder Chunk trägt seinen Weg im Dokument mit:

```json
{
  "section": "§ 4 Zahlungsbedingungen",
  "section_path": ["Vertrag", "§ 4 Zahlungsbedingungen"],
  "absatz": "(2)",
  "page": 12,
  "language": "de",
  "document_type": "contract",
  "paragraphs": 2
}
```

`absatz` ist die Marke des Absatzes, mit dem der Chunk beginnt; `null`, wenn er
ohne Marke beginnt. Damit lässt sich später auf einen Paragraphen oder einen
einzelnen Absatz einschränken, nach Dokumenttyp filtern und die Quelle genau
benennen.

## Die Absatzebene

Ein Paragraph gliedert sich in Absätze: „(1)“, „(2)“. Sie sind eine eigene
Ebene zwischen Abschnitt und Satz, nicht bloß Text:

```python
from deutsches_ki.documents import split_absaetze

for absatz in split_absaetze(section.content):
    print(absatz.marker, absatz.text)
```

```text
None  Der Auftraggeber beauftragt die Beispiel GmbH.
(2)   (2) Die Vergütung beträgt 1.000,00 EUR.
(3)   (3) Gem. Abs. 2 Nr. 4 gilt die Regelung.
```

Die Marke bleibt im Text stehen. Sie ist Gliederung und gehört in den Chunk; ein
Treffer auf „§ 4 Abs. 2“ soll den Absatz zeigen, nicht nur seinen Inhalt.
`Document.iter_absaetze()` gibt alle Absätze mit ihrem Abschnitt zurück.

## Feste Größe zum Vergleich

`strategy="fixed"` schneidet stur nach Token. Das ist keine Empfehlung, sondern
die Vergleichsgrundlage für Messungen: Wenn der aufwendige Chunker nicht
besser abschneidet, gehört das in den Benchmark.

## Überlappung

`overlap` wiederholt den Schluss des vorherigen Chunks. Das ist kein Ersatz für
saubere Grenzen, sondern eine Versicherung gegen Informationen, die genau auf
einer Grenze liegen.
