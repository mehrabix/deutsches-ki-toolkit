"""Tests für Anonymisierung und Pseudonymisierung."""

from __future__ import annotations

from deutsches_ki.core.enums import AnonymizeMode, DetectorSource, EntityType
from deutsches_ki.core.models import Entity
from deutsches_ki.pii.anonymize import Pseudonymizer, anonymize


def _entity(text: str, needle: str, entity_type: EntityType) -> Entity:
    start = text.index(needle)
    return Entity(
        type=entity_type,
        text=needle,
        start=start,
        end=start + len(needle),
        source=DetectorSource.REGEX,
    )


SENTENCE = "Max Mustermann arbeitet bei der Beispiel GmbH."


def _person_and_org(text: str) -> list[Entity]:
    return [
        _entity(text, "Max Mustermann", EntityType.PERSON),
        _entity(text, "Beispiel GmbH", EntityType.ORGANISATION),
    ]


def test_redact_replaces_with_bracketed_type() -> None:
    result = anonymize(SENTENCE, _person_and_org(SENTENCE), mode="redact")
    assert result.text == "[PERSON] arbeitet bei der [ORGANISATION]."


def test_replace_uses_type_name() -> None:
    result = anonymize(SENTENCE, _person_and_org(SENTENCE), mode="replace")
    assert result.text == "PERSON arbeitet bei der ORGANISATION."


def test_pseudonymize_is_stable_within_session() -> None:
    session = Pseudonymizer()
    first = anonymize(SENTENCE, _person_and_org(SENTENCE), mode="pseudonymize", session=session)
    second = anonymize(SENTENCE, _person_and_org(SENTENCE), mode="pseudonymize", session=session)
    assert first.text == "PERSON_001 arbeitet bei der ORGANISATION_001."
    assert second.text == first.text


def test_pseudonymize_counts_per_type() -> None:
    session = Pseudonymizer()
    text = "Max Mustermann und Erika Musterfrau."
    entities = [
        _entity(text, "Max Mustermann", EntityType.PERSON),
        _entity(text, "Erika Musterfrau", EntityType.PERSON),
    ]
    result = anonymize(text, entities, mode="pseudonymize", session=session)
    assert result.text == "PERSON_001 und PERSON_002."


def test_mask_keeps_edges() -> None:
    text = "IBAN DE89 3704 0044 0532 0130 00"
    entity = _entity(text, "DE89 3704 0044 0532 0130 00", EntityType.DE_IBAN)
    result = anonymize(text, [entity], mode="mask")
    assert result.text == "IBAN DE89 **** **** **** **** 00"


def test_hash_is_deterministic_with_same_key() -> None:
    entities = _person_and_org(SENTENCE)
    first = anonymize(SENTENCE, entities, mode="hash", key="geheim")
    second = anonymize(SENTENCE, entities, mode="hash", key="geheim")
    assert first.text == second.text
    assert "Max Mustermann" not in first.text


def test_hash_differs_with_other_key() -> None:
    entities = _person_and_org(SENTENCE)
    first = anonymize(SENTENCE, entities, mode="hash", key="eins")
    second = anonymize(SENTENCE, entities, mode="hash", key="zwei")
    assert first.text != second.text


def test_multiple_entities_keep_offsets_valid() -> None:
    text = "IBAN DE89 3704 0044 0532 0130 00, E-Mail max@example.de."
    entities = [
        _entity(text, "DE89 3704 0044 0532 0130 00", EntityType.DE_IBAN),
        _entity(text, "max@example.de", EntityType.EMAIL),
    ]
    result = anonymize(text, entities, mode="redact")
    assert result.text == "IBAN [DE_IBAN], E-Mail [EMAIL]."


def test_mapping_is_reported() -> None:
    result = anonymize(SENTENCE, _person_and_org(SENTENCE), mode="redact")
    assert result.mapping["Max Mustermann"] == "[PERSON]"
    assert result.mapping["Beispiel GmbH"] == "[ORGANISATION]"


def test_entities_are_returned() -> None:
    result = anonymize(SENTENCE, _person_and_org(SENTENCE), mode="redact")
    assert len(result.entities) == 2


def test_anonymize_detects_when_entities_omitted() -> None:
    text = "Bitte an DE89 3704 0044 0532 0130 00 überweisen."
    result = anonymize(text, mode="redact")
    assert result.text == "Bitte an [DE_IBAN] überweisen."


def test_mode_accepts_string() -> None:
    result = anonymize(SENTENCE, _person_and_org(SENTENCE), mode=AnonymizeMode.REDACT)
    assert result.text.startswith("[PERSON]")
