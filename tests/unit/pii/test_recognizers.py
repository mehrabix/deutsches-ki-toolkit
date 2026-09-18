"""Tests für die deutschen Erkennungsmuster."""

from __future__ import annotations

from deutsches_ki.core.enums import EntityType
from deutsches_ki.pii import detect
from deutsches_ki.pii.recognizers.german import (
    iban_is_valid,
    phone_is_valid,
    tax_id_is_valid,
)


def _types(text: str) -> set[EntityType]:
    return {entity.type for entity in detect(text)}


def test_detects_german_iban() -> None:
    entities = detect("Überweisung auf DE89 3704 0044 0532 0130 00 bitte.")
    assert [entity.type for entity in entities] == [EntityType.DE_IBAN]
    assert entities[0].text == "DE89 3704 0044 0532 0130 00"
    assert entities[0].confidence > 0.95


def test_rejects_iban_with_wrong_checksum() -> None:
    assert detect("DE89 3704 0044 0532 0130 01") == []
    assert iban_is_valid("DE89370400440532013000") is True
    assert iban_is_valid("DE89370400440532013001") is False


def test_detects_vat_id() -> None:
    assert EntityType.DE_VAT_ID in _types("USt-IdNr.: DE123456789")


def test_detects_tax_id_with_checksum() -> None:
    entities = detect("Steuer-ID 12 345 678 911")
    assert [entity.type for entity in entities] == [EntityType.DE_TAX_ID]


def test_rejects_tax_id_with_wrong_checksum() -> None:
    assert tax_id_is_valid("12345678911") is True
    assert tax_id_is_valid("12345678900") is False


def test_rejects_tax_id_with_all_digits_equal() -> None:
    assert tax_id_is_valid("11111111111") is False


def test_tax_number_requires_context() -> None:
    assert EntityType.DE_TAX_NUMBER in _types("Steuernummer: 12/345/67890")
    assert EntityType.DE_TAX_NUMBER not in _types("Code 12/345/67890")


def test_detects_svnr_with_valid_birthdate() -> None:
    entities = detect("Sozialversicherungsnummer 65170672M001")
    assert [entity.type for entity in entities] == [EntityType.DE_SVNR]


def test_rejects_svnr_with_impossible_month() -> None:
    assert detect("65177372M001") == []


def test_detects_id_card_only_with_context() -> None:
    assert EntityType.DE_ID_CARD in _types("Personalausweis T22000129")
    assert EntityType.DE_ID_CARD not in _types("T22000129")


def test_detects_handelsregisternummer() -> None:
    assert EntityType.DE_HR_NUMBER in _types("Eingetragen unter HRB 12345 B")


def test_detects_plz_only_with_context() -> None:
    assert EntityType.DE_PLZ in _types("PLZ 10115")
    assert EntityType.DE_PLZ not in _types("Artikelnummer 10115")


def test_detects_address() -> None:
    entities = detect("Anschrift: Beispielstraße 12a")
    assert EntityType.DE_ADDRESS in {entity.type for entity in entities}


def test_detects_mobile_and_landline() -> None:
    assert EntityType.PHONE in _types("Mobil: 0171 1234567")
    assert EntityType.PHONE in _types("Telefon: 030 12345678")


def test_landline_requires_context() -> None:
    assert EntityType.PHONE not in _types("Wert 030 12345678")


def test_rejects_short_phone_like_number() -> None:
    assert phone_is_valid("02024") is False


def test_detects_email() -> None:
    entities = detect("Kontakt: max.mustermann@example.de")
    assert [entity.type for entity in entities] == [EntityType.EMAIL]


def test_detects_bic_with_context() -> None:
    assert EntityType.DE_BIC in _types("BIC: DEUTDEFF")


def test_bic_requires_context() -> None:
    assert EntityType.DE_BIC not in _types("DEUTDEFF")


def test_detects_invoice_number_but_not_label() -> None:
    entities = detect("Rechnungsnummer: RE-2024-001")
    assert [entity.type for entity in entities] == [EntityType.DE_INVOICE_NUMBER]
    assert entities[0].text == "RE-2024-001"


def test_detects_customer_number() -> None:
    entities = detect("Kundennummer: 4711")
    assert [entity.type for entity in entities] == [EntityType.DE_CUSTOMER_NUMBER]
    assert entities[0].text == "4711"


def test_detects_order_and_contract_numbers() -> None:
    assert EntityType.DE_ORDER_NUMBER in _types("Auftragsnummer: AB-9981")
    assert EntityType.DE_CONTRACT_NUMBER in _types("Vertragsnummer: V-2024-77")


def test_context_raises_confidence() -> None:
    without = detect("DEUTDEFF")
    with_context = detect("BIC: DEUTDEFF")
    assert without == []
    assert with_context[0].confidence > 0.85
