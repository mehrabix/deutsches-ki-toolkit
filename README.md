# deutsches-ki-toolkit

**Deutsche Dokumente. Deutsche Daten. Antworten, auf die man sich verlassen kann.**

`deutsches-ki-toolkit` ist eine Python-Bibliothek für alle, die KI-Anwendungen mit
deutschsprachigen Dokumenten bauen. Sie kümmert sich um die vielen kleinen und großen
Eigenheiten, die generische Frameworks übersehen: Umlaute und ß, Komposita, deutsche
Firmen- und Personennamen, IBAN und Steuernummern, Verträge mit Paragraphen, Rechnungen,
Personalunterlagen und technische Dokumentation. Und sie sorgt dafür, dass sensible Daten
das eigene Netz nicht verlassen.

Das Toolkit tritt nicht an, um Docling, spaCy, Presidio, BGE-M3, pgvector oder Ollama zu
ersetzen. Es legt sich davor und verbindet diese Werkzeuge zu einer Kette, die deutsche
Sprache ernst nimmt – vom ersten Byte eines PDFs bis zur belegten Antwort.

```text
Deutsches Dokument  →  Struktur  →  PII  →  Chunks  →  Embeddings  →  Suche  →  Antwort mit Quelle
```

---

## Stand

Diese Übersicht sagt, was heute funktioniert. Alles darunter beschreibt das
Ziel des Projekts, nicht den Lieferstand der aktuellen Version.

**Läuft und ist getestet**

- Deutsche Textnormalisierung, Satzsegmentierung, Komposita-Zerlegung
- Deutsche PII-Erkennung mit Prüfsummen, fünf Anonymisierungsarten
- Strukturbasiertes Chunking mit Abschnitts- und Seitenangaben
- Suche im Arbeitsspeicher: Vektor und lexikalisch, vereint per RRF
- Deutsche Volltextsuche ohne `unaccent-Trick`
  (gegen echtes PostgreSQL geprüft, auch in der CI)
- Lexikalisches Reranking, RAG-Engine mit Prüfung der Quellenangaben
- Prompt-Injection- und Geheimniserkennung
- Bewertung mit Recall, MRR und nDCG samt Datensatz
- Erkennung der Dokumentart, Terminologie-Prüfung, Stilprüfung
- Fachpakete für Recht, Finanzen, Personal, Technik und Industrie
- Leistungsmessung und Vergleich von Embedding-Modellen
- Kommandozeile, MCP-Werkzeuge, Docker-Image
- Embeddings über BGE-M3 und Cross-Encoder-Reranking, gegen echte Modelle
  geprüft
- PDF über Docling, mit erhaltener Paragraphengliederung: `§ 4
  Zahlungsbedingungen` bleibt ein eigener Abschnitt statt einer langen Zeichenkette
- Einlesen erkennt die Sprache (deutsch, englisch, gemischt) und zieht deutsche
  Geschäftsangaben wie Rechnungs- und Kundennummer in die Metadaten
- spaCy- und Presidio-Detektoren gegen ein echtes deutsches Modell geprüft,
  samt CI-Lauf. Dabei bestätigt sich der Ausgangspunkt des Projekts: Presidio
  findet eine deutsche Steuernummer und eine Handelsregisternummer nicht, die
  eigenen Muster schon.
- Anbindung an Ollama gegen ein echtes Modell: Die Kette aus Suche, Prompt und
  Antwort läuft und liefert eine belegte deutsche Antwort. Zwei Beobachtungen
  dazu stehen weiter unten.

Der mitgelieferte Bewertungssatz (12 Fragen über die Testdateien) ergibt mit
dem Hashing-Modell: Recall@1 0,83, Recall@5 1,00, MRR 0,90, nDCG@5 0,93.
Nachvollziehbar mit:

```bash
deutsches-ki evaluate datasets/benchmark/deutsch_rag.yaml --corpus datasets/fixtures
```

Vorher waren es Recall@1 0,75 und MRR 0,84. Der Unterschied kommt von den
groben Wortstämmen in den Such-Token: „Ersatzteilen“ findet jetzt
„Ersatzteile“. Genau für solche Vergleiche ist der Bewertungslauf da.

Derselbe Befehl vergleicht auch Embedding-Modelle:

```bash
deutsches-ki evaluate datasets/benchmark/deutsch_rag.yaml --corpus datasets/fixtures --compare hashing,bge-m3
```

| Modell  | Dimension | Recall@5 |  MRR | nDCG@5 | ms je Frage |
|---------|-----------|----------|------|--------|-------------|
| hashing | 256       | 1,00     | 0,90 | 0,93   | 0,6         |
| BGE-M3  | 1024      | 1,00     | 1,00 | 1,00   | 260,0       |

Auf diesem kleinen Satz holt BGE-M3 jede Antwort auf Platz eins, braucht dafür
aber rund vierhundertmal so lange je Frage. Für zwölf Fragen ist das
nebensächlich, bei Tausenden Anfragen ist es eine Entscheidung. Genau deshalb
wird gemessen und nicht behauptet.

**Vorhanden, aber noch nicht gegen echte Systeme geprüft**

Die folgenden Bausteine sind geschrieben und lassen sich einschalten, wurden
aber noch nicht mit den jeweiligen Bibliotheken ausgeführt:

- GLiNER-Detektor (`gliner`)
- MCP-Server selbst (die Werkzeuge dahinter sind getestet)

**Was das Sprachmodell nicht leistet**

Die Anbindung ist geprüft, das Modell dahinter war das kleinste, das auf einem
Laptop läuft. Zwei Dinge fielen dabei auf und gehören hierhin:

Ein Modell mit einer Milliarde Parameter hält sich **nicht an die Zitatvorgabe**.
Es beantwortet die Frage richtig („Die Zahlungsfrist ist nach § 4 des Dokuments
30 Tage nach Rechnungsstellung“), lässt aber die geforderten Nummern `[1]` weg.
Die Zitatprüfung meldet das als „keine Quelle genannt“ statt es zu übersehen.

Das Urteil durch ein Sprachmodell ist **schwankend**. Dieselbe Frage, dieselben
Quellen, dieselbe Antwort, dreimal bewertet: Treue 0,0, dann 0,5, dann 1,0. Genau
deshalb sind die deterministischen Maße die Grundlage, und das Urteil durch ein
Modell ist eine freiwillige Zugabe. Ein Modell als Richter ist bequem, aber nicht
belastbar.

**Noch nicht gebaut**

- Bewertung der Antwortqualität über ein Sprachmodell (Treue, Relevanz) –
  die deterministischen Näherungen gibt es, das Urteil durch ein Modell nicht
- Enterprise-Datenbankanbindung (Fragen in SQL übersetzen)
- Web-Demo und Benchmark-Website
- Feintuning

---

## Warum es dieses Projekt gibt

Wer schon einmal eine RAG-Anwendung über deutsche Unternehmensdokumente gebaut hat, kennt
die Überraschungen. Sie tauchen nicht im Modell auf, sondern davor und danach.

**Komposita verstecken Bedeutung.** „USBCKabel“, „USB C Kabel“ und „USB-C-Kabel“ meinen
dasselbe. Für einen Tokenizer sind es drei verschiedene Dinge. Deutsche, niederländische,
schwedische und finnische Komposita verstecken ganze Wörter in einem Token. Wer nicht
zerlegt, bevor er indiziert, verliert Treffer – und die semantische Suche rettet das nur
selten. ([Bitext](https://www.bitext.com/blog/some-of-your-rag-related-issues-have-an-easy-quick-solution-decompounding/))

**Presidio kennt deutsches Recht nicht.** Die Standardinstallation liefert rund 30
Erkennungsmuster, die vor allem auf US-Formate ausgelegt sind. Deutsche Steuer-IDs und
Steuernummern sind nicht dabei, Personalausweisnummern auch nicht. Die Steuernummer allein
hat 16 Formate, eines pro Bundesland. Ein Praxistest ergab für IBAN, BIC, Steuer-ID und
Handelsregisternummer eine Trefferquote von 0 Prozent mit den Voreinstellungen. Selbst die
Sprachumschaltung hilft nicht überall: In Presidio-Issue
[#1343](https://github.com/data-privacy-stack/presidio/issues/1343) liefert
`get_supported_entities(language="de")` nur noch `BANK_ACCOUNT`, und Kontextwörter wirken
für Deutsch gar nicht.

**spaCy erkennt Organisationen im Deutschen nicht.** Das deutsche Modell ist darauf
trainiert, Firmennamen zu ignorieren, weil zu viele Fehlalarme entstehen. In einem
öffentlichen Vergleich erreichte `de_core_news_lg` knapp 78 Prozent, GLiNER rund 95
Prozent. Wer nur auf ein Modell setzt, verschenkt viel.

**PostgreSQL sucht Umlaute nicht so, wie man denkt.** „Schnösel“ und „Schnoesel“ finden
sich mit der Standardkonfiguration nicht gegenseitig. Auch `default_text_search_config =
'german'` ändert daran nichts. Es braucht eine eigene Textsuchkonfiguration und angepasste
`unaccent`-Regeln, damit `ä → ae` abgebildet wird.
([dbi services](https://www.dbi-services.com/blog/dealing-with-german-umlaute-in-postgresqls-full-text-search/))

**Generisches Chunking zerschneidet Paragraphen.** Deutsche Verträge und Gesetzestexte
leben von `§ 4 Abs. 2`. Ein Chunker, der stur nach Token zählt, reißt Absatz eins von
Absatz zwei weg – und genau dort steht die Ausnahme. Eine abschnittsbezogene Zerlegung
schneidet in Benchmarks besser ab als die übliche Feste-Größe-Strategie.

**Unfertige Bausteine im Ökosystem.** Docling zerlegt deutsche PDFs gelegentlich mit
falschen Leerzeichen und getrennten Wörtern
([Issue #1042](https://github.com/docling-project/docling/issues/1042)). Adressparser
scheitern an „Straße des 17. Juni“ oder an Postleitzahlen, die in der Hausnummer landen
([libpostal #510](https://github.com/openvenues/libpostal/issues/510)). Der deutsche
spaCy-Tokenizer stolpert über Ergänzungsstriche wie „Haupt- und Nebensatz“ und Kontraktionen
wie „unterm“ ([spaCy #2486](https://github.com/explosion/spaCy/issues/2486)).

**Und der rechtliche Rahmen.** Seit dem 2. August 2026 greift der EU AI Act in seiner
breiten Anwendung; Verstöße können bis zu 35 Millionen Euro kosten. Für den Mittelstand
ist Datensouveränität längst kein Marketingwort mehr, sondern eine Bedingung. Viele
Unternehmen wollen Dokumente gar nicht erst an einen Cloud-Anbieter geben.

Diese Liste ist der Grund, warum es dieses Toolkit gibt. Jeder Baustein oben ist für sich
lösbar – aber niemand will ihn zehnmal lösen.

---

## Was drin ist

- **Normalisierung** für Umlaute, ß, Anführungszeichen, Gedankenstriche und
  Ergänzungsstriche – getrennt für Anzeige und Suche, ohne den Originaltext zu zerstören
- **Satz- und Wortsegmentierung**, die Abkürzungen wie `z. B.`, `Dr.`, `Dipl.-Ing.`,
  `GmbH`, `e.V.`, `Nr.`, `Art.`, `Abs.` und `§` kennt
- **Entitätenerkennung** über mehrere Detektoren gleichzeitig (spaCy, Presidio, Regex,
  GLiNER, Transformer)
- **Deutsche PII** mit Prüfsummen: IBAN, BIC, USt-IdNr., Steuer-ID, Steuernummer,
  Sozialversicherungsnummer, Personalausweisnummer, Handelsregisternummer, Adressen,
  Telefonnummern, E-Mails sowie Geschäftskennungen wie Rechnungs-, Kunden-, Auftrags- und
  Vertragsnummern
- **Anonymisierung und Pseudonymisierung** mit den Modi `redact`, `replace`, `mask`,
  `hash` und `pseudonymize`, deterministisch innerhalb einer Sitzung
- **Dokumenteinlesung** über Docling für PDF, DOCX, XLSX, PPTX, HTML, Markdown, Bilder und
  Klartext – mit erhaltener Struktur statt einem langen String
- **Strukturbasiertes Chunking**, das an Überschriften, Paragraphen, Absätzen und Sätzen
  schneidet und die Token-Grenze zuletzt beachtet
- **Komposita-Analyse** und Zerlegung für die Suche
- **Suche mit angepasster Anfrage**: Wörterbuch, Lemmatisierung, Komposita, Fachglossar,
  Embedding-Ähnlichkeit
- **Embeddings** mit BGE-M3 als Ausgangspunkt und austauschbaren Anbietern
- **PostgreSQL + pgvector** mit deutscher Volltextsuche in derselben Datenbank
- **Hybride Suche** aus Vektor- und lexikalischer Suche, zusammengeführt per Reciprocal
  Rank Fusion
- **Reranking** als eigener, austauschbarer Schritt
- **RAG mit Pflicht zur Quelle**: jede Antwort kommt mit Dokument, Seite und Abschnitt
- **Lokaler Betrieb** mit Ollama oder vLLM, ohne dass ein Byte das Haus verlässt
- **Sicherheitsschicht** gegen Prompt-Injection und für klare Vertrauensgrenzen
- **Auswertung** mit deutschem Benchmark, Retrieval- und Generierungsmetriken
- **MCP-Server** und **Kommandozeile** für den Alltag

---

## Was das Toolkit bewusst nicht ist

Es ist keine Chat-Oberfläche, kein Agenten-Framework, keine Vektordatenbank, kein
PDF-Parser, kein LLM und keine Modelle zum Trainieren. All das gibt es bereits, und zwar
gut. Dieses Projekt konzentriert sich auf die Ebene darüber: deutsche Sprache, deutsche
Personenbezüge, deutsche Dokumentstruktur, nachvollziehbare Antworten und überprüfbare
Ergebnisse.

---

## Installation

```bash
pip install deutsches-ki-toolkit
```

Oder mit [uv](https://docs.astral.sh/uv/):

```bash
uv add deutsches-ki-toolkit
```

Voraussetzung ist Python 3.12 oder neuer.

Die Standardinstallation ist bewusst schlank. Schwere Bausteine lädst du bei Bedarf:

```bash
pip install "deutsches-ki-toolkit[docling]"    # Dokumente einlesen
pip install "deutsches-ki-toolkit[embeddings]" # BGE-M3 und Co.
pip install "deutsches-ki-toolkit[postgres]"   # pgvector + Volltextsuche
pip install "deutsches-ki-toolkit[mcp]"        # MCP-Server
pip install "deutsches-ki-toolkit[all]"
```

Das deutsche spaCy-Modell wird einmalig nachinstalliert:

```bash
python -m spacy download de_core_news_lg
```

---

## Schnellstart

```python
from deutsches_ki import GermanDocument

doc = GermanDocument.from_file("vertrag.pdf")

# Struktur steht, jetzt sensible Stellen finden
pii = doc.detect_pii()
print(pii)

# Vertraulich arbeiten und trotzdem suchen
doc.anonymize(mode="pseudonymize")

# Deutsches Chunking an §-Grenzen
chunks = doc.chunk(strategy="structural")

# Fragen stellen, Antwort mit Quelle erhalten
antwort = doc.search("Welche Kündigungsfrist gilt?")
print(antwort.answer)
for quelle in antwort.citations:
    print(quelle.document, quelle.page, quelle.section)
```

Mehr geht immer, aber das ist die kürzeste Strecke von einem PDF zu einer belegten
Antwort.

---

## Deutsche Texte normalisieren

```python
from deutsches_ki.text import normalize_german

normalize_german("Die Straße ist schön.", mode="display")
# "Die Straße ist schön."

normalize_german("Die Straße ist schön.", mode="search")
# "die strasse ist schoen"  (nur als Suchform, das Original bleibt erhalten)
```

Der wichtigste Grundsatz: **Originaltext nie zerstören.** `ß` wird nicht überall zu `ss`,
und Umlaute werden nicht überall zu `ae`, `oe`, `ue`. Es gibt zwei getrennte Wege:

- `display` – so, wie der Text aussehen soll. `Straße` bleibt `Straße`.
- `search` – eine zusätzliche Repräsentation, die `strasse` als Treffer erlaubt.

Deutsche Texte bringen weitere Eigenheiten mit, die hier aufgeräumt werden:

```python
from deutsches_ki.text import (
    normalize_unicode,  # ─ vs. –, „ vs. ", nicht umbrechende Leerzeichen
    normalize_quotes,  # „richtig“ und »so«
    normalize_dashes,  # Gedankenstrich, Bis-Strich, Bindestrich
    normalize_ergaenzung,  # "Haupt- und Nebensatz" → "Hauptsatz und Nebensatz"
    normalize_whitespace,
    normalize_for_search,
)
```

Der Ergänzungsstrich ist ein gutes Beispiel: „Haupt- und Nebensatz“ und „Hauptsatz und
Nebensatz“ bedeuten exakt dasselbe, sehen für ein Modell aber völlig verschieden aus.
`normalize_ergaenzung` macht daraus dieselbe Form.

---

## Sätze und Wörter trennen

```python
from deutsches_ki.text import split_sentences

saetze = split_sentences(
    "Die Frist beträgt 30 Tage (vgl. § 4 Abs. 2). "
    "Zahlungen sind an die Beispiel GmbH, z. B. per Überweisung, zu leisten."
)
for s in saetze:
    print(s.start, s.end, s.text)
```

Die Segmentierung ist auf die Fälle ausgelegt, an denen Standardlösungen scheitern:

```text
z. B.   Dr.   Prof.   Dipl.-Ing.   GmbH   AG   e.V.   Nr.   Art.   Abs.   §   bzw.   usw.
```

Zahlen mit Punkt am Satzende („… 3.500 Euro.“) werden nicht falsch getrennt, und
Aufzählungen wie „1.“ oder „a)“ bleiben zusammen.

---

## Entitäten und deutsche PII

```python
from deutsches_ki.pii import detect

treffer = detect(
    "Überweisung an Max Mustermann, IBAN DE89 3704 0044 0532 0130 00, USt-IdNr. DE123456789."
)
```

```json
[
  { "type": "PERSON", "text": "Max Mustermann", "confidence": 0.94, "source": "spacy" },
  { "type": "DE_IBAN", "text": "DE89 3704 0044 0532 0130 00", "confidence": 0.99, "source": "regex" },
  { "type": "DE_VAT_ID", "text": "DE123456789", "confidence": 0.99, "source": "regex" }
]
```

Erkannt werden unter anderem:

**Finanzen** – IBAN (mit Mod-97-Prüfung), BIC, Kartennummern.

**Steuern** – USt-IdNr./VAT-ID, Steuer-ID (elfstellig) und Steuernummer. Die Steuernummer
wird für alle 16 Bundesländer in ihren jeweiligen Formaten erkannt, jeweils mit
Plausibilitätsprüfung. Genau hier scheitern generische Werkzeuge.

**Kontakt** – Festnetz- und Mobilnummern in deutschen Schreibweisen, E-Mail-Adressen.

**Adressen** – Postleitzahl, Straße, Hausnummer, Hausnummernzusätze wie `12a`, Bereiche wie
`414-424`, Ort. Die Erkennung ist auf die deutsche Reihenfolge ausgelegt (Straße vor
Hausnummer) und nicht auf das US-amerikanische Muster.

**Persönliche Kennungen** – Sozialversicherungsnummer, Personalausweisnummer.

**Geschäftliches** – Handelsregisternummer (HRA/HRB), Rechnungsnummer, Kundennummer,
Auftragsnummer, Vertragsnummer.

**Personen und Organisationen** – über mehrere Detektoren hinweg, damit Firmennamen nicht
durchs Raster fallen.

### Mehrere Detektoren statt eines Modells

Kein einzelner Ansatz findet alles. Deshalb laufen die Detektoren zusammen und einander
ergänzend:

```python
EntityDetector
    ├── RegexDetector        # strukturierte Kennungen + Prüfsumme
    ├── PresidioDetector     # etablierter Rahmen, erweitert um deutsche Muster
    ├── SpaCyDetector        # Morphologie, Syntax, Personen und Orte
    ├── GliNERDetector       # Organisationen und unbekannte Namen
    └── TransformerDetector  # kontextabhängige Fälle
```

Jeder Treffer trägt seine Herkunft (`source`) und einen Konfidenzwert. Wer weniger
Fehlalarme braucht, kann nach Detektor filtern; wer mehr Recall braucht, schaltet GLiNER
dazu.

### Kontextwörter auf Deutsch

Erkennung wird deutlich besser, wenn ein Hinweiswort in der Nähe steht. Daher bringt das
Toolkit eigene deutsche Kontextlisten mit – „Rechnungsnummer“, „Kundennummer“,
„Steuernummer“, „IBAN“, „Ansprechpartner“, „geboren am“ und weitere. Englische
Kontextwörter helfen hier nicht, wie auch das Presidio-Projekt
[bestätigt](https://github.com/data-privacy-stack/presidio/issues/1343).

---

## Anonymisieren und pseudonymisieren

```python
from deutsches_ki.pii import anonymize

anonymize("Max Mustermann arbeitet bei der Beispiel GmbH.", mode="redact")
# "[PERSON] arbeitet bei der [ORGANISATION]."

anonymize("Max Mustermann arbeitet bei der Beispiel GmbH.", mode="pseudonymize")
# "PERSON_001 arbeitet bei der ORG_001."
```

Fünf Betriebsarten:

| Modus          | Ergebnis                                                        |
|----------------|-----------------------------------------------------------------|
| `redact`       | Platzhalter wie `[PERSON]`, `[IBAN]`                            |
| `replace`      | Ersetzung durch eine feste oder generierte Kennung              |
| `mask`         | Teilweise Verdeckung: `DE89 **** **** **** **** 00`             |
| `hash`         | Einweg-Hash, nicht umkehrbar                                    |
| `pseudonymize` | Stabile Kennung wie `PERSON_001`, innerhalb der Sitzung konstant |

Pseudonyme bleiben stabil: Derselbe Name bekommt in derselben Sitzung immer dieselbe
Kennung. Damit lassen sich Dokumente verarbeiten und vergleichen, ohne die echten Namen
weiterzugeben. Wenn du die Zuordnung zurückbrauchst, kann der Vorgang mit einem Schlüssel
umkehrbar gestaltet werden – standardmäßig ist er es nicht.

Der wichtigste Punkt: Anonymisierung ist kein Anhang, sondern sitzt in der Verarbeitungs-
kette. Texte werden anonymisiert, bevor sie ein Embedding-Modell oder ein Sprachmodell
sehen – nicht danach.

---

## Dokumente einlesen und Struktur erhalten

```python
from deutsches_ki.documents import parse

doc = parse("vertrag.pdf")

print(doc.title)
for section in doc.sections:
    print(section.level, section.title, section.page)
```

Das Toolkit wirft ein PDF nicht in einen großen String. Die Struktur bleibt über die
gesamte Kette erhalten:

```text
Dokument
├── Titel
├── Metadaten
├── Abschnitte
│   ├── Überschrift
│   ├── Absätze
│   ├── Tabellen
│   ├── Listen
│   └── Querverweise
└── Seiten
```

Für deutsche Verträge heißt das konkret, dass `§ 1 Vertragsgegenstand`,
`§ 2 Vergütung`, `§ 3 Zahlungsbedingungen`, `§ 4 Haftung` eigene, adressierbare Einheiten
bleiben – mit Seitenzahl und Positionsangabe. Tabellen werden als Tabellen weitergegeben
und nicht zu Fließtext zerrieben.

Unter der Haube liest Docling die Dateien. Die Arbeit des Toolkits beginnt danach:
Spracherkennung (Deutsch oder gemischt), deutsche Normalisierung, PII-Erkennung und das
Herausziehen deutscher Metadaten wie Rechnungsdatum, Rechnungsnummer oder Vertragsnummer.

---

## Deutsches Chunking

Chunking ist der Punkt, an dem die meisten deutschen RAG-Anwendungen Qualität verlieren.
Hier wird nicht bei einer festen Tokenzahl blind geschnitten, sondern nach einer
Rangfolge:

```text
Dokumentstruktur
      ↓
Abschnittsgrenzen
      ↓
Absatzgrenzen
      ↓
Satzgrenzen
      ↓
Token-Grenze (nur als letztes Mittel)
```

Schlecht:

```text
Chunk 1: § 4 Zahlungsbedingungen ...
Chunk 2: ... 30 Tage nach Rechnungsstellung ...
```

Besser:

```text
Chunk 1: § 4 Zahlungsbedingungen

         (1) Der Auftraggeber ...

         (2) Die Zahlung ist innerhalb von 30 Tagen
             nach Rechnungsstellung fällig.
```

Ein Absatz, der eine Ausnahme enthält, bleibt zusammen. Überlappung ist möglich, aber nicht
als Krücke, sondern um Abschnittskontext an den Rändern zu erhalten.

Jeder Chunk trägt seinen Weg im Dokument mit:

```json
{
  "document_id": "vertrag-2024-001",
  "section": "Zahlungsbedingungen",
  "section_path": ["Vertrag", "Zahlungsbedingungen"],
  "paragraph": "§ 3",
  "page": 12,
  "language": "de",
  "document_type": "contract"
}
```

Diese Angaben sind später Gold wert. Man kann Treffer auf einen Paragraphen einschränken,
nach Dokumenttyp filtern und die Quelle exakt benennen.

---

## Komposita

```python
from deutsches_ki.text import analyze_compound

analyze_compound("Versicherungsbeitrag")
```

```json
{
  "word": "Versicherungsbeitrag",
  "parts": ["Versicherung", "Beitrag"],
  "strategy": "dictionary"
}
```

Für die Suche wird ein Kompositum zusätzlich in eine Suchform überführt, in der die
Bestandteile sichtbar sind. Wer nach „Arbeitsunfähigkeitsbescheinigung“ sucht, soll auch
Textstellen finden, in denen von der „Bescheinigung der Arbeitsunfähigkeit“ die Rede ist.
Die Zerlegung stützt sich auf ein deutsches Wörterbuch, morphologische Analyse und – wenn
nötig – ein Sprachmodell als Rückfall. Sie ist bewusst heuristisch gehalten und liefert
mehrere Kandidaten statt einer einzigen, möglicherweise falschen Antwort.

---

## Suchanfragen erweitern

```python
from deutsches_ki.text import expand_query

expand_query("Urlaubsantrag genehmigen")
```

```python
["Urlaubsantrag", "Urlaubsfreigabe", "Urlaubsgenehmigung", "Abwesenheitsantrag", "Urlaubstage"]
```

Erweiterung entsteht aus mehreren Quellen und nicht aus einem Sprachmodell allein:

```text
Wörterbuch
    + Lemmatisierung
    + Komposita-Analyse
    + Fachglossar des Kunden
    + Embedding-Ähnlichkeit
    + optional: Sprachmodell
```

Ein selbst gepflegtes Glossar ist oft die beste Quelle, weil es die Sprache des
Unternehmens kennt. Deshalb kannst du eigene Begriffe mitgeben, ohne das Toolkit zu
verändern.

---

## Embeddings

```python
from deutsches_ki.embeddings import get_embedder

embedder = get_embedder("bge-m3")
vektoren = embedder.embed_documents(["Die Zahlungsfrist beträgt 30 Tage."])
```

Ausgangspunkt ist **BGE-M3**: mehrsprachig, 1024 Dimensionen, lange Eingaben bis 8192
Token und – wichtig – gleichzeitig für dichte, sparse und Multi-Vektor-Suche geeignet.
Damit ist das Modell ein solider Startpunkt, ohne dass du dich daran bindest.

Alle Anbieter folgen derselben Schnittstelle:

```python
class EmbeddingProvider:
    def embed_documents(self, texts): ...
    def embed_query(self, text): ...
```

Ausprobieren kannst du BGE-M3, multilingual-e5, deutsche Modelle, Qwen-Embeddings,
Ollama-Embeddings und OpenAI. Welches Modell wann gewinnt, steht in den Benchmarks – nicht
im Bauchgefühl.

---

## Speicher: PostgreSQL und pgvector

```python
from deutsches_ki.storage.pgvector import PgVectorStore

store = PgVectorStore("postgresql://localhost/deutsche_ki")
store.create_schema()
store.add_chunks(chunks, embedder)
```

```sql
CREATE TABLE chunks (
    id           UUID PRIMARY KEY,
    document_id  UUID NOT NULL,
    content      TEXT NOT NULL,
    metadata     JSONB,
    embedding    vector(1024)
);

CREATE INDEX chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
```

Die Tabellen decken Dokumente, Abschnitte, Chunks, Entitäten und Embeddings ab. pgvector
unterstützt exakte Suche sowie HNSW- und IVFFlat-Indexe. Für den Vergleich mit dem
Optimum lässt sich die exakte Suche jederzeit dazuschalten.

Ein Vorteil der Kombination: Suche und Volltext liegen in derselben Datenbank. Kein
zusätzlicher Suchdienst, keine zweite Datenhaltung, keine Synchronisierung.

---

## Deutsche Volltextsuche in PostgreSQL

Hier lauert eine Falle. Standardmäßig findet PostgreSQL „Schnösel“ und „Schnoesel“ nicht
gegenseitig – auch nicht mit `default_text_search_config = 'german'`. Der übliche Rat ist,
die `unaccent`-Regeln des Servers zu ändern, damit `ä` zu `ae` wird statt zu `a`. Das
verlangt Schreibrechte im Serververzeichnis und ist beim nächsten Update wieder weg.

Das Toolkit geht einen anderen Weg: Neben dem Originaltext steht eine Suchspalte, die
bereits in Python gefaltet und um Komposita-Bestandteile und Wortstämme ergänzt wurde.

```sql
content_search  TEXT NOT NULL,
search_vector   TSVECTOR GENERATED ALWAYS AS (
                    to_tsvector('simple'::regconfig, content_search)
                ) STORED
```

Damit ist die Volltextsuche in der Datenbank exakt dieselbe wie die lexikalische Suche im
Arbeitsspeicher: gleiche Faltung, gleiche Zerlegung, kein Sonderfall. Der Originaltext
bleibt unangetastet in `content` stehen, und es braucht keine Sonderrechte am Server.

Das ist die unspektakulärste, aber wirksamste Verbesserung für deutsche
Unternehmenssuche.

---

## Hybride Suche

Nur Vektoren reichen nicht. Wer nach `§ 37 Abs. 2 VOB/B` sucht, will den Paragraphen und
nicht semantisch Ähnliches. Deshalb laufen beide Verfahren zusammen:

```text
                    Anfrage
                       │
              ┌────────┴────────┐
              ↓                 ↓
       Vektorsuche        PostgreSQL-FTS
              │                 │
              └────────┬────────┘
                       ↓
                  Zusammenführung (RRF)
                       ↓
                   Reranker
```

```python
from deutsches_ki.retrieval import HybridRetriever

retriever = HybridRetriever(store, embedder, vector=True, lexical=True)
treffer = retriever.search("Welche Zahlungsfrist gilt?", top_k=20)
```

Zusammengeführt wird zunächst per **Reciprocal Rank Fusion**, weil das ohne Abstimmung
funktioniert und gute Ergebnisse liefert. Wer feiner steuern will, kann später gewichtete
oder gelernte Verfahren verwenden.

---

## Reranking

Die Vektorsuche holt großzügig Kandidaten, der Reranker sortiert sie neu:

```python
from deutsches_ki.reranking import get_reranker

reranker = get_reranker("bge-reranker-v2-m3")
top5 = reranker.rerank("Welche Zahlungsfrist gilt?", treffer)
```

```text
Top 30 aus der Suche  →  Reranker  →  Top 5 für das Sprachmodell
```

Cross-Encoder-Reranker, BGE-Reranker, Jina und Cohere lassen sich über dieselbe
Schnittstelle anbinden. Tausende Dokumente zu reranken ist weder sinnvoll noch schnell –
deshalb bleibt die Kandidatenmenge begrenzt.

---

## RAG mit Quellenangabe

```python
from deutsches_ki.rag import DeutschRAG

rag = DeutschRAG(retriever=retriever, reranker=reranker, llm=llm)

antwort = rag.ask("Welche Zahlungsfrist gilt laut Vertrag?")
```

```python
RAGAnswer(
    answer="Die Zahlungsfrist beträgt 30 Tage.",
    citations=[Citation(document="Vertrag.pdf", page=12, section="§ 4 Zahlungsbedingungen")],
    retrieved_chunks=[...],
    confidence=0.87,
    metadata={...},
)
```

Eine Antwort ohne Quelle ist nur eine Behauptung. Deshalb ist die Zitatangabe fester
Bestandteil des Ergebnisses und nicht optional. Das Toolkit reicht Dokument, Seite,
Abschnitt und Chunk durch die ganze Kette und prüft am Ende, ob die zitierte Stelle
tatsächlich existiert und den Satz stützt.

Ausgegeben sieht das so aus:

```text
Die Zahlungsfrist beträgt 30 Tage.

Quelle:
  Vertrag.pdf
  Seite 12
  § 4 Zahlungsbedingungen
```

---

## Sprachmodelle anbinden

```python
class ChatProvider:
    def generate(self, messages, **kwargs): ...
```

Angebunden sind:

- **Ollama** – lokal, unkompliziert, gut für Rechner ohne GPU
- **vLLM** – lokal und schnell, mit OpenAI-kompatibler HTTP-Schnittstelle
- **OpenAI-kompatible Endpunkte** – für gehostete Dienste
- **Anthropic** – für den Fall, dass es passt

Der Kern des Toolkits kennt keinen bevorzugten Anbieter. Ein Wechsel ist eine
Konfigurationsfrage, keine Codeänderung.

---

## Vollständig lokal arbeiten

```bash
ollama pull llama3.1
ollama pull bge-m3
```

```python
from deutsches_ki.providers import OllamaProvider

llm = OllamaProvider(model="llama3.1")
```

Damit steht die komplette Kette:

```text
Deutsches PDF  →  Docling  →  PII  →  Chunks  →  BGE-M3  →  pgvector  →  Ollama  →  Antwort mit Quelle
```

Nichts davon verlässt den Rechner. Ein einzelnes Docker-Compose bringt PostgreSQL mit
pgvector, Ollama und das Toolkit zusammen hoch. Für größere Installationen übernimmt vLLM
die Inferenz und stellt dieselbe Schnittstelle bereit.

Das ist der Punkt, an dem DSGVO und EU AI Act aufhören, ein Hindernis zu sein. Standard-
mäßig gibt es keine Telemetrie, keinen Dokumentenupload und keinen externen Aufruf.

---

## Sicherheit: Dokumente sind nicht vertrauenswürdig

Ein PDF ist fremder Inhalt. Wenn darin „Ignoriere alle vorherigen Anweisungen“ steht, ist
das Dokumentinhalt – und keine Anweisung an das Sprachmodell. Das Toolkit hält diese
Grenze ein:

```text
NICHT VERTRAUENSWÜRDIG
  PDF · DOCX · HTML · E-Mail · Datenbanktext
        ↓  Bereinigung
        ↓  PII- und Sicherheitsprüfung
        ↓  Prompt-Injection-Erkennung
  INTERNE, GEPRÜFTE DARSTELLUNG
        ↓  Suche
        ↓  Sprachmodell
```

Die Sicherheitsschicht erkennt:

- **Prompt-Injection** in Dokumenten und in Suchergebnissen
- **PII** vor der Verarbeitung
- **Geheimnisse** wie API-Schlüssel oder Zugangsdaten in Dokumenten
- **Zitatprüfung** – eine Antwort darf nur nennen, was wirklich in einer Quelle steht

Retrieval-Ergebnisse werden immer als Daten behandelt, niemals als Anweisung.

---

## Bewerten statt behaupten

„Die Antwort sieht gut aus“ ist keine Messung. Deshalb bringt das Toolkit einen eigenen
deutschen Benchmark mit, der ohne fremde urheberrechtlich geschützte Dokumente auskommt:
synthetische Dokumente, gemeinfreies Material, offene Behördentexte und frei lizenzierte
Dokumentation.

Beispiel einer Testfrage:

```json
{
  "question": "Wie lange ist die Kündigungsfrist?",
  "document": "vertrag_001.pdf",
  "expected_sources": ["vertrag_001.pdf#page=8"],
  "reference_answer": "Die Kündigungsfrist beträgt drei Monate.",
  "category": "legal",
  "difficulty": "medium"
}
```

Gemessen wird in vier Bereichen:

**Suche** – Recall@1, Recall@5, Recall@10, MRR, nDCG.

**Antwort** – Treue zur Quelle, Relevanz der Antwort, Korrektheit der Zitate,
Kontextausnutzung, Anteil erfundener Aussagen.

**Deutsche Qualität** – Grammatik, Fachterminologie, Anredeform, Klarheit, Umgang mit
Komposita.

**System** – Laufzeit, Token, Kosten (bei externen Modellen), Speicher, CPU, GPU.

Kategorien des Benchmarks: Allgemeines, Wirtschaft, Technik, Recht, Verwaltung, Finanzen,
Personal, Industrie. Gemischt deutsch/englisch ist ein eigener Prüfstein, weil viele
Unternehmen so schreiben.

Ergebnisse landen als JSON unter `benchmarks/results/` und sind reproduzierbar. Wenn ein
deutsches Embedding-Modell BGE-M3 nicht schlägt, schreibt das Toolkit das hin. Wenn
einfaches Chunking den komplizierten Chunker schlägt, ebenfalls. Das macht das Projekt
erst glaubwürdig.

---

## Läuft das wirklich? Tests und Qualitätssicherung

Jede Funktion hat Tests, und jede Änderung läuft durch dieselben Prüfungen, bevor sie
hereinkommt. Die Teststufen sind:

**Unit-Tests** – Normalisierung, jede PII-Erkennung einzeln (IBAN, Steuer-ID,
Steuernummer je Bundesland, Telefon, Adresse), Chunking, Komposita-Zerlegung,
Metadaten.

**Integrationstests** – die ganze Kette: PDF → Docling → Chunks, Chunks → Embeddings,
Embeddings → pgvector, Anfrage → Suche, Suche → Antwort. Diese Tests laufen gegen ein
echtes PostgreSQL mit pgvector.

**Regressionstests** – jeder gefundene Fehler wird zu einem Testfall. Der deutsche
spaCy-Tokenizer zerlegt „Haupt- und Nebensatz“ falsch? Dann gibt es dafür ab sofort einen
Test. Ein Kompositum wurde nicht gefunden? Ein permanenter Test. Der Ordner
`tests/regression/german/` wächst mit jedem behobenen Problem.

**Golden-Datensätze** – feste Beispieldateien mit festen Erwartungen:

```text
german_compounds.json     german_pii.json        german_addresses.json
german_legal.json         german_contracts.json  german_tables.json
german_rag.json
```

Wo ein Ergebnis feststehen kann, wird es festgeprüft und nicht von einem Modell bewertet.
Ein Sprachmodell als Richter ist bequem, aber schwankend. Deterministische Tests kommen
zuerst.

**Vor jeder Veröffentlichung** laufen:

```text
✓ Unit-Tests
✓ Integrationstests
✓ Typprüfung (mypy)
✓ Linting (ruff)
✓ Benchmark-Smoke-Test
✓ Paketbau
✓ Dokumentation
✓ Sicherheitsprüfung
```

Dieselben Schritte laufen in der CI bei jedem Push. Wer eine Änderung einreicht, sieht
sofort, ob sie etwas kaputt macht.

**Leistungsmessungen** erfassen Dokumente, Seiten, Chunks und Embeddings pro Sekunde,
die P95-Latenz sowie CPU- und Speicherverbrauch – als maschinenlesbares JSON, damit
Entwicklung sichtbar bleibt.

---

## Architektur

```text
                            ┌──────────────────────┐
                            │   Deine Anwendung    │
                            └──────────┬───────────┘
                                       ↓
                            ┌──────────────────────┐
                            │ deutsches-ki-toolkit │
                            └──────────┬───────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ↓                             ↓                             ↓
  Dokumente                    Deutsche Sprache              Datenschutz
         │                             │                             │
      Docling                       spaCy                        Presidio
         │                             │                        + deutsche Muster
         └─────────────────────────────┼─────────────────────────────┘
                                       ↓
                              Deutsche Aufbereitung
                                       │
                     ┌─────────────────┼─────────────────┐
                     ↓                 ↓                 ↓
                 Chunking          Entitäten         Metadaten
                     └─────────────────┼─────────────────┘
                                       ↓
                                  Embeddings
                                       │
                          ┌────────────┴────────────┐
                          ↓                         ↓
                       BGE-M3                andere Modelle
                          │
                          ↓
                       pgvector
                          │
                   ┌──────┴──────┐
                   ↓             ↓
             Vektorsuche   PostgreSQL-FTS
                   └──────┬──────┘
                          ↓
                    Hybride Suche
                          ↓
                      Reranker
                          ↓
                       Kontext
                          │
              ┌───────────┴───────────┐
              ↓                       ↓
           Ollama                    vLLM
              └───────────┬───────────┘
                          ↓
                     Antwort
                          │
                          ↓
                  Zitate + Bewertung
```

---

## Projektaufbau

```text
deutsches-ki-toolkit/
├── src/deutsches_ki/
│   ├── core/          # Datenmodelle: Document, Section, Chunk, Entity
│   ├── text/          # Normalisierung, Segmentierung, Komposita, Query-Expansion
│   ├── documents/     # Docling-Anbindung, Struktur, Metadaten
│   ├── pii/           # Detektoren, deutsche Recognizer, Anonymisierung
│   ├── chunking/      # strukturbasiertes Chunking
│   ├── embeddings/    # BGE-M3 und weitere Anbieter
│   ├── retrieval/     # Vektor-, Volltext- und hybride Suche
│   ├── reranking/     # Cross-Encoder und weitere Reranker
│   ├── rag/           # RAG-Engine mit Zitaten
│   ├── evaluation/    # Metriken und Benchmark-Werkzeuge
│   ├── providers/     # Ollama, vLLM, OpenAI-kompatibel, Anthropic
│   ├── security/      # Prompt-Injection, Vertrauensgrenzen
│   ├── storage/       # PostgreSQL + pgvector
│   ├── mcp/           # MCP-Server
│   └── cli/           # Kommandozeile
├── tests/             # unit · integration · regression · benchmark
├── benchmarks/        # pii · retrieval · chunking · rag
├── datasets/          # synthetic · fixtures
├── examples/          # basic · pii · document · rag · ollama · pgvector · mcp
├── docs/              # architecture · guides · concepts · benchmarks
├── scripts/           # benchmark.py · generate_dataset.py · evaluate.py
├── docker/            # Dockerfile · compose.yaml
└── pyproject.toml
```

---

## Kommandozeile

```bash
deutsches-ki parse vertrag.md
deutsches-ki pii rechnung.txt --json
deutsches-ki scan vertrag.md
deutsches-ki anonymize rechnung.txt --mode pseudonymize -o sauber.txt
deutsches-ki chunk vertrag.md --strategy structural --max-tokens 512
deutsches-ki embed ./dokumente --model bge-m3
deutsches-ki search ./dokumente "Wie lange ist die Kündigungsfrist?"
deutsches-ki ask "Welche Zahlungsbedingungen gelten?" --corpus ./dokumente
deutsches-ki evaluate datasets/benchmark/deutsch_rag.yaml --corpus ./dokumente
```

Ein typischer Durchlauf über einen ganzen Ordner:

```bash
deutsches-ki ingest ./dokumente --dsn postgresql://localhost/deutsche_ki
```

Danach beantwortet `ask` Fragen mit Quellenangabe. Ist in `deutsches-ki.yaml`
ein Sprachmodell eingetragen, wird die Antwort formuliert und die genannten
Quellen werden geprüft; ohne Eintrag kommt der bestpassende Abschnitt zurück.

Danach:

```bash
deutsches-ki ask "Welche Zahlungsbedingungen gelten?"
```

```text
Die Zahlungsfrist beträgt 30 Tage.

Quellen:
  Vertrag.pdf
  Seite 12
  § 4 Zahlungsbedingungen
```

---

## Konfiguration

Alles lässt sich in einer Datei `deutsches-ki.yaml` festhalten:

```yaml
language: de

documents:
  parser: docling

pii:
  enabled: true
  mode: anonymize
  detectors: [regex, presidio, spacy, gliner]

embeddings:
  provider: bge-m3

retrieval:
  vector: true
  lexical: true
  fusion: rrf
  top_k: 20

reranking:
  enabled: true
  provider: lexical
  top_k: 5

llm:
  provider: ollama
  model: llama3.1

storage:
  provider: pgvector
  dsn: postgresql://localhost/deutsche_ki
```

Ein Aufrufparameter schlägt die Datei, die Datei schlägt die Vorgabe. Fehlt die
Datei, gelten die Vorgaben. Für Container empfiehlt es sich, die Datei im
Repository zu lassen und Zugangsdaten beim Start zu übergeben.

---

## Docker

```bash
docker compose -f docker/compose.yaml up -d postgres
```

Gestartet wird PostgreSQL mit pgvector. Ollama kommt über ein Profil dazu, damit
niemand eine Grafikkarte braucht:

```bash
docker compose -f docker/compose.yaml --profile local-llm up -d
```

Das Toolkit selbst lässt sich ebenfalls als Image bauen:

```bash
docker build -f docker/Dockerfile -t deutsches-ki-toolkit .
docker run --rm -v "$PWD/datasets/fixtures:/daten:ro" deutsches-ki-toolkit pii /daten/rechnung.txt
```

Läuft Docker Hub im eigenen Netz nicht, lassen sich beide Images über eine
andere Registry bauen; die Basis ist jeweils ein `--build-arg`:

```bash
docker build -f docker/postgres/Dockerfile -t deutsches-ki-postgres:17 docker/postgres
POSTGRES_IMAGE=deutsches-ki-postgres:17 docker compose -f docker/compose.yaml up -d postgres
```

---

## Häufige Fragen

**Warum nicht einfach LangChain oder LlamaIndex?**
Kannst du. Beide sind gute Rahmenwerke. Sie kennen deutsche Komposita aber genauso wenig
wie deutsche Steuernummern. Dieses Toolkit lässt sich daneben betreiben und ergänzt genau
diese Lücken. Haystack und LlamaIndex lassen sich bei Bedarf anbinden, sind aber keine
Voraussetzung.

**Muss ich zwingend ein Sprachmodell einsetzen?**
Nein. Suche, PII-Erkennung, Chunking und Anonymisierung funktionieren ohne. Ein Modell
brauchst du erst für die Antwortformulierung und für die Bewertung von Antworten.

**Verlassen meine Daten den Rechner?**
Nur, wenn du einen externen Anbieter ausdrücklich konfigurierst. Standardmäßig gibt es
keine Telemetrie, kein Hochladen und keine externen Aufrufe.

**Ist das ein deutsches Sprachmodell?**
Nein. Das Toolkit ist sprachbewusst, aber modellneutral. Es arbeitet mit dem Modell deiner
Wahl – lokal oder gehostet.

---

## Mitmachen

Gute Einstiegspunkte sind ausdrücklich erwünscht:

- einen deutschen PII-Recognizer ergänzen
- einen Benchmark-Fall beisteuern
- das Chunking verbessern
- eine Testdatei hinzufügen
- Fachterminologie für eine Branche ergänzen
- ein Embedding-Modell vergleichen
- die Dokumentation schärfen
- einen Anbieter anbinden

Beiträge werden mit `good first issue`, `help wanted`, `German NLP`, `RAG`, `privacy`,
`benchmark` und `documentation` gekennzeichnet, damit man schnell findet, wo man anfangen
kann. Neue Fälle gehören immer mit einem Test dazu. Wer ein Problem meldet, hilft am
meisten mit einem Dokument, das es auslöst – anonymisiert oder synthetisch.

---

## Lizenz

Apache-2.0. Die Lizenz ist bewusst permissiv gewählt, inklusive ausdrücklicher
Patentregelung, damit auch Unternehmen das Toolkit ohne Bedenken einsetzen können.

---

## Quellen und weiterführende Links

- Presidio, offene Issues zur deutschen Unterstützung – [#1343](https://github.com/data-privacy-stack/presidio/issues/1343)
- Docling, Formatierung deutscher PDFs – [Issue #1042](https://github.com/docling-project/docling/issues/1042)
- libpostal, deutsche Adressen – [Issue #510](https://github.com/openvenues/libpostal/issues/510)
- spaCy, deutsches Lemmatisieren und Tokenisieren – [Issue #2486](https://github.com/explosion/spaCy/issues/2486)
- PostgreSQL und deutsche Umlaute in der Volltextsuche – [dbi services](https://www.dbi-services.com/blog/dealing-with-german-umlaute-in-postgresqls-full-text-search/)
- Komposita und Suchrelevanz – [Bitext](https://www.bitext.com/blog/some-of-your-rag-related-issues-have-an-easy-quick-solution-decompounding/)
- Deutsche NER im Vergleich: Presidio, spaCy, GLiNER – [Nils Durner](https://ndurner.github.io/ner)
- BGE-M3 – [Modellkarte](https://huggingface.co/BAAI/bge-m3)
- German-NLP: Sammlung deutschsprachiger Ressourcen – [adbar/German-NLP](https://github.com/adbar/German-NLP)

---

**deutsches-ki-toolkit** – gebaut für echte deutsche Daten. Dokumente, Datenschutz, Suche,
Antworten mit Quellen. Ehrlich gemessen.
