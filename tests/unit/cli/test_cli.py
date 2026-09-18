"""Tests für die Kommandozeile."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from deutsches_ki import __version__
from deutsches_ki.cli.main import app

runner = CliRunner()

CONTRACT = """\
# Vertrag

## Zahlungsbedingungen

Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.

## Kündigung

Die Kündigungsfrist beträgt drei Monate zum Monatsende.
"""

WITH_PII = "Bitte an DE89 3704 0044 0532 0130 00 überweisen."


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_parse_command(tmp_path: Path) -> None:
    file = tmp_path / "vertrag.md"
    file.write_text(CONTRACT, encoding="utf-8")

    result = runner.invoke(app, ["parse", str(file)])
    assert result.exit_code == 0
    assert "Zahlungsbedingungen" in result.stdout
    assert "Kündigung" in result.stdout


def test_pii_command_finds_iban(tmp_path: Path) -> None:
    file = tmp_path / "rechnung.txt"
    file.write_text(WITH_PII, encoding="utf-8")

    result = runner.invoke(app, ["pii", str(file)])
    assert result.exit_code == 0
    assert "DE_IBAN" in result.stdout


def test_pii_command_json(tmp_path: Path) -> None:
    file = tmp_path / "rechnung.txt"
    file.write_text(WITH_PII, encoding="utf-8")

    result = runner.invoke(app, ["pii", str(file), "--json"])
    assert result.exit_code == 0
    assert "DE_IBAN" in result.stdout
    assert "DE89 3704 0044 0532 0130 00" in result.stdout


def test_pii_command_without_hits(tmp_path: Path) -> None:
    file = tmp_path / "harmlos.txt"
    file.write_text("Ein ganz gewöhnlicher Satz.", encoding="utf-8")

    result = runner.invoke(app, ["pii", str(file)])
    assert result.exit_code == 0
    assert "Keine sensiblen Stellen" in result.stdout


def test_anonymize_command(tmp_path: Path) -> None:
    file = tmp_path / "rechnung.txt"
    file.write_text(WITH_PII, encoding="utf-8")

    result = runner.invoke(app, ["anonymize", str(file)])
    assert result.exit_code == 0
    assert "[DE_IBAN]" in result.stdout


def test_anonymize_command_writes_output(tmp_path: Path) -> None:
    file = tmp_path / "rechnung.txt"
    file.write_text(WITH_PII, encoding="utf-8")
    target = tmp_path / "sauber.txt"

    result = runner.invoke(app, ["anonymize", str(file), "-o", str(target)])
    assert result.exit_code == 0
    assert "[DE_IBAN]" in target.read_text(encoding="utf-8")


def test_anonymize_command_rejects_unknown_mode(tmp_path: Path) -> None:
    file = tmp_path / "rechnung.txt"
    file.write_text(WITH_PII, encoding="utf-8")

    result = runner.invoke(app, ["anonymize", str(file), "--mode", "quatsch"])
    assert result.exit_code == 1


def test_chunk_command(tmp_path: Path) -> None:
    file = tmp_path / "vertrag.md"
    file.write_text(CONTRACT, encoding="utf-8")

    result = runner.invoke(app, ["chunk", str(file), "--max-tokens", "32", "--overlap", "0"])
    assert result.exit_code == 0
    assert "Chunks" in result.stdout


def test_embed_command(tmp_path: Path) -> None:
    (tmp_path / "vertrag.md").write_text(CONTRACT, encoding="utf-8")

    result = runner.invoke(app, ["embed", str(tmp_path)])
    assert result.exit_code == 0
    assert "Chunks eingebettet" in result.stdout


def test_embed_command_without_files(tmp_path: Path) -> None:
    result = runner.invoke(app, ["embed", str(tmp_path)])
    assert result.exit_code == 1


def test_search_command(tmp_path: Path) -> None:
    (tmp_path / "vertrag.md").write_text(CONTRACT, encoding="utf-8")

    result = runner.invoke(app, ["search", str(tmp_path), "Wie lange ist die Zahlungsfrist?"])
    assert result.exit_code == 0
    assert "30 Tagen" in result.stdout
    assert "Quellen" in result.stdout


def test_ingest_command_without_dsn(tmp_path: Path) -> None:
    (tmp_path / "vertrag.md").write_text(CONTRACT, encoding="utf-8")

    result = runner.invoke(app, ["ingest", str(tmp_path)])

    assert result.exit_code == 1
    assert "Kein DSN" in result.stdout


def test_ask_command_without_llm(tmp_path: Path) -> None:
    (tmp_path / "vertrag.md").write_text(CONTRACT, encoding="utf-8")

    result = runner.invoke(
        app,
        ["ask", "Wie lange ist die Zahlungsfrist?", "--corpus", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert "Kein Sprachmodell eingetragen" in result.stdout
    assert "30 Tagen" in result.stdout


def test_evaluate_command(tmp_path: Path) -> None:
    corpus = tmp_path / "korpus"
    corpus.mkdir()
    (corpus / "vertrag.md").write_text(CONTRACT, encoding="utf-8")
    dataset = tmp_path / "datensatz.yaml"
    dataset.write_text(
        "name: mini\n"
        "cases:\n"
        "  - question: Wie lange ist die Zahlungsfrist?\n"
        "    expected_sources: ['vertrag.md']\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["evaluate", str(dataset), "--corpus", str(corpus)])

    assert result.exit_code == 0
    assert "Bewertung: mini" in result.stdout
    assert "Recall@1" in result.stdout


def test_evaluate_command_writes_json(tmp_path: Path) -> None:
    corpus = tmp_path / "korpus"
    corpus.mkdir()
    (corpus / "vertrag.md").write_text(CONTRACT, encoding="utf-8")
    dataset = tmp_path / "datensatz.yaml"
    dataset.write_text(
        "name: mini\ncases:\n  - question: Wie lange?\n    expected_sources: ['vertrag.md']\n",
        encoding="utf-8",
    )
    target = tmp_path / "bericht.json"

    result = runner.invoke(
        app,
        ["evaluate", str(dataset), "--corpus", str(corpus), "-o", str(target)],
    )

    assert result.exit_code == 0
    assert target.exists()
    assert '"mrr"' in target.read_text(encoding="utf-8")


def test_parse_command_missing_file() -> None:
    result = runner.invoke(app, ["parse", "gibt-es-nicht.txt"])
    assert result.exit_code != 0
