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

- **Struktur** — `§ 1`, `1.000,00`, `30.09.2024`, `z. B.` und `Gem.` sind
  keine Satzenden. Der Vergleich zeigt, was naives Trennen am Punkt anrichtet.
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

Alles läuft auf dem Server dieser Demo. Es wird nichts gespeichert.

Quelltext und Dokumentation: <https://github.com/mehrabix/deutsches-ki-toolkit>

Lokal starten:

```bash
uv sync --extra demo
uv run python demo/app.py
```

Der fünfte Schritt lädt ein Sprachmodell und braucht deshalb zusätzlich `torch`
und `transformers`.
