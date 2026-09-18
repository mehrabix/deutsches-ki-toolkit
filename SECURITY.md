# Sicherheitsrichtlinie

## Worum es geht

Dieses Projekt verarbeitet Dokumente, die personenbezogene Daten und Betriebsgeheimnisse
enthalten können. Fehler in der Erkennung oder Anonymisierung haben unmittelbare Folgen.
Deshalb nehmen wir Sicherheitsmeldungen ernst.

## Nicht vertrauenswürdige Eingaben

Dokumentinhalte werden grundsätzlich als nicht vertrauenswürdig behandelt. Text aus einem
PDF, einer DOCX-Datei oder einer Datenbank ist Datenmaterial und niemals eine Anweisung an
ein Sprachmodell. Wenn du eine Stelle findest, an der Dokumentinhalt als Steueranweisung
durchgereicht wird, ist das ein Sicherheitsproblem.

## Schwachstellen melden

Bitte melde Sicherheitslücken **nicht** über öffentliche Issues. Nutze stattdessen die
Funktion „Report a vulnerability“ im GitHub-Repository oder schreibe eine E-Mail an den
Maintainer. Nenne nach Möglichkeit:

- eine kurze Beschreibung des Problems
- eine Reproduktion (am besten mit einer synthetischen Datei, keine echten Daten)
- die betroffene Version
- mögliche Auswirkungen

Du bekommst eine Rückmeldung, sobald der Bericht gesichtet wurde. Bitte gib uns Zeit zur
Behebung, bevor du das Problem öffentlich machst.

## Unterstützte Versionen

Sicherheitsupdates erhalten die jeweils neueste Release-Reihe.

## Was nicht in dieses Repository gehört

Bitte committe keine echten personenbezogenen Daten, keine echten Verträge und keine
Zugangsdaten. Für Tests gehören ausschließlich synthetische oder offen lizenzierte
Dokumente nach `datasets/`.
