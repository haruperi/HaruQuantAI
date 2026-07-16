"""Convert supported values to deterministic JSON-safe representations.

Canonical serialization is pure and intentionally performs no redaction.
Callers must redact sensitive evidence before invoking this module.
"""

import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from app.utils.errors.exceptions import ValidationError

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)

_MAX_DEPTH = 32
_MAX_ITEMS = 10_000


def _format_datetime(value: datetime) -> str:
    """Format an aware UTC datetime for canonical JSON.

    Args:
        value: Candidate datetime.

    Returns:
        ISO 8601 text with six fractional digits and a ``Z`` suffix.

    Raises:
        ValidationError: The datetime is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValidationError("SERIALIZATION_DATETIME_INVALID")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _convert(  # noqa: C901, PLR0911, PLR0912
    value: object,
    *,
    depth: int,
    active: set[int],
    item_count: list[int],
) -> JsonValue:
    """Recursively convert one supported value under traversal bounds.

    Args:
        value: Candidate value at the current traversal node.
        depth: Current nesting depth, starting at zero.
        active: Identities of containers on the active recursion path.
        item_count: Shared single-element aggregate container-item counter.

    Returns:
        A deterministic JSON-safe scalar, list, or mapping.

    Raises:
        ValidationError: The value is unsupported, non-finite, cyclic, has an
            invalid key or datetime, or exceeds a traversal bound.
    """
    if depth > _MAX_DEPTH:
        raise ValidationError("SERIALIZATION_DEPTH_EXCEEDED")
    if isinstance(value, Enum):
        return _convert(
            value.value,
            depth=depth + 1,
            active=active,
            item_count=item_count,
        )
    if value is None or isinstance(value, bool | str | int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValidationError("SERIALIZATION_NON_FINITE")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValidationError("SERIALIZATION_NON_FINITE")
        return format(value, "f")
    if isinstance(value, datetime):
        return _format_datetime(value)

    object_id = id(value)
    if object_id in active:
        raise ValidationError("SERIALIZATION_CYCLE_DETECTED")
    if is_dataclass(value) and not isinstance(value, type):
        active.add(object_id)
        try:
            dataclass_fields = fields(value)
            _add_items(item_count, len(dataclass_fields))
            return {
                field.name: _convert(
                    getattr(value, field.name),
                    depth=depth + 1,
                    active=active,
                    item_count=item_count,
                )
                for field in dataclass_fields
            }
        finally:
            active.remove(object_id)
    if isinstance(value, Mapping):
        active.add(object_id)
        try:
            _add_items(item_count, len(value))
            converted: dict[str, JsonValue] = {}
            for key, nested in value.items():
                if not isinstance(key, str):
                    raise ValidationError("SERIALIZATION_KEY_INVALID")
                converted[key] = _convert(
                    nested,
                    depth=depth + 1,
                    active=active,
                    item_count=item_count,
                )
            return converted
        finally:
            active.remove(object_id)
    if isinstance(value, list | tuple):
        active.add(object_id)
        try:
            _add_items(item_count, len(value))
            return [
                _convert(
                    item,
                    depth=depth + 1,
                    active=active,
                    item_count=item_count,
                )
                for item in value
            ]
        finally:
            active.remove(object_id)
    raise ValidationError("SERIALIZATION_TYPE_UNSUPPORTED")


def _add_items(item_count: list[int], amount: int) -> None:
    """Add visited container items to the traversal counter.

    Args:
        item_count: Single-element aggregate counter for one conversion.
        amount: Number of newly visited items.

    Raises:
        ValidationError: The aggregate item limit is exceeded.
    """
    item_count[0] += amount
    if item_count[0] > _MAX_ITEMS:
        raise ValidationError("SERIALIZATION_ITEMS_EXCEEDED")


def to_json_safe(value: object) -> JsonValue:
    """Convert a supported value to deterministic JSON-safe data.

    Args:
        value: Supported scalar, enum, datetime, decimal, dataclass, mapping,
            list, or tuple.

    Returns:
        A newly constructed JSON-safe value with deterministic conversions.

    Raises:
        ValidationError: The value is unsupported, unsafe, cyclic, non-finite,
            or exceeds a conversion bound.
    """
    return _convert(value, depth=0, active=set(), item_count=[0])


def canonical_json(value: object) -> str:
    """Produce stable sorted-key UTF-8 JSON without hidden redaction.

    Args:
        value: Any value accepted by ``to_json_safe``.

    Returns:
        Compact Unicode JSON with sorted keys and deterministic separators.

    Raises:
        ValidationError: Conversion or UTF-8 JSON encoding fails.
    """
    try:
        encoded = json.dumps(
            to_json_safe(value),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValidationError("SERIALIZATION_ENCODING_FAILED") from error
    return encoded
