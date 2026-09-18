"""Deterministisches Embedding über Feature-Hashing.

Dieses Modell braucht kein Netz, kein Modell und keine GPU. Es ist die
Grundlage dafür, dass die gesamte Kette auch ohne schwere Abhängigkeiten
getestet werden kann. Für echte Qualität wird stattdessen BGE-M3 angebunden.

Ein deutscher Zusatz: Komposita werden vor dem Hashen zerlegt, damit
„Versicherungsbeitrag“ und „Beitrag“ sich näherkommen.
"""

from __future__ import annotations

import hashlib
import math

from deutsches_ki.text.tokens import search_tokens

__all__ = ["HashingEmbedder"]

_DIGEST_SIZE = 8


class HashingEmbedder:
    """Feature-Hashing mit L2-Normalisierung."""

    name = "hashing"

    def __init__(self, dimension: int = 256, *, expand_compounds: bool = True) -> None:
        if dimension <= 0:
            raise ValueError("dimension muss größer als 0 sein.")
        self.dimension = dimension
        self._expand_compounds = expand_compounds

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _tokens(self, text: str) -> list[str]:
        return search_tokens(text, expand_compounds=self._expand_compounds)

    def _bucket(self, token: str) -> tuple[int, float]:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=_DIGEST_SIZE).digest()
        value = int.from_bytes(digest, "big")
        sign = 1.0 if (value >> 8) & 1 else -1.0
        return value % self.dimension, sign

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in self._tokens(text):
            index, sign = self._bucket(token)
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]
