"""Sicherheitsschicht: Prompt-Injection, Geheimnisse, Vertrauensgrenzen."""

from __future__ import annotations

from deutsches_ki.security.injection import (
    InjectionFinding,
    contains_injection,
    detect_injection,
)
from deutsches_ki.security.report import SecurityReport, scan_text
from deutsches_ki.security.secrets import SecretFinding, contains_secrets, detect_secrets
from deutsches_ki.security.trust import UNTRUSTED_END, UNTRUSTED_START, wrap_untrusted

__all__ = [
    "UNTRUSTED_END",
    "UNTRUSTED_START",
    "InjectionFinding",
    "SecretFinding",
    "SecurityReport",
    "contains_injection",
    "contains_secrets",
    "detect_injection",
    "detect_secrets",
    "scan_text",
    "wrap_untrusted",
]
