"""Tests für die deutsche Stilprüfung."""

from __future__ import annotations

from deutsches_ki.style import check_style


def _rules(text: str) -> dict[str, int]:
    return check_style(text).by_rule()


def test_clean_short_german_sentence() -> None:
    report = check_style("Die Zahlung ist nach 30 Tagen fällig.")
    assert report.is_clean is True
    assert report.sentences == 1
    assert report.words == 7


def test_flags_long_sentence() -> None:
    sentence = " ".join(["der", "Auftraggeber"] * 15) + "."
    report = check_style(sentence)
    assert "langer_satz" in report.by_rule()
    assert report.longest_sentence_words > 25


def test_flags_passive_construction() -> None:
    assert "passiv" in _rules("Die Rechnung wird vom Auftraggeber geprüft.")
    assert "passiv" in _rules("Der Vertrag wurde gestern unterschrieben.")
    assert "passiv" in _rules("Die Datei wurde dokumentiert.")


def test_does_not_flag_every_wird() -> None:
    """„wird“ allein ist kein Passiv, und nach „wird“ kann ein Infinitiv stehen."""
    assert "passiv" not in _rules("Der Auftraggeber wird die Rechnung prüfen.")
    assert "passiv" not in _rules("Die Zahlung wird fällig.")


def test_flags_nominal_style() -> None:
    text = (
        "Die Berücksichtigung der Zahlungsbedingungen erfordert die Prüfung der "
        "Rechnungsstellung und die Bestätigung der Lieferung."
    )
    assert "nominalstil" in _rules(text)


def test_flags_anglicism() -> None:
    assert "anglizismus" in _rules("Der Stakeholder meldet ein Ticket nach dem Meeting.")


def test_flags_filler_word() -> None:
    assert "fuellwort" in _rules("Das ist eigentlich sozusagen ein Vertrag.")


def test_flags_repeated_word() -> None:
    assert "wortwiederholung" in _rules("Die die Zahlung ist fällig.")


def test_repetition_across_lines_is_not_flagged() -> None:
    """Eine Überschrift, die den Absatz eröffnet, ist keine Wiederholung."""
    text = "## Ersatzteile\n\nErsatzteile werden bestellt."
    assert "wortwiederholung" not in _rules(text)


def test_flags_very_long_word() -> None:
    assert "langes_wort" in _rules("Arbeitsunfähigkeitsbescheinigungspflichtigkeit")


def test_report_statistics() -> None:
    report = check_style("Ein kurzer Satz. Ein zweiter kurzer Satz.")
    assert report.sentences == 2
    assert report.average_sentence_words == 3.5
    assert report.longest_sentence_words == 4


def test_findings_carry_spans() -> None:
    text = "Der Stakeholder meldet sich."
    for finding in check_style(text).findings:
        assert text[finding.start : finding.end] == finding.text


def test_empty_text() -> None:
    report = check_style("")
    assert report.is_clean is True
    assert report.sentences == 0
    assert report.average_sentence_words == 0.0
