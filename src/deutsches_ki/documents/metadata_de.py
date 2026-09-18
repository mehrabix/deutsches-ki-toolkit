"""Deutsche Metadaten aus einem Dokument ziehen.

Rechnungsnummer, Kundennummer und ähnliches findet bereits die PII-Erkennung.
Hier werden diese Treffer nur benannt und um das Rechnungsdatum ergänzt, damit
sie später zum Filtern taugen.
"""

from __future__ import annotations

import re

from deutsches_ki.core.enums import EntityType
from deutsches_ki.pii.detect import detect

__all__ = ["extract_metadata"]

_KEYS: dict[EntityType, str] = {
    EntityType.DE_INVOICE_NUMBER: "invoice_number",
    EntityType.DE_CUSTOMER_NUMBER: "customer_number",
    EntityType.DE_ORDER_NUMBER: "order_number",
    EntityType.DE_CONTRACT_NUMBER: "contract_number",
    EntityType.DE_VAT_ID: "vat_id",
}

_DATE = re.compile(
    r"(?:Rechnungsdatum|Datum|vom)\s*[:#]?\s*(\d{1,2}\.\d{1,2}\.\d{2,4})",
    re.IGNORECASE,
)


def extract_metadata(text: str) -> dict[str, str]:
    """Sammelt deutsche Geschäftsangaben aus dem Text.

    Der erste Treffer je Art gewinnt; weitere werden nicht überschrieben.
    """
    metadata: dict[str, str] = {}

    for entity in detect(text):
        key = _KEYS.get(entity.type)
        if key is not None:
            metadata.setdefault(key, entity.text)

    match = _DATE.search(text)
    if match is not None:
        metadata.setdefault("date", match.group(1))

    return metadata
