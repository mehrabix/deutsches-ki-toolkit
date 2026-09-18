"""Klartext einlesen.

Die Arbeit steckt in ``markdown``, weil beide Parser dieselbe Struktur
aufbauen. Ein Vertrag im Textformat behält damit seine Gliederung.
"""

from __future__ import annotations

from deutsches_ki.documents.markdown import parse_plaintext, split_paragraphs

__all__ = ["parse_plaintext", "split_paragraphs"]
