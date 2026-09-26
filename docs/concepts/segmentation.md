# Satzsegmentierung

Wo ein deutscher Satz endet, ist nicht dieselbe Frage wie im Englischen. Ein
Punkt steht in `1.000,00`, `30.09.2024`, `z. B.`, `Abs. 2`, `Werkstattstr. 5`,
`Rechnungsnr. 7` und `Dr. med.` — an sechs dieser sieben Stellen trennt er
keinen Satz. Deshalb arbeitet die Segmentierung regelbasiert und kennt die
deutschen Schreibweisen.

## Die Kette

```text
Text
  ↓  Satzgrenzen     text/segment.py
  ↓  Abschnitt       documents/headings.py     „§ 4 Zahlungsbedingungen“
  ↓  Absatz          documents/absaetze.py     „(1)“, „(2)“
  ↓  Satz je Absatz
  ↓  Chunk           chunking/structural.py
```

Die Ebenen sind bewusst getrennt. Eine Überschrift ist keine Satzgrenze, und
eine Absatzmarke ist kein Satz. Wer alles in einen Segmentierer wirft, verliert
die Gliederung, die ein deutsches Rechtsdokument ausmacht.

## Wie eine Grenze entschieden wird

`_is_boundary` prüft in dieser Reihenfolge und nimmt die erste zutreffende
Regel:

1. **`!`, `?`, `…`** beenden immer einen Satz. Schließende Zeichen wie `“`, `«`
   oder `)` nach dem Satzzeichen gehören dazu, sonst bliebe ein Satzende im
   Anführungszeichen unerkannt: „Er sagte „Hallo.“ Danach ging er.“
2. **Bekannte Abkürzung** am Punkt: `z. B.`, `Dr.`, `Abs.`, `gem.` trennen
   keinen Satz. Steht die Abkürzung in `SENTENCE_END_ABBREVIATIONS` — `usw.`,
   `etc.`, `u. a.`, `BGB.` —, entscheidet der Satzanfang danach (siehe unten).
3. **Abkürzung vor einer Nummer**: `Werkstattstr. 5`, `Rechnungsnr. 7`,
   `im Jan. 2024`, `am Mo. 5. Mai`. Hier ist der Punkt kein Satzende, weil eine
   Nummer folgt.
4. **Gliederungszeichen**: ein einzelner Buchstabe oder eine römische Zahl am
   Wortanfang — „I. Der erste Punkt.“, „b. Der zweite Punkt.“
5. **Ziffer vor dem Punkt**: `1.000,00` und `30.09.2024` bleiben zusammen,
   `1. Januar` ebenfalls. Eine freistehende Ordnungszahl bis drei Stellen
   (`im 1. Quartal`) trennt nicht, außer nach einer Fundstelle: „Siehe Rn. 45.
   Die Norm ist einschlägig.“
6. **Sonst** trennt der Punkt, wenn danach ein Großbuchstabe, eine Ziffer, ein
   öffnendes Zeichen (`„`, `(`, `[`) oder ein Aufzählungspunkt steht.

Zusätzlich ist jede Leerzeile eine Grenze.

## Mehrdeutige Abkürzungen

Nach Duden, Rechtschreibregel D 4 ist der Punkt einer Abkürzung am Satzende
zugleich der Schlusspunkt: „… Zitate von Goethe, Schiller u. a. Ihr Vater …“.
Ob wirklich ein Satzende vorliegt, entscheiden **zwei** Signale zugleich:

```python
_starts_sentence(rest) = rest[:1].isupper() and first_word in _SENTENCE_OPENERS
```

`_SENTENCE_OPENERS` führt 192 Funktionswörter — Artikel, Pronomen,
Konnektoren, Präpositionen. Beide Signale müssen zutreffen:

| Folgetext | Großschreibung | Funktionswort | Satzanfang |
|---|---|---|---|
| `Der Kunde zahlt.` | ja | ja | **ja** |
| `Müller zahlt.` | ja | nein | nein |
| `der Kunde zahlt.` | nein | ja | nein |

Ein Inhaltswort setzt die Aufzählung fort („… u. a. Personen“), ein
Funktionswort beginnt einen neuen Satz („… u. a. Ihr Vater“).

## Die drei Fehlerrichtungen

Jede Regel kann in drei Richtungen irren:

- **Ein Satz wird zerrissen** — teuer. Der Chunk verliert seinen Zusammenhang,
  und eine Suche nach der Zahlungsfrist findet ein Bruchstück.
- **Zwei Sätze bleiben zusammen** — billig. Der Chunk ist etwas größer; die
  Bedeutung bleibt.
- **Die Gliederung geht verloren** — teuer auf anderem Weg: „§ 4 Abs. 2“ lässt
  sich dann nicht mehr adressieren.

Wo eine Regel nicht sicher entscheiden kann, wählt das Toolkit die billige
Richtung. Die Abkürzungsliste ist deshalb bewusst großzügig: 382 Einträge.

## Bekannte Grenzen

- **Eine freistehende Zahl am Satzende trennt nicht.** „Die Antwort ist 42.
  Danach gehen wir.“ bleibt ein Satz. Die Zahl ist von der Ordnungszahl in „das
  42. Element“ nicht zu unterscheiden. In deutschen Dokumenten überwiegen
  Ordnungszahlen und Aufzählungen, und ein zusammengezogener Satz ist der
  billigere Fehler.
- **Abkürzungen, die am Satzende stehen dürfen, sind eine feste Liste.** Fehlt
  eine, bleibt der Satz zusammengezogen — die billige Richtung.
- **Nur die erste Zeile einer Aufzählung wird erkannt.** „I.“ am Zeilenanfang
  gilt als Gliederungszeichen; dieselbe Form mitten im Satz nicht.

## Prüfsammlung

Die Fälle liegen als JSON neben dem Code und laufen in der CI:

```text
tests/regression/german/german_segmentation.json   91 Fälle   Satzgrenzen
tests/regression/german/german_absaetze.json        7 Fälle   Absatzebene
```

Ein neuer Fall kostet drei Zeilen, keinen Testcode:

```json
{ "input": "Die Frist i. H. v. 30 Tagen gilt.", "check": "sentence_count", "expected": 1 }
```

Die Prüfungen für die Segmentierung sind `sentence_count` (Anzahl der Sätze) und
`absatz_markers` (Marken der Absätze, ohne Marke als leerer Eintrag). Alle
weiteren Prüfungen stehen in `tests/regression/german/test_golden.py`.

## Wo der Code steht

| Datei | Aufgabe |
|---|---|
| `src/deutsches_ki/text/segment.py` | Satzgrenzen, Wortzerlegung |
| `src/deutsches_ki/text/abbreviations.py` | 382 Abkürzungen, davon 28 am Satzende möglich |
| `src/deutsches_ki/documents/headings.py` | Abschnitte und Überschriften |
| `src/deutsches_ki/documents/absaetze.py` | Absätze „(1)“, „(2)“ |
| `src/deutsches_ki/chunking/structural.py` | Chunks mit Abschnitt und Absatz |
