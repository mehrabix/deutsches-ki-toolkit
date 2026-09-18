# Beitragen zu deutsches-ki-toolkit

Danke, dass du mitmachen willst. Dieses Projekt lebt davon, dass deutsche Sprachfälle
gesammelt und dauerhaft abgesichert werden.

## Entwicklungsumgebung

Voraussetzungen: Python 3.12 oder neuer und [uv](https://docs.astral.sh/uv/).

```bash
uv sync --extra dev
uv run pytest -q
```

Die schweren Integrationen (spaCy, Presidio, Docling, sentence-transformers, pgvector)
sind optionale Extras. Die Testsuite läuft ohne sie. Wenn du an einer Integration
arbeitest, installiere das passende Extra:

```bash
uv sync --extra dev --extra nlp --extra presidio
```

**Achtung:** `uv sync` stellt die Umgebung exakt auf den Stand der Sperrdatei
zurück. Was du danach von Hand installierst, ist beim nächsten `uv sync` wieder
weg. Das betrifft vor allem das deutsche spaCy-Modell, das nicht auf PyPI liegt:

```bash
uv pip install --python .venv/Scripts/python.exe pip   # unter Windows
uv run python -m spacy download de_core_news_sm
```

Für die Embedding-Tests werden Modelle von Hugging Face geladen. Die
Voreinstellung in den Tests ist bewusst klein; lokal lässt sich ein größeres
Modell erzwingen:

```bash
set DEUTSCHES_KI_TEST_EMBEDDING_MODEL=BAAI/bge-m3   # unter Windows
uv run pytest tests/integration/test_embeddings.py -q
```

## Bevor du einen Pull Request öffnest

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
```

Alle vier Schritte laufen auch in der CI und müssen grün sein.

## Grundsätze

- **Originaltext bleibt erhalten.** Normalisierung erzeugt Suchformen, überschreibt aber
  niemals die Anzeigeform. `ß` wird nicht überall zu `ss`.
- **Deutsche Fälle werden zu Tests.** Jeder gefundene Fehler bekommt einen Regressionstest,
  meist als Eintrag unter `tests/regression/german/`.
- **Erkennung mit Prüfsumme.** Wo es eine Prüfsumme gibt (IBAN, Steuer-ID), wird sie
  benutzt. Muster allein reichen nicht.
- **Erst messen, dann behaupten.** Wenn ein einfacher Ansatz besser abschneidet als ein
  aufwendiger, schreiben wir das hin.
- **Keine erfundenen Zahlen.** Benchmarks werden reproduzierbar ausgeführt, nicht geschätzt.

## Gute erste Aufgaben

- einen deutschen PII-Recognizer ergänzen (mit Prüfsumme und Tests)
- einen Fall in `tests/regression/german/` beisteuern
- eine synthetische Testdatei unter `datasets/fixtures/` hinzufügen
- Fachterminologie für eine Branche ergänzen
- ein Embedding-Modell vergleichen
- die Dokumentation verbessern

## Commits

Kurze, beschreibende Commit-Nachrichten im Imperativ ("Add German IBAN recognizer") sind
willkommen. Ein Commit pro logischer Änderung.

## Lizenz

Mit deinem Beitrag stimmst du zu, dass er unter der Apache-2.0-Lizenz veröffentlicht wird.
