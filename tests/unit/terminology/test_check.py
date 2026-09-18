"""Tests für die Terminologie-Prüfung."""

from __future__ import annotations

from pathlib import Path

import pytest

from deutsches_ki.errors import ParseError
from deutsches_ki.terminology import Glossary, Term, check_terminology

GLOSSARY = Glossary(
    name="test",
    terms=[
        Term(preferred="Erholungsurlaub", aliases=["Urlaub"], domain="hr"),
        Term(preferred="Beschäftigte", aliases=["Mitarbeiter", "Arbeitnehmer"]),
        Term(preferred="Auftraggeber", aliases=["Kunde", "Kundin", "Client"]),
    ],
)


def test_finds_preferred_form() -> None:
    report = check_terminology("Der Erholungsurlaub beträgt 30 Tage.", GLOSSARY)
    assert len(report.occurrences) == 1
    assert report.occurrences[0].is_preferred is True
    assert report.occurrences[0].domain == "hr"
    assert report.is_consistent is True


def test_reports_deviation_and_inconsistency() -> None:
    text = "Der Mitarbeiter stellt einen Urlaub. Der Beschäftigte bekommt Erholungsurlaub."
    report = check_terminology(text, GLOSSARY)

    assert report.is_consistent is False
    preferred = {item.preferred for item in report.inconsistencies}
    assert "Erholungsurlaub" in preferred
    assert "Beschäftigte" in preferred

    urlaub = next(item for item in report.inconsistencies if item.preferred == "Erholungsurlaub")
    assert urlaub.surfaces == ["erholungsurlaub", "urlaub"]
    assert len(report.deviations()) == 2


def test_longest_form_wins() -> None:
    """„Erholungsurlaub“ darf nicht als „Urlaub“ gezählt werden."""
    report = check_terminology("Erholungsurlaub", GLOSSARY)
    assert len(report.occurrences) == 1
    assert report.occurrences[0].surface == "Erholungsurlaub"


def test_matching_ignores_case() -> None:
    report = check_terminology("erholungsurlaub", GLOSSARY)
    assert len(report.occurrences) == 1
    assert report.occurrences[0].is_preferred is True


def test_word_boundaries_are_respected() -> None:
    """Ein Begriff darf nicht mitten in einem längeren Wort anschlagen."""
    report = check_terminology("Urlaubsplanung und Kundencenter", GLOSSARY)
    assert report.occurrences == []


def test_counts_by_preferred() -> None:
    report = check_terminology("Der Kunde und der Kunde und die Kundin.", GLOSSARY)
    assert report.count_by_preferred() == {"Auftraggeber": 3}


def test_empty_text() -> None:
    report = check_terminology("", GLOSSARY)
    assert report.occurrences == []
    assert report.is_consistent is True


def test_glossary_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "glossar.yaml"
    GLOSSARY.to_file(target)

    loaded = Glossary.from_file(target)
    assert {term.preferred for term in loaded.terms} == {
        "Erholungsurlaub",
        "Beschäftigte",
        "Auftraggeber",
    }


def test_glossary_missing_file_raises() -> None:
    with pytest.raises(ParseError):
        Glossary.from_file("gibt-es-nicht.yaml")


def test_empty_glossary_matches_nothing() -> None:
    report = check_terminology("Ein beliebiger Text mit Kunde.", Glossary(name="leer"))
    assert report.occurrences == []


def test_merge_keeps_both_sides() -> None:
    other = Glossary(name="extra", terms=[Term(preferred="Werkvertrag")])
    merged = GLOSSARY.merge(other)
    assert len(merged.terms) == 4
    assert merged.name == "test+extra"
