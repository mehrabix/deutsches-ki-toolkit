# Textnormalisierung

Deutsche Texte brauchen zwei Formen: eine zum Anzeigen und eine zum Suchen.
Der Unterschied ist der ganze Punkt.

```python
from deutsches_ki.text import normalize_german

normalize_german("Die Straße ist schön.", mode="display")
# "Die Straße ist schön."

normalize_german("Die Straße ist schön.", mode="search")
# "die strasse ist schoen"
```

Die Anzeigeform bleibt unangetastet. `ß` wird nicht überall zu `ss`, und
Umlaute werden nicht überall aufgelöst. Die Suchform kommt zusätzlich.

## Die einzelnen Schritte

| Funktion               | Wirkung                                                  |
|------------------------|----------------------------------------------------------|
| `normalize_unicode`    | geschützte Leerzeichen, weiche Trennzeichen, Ligaturen   |
| `normalize_whitespace` | mehrfache Leerzeichen und Leerzeilen                     |
| `normalize_quotes`     | doppelte Anführungszeichen auf „…“                       |
| `normalize_dashes`     | Gedankenstrich, Minuszeichen, Bindestrich-Varianten      |
| `normalize_ergaenzung` | „Haupt- und Nebensatz“ → „Hauptsatz und Nebensatz“       |
| `normalize_umlauts`    | ä → ae, ö → oe, ü → ue (nur Suchform)                    |
| `normalize_ss`         | ß → ss (nur Suchform)                                    |
| `normalize_punctuation`| Satzzeichen entfernen                                    |
| `normalize_for_search` | die komplette Suchform                                   |

## Ergänzungsstriche

„Haupt- und Nebensatz“ und „Hauptsatz und Nebensatz“ bedeuten dasselbe, sehen
für ein Modell aber verschieden aus. `normalize_ergaenzung` ergänzt den
gemeinsamen Wortteil. Ob das gelingt, hängt von der Wortliste ab. Ist das
ergänzte Wort unbekannt, wird nur der Bindestrich entfernt, und die Suche
findet trotzdem beide Stellen.
