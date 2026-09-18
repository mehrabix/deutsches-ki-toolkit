"""Tests für die Erkennung von Geheimnissen."""

from __future__ import annotations

from deutsches_ki.security.secrets import contains_secrets, detect_secrets


def _rules(text: str) -> list[str]:
    return [finding.rule for finding in detect_secrets(text)]


def test_detects_openai_key() -> None:
    text = "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz012345"
    assert "openai_key" in _rules(text)


def test_detects_github_token() -> None:
    assert "github_token" in _rules("token: ghp_abcdefghijklmnopqrstuvwxyz0123456789")


def test_detects_aws_access_key() -> None:
    assert "aws_access_key" in _rules("AKIAIOSFODNN7EXAMPLE")


def test_detects_private_key_header() -> None:
    assert "private_key" in _rules("-----BEGIN RSA PRIVATE KEY-----\nMIIE...")


def test_detects_connection_string_with_password() -> None:
    assert "connection_string" in _rules("postgresql://benutzer:geheim@localhost:5432/db")


def test_detects_german_password_assignment() -> None:
    assert "password_assignment" in _rules("Passwort: SuperGeheim123")


def test_secret_is_masked_in_finding() -> None:
    findings = detect_secrets("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz012345")
    assert findings
    masked = findings[0].masked
    assert "abcdefghijklmnop" not in masked
    assert "****" in masked


def test_ordinary_text_has_no_secrets() -> None:
    text = "Die Zahlungsfrist beträgt 30 Tage. Der Token ist nicht genannt."
    assert detect_secrets(text) == []
    assert contains_secrets(text) is False


def test_contains_secrets_shortcut() -> None:
    assert contains_secrets("AKIAIOSFODNN7EXAMPLE") is True
