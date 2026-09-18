"""MCP-Server über die Werkzeuge des Toolkits.

Der Server ist eine dünne Hülle: Die Arbeit steckt in ``tools.py``. Dadurch
läuft das Toolkit auch ohne installierte MCP-Erweiterung.
"""

from __future__ import annotations

from typing import Any

from deutsches_ki.errors import MissingDependencyError
from deutsches_ki.mcp.tools import list_tools

__all__ = ["build_server", "main"]


def build_server() -> Any:
    """Baut den MCP-Server mit allen Werkzeugen."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
        raise MissingDependencyError(
            "Für den MCP-Server wird die Erweiterung 'mcp' benötigt. "
            'Installation: pip install "deutsches-ki-toolkit[mcp]"'
        ) from exc

    server = FastMCP("deutsches-ki")
    for spec in list_tools():
        server.add_tool(spec.handler, name=spec.name, description=spec.description)
    return server


def main() -> None:  # pragma: no cover - startet einen Server
    """Startet den MCP-Server über die Standardeingabe und -ausgabe."""
    build_server().run()
