"""Embedding-Anbieter."""

from __future__ import annotations

from typing import Any

from deutsches_ki.embeddings.base import EmbeddingProvider
from deutsches_ki.embeddings.hashing import HashingEmbedder

__all__ = ["EmbeddingProvider", "HashingEmbedder", "get_embedder"]

_MODEL_ALIASES: dict[str, str] = {
    "bge-m3": "BAAI/bge-m3",
    "multilingual-e5": "intfloat/multilingual-e5-large",
    "multilingual-e5-small": "intfloat/multilingual-e5-small",
    "e5": "intfloat/multilingual-e5-large",
}


def get_embedder(name: str = "hashing", **kwargs: Any) -> EmbeddingProvider:
    """Erzeugt einen Embedding-Anbieter anhand seines Namens.

    ``hashing`` ist das deterministische Modell ohne externe Abhängigkeit.
    Alles andere wird als Satz-Embedding-Modell geladen; bekannte Namen werden
    auf ihre Modellkennung abgebildet, ein lokaler Pfad funktioniert ebenfalls.
    """
    if name in {"hashing", "hash"}:
        return HashingEmbedder(**kwargs)

    from deutsches_ki.embeddings.sentence_transformers import SentenceTransformerEmbedder

    model = _MODEL_ALIASES.get(name, name)
    return SentenceTransformerEmbedder(model=model, **kwargs)
