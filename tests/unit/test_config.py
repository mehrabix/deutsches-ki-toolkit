"""Tests für die Konfiguration."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from deutsches_ki.config import Settings
from deutsches_ki.core.enums import AnonymizeMode, ChunkStrategy, Language


def test_defaults() -> None:
    settings = Settings()
    assert settings.language is Language.DE
    assert settings.chunking.strategy is ChunkStrategy.STRUCTURAL
    assert settings.chunking.max_tokens == 512
    assert settings.retrieval.top_k == 20
    assert settings.embeddings.provider == "hashing"
    assert settings.pii.mode is AnonymizeMode.REDACT


def test_load_from_file(tmp_path: Path) -> None:
    config = tmp_path / "deutsches-ki.yaml"
    config.write_text(
        "language: de\nchunking:\n  max_tokens: 128\n  overlap: 16\npii:\n  mode: pseudonymize\n",
        encoding="utf-8",
    )

    settings = Settings.load(config)

    assert settings.chunking.max_tokens == 128
    assert settings.chunking.overlap == 16
    assert settings.pii.mode is AnonymizeMode.PSEUDONYMIZE
    assert settings.chunking.strategy is ChunkStrategy.STRUCTURAL


def test_overrides_beat_file(tmp_path: Path) -> None:
    config = tmp_path / "deutsches-ki.yaml"
    config.write_text("chunking:\n  max_tokens: 128\n", encoding="utf-8")

    settings = Settings.load(config, chunking={"max_tokens": 64})
    assert settings.chunking.max_tokens == 64


def test_none_overrides_are_ignored() -> None:
    settings = Settings.load(document_type=None)
    assert settings.document_type is None


def test_missing_file_uses_defaults(tmp_path: Path) -> None:
    settings = Settings.load(tmp_path / "gibt-es-nicht.yaml")
    assert settings.chunking.max_tokens == 512


def test_invalid_value_raises() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"chunking": {"max_tokens": 0}})


def test_unknown_key_raises() -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate({"unbekannt": 1})
