"""Tests für deutsche Stoppwörter."""

from __future__ import annotations

from deutsches_ki.text.stopwords import STOPWORDS, content_terms, is_stopword


def test_common_words_are_stopwords() -> None:
    assert is_stopword("die")
    assert is_stopword("der")
    assert is_stopword("und")
    assert is_stopword("ist")
    assert is_stopword("Die")


def test_content_words_are_not_stopwords() -> None:
    assert not is_stopword("Zahlungsfrist")
    assert not is_stopword("Rechnung")
    assert not is_stopword("Vertrag")


def test_content_terms_drops_stopwords() -> None:
    terms = content_terms("Die Zahlung ist innerhalb von 30 Tagen fällig.")
    assert "zahlung" in terms
    assert "tage" in terms or "tagen" in terms
    assert "die" not in terms
    assert "ist" not in terms


def test_content_terms_expands_compounds() -> None:
    terms = content_terms("Versicherungsbeitrag")
    assert "versicherungsbeitrag" in terms
    assert "versicherung" in terms
    assert "beitrag" in terms


def test_content_terms_on_empty_text() -> None:
    assert content_terms("") == []


def test_stopword_set_is_lowercase() -> None:
    assert all(word == word.casefold() for word in STOPWORDS)


def test_umlaut_and_sharp_s_stopwords_match_folded_tokens() -> None:
    """Gefunden: „gemäß“ wurde nie erkannt.

    Die Such-Token sind gefaltet, „gemäß“ wird dort zu „gemaess“. Die Wortliste
    stand aber in normaler Schreibweise, deshalb lief der Vergleich ins Leere.
    """
    assert is_stopword("gemäß")
    assert is_stopword("über")
    assert "gemaess" not in content_terms("gemäß Vertrag")
    assert "ueber" not in content_terms("über die Zahlung")
