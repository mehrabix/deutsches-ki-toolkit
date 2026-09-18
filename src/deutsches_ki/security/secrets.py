"""Erkennung von Geheimnissen in Dokumenten.

Zugangsdaten gehören nicht in ein Sprachmodell und nicht in eine Fundstelle.
Der gefundene Text wird deshalb nur maskiert ausgegeben.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

__all__ = ["SecretFinding", "contains_secrets", "detect_secrets"]

_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("private_key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "high"),
    ("openai_key", r"\bsk-[A-Za-z0-9]{16,}\b", "high"),
    ("anthropic_key", r"\bsk-ant-[A-Za-z0-9_-]{16,}\b", "high"),
    ("github_token", r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", "high"),
    ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b", "high"),
    ("slack_token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "high"),
    (
        "jwt",
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b",
        "medium",
    ),
    (
        "connection_string",
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://"
        r"[^\s:@/]+:[^\s@/]+@[^\s/]+",
        "high",
    ),
    (
        "password_assignment",
        r"\b(?:passwort|password|passwd|pwd|secret|api[_-]?key|access[_-]?token)"
        r"\s*[:=]\s*[^\s,;]{4,}",
        "medium",
    ),
)

_COMPILED = tuple(
    (name, re.compile(pattern, re.IGNORECASE), severity) for name, pattern, severity in _PATTERNS
)

_HEAD = 4
_TAIL = 2


class SecretFinding(BaseModel):
    """Ein gefundenes Geheimnis, maskiert."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule: str
    severity: str
    masked: str
    start: int
    end: int


def _mask(value: str) -> str:
    if len(value) <= _HEAD + _TAIL:
        return "*" * len(value)
    return f"{value[:_HEAD]}{'*' * 8}{value[-_TAIL:]}"


def detect_secrets(text: str) -> list[SecretFinding]:
    """Findet Zugangsdaten und Schlüssel, ohne sie im Klartext auszugeben."""
    findings: list[SecretFinding] = []
    seen: set[tuple[int, int]] = set()
    for name, pattern, severity in _COMPILED:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if span in seen:
                continue
            seen.add(span)
            findings.append(
                SecretFinding(
                    rule=name,
                    severity=severity,
                    masked=_mask(match.group()),
                    start=match.start(),
                    end=match.end(),
                )
            )
    return sorted(findings, key=lambda finding: (finding.start, finding.end))


def contains_secrets(text: str) -> bool:
    """Kurzprüfung, ob überhaupt etwas gefunden wurde."""
    return bool(detect_secrets(text))
