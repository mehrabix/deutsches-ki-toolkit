"""Grobe Token-Schätzung ohne Modell.

Für Chunk-Grenzen reicht eine Schätzung. Ein Token entspricht im Deutschen
grob vier Zeichen. Wer es genauer braucht, kann die Grenzen über ``max_tokens``
einfach konservativer setzen.
"""

from __future__ import annotations

import re

__all__ = ["estimate_tokens", "split_tokens"]

_WHITESPACE = re.compile(r"\s+")


def estimate_tokens(text: str) -> int:
    """Schätzt die Tokenzahl eines Textes (rund vier Zeichen je Token)."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def split_tokens(text: str) -> list[str]:
    """Zerlegt Text an Leerzeichen in grobe Token."""
    stripped = text.strip()
    if not stripped:
        return []
    return _WHITESPACE.split(stripped)
