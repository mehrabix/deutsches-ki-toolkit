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
