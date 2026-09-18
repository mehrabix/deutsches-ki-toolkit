"""Erkennung von Prompt-Injection in Dokumenten.

Ein PDF ist fremder Inhalt. Wenn darin „Ignoriere alle vorherigen
Anweisungen“ steht, ist das Dokumentinhalt und keine Anweisung an das
Sprachmodell. Diese Erkennung macht solche Stellen sichtbar, bevor der Text in
einen Prompt gerät.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict

__all__ = ["InjectionFinding", "contains_injection", "detect_injection"]

_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        "ignore_instructions",
        r"\b(?:ignore|disregard|forget)\s+(?:all\s+)?(?:the\s+)?"
        r"(?:previous|prior|above|earlier|foregoing)\s+instructions?",
        "high",
    ),
    (
        "ignore_instructions_de",
        r"\b(?:ignorier|vergiss|missachte|verwerfe)\w*\s+(?:bitte\s+)?(?:alle\s+)?"
        r"(?:vorherigen|vorigen|obigen|bisherigen|früheren)\s+"
        r"(?:anweisungen|anweisung|instruktionen|hinweise)",
        "high",
    ),
    (
        "new_instructions",
        r"\b(?:neue|neuen|geänderte)\s+(?:anweisung|anweisungen|instruktionen)\b",
        "medium",
    ),
    (
        "override_instructions",
        r"\boverride\s+(?:the\s+)?(?:instructions?|rules?|system)\b",
        "high",
    ),
    (
        "system_prompt",
        r"\bsystem[\s_-]?(?:prompt|nachricht|message|anweisung)\b",
        "medium",
    ),
    (
        "role_reassignment",
        r"\b(?:you are now|from now on you are|du bist (?:jetzt|nun)|ab jetzt bist du)\b",
        "high",
    ),
    (
        "act_as",
        r"\b(?:act as|agiere als|verhalte dich wie|tu so als)\b",
        "medium",
    ),
    (
        "reveal_instructions",
        r"\b(?:reveal|show|print|repeat|gib|zeige|wiederhole)\w*\s+"
        r"(?:your|deine?n?|alle)\s+(?:instructions?|prompt|anweisungen|regeln)",
        "high",
    ),
    (
        "role_marker",
        r"(?m)^\s*(?:#{2,}\s*)?(?:system|assistant|user|entwickler)\s*:",
        "medium",
    ),
    (
        "special_token",
        r"<\|(?:system|assistant|user|im_start|im_end|endoftext)\|>",
        "high",
    ),
    (
        "exfiltrate",
        r"\b(?:sende|schicke|leite)\w*\s+(?:alle|die)\s+"
        r"(?:daten|dokumente|informationen)\s+(?:an|nach)\b",
        "medium",
    ),
)

_COMPILED = tuple(
    (name, re.compile(pattern, re.IGNORECASE), severity) for name, pattern, severity in _PATTERNS
)


class InjectionFinding(BaseModel):
    """Eine verdächtige Stelle im Dokument."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule: str
    severity: str
    text: str
    start: int
    end: int


def detect_injection(text: str) -> list[InjectionFinding]:
    """Findet Formulierungen, die wie eine Anweisung aussehen."""
    findings: list[InjectionFinding] = []
    seen: set[tuple[int, int]] = set()
    for name, pattern, severity in _COMPILED:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if span in seen:
                continue
            seen.add(span)
            findings.append(
                InjectionFinding(
                    rule=name,
                    severity=severity,
                    text=match.group().strip(),
                    start=match.start(),
                    end=match.end(),
                )
            )
    return sorted(findings, key=lambda finding: (finding.start, finding.end))


def contains_injection(text: str) -> bool:
    """Kurzprüfung, ob überhaupt etwas gefunden wurde."""
    return bool(detect_injection(text))
