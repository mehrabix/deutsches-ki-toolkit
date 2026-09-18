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
  "page": 12,
  "language": "de",
  "document_type": "contract",
  "paragraphs": 2
}
```

Damit lässt sich später auf einen Paragraphen einschränken, nach Dokumenttyp
filtern und die Quelle genau benennen.

## Feste Größe zum Vergleich

`strategy="fixed"` schneidet stur nach Token. Das ist keine Empfehlung, sondern
die Vergleichsgrundlage für Messungen: Wenn der aufwendige Chunker nicht
besser abschneidet, gehört das in den Benchmark.

## Überlappung

`overlap` wiederholt den Schluss des vorherigen Chunks. Das ist kein Ersatz für
saubere Grenzen, sondern eine Versicherung gegen Informationen, die genau auf
einer Grenze liegen.
