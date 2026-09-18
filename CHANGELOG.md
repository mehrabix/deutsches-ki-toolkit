# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden hier festgehalten.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionierung an [Semantic Versioning](https://semver.org/lang/de/).

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
