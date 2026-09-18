# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionierung an [Semantic Versioning](https://semver.org/lang/de/).

## [0.3.0a1]

Dritte Vorabversion. Aus der Kette wird ein Werkzeugkasten: prüfen, einordnen,
messen, vergleichen.

### Hinzugefügt

- **Terminologie-Prüfung**: Ein Glossar legt bevorzugte Schreibweisen fest; der
  Prüflauf meldet Stellen, an denen davon abgewichen wird.
- **Stilprüfung**: lange Sätze, Passivkonstruktionen, Nominalstil, Anglizismen,
  Füllwörter, Wortwiederholungen und sehr lange Wörter. Ausdrücklich als
  Hinweis, nicht als Korrektorat.
- **Dokumentklassifikation**: zwölf Arten, erkannt über gewichtete deutsche
  Wendungen und Strukturmerkmale. Der ausschlaggebende Beleg wird mitgeliefert.
- **Fachpakete**: Recht, Finanzen, Personal, Technik und Industrie. Reine
  Konfiguration und Daten, keine eigenen Codepfade.
- **Bewertung der Antwortqualität**: Quellendeckung, Antwortrelevanz und
  Quellenabdeckung, deterministisch berechnet, dazu ein optionales Urteil durch
  ein Sprachmodell.
- **Leistungsmessung**: Dokumente und Chunks je Sekunde, Latenz-Perzentile und
  Speicherspitze, als `deutsches-ki benchmark`.
- **Vergleich von Embedding-Modellen** auf demselben Bewertungssatz. Ein Modell,
  das sich nicht laden lässt, wird als Zeile gemeldet und bricht nichts ab.
- **Golden-Datensätze als JSON** unter `tests/regression/german/`. Neue Fälle
  brauchen keinen Testcode.
- **Deutsche Wortstämme** in den Such-Token. Damit findet „Ersatzteilen“ auch
  „Ersatzteile“.
- **GPU-Profil** für Ollama in Docker, damit niemand eine Grafikkarte braucht,
  sie aber nutzen kann.

### Geändert

- Neue Befehle: `classify`, `terminology`, `style`, `benchmark`, dazu
  `evaluate --compare` für den Modellvergleich.

### Behoben

- Die Stoppwortliste stand in normaler Schreibweise, die Such-Token sind aber
  gefaltet. „gemäß“ wurde deshalb nie als Stoppwort erkannt.
- Die Regel für Wortwiederholungen schlug über Zeilenumbrüche hinweg an. Eine
  Überschrift, die den eigenen Absatz eröffnet, gilt nicht mehr als Wiederholung.

### Gemessen

Der Bewertungssatz verbessert sich durch die Wortstämme deutlich:
Recall@1 von 0,75 auf 0,83, MRR von 0,84 auf 0,90, nDCG@5 von 0,88 auf 0,93,
Recall@5 bleibt bei 1,00.

## [0.2.0a1]

Zweite Vorabversion. Aus der Bibliothek ist eine Kette geworden: speichern,
suchen, neu sortieren, antworten, messen.

### Hinzugefügt

- **PostgreSQL mit pgvector**: Schema, HNSW-Index, Aufnahme von Dokumenten und
  Chunks, hybride Suche. Geprüft gegen echtes PostgreSQL, auch in der CI.
- **Deutsche Volltextsuche** über eine in Python gefaltete Suchspalte. Damit
  findet „Schnösel“ auch „Schnoesel“, ohne an den `unaccent`-Regeln des Servers
  zu drehen, und Komposita-Bestandteile werden mitindiziert.
- **Reranking**: lexikalischer Reranker ohne Modell, Cross-Encoder als
  optionale Erweiterung.
- **Sprachmodelle**: Anbindung an Ollama und an OpenAI-kompatible Schnittstellen
  wie vLLM, ohne zusätzliche Abhängigkeit in der Grundinstallation.
- **RAG-Engine** mit nummerierten Quellen und Prüfung der Quellenangaben:
  erfundene Verweise wie `[9]` werden gemeldet statt durchgereicht.
- **Bewertung**: Recall@1/5/10, Precision, MRR, nDCG, Trefferquote, dazu ein
  Datensatzformat, ein Bewertungslauf und der Befehl `deutsches-ki evaluate`.
- **Sicherheit**: Erkennung von Prompt-Injection auf Deutsch und Englisch,
  Erkennung von Geheimnissen mit Maskierung, Kennzeichnung von Dokumentinhalt
  als fremder Inhalt im Prompt.
- **MCP-Werkzeuge**: Dokumente einlesen, PII finden, anonymisieren, prüfen,
  suchen und bewerten, dazu der Server als dünne Hülle.
- **Docker**: Image für das Toolkit und Compose-Datei mit PostgreSQL und
  optional Ollama. Beide Images gebaut und ausgeführt.
- **Kommandozeile**: `scan`, `evaluate`, `ask` und ein echtes `ingest`.
- Bessere Fundstellen: Chunks tragen den Dateinamen, Abschnitt und Seitenzahl.

### Geändert

- Antworten laufen über die RAG-Engine, damit es nur einen Weg gibt.
- Fehler in der Suchreihenfolge behoben: Bei gleicher Punktzahl entschied die
  zufällige Chunk-Kennung, welcher Treffer zuerst kam. Jetzt entscheidet die
  Reihenfolge im Index, und Ergebnisse sind reproduzierbar.
- Komposita-Zerlegung vergleicht über die gefaltete Form. Vorher wurde
  „Kündigungsfrist“ nach dem Auflösen der Umlaute nicht mehr zerlegt.
- Abschnittstitel werden mitindiziert. Vorher fand eine Frage nach der
  „Zahlungsfrist“ den Abschnitt „§ 4 Zahlungsbedingungen“ nicht.

### Geprüft

- spaCy- und Presidio-Detektoren gegen ein echtes deutsches Modell, mit CI-Lauf.
  Dabei bestätigt sich: Presidio findet eine deutsche Steuernummer und eine
  Handelsregisternummer nicht, die eigenen Muster schon.

## [0.1.0a1]

Erste Vorabversion. Noch nicht vollständig, aber in sich lauffähig.

### Hinzugefügt

- Projektgerüst mit `pyproject.toml`, optionalen Extras, Ruff, MyPy und Pytest
- CI über GitHub Actions für Python 3.12 und 3.13
- Core-Datenmodelle (Document, Section, Chunk, Entity, Citation, Answer)
- Deutsche Textnormalisierung mit getrennten Modi für Anzeige und Suche
- Satzsegmentierung mit Kenntnis deutscher Abkürzungen
- Komposita-Zerlegung und Suchanfragen-Erweiterung
- Deutsche PII-Erkennung mit Prüfsummen (IBAN, Steuer-ID, Steuernummer, SVNR und weitere)
- Anonymisierung und Pseudonymisierung in fünf Betriebsarten
- Dokumenteinlesung für Text und Markdown, Docling als optionale Erweiterung
- Strukturbasiertes Chunking an Abschnitts-, Absatz- und Satzgrenzen
- Embedding-Schnittstelle mit deterministischem Hashing-Modell
- In-Memory-Suche (Vektor und lexikalisch) mit Reciprocal Rank Fusion
- `GermanDocument`-Fassade, YAML-Konfiguration und die Kommandozeile `deutsches-ki`
