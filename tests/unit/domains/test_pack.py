"""Tests für die Fachpakete."""

from __future__ import annotations

import pytest

from deutsches_ki.classification import DocumentType
from deutsches_ki.domains import available_domains, load_domain
from deutsches_ki.errors import ParseError
from deutsches_ki.terminology import check_terminology


def test_all_packs_are_listed() -> None:
    assert set(available_domains()) == {"legal", "finance", "hr", "technical", "industrial"}


def test_legal_pack_loads() -> None:
    pack = load_domain("legal")
    assert pack.name == "legal"
    assert pack.title == "Recht"
    assert DocumentType.CONTRACT in pack.document_types
    assert any(term.preferred == "Auftraggeber" for term in pack.terminology)


def test_unknown_pack_lists_alternatives() -> None:
    with pytest.raises(ParseError, match="Verfügbar"):
        load_domain("gibt-es-nicht")


def test_pack_is_cached() -> None:
    assert load_domain("finance") is load_domain("finance")


def test_glossary_finds_inconsistency() -> None:
    pack = load_domain("finance")
    report = check_terminology(
        "Die Rechnungsnummer lautet RE-1. Die RG-Nr lautet RE-2.",
        pack.glossary,
    )
    assert report.is_consistent is False
    assert "Rechnungsnummer" in {item.preferred for item in report.inconsistencies}


def test_hr_pack_covers_german_hr_terms() -> None:
    pack = load_domain("hr")
    report = check_terminology(
        "Der Mitarbeiter reicht einen Urlaub ein. Die Beschäftigte beantragt Erholungsurlaub.",
        pack.glossary,
    )
    assert report.is_consistent is False
    assert len(report.deviations()) == 2


def test_pack_merge_combines_document_types() -> None:
    merged = load_domain("legal").merge(load_domain("finance"))
    assert DocumentType.CONTRACT in merged.document_types
    assert DocumentType.INVOICE in merged.document_types
    assert merged.name == "legal+finance"


def test_every_pack_has_terminology() -> None:
    for name in available_domains():
        pack = load_domain(name)
        assert pack.terminology, f"{name} hat keine Begriffe"
        assert pack.document_types, f"{name} hat keine Dokumentarten"
