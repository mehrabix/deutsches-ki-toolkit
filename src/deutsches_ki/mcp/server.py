"""MCP-Server über die Werkzeuge des Toolkits.

Der Server ist eine dünne Hülle: Die Arbeit steckt in ``tools.py``. Dadurch
läuft das Toolkit auch ohne installierte MCP-Erweiterung, und die Werkzeuge
lassen sich einzeln prüfen.

Angesprochen wird ``MCPServer`` aus ``mcp.server.mcpserver``. In mcp 1.x hieß die
Klasse ``FastMCP``; seit 2.x trägt sie diesen Namen, und die Erweiterung ist
entsprechend auf ``mcp>=2`` gesetzt.
"""

from __future__ import annotations

from typing import Any

from deutsches_ki.errors import MissingDependencyError
from deutsches_ki.mcp.tools import guard, list_tools

__all__ = ["build_server", "main"]


def build_server() -> Any:
    """Baut den MCP-Server mit allen Werkzeugen."""
    try:
        from mcp.server.mcpserver import MCPServer
    except ImportError as exc:  # pragma: no cover - nur ohne Extra erreichbar
        raise MissingDependencyError(
            "Für den MCP-Server wird die Erweiterung 'mcp' in Version 2 oder neuer "
            'benötigt. Installation: pip install "deutsches-ki-toolkit[mcp]"'
        ) from exc

    server = MCPServer("deutsches-ki")
    for spec in list_tools():
        server.add_tool(guard(spec.handler), name=spec.name, description=spec.description)
    return server


def main() -> None:  # pragma: no cover - startet einen Server
    """Startet den MCP-Server über die Standardeingabe und -ausgabe."""
    build_server().run()
