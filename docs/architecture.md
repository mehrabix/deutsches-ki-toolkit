# Architektur

Das Toolkit sitzt über bestehenden Werkzeugen und verbindet sie zu einer
Kette, die deutsche Sprache ernst nimmt.

```text
Datei
  ↓
documents.parse         Struktur statt einem langen String
  ↓
pii.detect              deutsche Kennungen mit Prüfsumme
  ↓
pii.anonymize           sensible Stellen entfernen
  ↓
chunking.chunk_document an Abschnitts-, Absatz- und Satzgrenzen
  ↓
embeddings.get_embedder Vektor je Chunk
  ↓
retrieval               Vektorsuche und lexikalische Suche, per RRF vereint
  ↓
facade.GermanDocument   Antwort mit Quelle
```

## Schichten

**core** – die Datenmodelle (`Document`, `Section`, `Chunk`, `Entity`). Alles
andere arbeitet mit diesen Typen.

**text** – Normalisierung, Segmentierung, Komposita, Suchanfragen. Hier liegt
der deutsche Kern. Ein Grundsatz gilt überall: Der Originaltext bleibt
erhalten, die Suchform kommt zusätzlich.

**pii** – Erkennung und Anonymisierung. Erkennung läuft über mehrere
Detektoren; Treffer werden nach Priorität, Konfidenz und Länge zusammengeführt.

**documents** – Einlesen über Docling oder für Text und Markdown direkt.

**chunking**, **embeddings**, **retrieval** – die RAG-Bausteine.

**cli** – die Kommandozeile.

## Was bewusst fehlt

Keine Vektordatenbank, kein PDF-Parser, kein Sprachmodell, kein Agenten-
Framework. Diese Aufgaben übernehmen Docling, pgvector, Ollama und andere.
Das Toolkit liefert die deutsche Ebene darüber.
