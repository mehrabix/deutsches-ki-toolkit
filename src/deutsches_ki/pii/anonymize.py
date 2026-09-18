"""Anonymisieren und Pseudonymisieren deutscher Texte.

Die Anonymisierung sitzt in der Verarbeitungskette, nicht am Ende: Texte
werden bereinigt, bevor sie ein Embedding-Modell oder ein Sprachmodell sehen.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from deutsches_ki.core.enums import AnonymizeMode, EntityType
from deutsches_ki.core.models import Entity
from deutsches_ki.pii.detect import detect

__all__ = ["AnonymizeResult", "Pseudonymizer", "anonymize"]

_MASK_KEEP_HEAD = 4
_MASK_KEEP_TAIL = 2
_HASH_LENGTH = 12


class Pseudonymizer:
    """Vergibt innerhalb einer Sitzung stabile Kennungen je Entitätstyp.

    „Max Mustermann“ wird immer zu ``PERSON_001``, solange dieselbe Sitzung
    verwendet wird.
    """

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._assigned: dict[tuple[str, str], str] = {}

    def pseudonym(self, entity_type: EntityType | str, value: str) -> str:
        """Gibt die stabile Kennung für einen Wert zurück."""
        type_name = entity_type.value if isinstance(entity_type, EntityType) else str(entity_type)
        key = (type_name, value)
        assigned = self._assigned.get(key)
        if assigned is not None:
            return assigned
        self._counters[type_name] = self._counters.get(type_name, 0) + 1
        assigned = f"{type_name}_{self._counters[type_name]:03d}"
        self._assigned[key] = assigned
        return assigned


class AnonymizeResult(BaseModel):
    """Ergebnis einer Anonymisierung samt Zuordnung."""

    model_config = ConfigDict(extra="forbid")

    text: str
    mapping: dict[str, str] = Field(default_factory=dict)
    entities: list[Entity] = Field(default_factory=list)


def _mask(value: str) -> str:
    if len(value) <= _MASK_KEEP_HEAD + _MASK_KEEP_TAIL:
        return "*" * len(value)
    head = value[:_MASK_KEEP_HEAD]
    tail = value[-_MASK_KEEP_TAIL:]
    middle = "".join(
        " " if char.isspace() else "*" for char in value[_MASK_KEEP_HEAD:-_MASK_KEEP_TAIL]
    )
    return f"{head}{middle}{tail}"


def _hash(value: str, key: str | None) -> str:
    salt = key.encode("utf-8") if key else b""
    digest = hashlib.sha256(salt + value.encode("utf-8")).hexdigest()[:_HASH_LENGTH]
    return f"HASH_{digest}"


def _replacement(
    entity: Entity,
    mode: AnonymizeMode,
    key: str | None,
    session: Pseudonymizer,
) -> str:
    if mode is AnonymizeMode.REDACT:
        return f"[{entity.type.value}]"
    if mode is AnonymizeMode.REPLACE:
        return entity.type.value
    if mode is AnonymizeMode.MASK:
        return _mask(entity.text)
    if mode is AnonymizeMode.HASH:
        return _hash(entity.text, key)
    return session.pseudonym(entity.type, entity.text)


def anonymize(
    text: str,
    entities: Iterable[Entity] | None = None,
    mode: AnonymizeMode | str = AnonymizeMode.REDACT,
    *,
    key: str | None = None,
    session: Pseudonymizer | None = None,
    language: str = "de",
) -> AnonymizeResult:
    """Ersetzt sensible Stellen je nach Betriebsart.

    Die Kennungen werden in Leserichtung vergeben (der erste Name wird
    ``PERSON_001``) und die Ersetzungen danach von rechts nach links
    eingesetzt, damit die Positionen der übrigen Treffer gültig bleiben.
    """
    resolved_mode = AnonymizeMode(mode)
    resolved = list(entities) if entities is not None else detect(text, language=language)
    ordered = [
        entity
        for entity in sorted(resolved, key=lambda item: (item.start, item.end))
        if 0 <= entity.start < entity.end <= len(text)
    ]
    active_session = session if session is not None else Pseudonymizer()

    replacements = [_replacement(entity, resolved_mode, key, active_session) for entity in ordered]

    mapping: dict[str, str] = {}
    result = text
    for entity, replacement in reversed(list(zip(ordered, replacements, strict=True))):
        mapping[entity.text] = replacement
        result = result[: entity.start] + replacement + result[entity.end :]

    return AnonymizeResult(text=result, mapping=mapping, entities=ordered)
