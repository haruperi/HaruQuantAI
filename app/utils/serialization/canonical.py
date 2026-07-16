"""Deterministic JSON-safe conversion and canonical JSON serialization."""

from __future__ import annotations

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
    """Format datetime timezone-aware UTC datetime.

    Args:
        value: Datetime object to format.

    Returns:
        ISO 8601 string representation of the datetime.

    Raises:
        ValidationError: If the datetime is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValidationError("SERIALIZATION_DATETIME_INVALID")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _convert(  # noqa: C901, PLR0911, PLR0912 - bounded recursive type dispatch.
    value: object,
    *,
    depth: int,
    active: set[int],
    item_count: list[int],
) -> JsonValue:
    """Recursively convert supported python values to JSON-safe primitives.

    Args:
        value: Python object to convert.
        depth: Current recursion depth.
        active: Set of current parent object IDs for cycle detection.
        item_count: Aggregate item counter.

    Returns:
        JSON-safe primitive value.

    Raises:
        ValidationError: If nesting depth, item limit constraints, type
            restrictions are violated, or a cycle is detected.
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
            item_count[0] += len(dataclass_fields)
            if item_count[0] > _MAX_ITEMS:
                raise ValidationError("SERIALIZATION_ITEMS_EXCEEDED")
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
            item_count[0] += len(value)
            if item_count[0] > _MAX_ITEMS:
                raise ValidationError("SERIALIZATION_ITEMS_EXCEEDED")
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
            item_count[0] += len(value)
            if item_count[0] > _MAX_ITEMS:
                raise ValidationError("SERIALIZATION_ITEMS_EXCEEDED")
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


def to_json_safe(value: object) -> JsonValue:
    """Convert a supported value to deterministic JSON-safe data.

    Args:
        value: Supported value to convert.

    Returns:
        JSON-safe data.

    Raises:
        ValidationError: If the value is unsupported, cyclic, or unsafe.
    """
    return _convert(value, depth=0, active=set(), item_count=[0])


def canonical_json(value: object) -> str:
    """Produce stable sorted-key UTF-8 JSON without hidden redaction.

    Args:
        value: Supported value to serialize.

    Returns:
        Canonical JSON text.

    Raises:
        ValidationError: If conversion or JSON encoding fails.
    """
    safe_value = to_json_safe(value)
    try:
        encoded = json.dumps(
            safe_value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ValidationError("SERIALIZATION_ENCODING_FAILED") from error
    return encoded
