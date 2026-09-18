"""Tests für die Erweiterung von Suchanfragen."""

from __future__ import annotations

from deutsches_ki.text.query import default_glossary, expand_query


def test_query_keeps_original_terms() -> None:
    terms = expand_query("Zahlungsfrist")
    assert "Zahlungsfrist" in terms


def test_query_adds_compound_parts() -> None:
    terms = {term.lower() for term in expand_query("Versicherungsbeitrag")}
    assert "versicherung" in terms
    assert "beitrag" in terms


def test_query_uses_builtin_glossary() -> None:
    terms = {term.lower() for term in expand_query("Urlaubsantrag genehmigen")}
    assert "urlaubsfreigabe" in terms
    assert "urlaubsgenehmigung" in terms
    assert "abwesenheitsantrag" in terms


def test_query_accepts_custom_glossary() -> None:
    terms = expand_query("Arbeitsauftrag", glossary={"arbeitsauftrag": ["Werkvertrag"]})
    assert "Werkvertrag" in terms


def test_query_is_deduplicated() -> None:
    terms = expand_query("Urlaub Urlaubsantrag")
    lowered = [term.lower() for term in terms]
    assert len(lowered) == len(set(lowered))


def test_query_respects_max_terms() -> None:
    assert len(expand_query("Urlaubsantrag genehmigen", max_terms=3)) == 3


def test_default_glossary_has_lowercase_keys() -> None:
    glossary = default_glossary()
    assert glossary
    assert all(key == key.lower() for key in glossary)
