"""Zusammenfassender Prüfbericht für ein Dokument."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.security.injection import InjectionFinding, detect_injection
from deutsches_ki.security.secrets import SecretFinding, detect_secrets

__all__ = ["SecurityReport", "scan_text"]


class SecurityReport(BaseModel):
    """Was in einem Dokument auffällig ist."""

    model_config = ConfigDict(extra="forbid")

    injections: list[InjectionFinding] = Field(default_factory=list)
    secrets: list[SecretFinding] = Field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """Wurde nichts gefunden?"""
        return not self.injections and not self.secrets

    @property
    def has_high_severity(self) -> bool:
        """Gibt es einen Fund mit hoher Einstufung?"""
        injections = any(item.severity == "high" for item in self.injections)
        secrets = any(item.severity == "high" for item in self.secrets)
        return injections or secrets


def scan_text(text: str) -> SecurityReport:
    """Prüft Text auf Prompt-Injection und Geheimnisse."""
    return SecurityReport(
        injections=detect_injection(text),
        secrets=detect_secrets(text),
    )
