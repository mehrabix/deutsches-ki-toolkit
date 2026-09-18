"""Deutschsprachige KI-Infrastruktur für Dokumente, Datenschutz, Suche und RAG."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from deutsches_ki.facade import GermanDocument

__all__ = ["GermanDocument", "__version__"]

try:
    __version__ = version("deutsches-ki-toolkit")
except PackageNotFoundError:
    # Ein Quelltextbaum ohne Installation. Die Zahl steht in ``pyproject.toml``
    # und wird hier bewusst nicht wiederholt: Zweimal dieselbe Version zu
    # pflegen heißt, sie irgendwann auseinanderlaufen zu lassen.
    __version__ = "0.0.0"
