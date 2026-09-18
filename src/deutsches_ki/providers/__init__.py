"""Anbindung von Sprachmodellen."""

from __future__ import annotations

from typing import Any

from deutsches_ki.providers.base import ChatMessage, ChatProvider
from deutsches_ki.providers.ollama import OllamaProvider
from deutsches_ki.providers.openai_compatible import OpenAICompatibleProvider

__all__ = [
    "ChatMessage",
    "ChatProvider",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "get_provider",
]

_OPENAI_LIKE = {"openai", "openai-compatible", "vllm", "compatible"}


def get_provider(name: str = "ollama", **kwargs: Any) -> ChatProvider:
    """Erzeugt einen Anbieter anhand seines Namens.

    ``ollama`` spricht die Ollama-Schnittstelle, ``vllm`` und
    ``openai-compatible`` sprechen das OpenAI-Format. Jeder Anbieter folgt
    derselben Schnittstelle, ein Wechsel ist eine Konfigurationsfrage.
    """
    if name == "ollama":
        return OllamaProvider(**kwargs)
    if name in _OPENAI_LIKE:
        return OpenAICompatibleProvider(**kwargs)
    raise ValueError(f"Unbekannter Anbieter: {name}")
