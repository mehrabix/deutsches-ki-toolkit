"""Aufzählungen für Entitätstypen, Betriebsarten und Strategien."""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "AnonymizeMode",
    "ChunkStrategy",
    "DetectorSource",
    "EntityType",
    "Language",
]


class Language(StrEnum):
    """Erkannte Sprache eines Dokuments."""

    DE = "de"
    EN = "en"
    MIXED = "mixed"


class EntityType(StrEnum):
    """Entitätstypen, die das Toolkit unterscheidet."""

    PERSON = "PERSON"
    ORGANISATION = "ORGANISATION"
    LOCATION = "LOCATION"
    DATE = "DATE"
    MONEY = "MONEY"
    PHONE = "PHONE"
    EMAIL = "EMAIL"

    DE_IBAN = "DE_IBAN"
    DE_BIC = "DE_BIC"
    DE_VAT_ID = "DE_VAT_ID"
    DE_TAX_ID = "DE_TAX_ID"
    DE_TAX_NUMBER = "DE_TAX_NUMBER"
    DE_SVNR = "DE_SVNR"
    DE_ID_CARD = "DE_ID_CARD"
    DE_HR_NUMBER = "DE_HR_NUMBER"
    DE_PLZ = "DE_PLZ"
    DE_ADDRESS = "DE_ADDRESS"

    DE_INVOICE_NUMBER = "DE_INVOICE_NUMBER"
    DE_CUSTOMER_NUMBER = "DE_CUSTOMER_NUMBER"
    DE_ORDER_NUMBER = "DE_ORDER_NUMBER"
    DE_CONTRACT_NUMBER = "DE_CONTRACT_NUMBER"


class AnonymizeMode(StrEnum):
    """Betriebsarten der Anonymisierung."""

    REDACT = "redact"
    REPLACE = "replace"
    MASK = "mask"
    HASH = "hash"
    PSEUDONYMIZE = "pseudonymize"


class ChunkStrategy(StrEnum):
    """Verfahren zum Zerlegen von Dokumenten."""

    STRUCTURAL = "structural"
    FIXED = "fixed"


class DetectorSource(StrEnum):
    """Herkunft eines Entitätstreffers."""

    REGEX = "regex"
    SPACY = "spacy"
    PRESIDIO = "presidio"
    GLINER = "gliner"
    TRANSFORMER = "transformer"
