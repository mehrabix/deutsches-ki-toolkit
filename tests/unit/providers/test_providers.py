"""Tests für die Anbindung von Sprachmodellen.

Die HTTP-Schicht wird ersetzt, damit die Tests ohne laufenden Modellserver
auskommen. Geprüft wird, welche Adresse und welche Nutzlast ankommen.
"""

from __future__ import annotations

from typing import Any

import pytest

from deutsches_ki.errors import ProviderError
from deutsches_ki.providers import (
    ChatMessage,
    OllamaProvider,
    OpenAICompatibleProvider,
    get_provider,
)

MESSAGES = [ChatMessage(role="user", content="Wie lange ist die Zahlungsfrist?")]


def _capture(
    monkeypatch: pytest.MonkeyPatch, module: str, response: dict[str, Any]
) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    def fake_post(url: str, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        captured["url"] = url
        captured["payload"] = payload
        captured["kwargs"] = kwargs
        return response

    monkeypatch.setattr(f"deutsches_ki.providers.{module}.post_json", fake_post)
    return captured


def test_ollama_sends_chat_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture(monkeypatch, "ollama", {"message": {"content": "30 Tage"}})
    provider = OllamaProvider(model="llama3.1")

    assert provider.generate(MESSAGES) == "30 Tage"
    assert captured["url"].endswith("/api/chat")
    assert captured["payload"]["model"] == "llama3.1"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["messages"][0]["role"] == "user"


def test_ollama_rejects_missing_message(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture(monkeypatch, "ollama", {"done": True})
    with pytest.raises(ProviderError, match="Nachricht"):
        OllamaProvider().generate(MESSAGES)


def test_ollama_rejects_missing_content(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture(monkeypatch, "ollama", {"message": {}})
    with pytest.raises(ProviderError, match="Text"):
        OllamaProvider().generate(MESSAGES)


def test_ollama_strips_trailing_slash(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture(monkeypatch, "ollama", {"message": {"content": "ok"}})
    OllamaProvider(host="http://beispiel.local:11434/").generate(MESSAGES)
    assert captured["url"] == "http://beispiel.local:11434/api/chat"


def test_openai_compatible_sends_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture(
        monkeypatch,
        "openai_compatible",
        {"choices": [{"message": {"content": "Die Frist beträgt 30 Tage [1]."}}]},
    )
    provider = OpenAICompatibleProvider(model="qwen", api_key="geheim")

    answer = provider.generate(MESSAGES)
    assert answer.startswith("Die Frist")
    assert captured["url"].endswith("/chat/completions")
    assert captured["payload"]["model"] == "qwen"
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer geheim"


def test_openai_compatible_without_key_sends_no_header(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _capture(
        monkeypatch, "openai_compatible", {"choices": [{"message": {"content": "ok"}}]}
    )
    OpenAICompatibleProvider().generate(MESSAGES)
    assert captured["kwargs"]["headers"] == {}


def test_openai_compatible_rejects_empty_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture(monkeypatch, "openai_compatible", {"choices": []})
    with pytest.raises(ProviderError, match="Auswahl"):
        OpenAICompatibleProvider().generate(MESSAGES)


def test_get_provider_ollama() -> None:
    assert get_provider("ollama").name == "ollama"


def test_get_provider_vllm() -> None:
    assert get_provider("vllm").name == "openai-compatible"


def test_get_provider_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unbekannter Anbieter"):
        get_provider("zauberei")
