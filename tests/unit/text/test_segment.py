"""Tests für die Satz- und Wortsegmentierung."""

from __future__ import annotations

from deutsches_ki.text.segment import split_sentences, tokenize_words


def _texts(text: str) -> list[str]:
    return [sentence.text for sentence in split_sentences(text)]


def test_two_plain_sentences() -> None:
    assert _texts("Die Frist beträgt 30 Tage. Danach endet der Vertrag.") == [
        "Die Frist beträgt 30 Tage.",
        "Danach endet der Vertrag.",
    ]


def test_multi_word_abbreviation_is_not_split() -> None:
    assert _texts("Wir treffen uns z. B. am Montag. Danach fahren wir.") == [
        "Wir treffen uns z. B. am Montag.",
        "Danach fahren wir.",
    ]


def test_title_abbreviation_is_not_split() -> None:
    assert _texts("Dr. Müller kommt heute. Danach geht er.") == [
        "Dr. Müller kommt heute.",
        "Danach geht er.",
    ]


def test_legal_abbreviations_are_not_split() -> None:
    text = "§ 4 Abs. 2 regelt die Zahlung. Danach folgt § 5."
    assert len(_texts(text)) == 2


def test_business_abbreviations_are_not_split() -> None:
    text = "Gem. Abs. 2 Nr. 4 gilt die Regelung sinngemäß. Danach folgt § 5."
    assert _texts(text) == [
        "Gem. Abs. 2 Nr. 4 gilt die Regelung sinngemäß.",
        "Danach folgt § 5.",
    ]


def test_multi_part_business_abbreviations_are_not_split() -> None:
    text = "Die Frist i. H. v. 30 Tagen gilt i. d. R. nicht. Sie gilt i. V. m. § 4."
    assert len(_texts(text)) == 2


def test_decimal_number_is_not_split() -> None:
    assert _texts("Der Preis beträgt 3.500 Euro. Danach steigt er.") == [
        "Der Preis beträgt 3.500 Euro.",
        "Danach steigt er.",
    ]


def test_ordinal_month_is_not_split() -> None:
    text = "Am 1. Januar beginnt das Jahr. Es endet im Dezember."
    assert len(_texts(text)) == 2


def test_question_and_exclamation() -> None:
    assert _texts("Ist das korrekt? Ja! Dann weiter.") == [
        "Ist das korrekt?",
        "Ja!",
        "Dann weiter.",
    ]


def test_paragraph_break_is_a_boundary() -> None:
    assert _texts("Erster Absatz\n\nZweiter Absatz") == [
        "Erster Absatz",
        "Zweiter Absatz",
    ]


def test_spans_map_back_to_source() -> None:
    text = "Die Frist beträgt 30 Tage. Danach endet der Vertrag."
    for sentence in split_sentences(text):
        assert text[sentence.start : sentence.end] == sentence.text


def test_empty_text_returns_nothing() -> None:
    assert split_sentences("   ") == []


def test_tokenize_words_with_hyphen() -> None:
    tokens = [token.text for token in tokenize_words("Haupt- und Nebensatz")]
    assert tokens == ["Haupt", "und", "Nebensatz"]


def test_tokenize_words_keeps_umlauts() -> None:
    tokens = [token.text for token in tokenize_words("Die Straße ist schön.")]
    assert tokens == ["Die", "Straße", "ist", "schön"]


# --- Ordnungszahlen vor großgeschriebenem Substantiv ---
#
# Vorher endete der Satz nach „1.“, weil nur Monatsnamen, Ziffern und
# kleingeschriebene Wörter geprüft wurden. „Im 1. Quartal“ wurde damit zu
# „Im 1.“ und „Quartal 2025 stieg der Umsatz.“


def test_ordinal_before_noun_is_not_split() -> None:
    text = "Im 1. Quartal 2025 stieg der Umsatz. Danach fiel er."
    assert _texts(text) == ["Im 1. Quartal 2025 stieg der Umsatz.", "Danach fiel er."]


def test_ordinal_edition_is_not_split() -> None:
    text = "Die 2. Auflage erschien 2024. Sie war schnell vergriffen."
    assert len(_texts(text)) == 2


def test_ordinal_in_address_is_not_split() -> None:
    text = "Das Büro liegt im 3. Stock. Es ist hell."
    assert _texts(text) == ["Das Büro liegt im 3. Stock.", "Es ist hell."]


def test_ordinal_chapter_is_not_split() -> None:
    text = "Lesen Sie das 1. Kapitel. Es ist kurz."
    assert _texts(text) == ["Lesen Sie das 1. Kapitel.", "Es ist kurz."]


def test_numbered_list_is_split_at_items() -> None:
    text = "1. Der erste Punkt. 2. Der zweite Punkt. 3. Der dritte Punkt."
    assert len(_texts(text)) == 3


def test_year_at_sentence_end_is_split() -> None:
    text = "Das war 1990. Danach kam die Neuzeit."
    assert _texts(text) == ["Das war 1990.", "Danach kam die Neuzeit."]


# --- Abkürzungen am Satzende (Duden D 4) ---


def test_usw_at_sentence_end_is_split() -> None:
    text = "Wir kaufen Äpfel, Birnen usw. Danach gehen wir nach Hause."
    assert _texts(text) == ["Wir kaufen Äpfel, Birnen usw.", "Danach gehen wir nach Hause."]


def test_etc_at_sentence_end_is_split() -> None:
    text = "Das gilt für Äpfel, Birnen etc. Danach gehen wir nach Hause."
    assert len(_texts(text)) == 2


def test_ua_at_sentence_end_is_split() -> None:
    text = "Es waren Herr Meier, Frau Schulz u. a. Sie kamen zu spät."
    assert len(_texts(text)) == 2


def test_ua_before_content_word_continues_the_list() -> None:
    """Nach „u. a.“ entscheidet der Satzanfang.

    Steht dort ein Inhaltswort, geht die Aufzählung weiter. Der Punkt trennt
    dann keinen Satz.
    """
    text = "Es waren u. a. Personen anwesend, die niemand kannte."
    assert len(_texts(text)) == 1


def test_year_with_era_abbreviation_is_split() -> None:
    """„v. Chr.“ endet einen Satz, wenn ein Funktionswort folgt."""
    text = "Er starb 44 v. Chr. in Rom."
    assert len(_texts(text)) == 1
    text = "Das war 500 v. Chr. Danach kam die Neuzeit."
    assert len(_texts(text)) == 2


# --- Fundstellen ---


def test_reference_number_before_sentence_start_is_split() -> None:
    text = "Siehe Rn. 45. Die Norm ist einschlägig."
    assert _texts(text) == ["Siehe Rn. 45.", "Die Norm ist einschlägig."]


def test_reference_number_before_content_word_is_not_split() -> None:
    """„Art. 3. Absatz 2“ ist eine Angabe, kein Satzende."""
    text = "Art. 3. Absatz 2 regelt die Zahlung."
    assert len(_texts(text)) == 1


# --- Datumsangaben ---


def test_date_at_sentence_end_is_split() -> None:
    text = "Zahlbar bis 30.09.2024. Danach fallen Zinsen an."
    assert _texts(text) == ["Zahlbar bis 30.09.2024.", "Danach fallen Zinsen an."]


def test_date_inside_sentence_is_not_split() -> None:
    text = "Die Zahlung ist am 30.09.2024 fällig."
    assert len(_texts(text)) == 1


def test_date_with_spaces_is_not_split() -> None:
    text = "Der Termin ist am 30. 09. 2024 in Berlin."
    assert len(_texts(text)) == 1


# --- Weitere Abkürzungen ---


def test_editor_and_edition_are_not_split() -> None:
    text = "Vgl. Hrsg. Schmidt, 3. Aufl. Die Quelle ist gut."
    assert len(_texts(text)) == 2


def test_other_missing_abbreviations_are_not_split() -> None:
    for text in (
        "Das Kap. 3 Ziff. 2 ist maßgeblich. Es gilt ab sofort.",
        "Abb. 2 zeigt den Aufbau. Er ist einfach.",
        "Davon zu unterscheiden ist ebd. Die Fundstelle bleibt offen.",
    ):
        assert len(_texts(text)) == 2, text


# --- Anschriften und eingeklebte Abkürzungen ---
#
# Vorher zerfiel „Werkstattstr. 5, 10115 Berlin.“ in zwei Sätze. Die Abkürzung
# „Str.“ steht am Ende eines Kompositums, dort greift keine der bekannten
# Abkürzungen, und auf den Punkt folgt die Hausnummer — eine Ziffer, die einen
# Satz beginnen darf. Dieselbe Ursache trifft Rechnungs- und Bestellnummern:
# „Rechnungsnr. 5“. Ohne Nummer bleibt der Punkt ein Satzende.


def test_street_abbreviation_with_house_number_is_not_split() -> None:
    text = "Der Auftraggeber beauftragt die Beispiel GmbH, Werkstattstr. 5, 10115 Berlin."
    assert _texts(text) == [text]


def test_street_abbreviations_in_addresses_are_not_split() -> None:
    for text in (
        "Wohnhaft Musterstr. 12, 10115 Berlin.",
        "Die Firma sitzt in der Hauptstr. 42, 80331 München.",
        "Bahnhofstr. 5",
        "Am Marktpl. 3",
        "Lindenstr. 414-424",
    ):
        assert len(_texts(text)) == 1, text


def test_glued_abbreviation_with_number_is_not_split() -> None:
    for text in (
        "Rechnungsnr. 5 ist offen.",
        "Auftragsnr. 2024-001 liegt vor.",
        "Bestellnr. 8 fehlt.",
        "Kundennr. 4711",
        "Vertragsnr. 3 ist gültig.",
        "Sammelbd. 3",
    ):
        assert len(_texts(text)) == 1, text


def test_ordinary_word_ending_in_abbreviation_still_splits() -> None:
    """Die Regel darf keine echten Satzenden verschlucken.

    „Amerika.“ endet auf „ca.“, „Stoff.“ auf „ff.“, „Start.“ auf „art.“ — das
    sind keine Komposita mit eingeklebter Abkürzung.
    """
    for text in (
        "In Amerika. 5 Jahre später.",
        "Der Stoff. 5 Meter reichen.",
        "Der Start. 5 Minuten später.",
        "Er trägt einen Bart. Danach ging er.",
    ):
        assert len(_texts(text)) == 2, text


def test_glued_abbreviation_at_sentence_end_is_split() -> None:
    """Ohne Nummer bleibt „Hauptstr.“ ein mögliches Satzende."""
    text = "Er wohnt in der Hauptstr. Danach zog er um."
    assert _texts(text) == ["Er wohnt in der Hauptstr.", "Danach zog er um."]


def test_street_abbreviation_before_city_is_not_split() -> None:
    text = "Lieferung an die Lindenstr. 414-424, 50667 Köln. Danach nichts mehr."
    assert len(_texts(text)) == 2


def test_plain_number_at_sentence_end_stays_merged() -> None:
    """Bekannte Grenze der Regel für Ordnungszahlen.

    „Die Antwort ist 42.“ endet einen Satz, wird aber wie die Ordnungszahl in
    „das 42. Element“ behandelt und bleibt am Folgesatz hängen. Das ist die
    bewusste Richtung: Ein zusammengezogener Satz ist der billigere Fehler als
    ein mitten im Satz zerrissener. In deutschen Dokumenten überwiegen
    Ordnungszahlen und Aufzählungen bei Weitem.
    """
    assert len(_texts("Die Antwort ist 42. Danach gehen wir.")) == 1


# --- Weitere Fälle aus der Durchsicht ---
#
# Diese Beispiele stammen aus einer Prüfung der Segmentierung. Sie decken
# Schreibweisen ab, die in deutschen Geschäfts- und Behördentexten häufig
# vorkommen und in keiner der Gruppen oben stehen.


def test_clock_time_with_dot_is_not_split() -> None:
    text = "Dr. Müller sagte: „Wir treffen uns um 10.30 Uhr.“"
    assert _texts(text) == [text]


def test_money_amount_ends_sentence_before_new_one() -> None:
    text = "Die Kosten betragen 1.250,50 EUR. Die Zahlung erfolgt am 1. Oktober."
    assert _texts(text) == [
        "Die Kosten betragen 1.250,50 EUR.",
        "Die Zahlung erfolgt am 1. Oktober.",
    ]


def test_reference_chain_with_lit_is_not_split() -> None:
    text = "Gem. § 4 Abs. 2 Nr. 3 lit. a) gilt die Regelung."
    assert _texts(text) == [text]


def test_multiline_address_block_stays_together() -> None:
    text = "Muster GmbH\nz. Hd. Frau Müller\nHauptstr. 15\n10115 Berlin"
    assert _texts(text) == [text]


def test_comma_keeps_abbreviation_inside_the_sentence() -> None:
    """Der Punkt vor einer Abkürzung entscheidet nicht allein.

    Auf „Berlin.“ folgt mit „z. B.“ keine neue Aussage, sondern eine
    Aufzählung: erst der Satzanfang danach entscheidet.
    """
    assert _texts("Die Firma sitzt in Berlin, z. B. am Alexanderplatz.") == [
        "Die Firma sitzt in Berlin, z. B. am Alexanderplatz."
    ]
    assert len(_texts("Die Firma sitzt in Berlin. Danach beginnt die Pause.")) == 2


def test_paragraphs_of_a_paragraph_section_stay_addressable() -> None:
    text = (
        "§ 1 Allgemeine Bestimmungen\n\n(1) Dies ist der erste Absatz.\n\n"
        "(2) Dies ist der zweite Absatz.\n\n§ 2 Haftung\n\n(1) Der zweite Paragraph."
    )
    assert _texts(text) == [
        "§ 1 Allgemeine Bestimmungen",
        "(1) Dies ist der erste Absatz.",
        "(2) Dies ist der zweite Absatz.",
        "§ 2 Haftung",
        "(1) Der zweite Paragraph.",
    ]


# --- Monats- und Wochentagskürzel ---
#
# „Jan.“ und „Mo.“ standen nicht in der Liste der Abkürzungen. Auf den Punkt
# folgte eine Zahl, und eine Zahl durfte einen Satz beginnen: „im Jan.“ und
# „2024.“ wurden zwei Sätze.


def test_month_abbreviation_before_year_is_not_split() -> None:
    for text in (
        "Der Termin ist im Jan. 2024.",
        "Der Termin ist im Feb. und im Mär. 2025.",
        "Der Kurs beginnt im Okt. 2025.",
    ):
        assert len(_texts(text)) == 1, text


def test_weekday_abbreviation_before_date_is_not_split() -> None:
    assert _texts("Am Mo. 5. Mai beginnt die Frist.") == ["Am Mo. 5. Mai beginnt die Frist."]


def test_word_so_still_ends_a_sentence() -> None:
    """„so.“ als Wort bleibt ein Satzende.

    „So.“ ist auch das Wochentagskürzel für Sonntag. Die Regel greift deshalb
    nur, wenn eine Zahl folgt: „am So. 5. Mai“, nicht „Das ist so. Danach“.
    """
    assert _texts("Das ist so. Danach gehen wir.") == ["Das ist so.", "Danach gehen wir."]


# --- Anführungszeichen ---
#
# Zwischen Punkt und Leerzeichen stand noch das schließende Anführungszeichen.
# Die Grenze verlangte ein Leerzeichen direkt nach dem Punkt und fand sie
# deshalb nicht: „Er sagte „Hallo.“ Danach“ blieb ein Satz.


def test_sentence_end_inside_quotes_is_split() -> None:
    assert _texts("Er sagte „Hallo.“ Danach ging er.") == [
        "Er sagte „Hallo.“",
        "Danach ging er.",
    ]


def test_question_inside_quotes_is_split() -> None:
    assert len(_texts("Sie fragte: „Kommst du?“ Ich antwortete nicht.")) == 2


# --- Gliederungen mit römischen Zahlen und Buchstaben ---
#
# „I.“ und „a.“ galten als eigener Satz, und ein Aufzählungspunkt mit kleinem
# Buchstaben wurde gar nicht als Satzanfang erkannt.


def test_roman_numeral_enumeration_stays_with_its_item() -> None:
    assert _texts("I. Der erste Punkt. II. Der zweite Punkt.") == [
        "I. Der erste Punkt.",
        "II. Der zweite Punkt.",
    ]


def test_letter_enumeration_stays_with_its_item() -> None:
    assert _texts("a. Der erste Punkt. b. Der zweite Punkt.") == [
        "a. Der erste Punkt.",
        "b. Der zweite Punkt.",
    ]


def test_common_titles_and_company_forms_are_not_split() -> None:
    for text in (
        "Die Beispiel GmbH & Co. KG wurde gegründet.",
        "Frau Dr. med. Anna Müller kam.",
        "Prof. Dr. Dr. h. c. Max Mustermann sprach.",
    ):
        assert len(_texts(text)) == 1, text


# --- Gesetzbücher am Satzende ---
#
# „BGB.“ stand zwar in der Liste, durfte aber kein Satzende sein. „… aus § 823
# Abs. 1 BGB. Danach verjährt er.“ blieb deshalb ein Satz.


def test_law_code_at_sentence_end_is_split() -> None:
    assert _texts("Der Anspruch folgt aus § 823 Abs. 1 BGB. Danach verjährt er.") == [
        "Der Anspruch folgt aus § 823 Abs. 1 BGB.",
        "Danach verjährt er.",
    ]


def test_law_code_inside_a_sentence_is_not_split() -> None:
    for text in (
        "Das BGB regelt die Ansprüche.",
        "Der Anspruch aus § 823 BGB verjährt in drei Jahren.",
    ):
        assert len(_texts(text)) == 1, text


# --- Adressen im Web ---


def test_url_and_email_are_not_split() -> None:
    for text in (
        "Die Adresse ist https://beispiel.de.",
        "Kontakt: max.mustermann@example.de.",
        "Die Domain beispiel.de kostet 5 EUR.",
        "Die Adresse a.b@example.de ist gültig.",
    ):
        assert len(_texts(text)) == 1, text


def test_url_at_sentence_end_is_split() -> None:
    assert _texts("Siehe https://example.de/pfad. Danach folgt mehr.") == [
        "Siehe https://example.de/pfad.",
        "Danach folgt mehr.",
    ]
