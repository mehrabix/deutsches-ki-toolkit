"""Dokumentarten, die das Toolkit unterscheidet."""

from __future__ import annotations

from enum import StrEnum

__all__ = ["DocumentType"]


class DocumentType(StrEnum):
    """Erkannte Art eines Dokuments."""

    CONTRACT = "contract"
    INVOICE = "invoice"
    OFFER = "offer"
    ORDER = "order"
    LEGAL_DOCUMENT = "legal_document"
    HR_DOCUMENT = "hr_document"
    TECHNICAL_DOCUMENT = "technical_document"
    MANUAL = "manual"
    SPECIFICATION = "specification"
    REPORT = "report"
    EMAIL = "email"
    UNKNOWN = "unknown"
