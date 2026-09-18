# deutsches-ki-toolkit

[Deutsch](README.md) · **English**

**German documents. German data. Answers you can rely on.**

`deutsches-ki-toolkit` is a Python library for anyone building AI applications over
German-language documents. It handles the many small and large peculiarities that generic
frameworks miss: umlauts and ß, compound words, German company and person names, IBANs and
tax numbers, contracts with sections, invoices, HR records and technical documentation. And
it makes sure sensitive data never leaves your own network.

The toolkit does not set out to replace Docling, spaCy, Presidio, BGE-M3, pgvector or
Ollama. It sits in front of them and joins them into a pipeline that takes German seriously
— from the first byte of a PDF to an answer you can verify.

```text
German document  →  Structure  →  PII  →  Chunks  →  Embeddings  →  Search  →  Answer with source
```

---

## Status

This overview says what works today. Everything below describes the aim of the project, not
what the current release delivers.

**Working and tested**

- German text normalization, sentence segmentation, compound splitting
- German PII detection with checksums, five anonymization modes
- Structure-based chunking with section and page references
- In-memory search: vector and lexical, merged with RRF
- German full-text search without the `unaccent` trick
  (verified against real PostgreSQL, including in CI)
- Lexical reranking, RAG engine with citation checking
- Prompt-injection and secret detection
- Evaluation with recall, MRR and nDCG, including a dataset
- Document type detection, terminology checking, style checking
- Domain packages for legal, finance, HR, technical and industry
- Performance measurement and comparison of embedding models
- Command line, MCP tools, Docker image
- Embeddings via BGE-M3 and cross-encoder reranking, verified against real models
- PDF via Docling with the section structure preserved: `§ 4 Zahlungsbedingungen` stays its
  own section instead of becoming one long string
- Reading detects the language (German, English, mixed) and pulls German business
  identifiers such as invoice and customer numbers into the metadata
- spaCy and Presidio detectors verified against a real German model, with a CI run. This
  confirms the starting point of the project: Presidio does not find a German Steuernummer
  or a Handelsregisternummer, the built-in patterns do.
- Ollama connection against a real model: the chain of search, prompt and answer runs and
  returns a verifiable German answer. Two observations about it are below.
- GLiNER detector against a real model: it finds organizations that the German spaCy model
  deliberately skips.
- MCP server: tools are called through the real MCP interface, and a missing document comes
  back as an error result instead of a crash.
- Web demo with five steps. Each step puts the German handling next to a naive one, so the
  difference is visible rather than claimed.

The included evaluation set (12 questions over the test files) gives, with the hashing
model: Recall@1 0.92, Recall@5 1.00, MRR 0.94, nDCG@5 0.96. Reproducible with:

```bash
deutsches-ki evaluate datasets/benchmark/deutsch_rag.yaml --corpus datasets/fixtures
```

Those numbers depend on the corpus, and that is not a side note. If the test document also
exists in a second format, the run reads it too, and the same command gives Recall@1 0.58
instead of 0.92. The best hit is then `vertrag.pdf#§ 4 Zahlungsbedingungen` at 0.033 ahead
of `vertrag.md#§ 4 Zahlungsbedingungen` at 0.032 — the same section, just from the other
file, and the evaluation set expects the Markdown one. If you quote a metric, quote the
corpus with it.

Before that it was Recall@1 0.75 and MRR 0.84. The difference comes from coarse word stems
in the search tokens: „Ersatzteilen“ now finds „Ersatzteile“. That is exactly what the
evaluation run is for.

The same command also compares embedding models:

```bash
deutsches-ki evaluate datasets/benchmark/deutsch_rag.yaml --corpus datasets/fixtures --compare hashing,bge-m3
```

| Model   | Dimension | Recall@5 |  MRR | nDCG@5 | ms per question |
|---------|-----------|----------|------|--------|-----------------|
| hashing | 256       | 1.00     | 0.78 | 0.84   | 1.5             |
| BGE-M3  | 1024      | 1.00     | 0.88 | 0.91   | 182.9           |

Both find every answer among the first five. BGE-M3 puts them on rank one more often and
needs about a hundred and twenty times as long per question. For twelve questions that is
irrelevant; for thousands of requests it is a decision. Which is why this gets measured
rather than claimed.

The same holds for the German handling itself. Over the same twelve questions the German
search reaches 10 of 12, and a carefully built naive search with punctuation cleanup and a
stopword list also reaches 10 of 12. Only the careless variant — split on whitespace, leave
punctuation attached — drops to 8 of 12. So the advantage does not show everywhere, only
where German is hard: „Ersatzteilen“ finds the section „Ersatzteile“, and none of the naive
variants manage that. The German search also loses the occasional case, for instance
„Wartung“ against „Wartungsintervalle“. Anyone claiming otherwise has not measured.

**Present, but not yet verified against real systems**

Nothing is open here at the moment. Every optional component has been run against the real
library at least once, and most of them run in CI.

**What the language model does not do**

The connection is verified; the model behind it was the smallest one that runs on a laptop.
Two things stood out and belong here:

A model with one billion parameters **does not follow the citation instruction**. It answers
the question correctly („Die Zahlungsfrist ist nach § 4 des Dokuments 30 Tage nach
Rechnungsstellung“) but leaves out the required numbers `[1]`. The citation check reports
that as „no source given“ instead of overlooking it.

Judging with a language model is **unstable**. The same question, the same sources, the same
answer, scored three times: faithfulness 0.0, then 0.5, then 1.0. That is exactly why the
deterministic measures are the foundation and a model's judgment is a voluntary extra. A
model as judge is convenient, but not reliable.

**Not built yet**

- Answer-quality evaluation via a language model (faithfulness, relevance) – the
  deterministic approximations exist, the model's judgment does not
- Enterprise database connectivity (translating questions into SQL)
- Benchmark website: the web demo exists, a public page with measurements from several runs
  does not
- Fine-tuning

---

## Why this project exists

Anyone who has built a RAG application over German business documents knows the surprises.
They do not show up in the model, but before and after it.

**Compounds hide meaning.** „USBCKabel“, „USB C Kabel“ and „USB-C-Kabel“ mean the same
thing. To a tokenizer they are three different things. German, Dutch, Swedish and Finnish
compounds hide whole words inside a single token. If you do not split before indexing, you
lose hits — and semantic search only rarely rescues that.
([Bitext](https://www.bitext.com/blog/some-of-your-rag-related-issues-have-an-easy-quick-solution-decompounding/))

**Presidio does not know German tax law.** The default installation ships around 30
detection patterns aimed mainly at US formats. German Steuer-IDs and Steuernummern are not
among them, nor are German ID card numbers. The Steuernummer alone has 16 formats, one per
federal state. A practical test gave a hit rate of 0 percent for IBAN, BIC, Steuer-ID and
Handelsregisternummer with the default settings. Even switching the language does not help
everywhere: in Presidio issue
[#1343](https://github.com/data-privacy-stack/presidio/issues/1343),
`get_supported_entities(language="de")` returns only `BANK_ACCOUNT`, and context words do
not work for German at all.

**spaCy does not recognize organizations in German.** The German model is trained to ignore
company names because they cause too many false positives. In a public comparison,
`de_core_news_lg` reached just under 78 percent while GLiNER reached around 95 percent.
Relying on a single model leaves a lot on the table.

**PostgreSQL does not search umlauts the way you expect.** „Schnösel“ and „Schnoesel“ do not
find each other with the default configuration. Neither does
`default_text_search_config = 'german'` change that. It takes a custom text search
configuration and adjusted `unaccent` rules so that `ä → ae` is mapped.
([dbi services](https://www.dbi-services.com/blog/dealing-with-german-umlaute-in-postgresqls-full-text-search/))

**Generic chunking cuts paragraphs apart.** German contracts and legal texts live on
`§ 4 Abs. 2`. A chunker that stubbornly counts tokens tears paragraph one away from
paragraph two — and that is exactly where the exception is. Section-aware splitting
performs better in benchmarks than the usual fixed-size strategy.

**Unfinished components in the ecosystem.** Docling occasionally splits German PDFs with
wrong spaces and separated words
([issue #1042](https://github.com/docling-project/docling/issues/1042)). Address parsers
fail on „Straße des 17. Juni“ or on postal codes that end up inside the house number
([libpostal #510](https://github.com/openvenues/libpostal/issues/510)). The German spaCy
tokenizer stumbles over suspended hyphens like „Haupt- und Nebensatz“ and contractions like
„unterm“ ([spaCy #2486](https://github.com/explosion/spaCy/issues/2486)).

**And the legal framework.** Since 2 August 2026 the EU AI Act applies in its broad scope;
violations can cost up to 35 million euros. For mid-sized companies, data sovereignty
stopped being a marketing word a long time ago and became a requirement. Many companies do
not want to hand their documents to a cloud provider in the first place.

This list is the reason the toolkit exists. Every item above is solvable on its own — but
nobody wants to solve it ten times.

---

## What's inside

- **Normalization** for umlauts, ß, quotation marks, dashes and suspended hyphens —
  separate paths for display and search, without destroying the original text
- **Sentence and word segmentation** that knows German abbreviations (`z. B.`,
  `Dr.`, `Dipl.-Ing.`, `Nr.`, `Abs.`), plus ordinals ("im 1. Quartal", "die 2.
  Auflage") and abbreviations that may end a sentence ("usw.", "u. a.", per
  Duden rule D 4)
- **Entity recognition** across several detectors at once (spaCy, Presidio, regex, GLiNER,
  transformer)
- **German PII** with checksums: IBAN, BIC, USt-IdNr., Steuer-ID, Steuernummer, social
  security number, ID card number, Handelsregisternummer, addresses, phone numbers, email
  addresses and business identifiers such as invoice, customer, order and contract numbers
- **Anonymization and pseudonymization** with the modes `redact`, `replace`, `mask`, `hash`
  and `pseudonymize`, deterministic within a session
- **Document reading** via Docling for PDF, DOCX, XLSX, PPTX, HTML, Markdown, images and
  plain text — with the structure preserved instead of one long string
- **Structure-based chunking** that cuts at headings, sections, paragraphs and sentences and
  treats the token limit as a last resort
- **Compound analysis** and splitting for search
- **Search with expanded queries**: dictionary, lemmatization, compounds, domain glossary,
  embedding similarity
- **Embeddings** with BGE-M3 as the starting point and interchangeable providers
- **PostgreSQL + pgvector** with German full-text search in the same database
- **Hybrid search** from vector and lexical retrieval, merged with Reciprocal Rank Fusion
- **Reranking** as its own interchangeable step
- **RAG with mandatory sources**: every answer comes with document, page and section
- **Local operation** with Ollama or vLLM, without a single byte leaving the building
- **Security layer** against prompt injection and for clear trust boundaries
- **Evaluation** with a German benchmark, retrieval and generation metrics
- **MCP server** and **command line** for everyday use

---

## What the toolkit deliberately is not

It is not a chat interface, not an agent framework, not a vector database, not a PDF parser,
not an LLM and not a set of models to train. All of that already exists, and it is good.
This project focuses on the layer above: German language, German personal data, German
document structure, traceable answers and verifiable results.

---

## Installation

```bash
pip install deutsches-ki-toolkit
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add deutsches-ki-toolkit
```

Python 3.12 or newer is required.

The default installation is deliberately slim. Heavy components are installed on demand:

```bash
pip install "deutsches-ki-toolkit[docling]"    # reading documents
pip install "deutsches-ki-toolkit[embeddings]" # BGE-M3 and friends
pip install "deutsches-ki-toolkit[postgres]"   # pgvector + full-text search
pip install "deutsches-ki-toolkit[mcp]"        # MCP server
pip install "deutsches-ki-toolkit[all]"
```

The German spaCy model is installed once afterwards:

```bash
python -m spacy download de_core_news_lg
```

---

## Quick start

```python
from deutsches_ki import GermanDocument

doc = GermanDocument.from_file("vertrag.pdf")

# Structure is in place, now find the sensitive parts
pii = doc.detect_pii()
print(pii)

# Work confidentially and still be able to search
doc.anonymize(mode="pseudonymize")

# German chunking at § boundaries
chunks = doc.chunk(strategy="structural")

# Ask questions, get an answer with its source
answer = doc.search("Welche Kündigungsfrist gilt?")
print(answer.answer)
for citation in answer.citations:
    print(citation.document, citation.page, citation.section)
```

There is always more you can do, but that is the shortest route from a PDF to a verifiable
answer.

---

## Normalizing German text

```python
from deutsches_ki.text import normalize_german

normalize_german("Die Straße ist schön.", mode="display")
# "Die Straße ist schön."

normalize_german("Die Straße ist schön.", mode="search")
# "die strasse ist schoen"  (search form only, the original stays intact)
```

The most important principle: **never destroy the original text.** `ß` does not become `ss`
everywhere, and umlauts do not become `ae`, `oe`, `ue` everywhere. There are two separate
paths:

- `display` – how the text should look. `Straße` stays `Straße`.
- `search` – an additional representation that lets `strasse` match.

German text brings further peculiarities that get cleaned up here:

```python
from deutsches_ki.text import (
    normalize_unicode,  # ─ vs. –, „ vs. ", non-breaking spaces
    normalize_quotes,  # „richtig“ and »so«
    normalize_dashes,  # dash, range dash, hyphen
    normalize_ergaenzung,  # "Haupt- und Nebensatz" → "Hauptsatz und Nebensatz"
    normalize_whitespace,
    normalize_for_search,
)
```

The suspended hyphen is a good example: „Haupt- und Nebensatz“ and „Hauptsatz und Nebensatz“
mean exactly the same thing, but look entirely different to a model.
`normalize_ergaenzung` turns them into the same form.

---

## Splitting sentences and words

```python
from deutsches_ki.text import split_sentences

sentences = split_sentences(
    "Die Frist beträgt 30 Tage (vgl. § 4 Abs. 2). "
    "Zahlungen sind an die Beispiel GmbH, z. B. per Überweisung, zu leisten."
)
for sentence in sentences:
    print(sentence.start, sentence.end, sentence.text)
```

The segmentation targets the cases where standard solutions fail:

```text
z. B.   Dr.   Prof.   Dipl.-Ing.   GmbH   AG   e.V.   Nr.   Art.   Abs.   §   bzw.   usw.
```

Numbers with a period at the end of a sentence („… 3.500 Euro.“) are not split incorrectly,
and list markers such as „1.“ or „a)“ stay with their item.

---

## Entities and German PII

```python
from deutsches_ki.pii import detect

matches = detect(
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

Detected types include:

**Finance** – IBAN (with Mod-97 check), BIC, card numbers.

**Tax** – USt-IdNr./VAT ID, Steuer-ID (eleven digits) and Steuernummer (state tax number).
The Steuernummer is recognized in the formats of all 16 federal states, each with a
plausibility check. This is exactly where generic tools fail.

**Contact** – landline and mobile numbers in German notation, email addresses.

**Addresses** – postal code, street, house number, house number suffixes such as `12a`,
ranges such as `414-424`, city. Detection follows the German order (street before house
number) rather than the US pattern.

**Personal identifiers** – social security number, ID card number.

**Business** – Handelsregisternummer (HRA/HRB), invoice number, customer number, order
number, contract number.

**People and organizations** – across several detectors, so company names do not slip
through.

### Several detectors instead of one model

No single approach finds everything. So the detectors run together and complement each
other:

```python
EntityDetector
    ├── RegexDetector        # structured identifiers + checksum
    ├── PresidioDetector     # established framework, extended with German patterns
    ├── SpaCyDetector        # morphology, syntax, people and places
    ├── GliNERDetector       # organizations and unknown names
    └── TransformerDetector  # context-dependent cases
```

Every match carries its origin (`source`) and a confidence value. If you need fewer false
positives you can filter by detector; if you need more recall you switch on GLiNER.

### German context words

Detection gets noticeably better when a cue word is nearby. That is why the toolkit ships
its own German context lists — „Rechnungsnummer“, „Kundennummer“, „Steuernummer“, „IBAN“,
„Ansprechpartner“, „geboren am“ and more. English context words do not help here, as the
Presidio project
[confirms](https://github.com/data-privacy-stack/presidio/issues/1343).

---

## Anonymizing and pseudonymizing

```python
from deutsches_ki.pii import anonymize

anonymize("Max Mustermann arbeitet bei der Beispiel GmbH.", mode="redact")
# "[PERSON] arbeitet bei der [ORGANISATION]."

anonymize("Max Mustermann arbeitet bei der Beispiel GmbH.", mode="pseudonymize")
# "PERSON_001 arbeitet bei der ORG_001."
```

Five modes:

| Mode           | Result                                                              |
|----------------|---------------------------------------------------------------------|
| `redact`       | Placeholders such as `[PERSON]`, `[IBAN]`                            |
| `replace`      | Replaced with a fixed or generated identifier                        |
| `mask`         | Partially hidden: `DE89 **** **** **** **** 00`                      |
| `hash`         | One-way hash, not reversible                                         |
| `pseudonymize` | Stable identifier such as `PERSON_001`, constant within the session  |

Pseudonyms stay stable: the same name always gets the same identifier within a session. That
lets you process and compare documents without passing on the real names. If you need the
mapping back, the process can be made reversible with a key — by default it is not.

The most important point: anonymization is not an appendix, it sits inside the processing
chain. Text is anonymized before it reaches an embedding model or a language model — not
after.

---

## Reading documents and keeping structure

```python
from deutsches_ki.documents import parse

doc = parse("vertrag.pdf")

print(doc.title)
for section in doc.sections:
    print(section.level, section.title, section.page)
```

The toolkit does not throw a PDF into one big string. The structure survives the whole
chain:

```text
Document
├── Title
├── Metadata
├── Sections
│   ├── Heading
│   ├── Paragraphs
│   ├── Tables
│   ├── Lists
│   └── Cross references
└── Pages
```

For German contracts this means concretely that `§ 1 Vertragsgegenstand`, `§ 2 Vergütung`,
`§ 3 Zahlungsbedingungen`, `§ 4 Haftung` stay separate, addressable units — with page number
and position. Tables are passed on as tables and not ground down into running text.

Under the hood Docling reads the files. The toolkit's work starts afterwards: language
detection (German or mixed), German normalization, PII detection and pulling out German
metadata such as invoice date, invoice number or contract number.

---

## German chunking

Chunking is where most German RAG applications lose quality. Nothing is cut blindly at a
fixed token count here; there is an order of precedence:

```text
Document structure
      ↓
Section boundaries
      ↓
Paragraph boundaries
      ↓
Sentence boundaries
      ↓
Token limit (last resort only)
```

Bad:

```text
Chunk 1: § 4 Zahlungsbedingungen ...
Chunk 2: ... 30 Tage nach Rechnungsstellung ...
```

Better:

```text
Chunk 1: § 4 Zahlungsbedingungen

         (1) Der Auftraggeber ...

         (2) Die Zahlung ist innerhalb von 30 Tagen
             nach Rechnungsstellung fällig.
```

A paragraph containing an exception stays together. Overlap is possible, but not as a
crutch — it is there to keep section context at the edges.

Every chunk carries its path through the document:

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

That information is worth gold later. You can restrict hits to one paragraph, filter by
document type and name the source exactly.

---

## Compounds

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

For search, a compound is additionally turned into a search form in which its parts are
visible. Someone searching for „Arbeitsunfähigkeitsbescheinigung“ should also find passages
that talk about the „Bescheinigung der Arbeitsunfähigkeit“. The splitting relies on a German
dictionary, morphological analysis and — if necessary — a language model as a fallback. It
is deliberately heuristic and returns several candidates rather than a single, possibly
wrong answer.

---

## Expanding queries

```python
from deutsches_ki.text import expand_query

expand_query("Urlaubsantrag genehmigen")
```

```python
["Urlaubsantrag", "Urlaubsfreigabe", "Urlaubsgenehmigung", "Abwesenheitsantrag", "Urlaubstage"]
```

Expansion comes from several sources, not from a language model alone:

```text
Dictionary
    + lemmatization
    + compound analysis
    + the customer's domain glossary
    + embedding similarity
    + optional: language model
```

A glossary you maintain yourself is often the best source, because it knows the language of
the company. That is why you can pass in your own terms without changing the toolkit.

---

## Embeddings

```python
from deutsches_ki.embeddings import get_embedder

embedder = get_embedder("bge-m3")
vectors = embedder.embed_documents(["Die Zahlungsfrist beträgt 30 Tage."])
```

The starting point is **BGE-M3**: multilingual, 1024 dimensions, long inputs up to 8192
tokens and — importantly — suitable for dense, sparse and multi-vector retrieval at the same
time. That makes it a solid default without tying you to it.

All providers follow the same interface:

```python
class EmbeddingProvider:
    def embed_documents(self, texts): ...
    def embed_query(self, text): ...
```

You can try BGE-M3, multilingual-e5, German models, Qwen embeddings, Ollama embeddings and
OpenAI. Which model wins when is in the benchmarks — not in a gut feeling.

---

## Storage: PostgreSQL and pgvector

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

The tables cover documents, sections, chunks, entities and embeddings. pgvector supports
exact search as well as HNSW and IVFFlat indexes. For comparison against the optimum, exact
search can be switched on at any time.

One advantage of the combination: search and full text live in the same database. No extra
search service, no second data store, no synchronization.

---

## German full-text search in PostgreSQL

A trap lurks here. By default PostgreSQL does not find „Schnösel“ and „Schnoesel“ for each
other — not even with `default_text_search_config = 'german'`. The usual advice is to change
the server's `unaccent` rules so that `ä` becomes `ae` instead of `a`. That requires write
access to the server directory and is gone again with the next update.

The toolkit takes a different route: next to the original text sits a search column that has
already been folded in Python and extended with compound parts and word stems.

```sql
content_search  TEXT NOT NULL,
search_vector   TSVECTOR GENERATED ALWAYS AS (
                    to_tsvector('simple'::regconfig, content_search)
                ) STORED
```

That makes full-text search in the database exactly the same as lexical search in memory:
same folding, same splitting, no special case. The original text stays untouched in
`content`, and no special server privileges are needed.

This is the least spectacular but most effective improvement for German enterprise search.

---

## Hybrid search

Vectors alone are not enough. Someone searching for `§ 37 Abs. 2 VOB/B` wants that
paragraph, not something semantically similar. So both methods run together:

```text
                    Query
                       │
              ┌────────┴────────┐
              ↓                 ↓
       Vector search      PostgreSQL FTS
              │                 │
              └────────┬────────┘
                       ↓
                Fusion (RRF)
                       ↓
                   Reranker
```

```python
from deutsches_ki.retrieval import HybridRetriever

retriever = HybridRetriever(store, embedder, vector=True, lexical=True)
matches = retriever.search("Welche Zahlungsfrist gilt?", top_k=20)
```

Fusion starts with **Reciprocal Rank Fusion**, because it works without tuning and gives
good results. If you need finer control you can move to weighted or learned methods later.

---

## Reranking

Vector search fetches candidates generously; the reranker reorders them:

```python
from deutsches_ki.reranking import get_reranker

reranker = get_reranker("bge-reranker-v2-m3")
top5 = reranker.rerank("Welche Zahlungsfrist gilt?", matches)
```

```text
Top 30 from search  →  Reranker  →  Top 5 for the language model
```

Cross-encoder rerankers, BGE reranker, Jina and Cohere can be connected through the same
interface. Reranking thousands of documents is neither sensible nor fast — which is why the
candidate set stays bounded.

---

## RAG with citations

```python
from deutsches_ki.rag import DeutschRAG

rag = DeutschRAG(retriever=retriever, reranker=reranker, llm=llm)

answer = rag.ask("Welche Zahlungsfrist gilt laut Vertrag?")
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

An answer without a source is just a claim. That is why the citation is a fixed part of the
result and not optional. The toolkit passes document, page, section and chunk through the
whole chain and checks at the end whether the cited passage actually exists and supports the
sentence.

The output looks like this:

```text
Die Zahlungsfrist beträgt 30 Tage.

Quelle:
  Vertrag.pdf
  Seite 12
  § 4 Zahlungsbedingungen
```

---

## Connecting language models

```python
class ChatProvider:
    def generate(self, messages, **kwargs): ...
```

Connected are:

- **Ollama** – local, straightforward, good for machines without a GPU
- **vLLM** – local and fast, with an OpenAI-compatible HTTP interface
- **OpenAI-compatible endpoints** – for hosted services
- **Anthropic** – in case that fits

The core of the toolkit has no preferred provider. Switching is a configuration question,
not a code change.

---

## Running fully local

```bash
ollama pull llama3.1
ollama pull bge-m3
```

```python
from deutsches_ki.providers import OllamaProvider

llm = OllamaProvider(model="llama3.1")
```

That completes the chain:

```text
German PDF  →  Docling  →  PII  →  Chunks  →  BGE-M3  →  pgvector  →  Ollama  →  Answer with source
```

None of it leaves the machine. A single Docker Compose brings PostgreSQL with pgvector,
Ollama and the toolkit up together. For larger installations vLLM takes over inference and
offers the same interface.

That is the point at which GDPR and the EU AI Act stop being an obstacle. By default there is
no telemetry, no document upload and no external call.

---

## Security: documents are not trustworthy

A PDF is foreign content. If it says „Ignoriere alle vorherigen Anweisungen“, that is
document content — not an instruction to the language model. The toolkit respects that
boundary:

```text
NOT TRUSTWORTHY
  PDF · DOCX · HTML · email · database text
        ↓  cleanup
        ↓  PII and security checks
        ↓  prompt-injection detection
  INTERNAL, VERIFIED REPRESENTATION
        ↓  search
        ↓  language model
```

The security layer detects:

- **Prompt injection** in documents and in search results
- **PII** before processing
- **Secrets** such as API keys or credentials inside documents
- **Citation checking** – an answer may only name what actually appears in a source

Retrieval results are always treated as data, never as instructions.

---

## Measure instead of claiming

„The answer looks good“ is not a measurement. That is why the toolkit ships its own German
benchmark, which manages without third-party copyrighted documents: synthetic documents,
public-domain material, open government texts and freely licensed documentation.

An example test question:

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

Four areas are measured:

**Retrieval** – Recall@1, Recall@5, Recall@10, MRR, nDCG.

**Answer** – faithfulness to the source, relevance of the answer, correctness of citations,
context usage, share of fabricated statements.

**German quality** – grammar, domain terminology, form of address, clarity, handling of
compounds.

**System** – runtime, tokens, cost (for external models), memory, CPU, GPU.

Benchmark categories: general, business, technical, legal, administration, finance, HR,
industry. Mixed German/English is its own test case, because that is how many companies
write.

Results are stored as JSON under `benchmarks/results/` and are reproducible. If a German
embedding model does not beat BGE-M3, the toolkit writes that down. If simple chunking beats
the elaborate chunker, likewise. That is what makes the project credible in the first place.

---

## Does it actually work? Tests and quality assurance

Every feature has tests, and every change goes through the same checks before it lands. The
test levels are:

**Unit tests** – normalization, every PII detector on its own (IBAN, Steuer-ID, Steuernummer
per federal state, phone, address), chunking, compound splitting, metadata.

**Integration tests** – the whole chain: PDF → Docling → chunks, chunks → embeddings,
embeddings → pgvector, query → search, search → answer. These run against a real PostgreSQL
with pgvector.

**Regression tests** – every bug found becomes a test case. The German spaCy tokenizer
splits „Haupt- und Nebensatz“ incorrectly? From now on there is a test for it. A compound
was not found? A permanent test. The folder `tests/regression/german/` grows with every
problem fixed.

**Golden datasets** – fixed sample files with fixed expectations:

```text
german_compounds.json     german_pii.json        german_addresses.json
german_legal.json         german_contracts.json  german_tables.json
german_rag.json
```

Where a result can be fixed, it is asserted rather than judged by a model. A language model
as judge is convenient, but unstable. Deterministic tests come first.

**Before every release:**

```text
✓ Unit tests
✓ Integration tests
✓ Type checking (mypy)
✓ Linting (ruff)
✓ Benchmark smoke test
✓ Package build
✓ Documentation
✓ Security check
```

The same steps run in CI on every push. Anyone submitting a change sees immediately whether
it breaks something.

**Performance measurements** capture documents, pages, chunks and embeddings per second, the
P95 latency and CPU and memory usage — as machine-readable JSON, so that development stays
visible.

---

## Architecture

```text
                            ┌──────────────────────┐
                            │   Your application   │
                            └──────────┬───────────┘
                                       ↓
                            ┌──────────────────────┐
                            │ deutsches-ki-toolkit │
                            └──────────┬───────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ↓                             ↓                             ↓
  Documents                    German language                Data protection
         │                             │                             │
      Docling                       spaCy                        Presidio
         │                             │                       + German patterns
         └─────────────────────────────┼─────────────────────────────┘
                                       ↓
                              German preparation
                                       │
                      ┌────────────────┼────────────────┐
                      ↓                ↓                ↓
                  Chunking         Entities         Metadata
                      └────────────────┼────────────────┘
                                       ↓
                                  Embeddings
                                       │
                           ┌───────────┴───────────┐
                           ↓                       ↓
                        BGE-M3              other models
                           │
                           ↓
                        pgvector
                           │
                    ┌──────┴──────┐
                    ↓             ↓
             Vector search   PostgreSQL FTS
                    └──────┬──────┘
                           ↓
                     Hybrid search
                           ↓
                       Reranker
                           ↓
                        Context
                           │
              ┌────────────┴────────────┐
              ↓                         ↓
           Ollama                      vLLM
              └────────────┬────────────┘
                           ↓
                        Answer
                           │
                           ↓
                  Citations + evaluation
```

---

## Project layout

```text
deutsches-ki-toolkit/
├── src/deutsches_ki/
│   ├── core/          # data models: Document, Section, Chunk, Entity
│   ├── text/          # normalization, segmentation, compounds, query expansion
│   ├── documents/     # Docling integration, structure, metadata
│   ├── pii/           # detectors, German recognizers, anonymization
│   ├── chunking/      # structure-based chunking
│   ├── embeddings/    # BGE-M3 and other providers
│   ├── retrieval/     # vector, full-text and hybrid search
│   ├── reranking/     # cross-encoder and other rerankers
│   ├── rag/           # RAG engine with citations
│   ├── evaluation/    # metrics and benchmark tooling
│   ├── providers/     # Ollama, vLLM, OpenAI-compatible, Anthropic
│   ├── security/      # prompt injection, trust boundaries
│   ├── storage/       # PostgreSQL + pgvector
│   ├── mcp/           # MCP server
│   └── cli/           # command line
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

## Command line

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

A typical run over a whole folder:

```bash
deutsches-ki ingest ./dokumente --dsn postgresql://localhost/deutsche_ki
```

After that, `ask` answers questions with citations. If a language model is configured in
`deutsches-ki.yaml`, the answer is phrased by it and the cited sources are checked; without
one, the best-matching section comes back.

Then:

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

## Configuration

Everything can be put in a `deutsches-ki.yaml` file:

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

A command-line argument beats the file, the file beats the default. If the file is missing,
the defaults apply. For containers it is best to keep the file in the repository and pass
credentials in at startup.

---

## Docker

```bash
docker compose -f docker/compose.yaml up -d postgres
```

This starts PostgreSQL with pgvector. Ollama comes along through a profile so that nobody
needs a GPU:

```bash
docker compose -f docker/compose.yaml --profile local-llm up -d
```

The toolkit itself can also be built as an image:

```bash
docker build -f docker/Dockerfile -t deutsches-ki-toolkit .
docker run --rm -v "$PWD/datasets/fixtures:/daten:ro" deutsches-ki-toolkit pii /daten/rechnung.txt
```

If Docker Hub is not reachable inside your network, both images can be built against a
different registry; the base image is a `--build-arg` in each case:

```bash
docker build -f docker/postgres/Dockerfile -t deutsches-ki-postgres:17 docker/postgres
POSTGRES_IMAGE=deutsches-ki-postgres:17 docker compose -f docker/compose.yaml up -d postgres
```

---

## Web demo

The `demo/` folder holds a demo with five steps: split, find sensitive data, search, answer,
and phrase with a language model. The first four put the German handling next to a naive
one, so the difference is visible rather than claimed. It starts locally like this:

```bash
uv sync --extra demo
uv run python demo/app.py
```

The fifth step loads a small language model and lets it phrase the answer. On Hugging Face
ZeroGPU the graphics card does that, locally the CPU. The interesting part is less the answer
than what happens afterwards: the toolkit checks the cited source numbers against the
sections it was given. A model that writes `[9]` when there were three sources gets caught
instead of slipping through.

The first four steps need nothing but Gradio. For PDF upload `docling` is added, for the
fifth step `torch` and `transformers`. Everything runs on your own machine; nothing is
stored and nothing is sent out.

The same demo runs without installation at
<https://huggingface.co/spaces/mehrabix/deutsches-ki-toolkit>.

---

## Frequently asked questions

**Why not just use LangChain or LlamaIndex?**
You can. Both are good frameworks. They know just as little about German compounds as they do
about German tax numbers. This toolkit can be run alongside them and fills exactly those
gaps. Haystack and LlamaIndex can be connected if needed, but are not a prerequisite.

**Do I have to use a language model?**
No. Search, PII detection, chunking and anonymization work without one. You only need a model
for phrasing answers and for evaluating them.

**Does my data leave the machine?**
Only if you explicitly configure an external provider. By default there is no telemetry, no
upload and no external call.

**Is this a German language model?**
No. The toolkit is language-aware but model-neutral. It works with the model of your choice —
local or hosted.

---

## Contributing

Good starting points are explicitly welcome:

- add a German PII recognizer
- contribute a benchmark case
- improve the chunking
- add a test file
- add domain terminology for an industry
- compare an embedding model
- sharpen the documentation
- connect a provider

Contributions are labeled with `good first issue`, `help wanted`, `German NLP`, `RAG`,
`privacy`, `benchmark` and `documentation`, so you can quickly find where to start. New cases
always come with a test. If you report a problem, the most helpful thing is a document that
triggers it — anonymized or synthetic.

---

## License

Apache-2.0. The license is deliberately permissive, including an explicit patent grant, so
that companies can use the toolkit without hesitation.

---

## Sources and further reading

- Presidio, open issues on German support – [#1343](https://github.com/data-privacy-stack/presidio/issues/1343)
- Docling, formatting of German PDFs – [issue #1042](https://github.com/docling-project/docling/issues/1042)
- libpostal, German addresses – [issue #510](https://github.com/openvenues/libpostal/issues/510)
- spaCy, German lemmatization and tokenization – [issue #2486](https://github.com/explosion/spaCy/issues/2486)
- PostgreSQL and German umlauts in full-text search – [dbi services](https://www.dbi-services.com/blog/dealing-with-german-umlaute-in-postgresqls-full-text-search/)
- Compounds and search relevance – [Bitext](https://www.bitext.com/blog/some-of-your-rag-related-issues-have-an-easy-quick-solution-decompounding/)
- German NER compared: Presidio, spaCy, GLiNER – [Nils Durner](https://ndurner.github.io/ner)
- BGE-M3 – [model card](https://huggingface.co/BAAI/bge-m3)
- German-NLP: a collection of German-language resources – [adbar/German-NLP](https://github.com/adbar/German-NLP)

---

**deutsches-ki-toolkit** – built for real German data. Documents, data protection, search,
answers with sources. Measured honestly.
