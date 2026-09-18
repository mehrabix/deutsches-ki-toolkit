"""Deutsche PII-Erkennung und Anonymisierung."""

from __future__ import annotations

from deutsches_ki.pii.anonymize import AnonymizeResult, Pseudonymizer, anonymize
from deutsches_ki.pii.base import EntityDetector
from deutsches_ki.pii.detect import default_detectors, detect, resolve_entities
from deutsches_ki.pii.detectors.regex import RegexDetector
from deutsches_ki.pii.recognizers.german import Recognizer, default_recognizers

__all__ = [
    "AnonymizeResult",
    "EntityDetector",
    "Pseudonymizer",
    "Recognizer",
    "RegexDetector",
    "anonymize",
    "default_detectors",
    "default_recognizers",
    "detect",
    "resolve_entities",
]
