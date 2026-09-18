"""Integrationstest für den Ollama-Anbieter gegen einen echten HTTP-Server.

Hier läuft kein Modell, sondern ein kleiner Server, der die Ollama-Schnittstelle
spricht. Damit wird die tatsächliche HTTP-Schicht geprüft: Adresse, Nutzlast,
Antwortformat und Fehlerbehandlung. Das Modell selbst ist dafür unerheblich, und
der Test braucht weder Erweiterung noch Netz noch Grafikkarte.

Was hier nicht geprüft wird: ob ein Modell gute Antworten gibt. Dafür braucht es
ein echtes Modell, und das gehört in einen eigenen Lauf.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, ClassVar

import pytest

from deutsches_ki.core.models import Chunk
from deutsches_ki.embeddings import get_embedder
from deutsches_ki.errors import ProviderError
from deutsches_ki.providers import (
    ChatMessage,
    OllamaProvider,
    OpenAICompatibleProvider,
    get_provider,
)
from deutsches_ki.rag import DeutschRAG
from deutsches_ki.retrieval import InMemoryRetriever

pytestmark = pytest.mark.integration


class _Handler(BaseHTTPRequestHandler):
    """Antwortet auf ``/api/chat`` mit einer vorbereiteten Antwort."""

    answer: str = "Antwort"
    status: int = 200
    requests: ClassVar[list[dict[str, Any]]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        body = json.loads(raw.decode("utf-8"))
        _Handler.requests.append(
            {
                "path": self.path,
                "body": body,
                "authorization": self.headers.get("Authorization"),
            }
        )

        if self.status != 200:
            payload: dict[str, Any] = {"error": "etwas ging schief"}
        elif self.path == "/api/chat":
            payload = {
                "model": body.get("model", "unbekannt"),
                "message": {"role": "assistant", "content": self.answer},
                "done": True,
            }
        else:
            # OpenAI-kompatibles Format, wie es vLLM liefert.
            payload = {
                "model": body.get("model", "unbekannt"),
                "choices": [{"index": 0, "message": {"role": "assistant", "content": self.answer}}],
            }

        data = json.dumps(payload).encode("utf-8")
        self.send_response(self.status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args: Any) -> None:
        """Protokollausgabe unterdrücken."""
        return


@pytest.fixture
def ollama_server() -> Iterator[str]:
    """Startet den Ersatzserver und gibt seine Adresse zurück."""
    _Handler.answer = "Antwort"
    _Handler.status = 200
    _Handler.requests = []

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _provider(host: str) -> OllamaProvider:
    return OllamaProvider(model="testmodell", host=host)


CHUNKS = [
    Chunk(
        content="Die Zahlung ist innerhalb von 30 Tagen nach Rechnungsstellung fällig.",
        metadata={"section": "§ 4 Zahlungsbedingungen", "document": "vertrag.md"},
    ),
    Chunk(
        content="Die Kündigungsfrist beträgt drei Monate zum Monatsende.",
        metadata={"section": "§ 7 Kündigung", "document": "vertrag.md"},
    ),
]


def _rag(host: str, *, answer: str) -> DeutschRAG:
    _Handler.answer = answer
    retriever = InMemoryRetriever(get_embedder("hashing"))
    retriever.add(CHUNKS)
    return DeutschRAG(retriever, llm=_provider(host), candidates=2, top_k=2)


# --- HTTP-Schicht ----------------------------------------------------------


def test_request_reaches_the_right_endpoint(ollama_server: str) -> None:
    _provider(ollama_server).generate([ChatMessage(role="user", content="Frage?")])

    assert len(_Handler.requests) == 1
    assert _Handler.requests[0]["path"] == "/api/chat"


def test_request_carries_model_messages_and_stream_flag(ollama_server: str) -> None:
    provider = OllamaProvider(model="testmodell", host=ollama_server)
    provider.generate([ChatMessage(role="user", content="Wie lange ist die Frist?")])

    body = _Handler.requests[0]["body"]
    assert body["model"] == "testmodell"
    assert body["stream"] is False
    assert body["messages"] == [{"role": "user", "content": "Wie lange ist die Frist?"}]


def test_answer_is_returned(ollama_server: str) -> None:
    _Handler.answer = "Die Frist beträgt 30 Tage [1]."
    text = _provider(ollama_server).generate([ChatMessage(role="user", content="Frage?")])
    assert text == "Die Frist beträgt 30 Tage [1]."


def test_http_error_becomes_provider_error(ollama_server: str) -> None:
    _Handler.status = 500
    with pytest.raises(ProviderError, match="500"):
        _provider(ollama_server).generate([ChatMessage(role="user", content="Frage?")])


def test_unreachable_host_becomes_provider_error() -> None:
    """Ein Port, auf dem nichts lauscht, darf keinen rohen URLError durchreichen."""
    provider = OllamaProvider(model="testmodell", host="http://127.0.0.1:1")
    with pytest.raises(ProviderError):
        provider.generate([ChatMessage(role="user", content="Frage?")])


def test_get_provider_builds_an_ollama_provider() -> None:
    assert get_provider("ollama", model="x", host="http://127.0.0.1:1").name == "ollama"


# --- OpenAI-kompatible Anbindung (vLLM) ------------------------------------


def _openai(host: str, *, api_key: str | None = None) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(model="testmodell", base_url=host, api_key=api_key)


def test_openai_compatible_uses_chat_completions(ollama_server: str) -> None:
    _Handler.answer = "Antwort aus vLLM [1]."
    text = _openai(ollama_server).generate([ChatMessage(role="user", content="Frage?")])

    assert _Handler.requests[0]["path"] == "/chat/completions"
    assert text == "Antwort aus vLLM [1]."


def test_openai_compatible_sends_bearer_token(ollama_server: str) -> None:
    _openai(ollama_server, api_key="geheim").generate([ChatMessage(role="user", content="F")])
    assert _Handler.requests[0]["authorization"] == "Bearer geheim"


def test_openai_compatible_without_key_sends_no_header(ollama_server: str) -> None:
    _openai(ollama_server).generate([ChatMessage(role="user", content="F")])
    assert _Handler.requests[0]["authorization"] is None


def test_openai_compatible_reports_http_error(ollama_server: str) -> None:
    _Handler.status = 503
    with pytest.raises(ProviderError, match="503"):
        _openai(ollama_server).generate([ChatMessage(role="user", content="F")])


# --- Die ganze Kette mit einem Sprachmodell --------------------------------


def test_ask_returns_a_formulated_answer(ollama_server: str) -> None:
    rag = _rag(ollama_server, answer="Die Zahlungsfrist beträgt 30 Tage [1].")
    answer = rag.ask("Wie lange ist die Zahlungsfrist?")

    assert answer.answer.startswith("Die Zahlungsfrist")
    assert answer.metadata["mode"] == "llm"
    assert answer.metadata["citations"]["valid"] == [1]
    assert answer.metadata["citations"]["unknown"] == []
    assert answer.citations[0].section == "§ 4 Zahlungsbedingungen"


def test_prompt_marks_document_content_as_untrusted(ollama_server: str) -> None:
    rag = _rag(ollama_server, answer="Antwort [1].")
    rag.ask("Wie lange ist die Zahlungsfrist?")

    sent = _Handler.requests[0]["body"]["messages"]
    assert sent[0]["role"] == "system"
    assert "keine Anweisung" in sent[0]["content"]
    assert "DOKUMENTINHALT" in sent[1]["content"]
    assert "[1] § 4 Zahlungsbedingungen" in sent[1]["content"]


def test_end_to_end_detects_an_invented_citation(ollama_server: str) -> None:
    """Ein erfundenes Zitat darf nicht unbemerkt durchgehen."""
    rag = _rag(ollama_server, answer="Laut [9] gilt etwas ganz anderes.")
    answer = rag.ask("Wie lange ist die Zahlungsfrist?")

    assert answer.metadata["citations"]["unknown"] == [9]
    assert answer.metadata["citations"]["all_valid"] is False


def test_answer_without_any_citation_is_flagged(ollama_server: str) -> None:
    rag = _rag(ollama_server, answer="Die Frist beträgt 30 Tage.")
    answer = rag.ask("Wie lange ist die Zahlungsfrist?")

    assert answer.metadata["citations"]["has_citations"] is False
