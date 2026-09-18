"""Web-Demo für das Deutsche-KI-Toolkit.

Zeigt vier Schritte: Struktur, sensible Daten, Suche, Frage. Jeder Schritt
stellt die deutsche Behandlung einer naiven gegenüber, damit der Unterschied
sichtbar wird statt behauptet.

Die Demo braucht außer Gradio nichts. Docling ist optional: Ohne Docling
lassen sich Text- und Markdown-Dateien hochladen, aber keine PDFs.
"""

from __future__ import annotations

import html

import gradio as gr

from deutsches_ki import GermanDocument
from deutsches_ki.chunking import chunk_text
from deutsches_ki.pii import anonymize, detect
from deutsches_ki.text import search_tokens, split_sentences

BEISPIEL_VERTRAG = """§ 1 Vertragsgegenstand
Der Auftraggeber beauftragt die Beispiel GmbH, Werkstattstr. 5, 10115 Berlin.
(2) Die Vergütung beträgt 1.000,00 EUR zzgl. 19 % USt., zahlbar bis 30.09.2024.
(3) Gem. Abs. 2 Nr. 4 gilt die Regelung sinngemäß, d. h. auch für Dritte.
(4) Lieferungen erfolgen an Werktagen, z. B. montags, bzw. nach Absprache.

§ 4 Zahlungsbedingungen
(1) Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.
(2) Bei verspäteter Zahlung fallen Verzugszinsen in Höhe von neun Prozent über dem Basiszinssatz an.

§ 7 Kündigung
Die Kündigungsfrist beträgt drei Monate zum Monatsende. Kündigungen bedürfen der Schriftform.
"""

BEISPIEL_RECHNUNG = """Rechnung RE-2024-001 vom 30.09.2024

Kunde: Max Mustermann
Werkstattstr. 5, 10115 Berlin
Tel.: 030 1234567
E-Mail: max.mustermann@example.de

IBAN: DE89 3704 0044 0532 0130 00
BIC: COBADEFFXXX
Steuer-ID: 37 282 426 236
USt-IdNr.: DE123456789

Nettobetrag: 1.000,00 EUR
"""

BEISPIEL_FRAGE = "Wie lange ist die Zahlungsfrist?"
BEISPIEL_KUENDIGUNG = "Wie lange ist die Kündigungsfrist?"

MODI = {
    "Schwärzen — [PERSON]": "redact",
    "Ersetzen — PERSON": "replace",
    "Maskieren — Max***nn": "mask",
    "Hashen — HASH_a1b2c3": "hash",
    "Pseudonymisieren — PERSON_001": "pseudonymize",
}

PRUEFSUMMEN = {
    "de_iban": "Mod-97",
    "de_tax_id": "ISO 7064",
    "de_svnr": "ISO 7064",
}

FARBEN = {
    "PERSON": "#ffd6d6",
    "ORGANISATION": "#ffe8c2",
    "LOCATION": "#fff3bf",
    "EMAIL": "#d6e8ff",
    "PHONE": "#d6e8ff",
    "DE_IBAN": "#d9f2d9",
    "DE_BIC": "#d9f2d9",
    "DE_TAX_ID": "#ead6ff",
    "DE_VAT_ID": "#ead6ff",
    "DE_HR_NUMBER": "#ead6ff",
    "DATE": "#eeeeee",
    "MONEY": "#eeeeee",
}


def _naive_tokens(text: str) -> list[str]:
    """Die naive Vergleichsbasis: klein schreiben, an Leerzeichen trennen."""
    return [token for token in text.lower().split() if token]


def _naive_chunks(text: str, size: int = 140) -> list[str]:
    """Die naive Vergleichsbasis: stumpf nach Zeichen schneiden."""
    return [text[index : index + size] for index in range(0, len(text), size)]


def _document(text: str) -> GermanDocument:
    return GermanDocument.from_text(text, title="Demo")


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_Keine Treffer._"
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        cells = [str(cell).replace("|", "\\|").replace("\n", " ") for cell in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Schritt 1: Struktur
# --------------------------------------------------------------------------


def schritt_struktur(text: str) -> tuple[str, str, str]:
    """Vergleicht naives Trennen mit der deutschen Segmentierung."""
    text = text or ""
    naive = [part.strip() for part in text.split(".") if part.strip()]
    document = _document(text)
    saetze = split_sentences(text)
    abschnitte = list(document.document.iter_sections())

    naiv_text = "\n".join(f"- {html.escape(part[:80])}" for part in naive[:14])
    gut_text = "\n".join(f"- {html.escape(satz.text[:80])}" for satz in saetze[:14])

    kopf = f"**{len(naive)} Bruchstücke**\n\n"
    rechts = f"**{len(saetze)} Sätze**\n\n{gut_text}"

    if abschnitte:
        zeilen = [[str(a.level), a.title or "—", "ja" if a.children else "—"] for a in abschnitte]
        gliederung = _markdown_table(["Ebene", "Überschrift", "Unterabschnitte"], zeilen)
    else:
        gliederung = "_Keine Überschriften erkannt._"

    naiv_chunks = _naive_chunks(text)
    gute_chunks = chunk_text(text, strategy="structural")

    naiv_tabelle = _markdown_table(
        ["#", "Textanfang"],
        [[str(i + 1), part[:70]] for i, part in enumerate(naiv_chunks[:3])],
    )
    gut_tabelle = _markdown_table(
        ["#", "Abschnitt", "Textanfang"],
        [
            [str(i + 1), chunk.section or "—", chunk.content[:70]]
            for i, chunk in enumerate(gute_chunks[:3])
        ],
    )

    rest = (
        "**Erkannte Gliederung**\n\n"
        + gliederung
        + f"\n\n**Naiv nach Zeichen geschnitten — {len(naiv_chunks)} Stücke**\n\n"
        + naiv_tabelle
        + f"\n\n**Strukturell an Abschnitten — {len(gute_chunks)} Stücke**\n\n"
        + gut_tabelle
    )
    return kopf + naiv_text, rechts, rest


# --------------------------------------------------------------------------
# Schritt 2: Sensible Daten
# --------------------------------------------------------------------------


def schritt_pii(text: str, modus: str) -> tuple[str, str, str, str]:
    """Zeigt Fundstellen, Prüfsummen, Hervorhebung und den gewählten Modus."""
    text = text or ""
    entities = detect(text)
    ergebnis = anonymize(text, entities, mode=MODI.get(modus, "redact"))

    zeilen = []
    for entity in entities:
        name = str(entity.metadata.get("recognizer", entity.source.value))
        zeilen.append(
            [
                entity.type.value,
                entity.text[:40],
                PRUEFSUMMEN.get(name, "—"),
                name,
                f"{entity.confidence:.2f}",
            ]
        )
    tabelle = f"**{len(entities)} Fundstellen**\n\n" + _markdown_table(
        ["Typ", "Fund", "Prüfsumme", "Erkennung", "Konfidenz"], zeilen
    )

    teile = []
    zuletzt = 0
    for entity in sorted(entities, key=lambda item: item.start):
        if entity.start < zuletzt:
            continue
        teile.append(html.escape(text[zuletzt : entity.start]))
        farbe = FARBEN.get(entity.type.value, "#eeeeee")
        teile.append(
            f'<mark style="background:{farbe};padding:1px 3px;border-radius:3px" '
            f'title="{html.escape(entity.type.value)}">{html.escape(entity.text)}</mark>'
        )
        zuletzt = entity.end
    teile.append(html.escape(text[zuletzt:]))
    hervorgehoben = (
        '<div style="white-space:pre-wrap;font-family:monospace;font-size:13px;'
        'line-height:1.6">' + "".join(teile) + "</div>"
    )

    anonym = (
        '<div style="white-space:pre-wrap;font-family:monospace;font-size:13px;'
        'line-height:1.6">' + html.escape(ergebnis.text) + "</div>"
    )

    zuordnung = _markdown_table(
        ["Original", "Ersetzt durch"],
        [[original, ersetzt] for original, ersetzt in list(ergebnis.mapping.items())[:20]],
    )
    return tabelle, hervorgehoben, anonym, zuordnung


# --------------------------------------------------------------------------
# Schritt 3 und 4: Suche und Frage
# --------------------------------------------------------------------------


def _naive_suche(frage: str, chunks: list[str]) -> list[tuple[float, str]]:
    wanted = set(_naive_tokens(frage))
    treffer = []
    for content in chunks:
        overlap = len(wanted & set(_naive_tokens(content)))
        if overlap:
            treffer.append((overlap / max(len(wanted), 1), content))
    treffer.sort(key=lambda item: -item[0])
    return treffer[:5]


def schritt_suche(text: str, frage: str) -> tuple[str, str, str]:
    """Stellt naive und deutsche Suchbegriffe und Treffer gegenüber."""
    text = text or ""
    frage = frage or ""
    document = _document(text)
    retriever = document.build_retriever()
    chunks = [chunk.content for chunk in document.chunk(strategy="structural")]

    tokens = _markdown_table(
        ["Verfahren", "Begriffe für die Frage"],
        [
            ["naiv", ", ".join(_naive_tokens(frage)) or "—"],
            ["deutsch", ", ".join(dict.fromkeys(search_tokens(frage))) or "—"],
        ],
    )

    naiv = _naive_suche(frage, chunks)
    naiv_text = _markdown_table(
        ["Überdeckung", "Textausschnitt"],
        [[f"{score:.2f}", content[:90]] for score, content in naiv],
    )

    deutsch = retriever.search(frage, top_k=5)
    deutsch_text = _markdown_table(
        ["Punktzahl", "Abschnitt", "Textausschnitt"],
        [
            [f"{result.score:.4f}", str(result.chunk.section or "—"), result.chunk.content[:90]]
            for result in deutsch
        ],
    )
    return tokens, naiv_text, deutsch_text


def schritt_frage(text: str, frage: str) -> tuple[str, str]:
    """Beantwortet eine Frage aus dem Text, ohne Sprachmodell."""
    document = _document(text or "")
    antwort = document.search(frage or "", top_k=5)

    if not antwort.retrieved_chunks:
        return "_Keine Stelle gefunden._", ""

    kopf = (
        f"**Antwort (aus dem Text, ohne Sprachmodell)**\n\n{antwort.answer}\n\n"
        f"**Vertrauen:** {antwort.confidence:.2f} · "
        f"**Verfahren:** {antwort.metadata.get('mode', '—')}"
    )

    zeilen = [
        [
            citation.document,
            str(citation.section or "—"),
            str(citation.page if citation.page is not None else "—"),
            f"{citation.score:.4f}",
        ]
        for citation in antwort.citations
    ]
    belege = _markdown_table(["Dokument", "Abschnitt", "Seite", "Punktzahl"], zeilen)

    fundstellen = _markdown_table(
        ["Abschnitt", "Textausschnitt"],
        [[str(chunk.section or "—"), chunk.content[:100]] for chunk in antwort.retrieved_chunks],
    )
    return kopf, "**Belege**\n\n" + belege + "\n\n**Herangezogene Stellen**\n\n" + fundstellen


def _datei_lesen(datei: str | None) -> tuple[str, str, str, str]:
    """Liest eine hochgeladene Datei und legt sie in alle Felder."""
    if not datei:
        raise gr.Error("Keine Datei ausgewählt.")
    try:
        text = GermanDocument.from_file(datei).text
    except Exception as error:
        raise gr.Error(f"Datei nicht lesbar: {error}. Für PDF wird Docling gebraucht.") from error
    return text, text, text, text


# --------------------------------------------------------------------------
# Oberfläche
# --------------------------------------------------------------------------


with gr.Blocks(title="Deutsches KI-Toolkit") as demo:
    gr.Markdown(
        """
        # Deutsches KI-Toolkit

        Deutsche Texte werden anders zerlegt, anders gesucht und anders auf
        personenbezogene Daten geprüft als englische. Jeder Schritt unten stellt
        die deutsche Behandlung einer naiven gegenüber.

        Alles läuft auf diesem Server, es wird nichts gespeichert.
        """
    )

    with gr.Tab("Struktur"):
        gr.Markdown(
            "Ein Punkt trennt keinen Satz, wenn davor `§ 1`, `1.000,00`, "
            "`30.09.2024`, `z. B.` oder `Gem.` steht."
        )
        struktur_eingabe = gr.Textbox(label="Text", lines=12, value=BEISPIEL_VERTRAG)
        struktur_button = gr.Button("Zerlegen", variant="primary")
        with gr.Row():
            struktur_naiv = gr.Markdown()
            struktur_gut = gr.Markdown()
        struktur_rest = gr.Markdown()
        struktur_button.click(
            schritt_struktur,
            inputs=struktur_eingabe,
            outputs=[struktur_naiv, struktur_gut, struktur_rest],
        )

    with gr.Tab("Sensible Daten"):
        gr.Markdown(
            "Prüfsummen entscheiden mit. `DE89 3704 0044 0532 0130 00` wird "
            "erkannt, `…0130 01` nicht — der Modulo-97-Test schlägt fehl."
        )
        pii_eingabe = gr.Textbox(label="Text", lines=14, value=BEISPIEL_RECHNUNG)
        pii_modus = gr.Radio(label="Verfahren", choices=list(MODI), value=next(iter(MODI)))
        pii_button = gr.Button("Prüfen und ersetzen", variant="primary")
        pii_tabelle = gr.Markdown()
        with gr.Row():
            with gr.Column():
                gr.Markdown("**Fundstellen**")
                pii_hervor = gr.HTML()
            with gr.Column():
                gr.Markdown("**Ersetzt**")
                pii_anonym = gr.HTML()
        pii_zuordnung = gr.Markdown()
        pii_button.click(
            schritt_pii,
            inputs=[pii_eingabe, pii_modus],
            outputs=[pii_tabelle, pii_hervor, pii_anonym, pii_zuordnung],
        )

    with gr.Tab("Suche"):
        gr.Markdown(
            "„Zahlungsfrist“ steht so nicht im Text. Die deutsche Suche zerlegt "
            "das Wort in `zahlung` und `frist` und findet die Stelle trotzdem."
        )
        suche_text = gr.Textbox(label="Text", lines=8, value=BEISPIEL_VERTRAG)
        suche_frage = gr.Textbox(label="Frage", value=BEISPIEL_FRAGE)
        suche_button = gr.Button("Suchen", variant="primary")
        suche_tokens = gr.Markdown()
        with gr.Row():
            suche_naiv = gr.Markdown()
            suche_deutsch = gr.Markdown()
        suche_button.click(
            schritt_suche,
            inputs=[suche_text, suche_frage],
            outputs=[suche_tokens, suche_naiv, suche_deutsch],
        )

    with gr.Tab("Frage"):
        gr.Markdown(
            "Die Antwort stammt aus dem Text, nicht aus einem Sprachmodell. "
            "Deshalb lässt sich jede Angabe belegen."
        )
        frage_text = gr.Textbox(label="Text", lines=8, value=BEISPIEL_VERTRAG)
        frage_frage = gr.Textbox(label="Frage", value=BEISPIEL_KUENDIGUNG)
        frage_button = gr.Button("Beantworten", variant="primary")
        frage_antwort = gr.Markdown()
        frage_belege = gr.Markdown()
        frage_button.click(
            schritt_frage,
            inputs=[frage_text, frage_frage],
            outputs=[frage_antwort, frage_belege],
        )

    with gr.Accordion("Eigene Datei verwenden", open=False):
        gr.Markdown(
            "`.txt` und `.md` funktionieren immer. Für PDF wird Docling gebraucht "
            '(`pip install "deutsches-ki-toolkit[docling]"`). Die Datei wird in '
            "alle vier Schritte übernommen."
        )
        datei = gr.File(label="Datei", type="filepath")
        datei_button = gr.Button("Übernehmen")
        datei_button.click(
            _datei_lesen,
            inputs=datei,
            outputs=[struktur_eingabe, pii_eingabe, suche_text, frage_text],
        )

    demo.load(
        lambda: ("Wählen Sie einen Schritt.", "", ""),
        outputs=[struktur_naiv, struktur_gut, struktur_rest],
    )


if __name__ == "__main__":
    demo.launch()
