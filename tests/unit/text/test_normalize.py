"""Tests für die deutsche Textnormalisierung."""

from __future__ import annotations

from deutsches_ki.text.normalize import (
    normalize_dashes,
    normalize_ergaenzung,
    normalize_for_search,
    normalize_german,
    normalize_quotes,
    normalize_ss,
    normalize_umlauts,
    normalize_unicode,
    normalize_whitespace,
)


def test_normalize_unicode_replaces_nbsp() -> None:
    assert normalize_unicode("a\u00a0b") == "a b"
    assert normalize_unicode("soft\u00adhyphen") == "softhyphen"


def test_normalize_unicode_line_endings() -> None:
    assert normalize_unicode("a\r\nb\rc") == "a\nb\nc"


def test_normalize_whitespace() -> None:
    assert normalize_whitespace("a   b\n\n\n\nc") == "a b\n\nc"
    assert normalize_whitespace("  rand  ") == "rand"


def test_normalize_quotes_sets_german_form() -> None:
    assert normalize_quotes('Er sagte "Hallo".') == "Er sagte „Hallo“."
    assert normalize_quotes("»so«") == "„so“"


def test_normalize_dashes() -> None:
    assert normalize_dashes("Wort\u2014Wort") == "Wort\u2013Wort"
    assert normalize_dashes("5\u22123") == "5-3"


def test_normalize_umlauts_and_ss() -> None:
    assert normalize_umlauts("schön müde") == "schoen muede"
    assert normalize_umlauts("Ärger Öl Über") == "Aerger Oel Ueber"
    assert normalize_ss("Straße") == "Strasse"


def test_normalize_ergaenzung_resolves_stem() -> None:
    assert normalize_ergaenzung("Haupt- und Nebensatz") == "Hauptsatz und Nebensatz"


def test_normalize_ergaenzung_unknown_word() -> None:
    assert normalize_ergaenzung("Haupt- und Xyz") == "Haupt und Xyz"


def test_display_keeps_sharp_s_and_umlauts() -> None:
    text = "Die Straße ist schön."
    assert normalize_german(text, mode="display") == "Die Straße ist schön."


def test_search_form_folds_umlauts_and_ss() -> None:
    assert normalize_german("Die Straße ist schön.", mode="search") == ("die strasse ist schoen")


def test_search_form_drops_punctuation() -> None:
    assert normalize_for_search("Zahlung (30 Tage), zzgl. MwSt.!") == ("zahlung 30 tage zzgl mwst")


def test_search_form_handles_ergaenzung() -> None:
    assert normalize_for_search("Haupt- und Nebensatz") == "hauptsatz und nebensatz"


def test_search_form_collapses_whitespace() -> None:
    assert normalize_for_search("  viele    Leerzeichen  ") == "viele leerzeichen"
