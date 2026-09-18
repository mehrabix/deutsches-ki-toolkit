"""Anbindung an Ollama.

Ollama läuft lokal und ist der unkomplizierteste Weg zu einem eigenen
Sprachmodell. Nichts verlässt dabei den Rechner.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from deutsches_ki.errors import ProviderError
from deutsches_ki.providers.base import ChatMessage
from deutsches_ki.providers.http import post_json

__all__ = ["OllamaProvider"]

DEFAULT_HOST = "http://localhost:11434"


class OllamaProvider:
    """Fragt ein Modell über die Ollama-HTTP-Schnittstelle."""

    name = "ollama"

    def __init__(
        self,
        model: str = "llama3.1",
        *,
        host: str = DEFAULT_HOST,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        """Schickt die Nachrichten an ``/api/chat`` und gibt den Text zurück."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
            "stream": False,
        }
        payload.update(kwargs)

        data = post_json(f"{self.host}/api/chat", payload, timeout=self.timeout)
        message = data.get("message")
        if not isinstance(message, dict):
            raise ProviderError("Antwort von Ollama enthielt keine Nachricht.")
        content = message.get("content")
        if not isinstance(content, str):
            raise ProviderError("Antwort von Ollama enthielt keinen Text.")
        return content
