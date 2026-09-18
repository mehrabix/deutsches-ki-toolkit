# Erkennung sensibler Daten

Die Erkennung besteht aus mehreren Detektoren. Jeder Treffer kennt seine
Herkunft und seine Konfidenz. Bei Überlappungen gewinnt der Detektor mit
höherer Priorität, danach die höhere Konfidenz, danach der längere Treffer.

## Was erkannt wird

Strukturierte Kennungen mit Prüfsumme:

- **IBAN** – Modulo-97-Prüfung
- **Steuer-ID** – elfstellig, ISO 7064 Mod 11,10
- **Sozialversicherungsnummer** – Form und Geburtsdatum

Kennungen ohne allgemeine Prüfsumme, dafür mit deutschem Kontextwort:

- **USt-IdNr.** – `DE` und neun Ziffern
- **Steuernummer** – Formate mit Schrägstrichen, Kontext nötig
- **Personalausweisnummer**, **Postleitzahl**, **BIC**

Weitere Typen: Adressen (Straße vor Hausnummer), Telefon und Mobil, E-Mail,
Handelsregisternummer sowie Rechnungs-, Kunden-, Auftrags- und Vertragsnummern.

## Warum Kontextwörter

Ein deutsches Kontextwort in der Nähe hebt die Konfidenz und kann einen Treffer
überhaupt erst zulassen. Englische Kontextwörter helfen hier nicht. Das ist
einer der Gründe, warum generische Werkzeuge bei deutschen Dokumenten
schwächeln.

## Anonymisieren

```python
from deutsches_ki.pii import anonymize

anonymize(text, mode="redact")  # [PERSON]
anonymize(text, mode="replace")  # PERSON
anonymize(text, mode="mask")  # DE89 **** **** 001
anonymize(text, mode="hash", key="…")  # HASH_ab12cd34
anonymize(text, mode="pseudonymize")  # PERSON_001
```

Pseudonyme gelten innerhalb einer Sitzung: Derselbe Name bekommt dieselbe
Kennung. Die Kennungen werden in Leserichtung vergeben, der erste Name wird
also `PERSON_001`.

## Personen und Organisationen

Namen erfordern ein Sprachmodell. Ohne die optionale Erweiterung `nlp` findet
das Toolkit nur strukturierte Kennungen. Wer Firmennamen braucht, sollte
zusätzlich GLiNER einschalten: Das deutsche spaCy-Modell lässt Organisationen
bewusst aus.
