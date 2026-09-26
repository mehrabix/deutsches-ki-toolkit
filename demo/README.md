---
title: Deutsches KI-Toolkit
emoji: 📑
colorFrom: yellow
colorTo: red
sdk: gradio
app_file: app.py
pinned: false
python_version: "3.12"
license: apache-2.0
---

# Deutsches KI-Toolkit — Demo

Fünf Schritte an deutschen Texten: zerlegen, sensible Daten finden, suchen,
beantworten, mit einem Sprachmodell formulieren. Die ersten vier stellen die
deutsche Behandlung einer naiven gegenüber, damit der Unterschied sichtbar wird
statt behauptet.

- **Struktur** — Satzgrenzen werden kontextabhängig erkannt: Abkürzungen
  (`z. B.`, `Gem.`, `Abs.`), Geldbeträge (`1.000,00`), Datumsangaben
  (`30.09.2024`) und Paragraphen (`§ 1`) beenden keinen Satz. Bei mehrdeutigen
  Abkürzungen entscheiden der nachfolgende Kontext und die Groß- und
  Kleinschreibung. Die Sätze stehen unter der Überschrift, zu der sie gehören,
  statt in einer flachen Liste. Der Vergleich zeigt, was naives Trennen am Punkt
  anrichtet.
- **Sensible Daten** — Prüfsummen entscheiden mit. Eine IBAN wird nur gemeldet,
  wenn der Modulo-97-Test aufgeht; eine um eine Ziffer veränderte IBAN fällt
  durch. Umschalten zwischen Schwärzen, Ersetzen, Maskieren, Hashen und
  Pseudonymisieren.
- **Suche** — „Zahlungsfrist“ steht so nicht im Text. Die deutsche Suche zerlegt
  das Wort in `zahlung` und `frist`.
- **Frage** — die Antwort stammt aus dem Text, nicht aus einem Sprachmodell,
  deshalb lässt sich jede Angabe belegen.
- **Sprachmodell** — ein kleines Modell formuliert die Antwort, auf ZeroGPU auf
  der Grafikkarte. Danach prüft das Toolkit, ob die genannten Quellennummern
  wirklich existieren. Ein Modell, das `[9]` schreibt, obwohl es drei Quellen
  gab, fällt damit auf.

Alles läuft auf dem Server dieser Demo. Die Anwendung schreibt keine Dateien,
führt keine Datenbank und sendet nichts an Dritte; hochgeladene Dateien liegen
nur vorübergehend im Container. Die anonyme Nutzungsstatistik von Gradio ist
abgeschaltet. Die Plattform protokolliert technische Ausgaben des Containers.

Quelltext und Dokumentation: <https://github.com/mehrabix/deutsches-ki-toolkit>

Lokal starten:

```bash
uv sync --extra demo
uv run python demo/app.py
```

Der fünfte Schritt lädt ein Sprachmodell und braucht deshalb zusätzlich `torch`
und `transformers`.
