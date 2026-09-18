"""Erkennung der Dokumentart."""

from __future__ import annotations

from deutsches_ki.classification.rules import ClassificationResult, classify_document
from deutsches_ki.classification.types import DocumentType

__all__ = ["ClassificationResult", "DocumentType", "classify_document"]
