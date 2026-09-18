"""Schnittstelle für Sprachmodelle.

Der Kern des Toolkits kennt keinen bevorzugten Anbieter. Ein Wechsel ist eine
Konfigurationsfrage, keine Codeänderung.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

__all__ = ["ChatMessage", "ChatProvider"]


class ChatMessage(BaseModel):
    """Eine Nachricht im Gespräch."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str


@runtime_checkable
class ChatProvider(Protocol):
    """Ein Sprachmodell erzeugt aus Nachrichten eine Antwort."""

    name: str

    def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        """Gibt den Text der Antwort zurück."""
        ...
