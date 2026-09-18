"""Reranking: Modelle, die Treffer neu sortieren."""

from __future__ import annotations

from typing import Any

from deutsches_ki.reranking.base import Reranker
from deutsches_ki.reranking.lexical import LexicalReranker

__all__ = ["LexicalReranker", "Reranker", "get_reranker"]


def get_reranker(name: str = "lexical", **kwargs: Any) -> Reranker:
    """Erzeugt einen Reranker anhand seines Namens.

    ``lexical`` kommt ohne Modell aus. Alles andere wird als Cross-Encoder
    geladen; bekannte Namen werden auf ihre Modellkennung abgebildet.
    """
    if name in {"lexical", "overlap"}:
        return LexicalReranker(**kwargs)

    from deutsches_ki.reranking.cross_encoder import CrossEncoderReranker

    return CrossEncoderReranker(model=name, **kwargs)
