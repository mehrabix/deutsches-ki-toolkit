"""Kleine HTTP-Hilfe für die Anbieter.

Bewusst über ``urllib`` aus der Standardbibliothek, damit die Grundinstallation
keine zusätzliche Abhängigkeit bekommt.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from deutsches_ki.errors import ProviderError

__all__ = ["post_json"]


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Schickt JSON per POST und gibt die JSON-Antwort zurück."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ProviderError(f"{exc.code} {exc.reason}: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Nicht erreichbar: {exc.reason}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError("Antwort war kein gültiges JSON.") from exc
    if not isinstance(parsed, dict):
        raise ProviderError("Antwort war kein JSON-Objekt.")
    return parsed
