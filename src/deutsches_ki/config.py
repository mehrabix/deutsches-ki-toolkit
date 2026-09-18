"""Konfiguration aus ``deutsches-ki.yaml`` und Aufrufparametern."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.core.enums import AnonymizeMode, ChunkStrategy, Language

__all__ = [
    "CONFIG_FILENAME",
    "ChunkingConfig",
    "DocumentsConfig",
    "EmbeddingsConfig",
    "PiiConfig",
    "RetrievalConfig",
    "Settings",
]

CONFIG_FILENAME = "deutsches-ki.yaml"


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DocumentsConfig(_Section):
    """Wie Dokumente eingelesen werden."""

    parser: str | None = None


class PiiConfig(_Section):
    """Erkennung und Anonymisierung sensibler Daten."""

    enabled: bool = True
    mode: AnonymizeMode = AnonymizeMode.REDACT
    detectors: list[str] = Field(default_factory=lambda: ["regex"])


class ChunkingConfig(_Section):
    """Wie Dokumente zerlegt werden."""

    strategy: ChunkStrategy = ChunkStrategy.STRUCTURAL
    max_tokens: int = Field(default=512, gt=0)
    overlap: int = Field(default=64, ge=0)


class EmbeddingsConfig(_Section):
    """Welches Embedding-Modell verwendet wird."""

    provider: str = "hashing"
    device: str | None = None


class RetrievalConfig(_Section):
    """Wie gesucht wird."""

    vector: bool = True
    lexical: bool = True
    fusion: str = "rrf"
    top_k: int = Field(default=20, ge=1)


class Settings(_Section):
    """Gesamte Konfiguration mit sinnvollen Vorgaben."""

    language: Language = Language.DE
    document_type: str | None = None
    documents: DocumentsConfig = Field(default_factory=DocumentsConfig)
    pii: PiiConfig = Field(default_factory=PiiConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)

    @classmethod
    def load(cls, path: str | Path | None = None, **overrides: Any) -> Settings:
        """Lädt die Konfiguration aus einer Datei, danach kommen Überschreibungen.

        Existiert die Datei nicht, gelten die Vorgaben. Ein Aufrufparameter
        schlägt die Datei, die Datei schlägt die Vorgabe.
        """
        candidate = Path(path) if path is not None else Path(CONFIG_FILENAME)
        data: dict[str, Any] = {}
        if candidate.exists():
            raw = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            if isinstance(raw, dict):
                data = raw
        if overrides:
            data = _merge(
                data, {key: value for key, value in overrides.items() if value is not None}
            )
        return cls.model_validate(data)


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            result[key] = _merge(existing, value)
        else:
            result[key] = value
    return result
