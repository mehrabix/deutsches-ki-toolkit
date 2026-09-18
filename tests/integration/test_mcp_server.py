"""Integrationstest für den MCP-Server.

Läuft nur, wenn die Erweiterung ``mcp`` installiert ist:

    uv sync --extra dev --extra mcp
    uv run pytest tests/integration/test_mcp_server.py -q

Geprüft wird der echte Server, nicht nur die Werkzeugliste: Werkzeuge werden
über die MCP-Schnittstelle aufgerufen.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from deutsches_ki.mcp import list_tools
from deutsches_ki.mcp.server import build_server

pytestmark = [pytest.mark.integration, pytest.mark.optional]

pytest.importorskip("mcp.server.mcpserver", reason="Die Erweiterung 'mcp' fehlt.")

FIXTURES = Path(__file__).resolve().parents[2] / "datasets" / "fixtures"


def _tools() -> dict[str, object]:
    server = build_server()
    listed = asyncio.run(server.list_tools())
    return {tool.name: tool for tool in listed}


def _call(name: str, arguments: dict[str, object]) -> object:
    server = build_server()
    return asyncio.run(server.call_tool(name, arguments))


def test_every_tool_is_registered() -> None:
    assert set(_tools()) == {spec.name for spec in list_tools()}


def test_tools_carry_a_description() -> None:
    for name, tool in _tools().items():
        assert getattr(tool, "description", None), f"{name} hat keine Beschreibung"


def test_call_through_the_mcp_interface() -> None:
    result = _call("analyze_german_text", {"text": "Der Versicherungsbeitrag steigt."})

    assert result.is_error is False  # type: ignore[attr-defined]
    payload = result.structured_content  # type: ignore[attr-defined]
    assert payload["sentence_count"] == 1
    assert any(item["word"] == "Versicherungsbeitrag" for item in payload["compounds"])


def test_pii_tool_through_the_mcp_interface() -> None:
    result = _call("detect_german_pii", {"path": str(FIXTURES / "rechnung.txt")})

    assert result.is_error is False  # type: ignore[attr-defined]
    types = {entity["type"] for entity in result.structured_content["entities"]}  # type: ignore[attr-defined]
    assert "DE_IBAN" in types


def test_search_tool_through_the_mcp_interface() -> None:
    result = _call(
        "search_german_documents",
        {"directory": str(FIXTURES), "question": "Wie lange ist die Zahlungsfrist?"},
    )

    assert result.is_error is False  # type: ignore[attr-defined]
    payload = result.structured_content  # type: ignore[attr-defined]
    assert payload["count"] > 0
    assert payload["results"][0]["section"] == "§ 4 Zahlungsbedingungen"


def test_missing_file_is_reported_not_raised() -> None:
    """Ein fehlendes Dokument darf den Server nicht abbrechen."""
    result = _call("parse_german_document", {"path": "gibt-es-nicht.txt"})

    assert result.is_error is False  # type: ignore[attr-defined]
    assert "error" in result.structured_content  # type: ignore[attr-defined]
