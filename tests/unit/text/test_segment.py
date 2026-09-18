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


def test_plain_number_at_sentence_end_stays_merged() -> None:
    """Bekannte Grenze der Regel für Ordnungszahlen.

    „Die Antwort ist 42.“ endet einen Satz, wird aber wie die Ordnungszahl in
    „das 42. Element“ behandelt und bleibt am Folgesatz hängen. Das ist die
    bewusste Richtung: Ein zusammengezogener Satz ist der billigere Fehler als
    ein mitten im Satz zerrissener. In deutschen Dokumenten überwiegen
    Ordnungszahlen und Aufzählungen bei Weitem.
    """
    assert len(_texts("Die Antwort ist 42. Danach gehen wir.")) == 1
