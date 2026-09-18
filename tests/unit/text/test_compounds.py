"""Tests für die Komposita-Zerlegung."""

from __future__ import annotations

from deutsches_ki.text.compounds import analyze_compound, decompound_for_search


def _lowered_parts(word: str) -> list[str]:
    return [part.lower() for part in analyze_compound(word).parts]


def test_simple_two_part_compound() -> None:
    assert _lowered_parts("Versicherungsbeitrag") == ["versicherung", "beitrag"]


def test_compound_with_fugen_s() -> None:
    assert _lowered_parts("Krankenversicherung") == ["kranken", "versicherung"]


def test_three_part_compound() -> None:
    assert _lowered_parts("Arbeitsunfähigkeitsbescheinigung") == [
        "arbeit",
        "unfähigkeit",
        "bescheinigung",
    ]


def test_compound_is_flagged() -> None:
    analysis = analyze_compound("Versicherungsbeitrag")
    assert analysis.is_compound is True
    assert analysis.strategy == "dictionary"
    assert analysis.score == 1.0


def test_non_compound_word_stays_whole() -> None:
    analysis = analyze_compound("Vertrag")
    assert analysis.parts == ["Vertrag"]
    assert analysis.is_compound is False
    assert analysis.strategy == "none"


def test_short_word_stays_whole() -> None:
    analysis = analyze_compound("Tag")
    assert analysis.parts == ["Tag"]
    assert analysis.is_compound is False


def test_unknown_word_stays_whole() -> None:
    analysis = analyze_compound("Xyzzyx")
    assert analysis.parts == ["Xyzzyx"]
    assert analysis.is_compound is False


def test_punctuation_is_handled() -> None:
    analysis = analyze_compound("Versicherungsbeitrag,")
    assert analysis.is_compound is False


def test_decompound_for_search() -> None:
    result = decompound_for_search("Versicherungsbeitrag")
    assert result.lower() == "versicherung beitrag"


def test_decompound_for_search_keeps_other_words() -> None:
    result = decompound_for_search("Der Versicherungsbeitrag steigt.")
    words = result.lower().split()
    assert words[0] == "der"
    assert "versicherung" in words
    assert "beitrag" in words


def test_custom_dictionary() -> None:
    analysis = analyze_compound("Haustür", dictionary={"haus", "tür"})
    assert [part.lower() for part in analysis.parts] == ["haus", "tür"]
