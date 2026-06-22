"""Shared private helpers for the Analytics service.

This module centralises the three utilities that were previously copy-pasted
across every analytics sub-module:

* ``validate_request_id_strict`` – strict ``request_id`` validation.
* ``to_float_list``              – convert any numeric series to ``list[float]``.
* ``to_trade_list``              – coerce trade inputs to ``list[dict]``.
* ``parse_utc_time``             – parse any timestamp to a UTC-aware
                                   ``datetime`` (never naive).

All helpers are internal (leading-underscore callers use the raw names here).
Nothing in this module performs I/O, network calls, database mutations, or
trading side effects.

Side effects:
    None.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from app.utils.errors import ValidationError


def validate_request_id_strict(request_id: str | None) -> None:
    """Raise ``ValidationError`` when ``request_id`` is present but invalid.

    ``None`` is accepted (the field is optional).  A non-``None`` value must
    be a non-empty, non-whitespace string.

    Args:
        request_id: Caller-supplied trace identifier or ``None``.

    Raises:
        ValidationError: If ``request_id`` is not ``None`` and is either not
            a ``str`` or contains only whitespace.

    Side effects:
        None.
    """
    if request_id is None:
        return
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValidationError(
            "request_id must be a non-empty string when supplied."
        )


def to_float_list(series: Any) -> list[float]:
    """Convert a numeric series to a plain ``list[float]``.

    Accepts NumPy arrays, pandas Series (anything with ``.tolist()``), plain
    Python lists, and ``None`` (returns empty list).

    Args:
        series: Numeric sequence, array-like, or ``None``.

    Returns:
        A new ``list[float]``.  Returns ``[]`` for ``None`` or unsupported
        types.

    Side effects:
        None.
    """
    if series is None:
        return []
    if hasattr(series, "tolist"):
        return cast("list[float]", series.tolist())
    if isinstance(series, list):
        return [float(x) for x in series]
    return []


def to_trade_list(trades: Any) -> list[dict[str, Any]]:
    """Coerce various trade-input types to a ``list[dict]``.

    Supports:
    * ``None``              → empty list.
    * pandas ``DataFrame``  → ``records`` dict list via ``.to_dict``.
    * ``list[dict]``        → returned as-is (each element is a copy-reference).
    * ``list[Pydantic]``    → each item converted via ``.model_dump()``.
    * ``list[object]``      → each item converted via ``.__dict__`` or ``dict()``.

    Args:
        trades: Trade records in any supported format.

    Returns:
        A ``list`` of ``dict`` trade records.

    Side effects:
        None.
    """
    if trades is None:
        return []
    if hasattr(trades, "to_dict"):
        return cast(
            "list[dict[str, Any]]",
            trades.to_dict("records"),
        )
    if isinstance(trades, list):
        result: list[dict[str, Any]] = []
        for item in trades:
            if isinstance(item, dict):
                result.append(item)
            elif hasattr(item, "model_dump"):
                result.append(item.model_dump())
            elif hasattr(item, "__dict__"):
                result.append(item.__dict__)
            else:
                result.append(dict(item))
        return result
    return []


def parse_utc_time(t_val: Any) -> datetime | None:
    """Parse any timestamp representation to a UTC-aware ``datetime``.

    Never returns a timezone-naive ``datetime``.  Returns ``None`` when the
    input cannot be parsed.

    Supported input types:
    * ``datetime``  – returned as-is when already timezone-aware; localised
                      to UTC when naive.
    * ``str``       – parsed via ``datetime.fromisoformat``; ``"Z"`` suffix
                      is rewritten to ``"+00:00"``.
    * ``int|float`` – interpreted as a POSIX timestamp in UTC.

    Args:
        t_val: Timestamp in any supported representation.

    Returns:
        A UTC-aware ``datetime``, or ``None`` if parsing fails.

    Side effects:
        None.
    """
    if isinstance(t_val, datetime):
        if t_val.tzinfo is None:
            return t_val.replace(tzinfo=UTC)
        return t_val.astimezone(UTC)
    if isinstance(t_val, str):
        try:
            normalised = t_val.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalised)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except (ValueError, AttributeError):
            return None
    if isinstance(t_val, (int, float)):
        try:
            return datetime.fromtimestamp(float(t_val), tz=UTC)
        except (OSError, OverflowError, ValueError):
            return None
    return None
