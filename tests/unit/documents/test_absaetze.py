"""Tests für die Absatzebene innerhalb eines Abschnitts."""

from __future__ import annotations

from deutsches_ki.chunking import chunk_text, estimate_tokens
from deutsches_ki.core.models import Document
from deutsches_ki.documents.absaetze import split_absaetze

VERTRAG = """§ 1 Vertragsgegenstand
Der Auftraggeber beauftragt die Beispiel GmbH.
(2) Die Vergütung beträgt 1.000,00 EUR.
(3) Gem. Abs. 2 Nr. 4 gilt die Regelung."""

INHALT = (
    "Der Auftraggeber beauftragt die Beispiel GmbH.\n"
    "(2) Die Vergütung beträgt 1.000,00 EUR.\n"
    "(3) Gem. Abs. 2 Nr. 4 gilt die Regelung."
)


def test_split_absaetze_returns_marker_and_text() -> None:
    absaetze = split_absaetze(INHALT)
    assert [(absatz.marker, absatz.text) for absatz in absaetze] == [
        (None, "Der Auftraggeber beauftragt die Beispiel GmbH."),
        ("(2)", "(2) Die Vergütung beträgt 1.000,00 EUR."),
        ("(3)", "(3) Gem. Abs. 2 Nr. 4 gilt die Regelung."),
    ]


def test_blank_lines_between_markers() -> None:
    absaetze = split_absaetze("(1) Erster Absatz.\n\n(2) Zweiter Absatz.")
    assert [(absatz.marker, absatz.text) for absatz in absaetze] == [
        ("(1)", "(1) Erster Absatz."),
        ("(2)", "(2) Zweiter Absatz."),
    ]


def test_section_without_markers_is_one_absatz() -> None:
    absaetze = split_absaetze("Ein Abschnitt ohne Gliederung.")
    assert len(absaetze) == 1
    assert absaetze[0].marker is None
    assert absaetze[0].text == "Ein Abschnitt ohne Gliederung."


def test_text_before_the_first_marker_keeps_its_own_absatz() -> None:
    absaetze = split_absaetze("Einleitung ohne Marke.\n(1) Der erste Absatz.")
    assert [absatz.marker for absatz in absaetze] == [None, "(1)"]


def test_marker_with_letter_is_recognised() -> None:
    absaetze = split_absaetze("(2a) Zwischenform.")
    assert absaetze[0].marker == "(2a)"
    assert absaetze[0].text == "(2a) Zwischenform."


def test_marker_inside_a_line_is_not_a_marker() -> None:
    absaetze = split_absaetze("Der Verweis auf (1) steht mitten im Satz.")
    assert len(absaetze) == 1
    assert absaetze[0].marker is None


def test_empty_text_has_no_absatz() -> None:
    assert split_absaetze("") == []
    assert split_absaetze("   \n  ") == []


def test_document_iter_absaetze_pairs_section_and_absatz() -> None:
    document = Document.from_text(VERTRAG)
    paare = document.iter_absaetze()
    assert [(section.title, absatz.marker) for section, absatz in paare] == [
        ("§ 1 Vertragsgegenstand", None),
        ("§ 1 Vertragsgegenstand", "(2)"),
        ("§ 1 Vertragsgegenstand", "(3)"),
    ]


def test_chunk_metadata_carries_the_absatz_marker() -> None:
    chunks = chunk_text(VERTRAG, max_tokens=512)
    assert [chunk.metadata["absatz"] for chunk in chunks] == [None]
    assert chunks[0].section == "§ 1 Vertragsgegenstand"


def test_chunk_metadata_marker_when_the_absatz_opens_the_chunk() -> None:
    eins = "(1) Erster Absatz mit Text."
    zwei = "(2) Zweiter Absatz mit Text."
    groesse = max(estimate_tokens(eins), estimate_tokens(zwei))
    chunks = chunk_text(f"{eins}\n\n{zwei}", max_tokens=groesse, overlap=0)
    assert [chunk.metadata["absatz"] for chunk in chunks] == ["(1)", "(2)"]
