"""Erzeugung stabiler Bezeichner."""

from __future__ import annotations

from uuid import uuid4

__all__ = ["new_id"]


def new_id(prefix: str = "") -> str:
    """Erzeugt einen kurzen, eindeutigen Bezeichner mit optionalem Präfix."""
    value = uuid4().hex[:16]
    return f"{prefix}-{value}" if prefix else value
