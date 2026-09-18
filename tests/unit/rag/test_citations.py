"""Tests für die Prüfung der Quellenangaben."""

from __future__ import annotations

from deutsches_ki.rag.citations import extract_markers, validate_citations


def test_extract_markers_in_order() -> None:
    assert extract_markers("Siehe [1] und [2], nicht [1].") == [1, 2, 1]


def test_extract_markers_without_any() -> None:
    assert extract_markers("Keine Quelle genannt.") == []


def test_all_citations_valid() -> None:
    report = validate_citations("Die Frist beträgt 30 Tage [1].", 3)
    assert report.valid == [1]
    assert report.unknown == []
    assert report.all_valid is True
    assert report.has_citations is True


def test_unknown_citation_is_reported() -> None:
    report = validate_citations("Laut [4] und [1] gilt das.", 2)
    assert report.valid == [1]
    assert report.unknown == [4]
    assert report.all_valid is False


def test_citation_zero_is_unknown() -> None:
    report = validate_citations("Siehe [0].", 1)
    assert report.unknown == [0]


def test_answer_without_citation_is_flagged() -> None:
    report = validate_citations("Die Frist beträgt 30 Tage.", 2)
    assert report.has_citations is False
    assert report.all_valid is False
    assert report.source_count == 2
