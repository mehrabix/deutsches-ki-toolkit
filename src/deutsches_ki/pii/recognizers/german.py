"""Deutsche Erkennungsmuster mit Prüfsummen.

Wo es eine Prüfsumme gibt (IBAN, Steuer-ID), wird sie benutzt. Muster allein
reichen nicht: Ohne Prüfsumme entstehen zu viele Fehlalarme. Wo es keine
Prüfsumme gibt (USt-IdNr., Steuernummer), entscheidet ein deutsches
Kontextwort mit.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from deutsches_ki.core.enums import EntityType

__all__ = ["Recognizer", "default_recognizers"]


@dataclass(frozen=True)
class Recognizer:
    """Ein einzelnes Erkennungsmuster samt Prüfung und Kontextbezug."""

    name: str
    entity_type: EntityType
    pattern: re.Pattern[str]
    group: int = 0
    confidence: float = 0.9
    validate: Callable[[str], bool] | None = field(default=None)
    context_key: str | None = field(default=None)
    requires_context: bool = False


# --------------------------------------------------------------------------
# Prüfsummen und Plausibilitätsprüfungen
# --------------------------------------------------------------------------


def compact(value: str) -> str:
    """Entfernt Leerzeichen und Bindestriche."""
    return re.sub(r"[\s-]+", "", value)


def iban_is_valid(value: str) -> bool:
    """Prüft eine IBAN über den Modulo-97-Test."""
    iban = compact(value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", iban):
        return False
    rearranged = iban[4:] + iban[:4]
    try:
        digits = "".join(str(int(char, 36)) for char in rearranged)
    except ValueError:  # pragma: no cover - defensiv
        return False
    return int(digits) % 97 == 1


def tax_id_is_valid(value: str) -> bool:
    """Prüft die Steuer-ID (elfstellig, ISO 7064 Mod 11,10)."""
    digits = [int(char) for char in re.sub(r"\D", "", value)]
    if len(digits) != 11:
        return False
    if len(set(digits)) == 1:
        return False

    counts = Counter(digits[:10])
    doubled = sum(1 for count in counts.values() if count == 2)
    tripled = sum(1 for count in counts.values() if count == 3)
    if not ((doubled == 1 and tripled == 0) or (doubled == 0 and tripled == 1)):
        return False

    product = 10
    for digit in digits[:10]:
        step = (digit + product) % 10
        if step == 0:
            step = 10
        product = (2 * step) % 11
    checksum = 11 - product
    if checksum == 10:
        checksum = 0
    return checksum == digits[10]


def svnr_is_valid(value: str) -> bool:
    """Prüft die Form der Sozialversicherungsnummer und das Geburtsdatum."""
    match = re.fullmatch(r"(\d{2})(\d{2})(\d{2})(\d{2})([A-Z])(\d{3})", compact(value).upper())
    if match is None:
        return False
    day = int(match.group(2))
    month = int(match.group(3))
    return 1 <= day <= 31 and 1 <= month <= 12


def phone_is_valid(value: str) -> bool:
    """Plausible Länge einer Telefonnummer (7 bis 15 Ziffern)."""
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 15


def package_number_is_valid(value: str) -> bool:
    """Eine Kennung muss mindestens eine Ziffer enthalten."""
    return any(char.isdigit() for char in value)


# --------------------------------------------------------------------------
# Muster
# --------------------------------------------------------------------------

_ALNUM = r"[A-Za-z0-9][A-Za-z0-9./_-]{2,}"

_STREET_SUFFIX = (
    r"(?:straße|strasse|str\.?|weg|allee|platz|gasse|ring|damm|ufer|steig|"
    r"chaussee|graben|markt|berg|feld|hof|garten|park)"
)


def _compile(pattern: str, flags: int = 0) -> re.Pattern[str]:
    return re.compile(pattern, flags)


def default_recognizers() -> tuple[Recognizer, ...]:
    """Alle mitgelieferten deutschen Erkennungsmuster."""
    return (
        Recognizer(
            name="de_iban",
            entity_type=EntityType.DE_IBAN,
            pattern=_compile(r"\bDE\d{2}(?:[ ]?\d{4}){4}[ ]?\d{2}\b"),
            confidence=0.99,
            validate=iban_is_valid,
            context_key="iban",
        ),
        Recognizer(
            name="de_bic",
            entity_type=EntityType.DE_BIC,
            pattern=_compile(r"\b[A-Z]{4}DE[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),
            confidence=0.85,
            context_key="bic",
            requires_context=True,
        ),
        Recognizer(
            name="de_vat_id",
            entity_type=EntityType.DE_VAT_ID,
            pattern=_compile(r"\bDE\d{9}\b"),
            confidence=0.8,
            context_key="vat",
        ),
        Recognizer(
            name="de_tax_id",
            entity_type=EntityType.DE_TAX_ID,
            pattern=_compile(r"\b\d{2}[ ]?\d{3}[ ]?\d{3}[ ]?\d{3}\b"),
            confidence=0.95,
            validate=tax_id_is_valid,
            context_key="tax_id",
        ),
        Recognizer(
            name="de_tax_number",
            entity_type=EntityType.DE_TAX_NUMBER,
            pattern=_compile(r"\b\d{2,3}\s?/\s?\d{3}\s?/\s?\d{4,5}\b"),
            confidence=0.85,
            context_key="tax_number",
            requires_context=True,
        ),
        Recognizer(
            name="de_svnr",
            entity_type=EntityType.DE_SVNR,
            pattern=_compile(r"\b\d{8}[A-Z]\d{3}\b"),
            confidence=0.9,
            validate=svnr_is_valid,
            context_key="svnr",
        ),
        Recognizer(
            name="de_id_card",
            entity_type=EntityType.DE_ID_CARD,
            pattern=_compile(r"\b[A-Z]\d{8}\b"),
            confidence=0.8,
            context_key="id_card",
            requires_context=True,
        ),
        Recognizer(
            name="de_hr_number",
            entity_type=EntityType.DE_HR_NUMBER,
            pattern=_compile(r"\bHR[AB]\s?\d{1,7}\s?[A-Z]?\b"),
            confidence=0.9,
        ),
        Recognizer(
            name="de_plz",
            entity_type=EntityType.DE_PLZ,
            pattern=_compile(r"\b\d{5}\b"),
            confidence=0.8,
            context_key="plz",
            requires_context=True,
        ),
        Recognizer(
            name="de_address",
            entity_type=EntityType.DE_ADDRESS,
            pattern=_compile(
                r"\b[A-ZÄÖÜ][\wÄÖÜäöüß.-]{0,30}"
                + _STREET_SUFFIX
                + r"\s+\d{1,4}\s?[a-zA-Z]?(?:\s?[-\u2013]\s?\d{1,4}[a-zA-Z]?)?",
                re.IGNORECASE,
            ),
            confidence=0.85,
            context_key="address",
        ),
        Recognizer(
            name="de_mobile",
            entity_type=EntityType.PHONE,
            pattern=_compile(r"\b01[567]\d(?:[\s/.-]?\d){6,7}\b"),
            confidence=0.9,
            validate=phone_is_valid,
            context_key="phone",
        ),
        Recognizer(
            name="de_phone_intl",
            entity_type=EntityType.PHONE,
            pattern=_compile(r"\+49[\s/.-]?\(?\d{1,5}\)?[\s/.-]?\d{2,8}(?:[\s/.-]?\d{1,8})?"),
            confidence=0.9,
            validate=phone_is_valid,
            context_key="phone",
        ),
        Recognizer(
            name="de_phone",
            entity_type=EntityType.PHONE,
            pattern=_compile(r"\b0\d{1,5}[\s/.-]\d{2,8}(?:[\s/.-]?\d{1,8})?"),
            confidence=0.85,
            validate=phone_is_valid,
            context_key="phone",
            requires_context=True,
        ),
        Recognizer(
            name="email",
            entity_type=EntityType.EMAIL,
            pattern=_compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
            confidence=0.95,
        ),
        Recognizer(
            name="de_invoice_number",
            entity_type=EntityType.DE_INVOICE_NUMBER,
            pattern=_compile(
                rf"(?:Rechnungs?(?:nummer|nr\.?)|Rechnung\s*Nr\.?)\s*[:#]?\s*({_ALNUM})",
                re.IGNORECASE,
            ),
            group=1,
            confidence=0.9,
            validate=package_number_is_valid,
        ),
        Recognizer(
            name="de_customer_number",
            entity_type=EntityType.DE_CUSTOMER_NUMBER,
            pattern=_compile(
                rf"(?:Kunden(?:nummer|nr\.?)|Kd\.?-?\s?Nr\.?)\s*[:#]?\s*({_ALNUM})",
                re.IGNORECASE,
            ),
            group=1,
            confidence=0.9,
            validate=package_number_is_valid,
        ),
        Recognizer(
            name="de_order_number",
            entity_type=EntityType.DE_ORDER_NUMBER,
            pattern=_compile(
                rf"(?:Auftrags?(?:nummer|nr\.?)|Bestell(?:nummer|nr\.?))\s*[:#]?\s*({_ALNUM})",
                re.IGNORECASE,
            ),
            group=1,
            confidence=0.9,
            validate=package_number_is_valid,
        ),
        Recognizer(
            name="de_contract_number",
            entity_type=EntityType.DE_CONTRACT_NUMBER,
            pattern=_compile(
                rf"(?:Vertrags?(?:nummer|nr\.?)|Vertrag\s*Nr\.?)\s*[:#]?\s*({_ALNUM})",
                re.IGNORECASE,
            ),
            group=1,
            confidence=0.9,
            validate=package_number_is_valid,
        ),
    )
