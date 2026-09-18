"""Gemeinsame Test-Fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "datasets" / "fixtures"


@pytest.fixture
def fixture_dir() -> Path:
    """Pfad zu den synthetischen Testdateien."""
    return FIXTURE_DIR
