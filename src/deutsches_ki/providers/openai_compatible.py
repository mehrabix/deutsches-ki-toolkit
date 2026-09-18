"""Anbindung an OpenAI-kompatible Schnittstellen.

vLLM stellt dieselbe Schnittstelle bereit wie OpenAI. Damit funktioniert
derselbe Anbieter gegen einen lokalen Modellserver oder gegen einen gehosteten
Dienst, ohne dass der Aufrufer das wissen muss.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from deutsches_ki.errors import ProviderError
from deutsches_ki.providers.base import ChatMessage
from deutsches_ki.providers.http import post_json

__all__ = ["OpenAICompatibleProvider"]

DEFAULT_BASE_URL = "http://localhost:8000/v1"


class OpenAICompatibleProvider:
    """Fragt ``/chat/completions`` im OpenAI-Format."""

    name = "openai-compatible"

    def __init__(
        self,
        model: str = "local-model",
        *,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, messages: Sequence[ChatMessage], **kwargs: Any) -> str:
        """Schickt die Nachrichten und gibt den Text der ersten Antwort zurück."""
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
        }
        payload.update(kwargs)

        data = post_json(
            f"{self.base_url}/chat/completions",
            payload,
            headers=headers,
            timeout=self.timeout,
        )
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError("Antwort enthielt keine Auswahl.")
        first = choices[0]
        if not isinstance(first, dict):
            raise ProviderError("Antwort hatte ein unerwartetes Format.")
        message = first.get("message")
        if not isinstance(message, dict):
            raise ProviderError("Antwort enthielt keine Nachricht.")
        content = message.get("content")
        if not isinstance(content, str):
            raise ProviderError("Antwort enthielt keinen Text.")
        return content
