"""Versioned hash-derived deterministic random streams."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.kernel.errors import ValidationError
from app.kernel.serialization import canonical_json

_VERSION = "v1"
_MAX_DECIMAL_PLACES = 28


def derive_random_stream(master_seed: int, stream_name: str) -> dict[str, object]:
    """Derive a named stream independently of construction order.

    Args:
        master_seed: Explicit integer master seed.
        stream_name: Stable stream name.

    Returns:
        Initial stream state.

    Raises:
        ValidationError: If seed or name is invalid.
    """
    if (
        isinstance(master_seed, bool)
        or not isinstance(master_seed, int)
        or not stream_name
        or stream_name != stream_name.strip()
    ):
        raise ValidationError("RANDOM_STREAM_INVALID")
    return {
        "master_seed": master_seed,
        "stream_name": stream_name,
        "algorithm_version": _VERSION,
        "draw_index": 0,
    }


def _draw(stream: Mapping[str, object]) -> tuple[int, dict[str, object]]:
    """Derive one integer draw and return an advanced stream.

    Args:
        stream: Current stream state.

    Returns:
        Integer draw and advanced state.

    Raises:
        ValidationError: If state is malformed.
    """
    required = {"master_seed", "stream_name", "algorithm_version", "draw_index"}
    draw_index = stream.get("draw_index")
    if (
        set(stream) != required
        or stream.get("algorithm_version") != _VERSION
        or not isinstance(stream.get("master_seed"), int)
        or not isinstance(stream.get("stream_name"), str)
        or not isinstance(draw_index, int)
        or isinstance(draw_index, bool)
        or draw_index < 0
    ):
        raise ValidationError("RANDOM_STREAM_INVALID")
    material = canonical_json(dict(stream)).encode("utf-8")
    number = int.from_bytes(hashlib.sha256(material).digest(), "big")
    advanced = dict(stream)
    advanced["draw_index"] = draw_index + 1
    return number, advanced


def next_uniform(
    stream: Mapping[str, object],
    *,
    lower: Decimal | int | str = Decimal(0),
    upper: Decimal | int | str = Decimal(1),
    decimal_places: int = 18,
) -> tuple[str, dict[str, object]]:
    """Return an exact bounded uniform decimal and advanced stream.

    Args:
        stream: Current stream state.
        lower: Inclusive lower bound.
        upper: Exclusive upper bound.
        decimal_places: Exact output precision.

    Returns:
        Decimal text and advanced state.

    Raises:
        ValidationError: If bounds are invalid.
    """
    low, high = Decimal(lower), Decimal(upper)
    if (
        not low.is_finite()
        or not high.is_finite()
        or low >= high
        or not 1 <= decimal_places <= _MAX_DECIMAL_PLACES
    ):
        raise ValidationError("RANDOM_BOUNDS_INVALID")
    number, advanced = _draw(stream)
    scale = 10**decimal_places
    fraction = Decimal(number % scale) / Decimal(scale)
    value = low + (high - low) * fraction
    return format(value, f".{decimal_places}f"), advanced


def next_int(
    stream: Mapping[str, object], *, lower: int, upper: int
) -> tuple[int, dict[str, object]]:
    """Return a bounded inclusive integer and advanced stream.

    Args:
        stream: Current stream state.
        lower: Inclusive lower bound.
        upper: Exclusive upper bound.

    Returns:
        Integer draw and advanced state.

    Raises:
        ValidationError: If bounds are invalid.
    """
    if isinstance(lower, bool) or isinstance(upper, bool) or lower > upper:
        raise ValidationError("RANDOM_BOUNDS_INVALID")
    number, advanced = _draw(stream)
    return lower + number % (upper - lower + 1), advanced


def next_choice(
    stream: Mapping[str, object],
    choices: Sequence[str],
    *,
    weights: Sequence[int] | None = None,
) -> tuple[str, dict[str, object]]:
    """Return a deterministic weighted choice and advanced stream.

    Args:
        stream: Current stream state.
        choices: Non-empty choices.
        weights: Optional positive integer weights.

    Returns:
        Selected choice and advanced state.

    Raises:
        ValidationError: If choices or weights are invalid.
        AssertionError: If validated weights cannot resolve.
    """
    if not choices or any(not choice for choice in choices):
        raise ValidationError("RANDOM_CHOICES_INVALID")
    active_weights = tuple(weights) if weights is not None else (1,) * len(choices)
    if len(active_weights) != len(choices) or any(
        isinstance(weight, bool) or weight <= 0 for weight in active_weights
    ):
        raise ValidationError("RANDOM_WEIGHTS_INVALID")
    number, advanced = _draw(stream)
    offset = number % sum(active_weights)
    for choice, weight in zip(choices, active_weights, strict=True):
        if offset < weight:
            return choice, advanced
        offset -= weight
    raise AssertionError("weighted selection must resolve")


def get_stream_identity(stream: Mapping[str, object]) -> dict[str, object]:
    """Return detached replay identity for a validated stream.

    Args:
        stream: Current stream state.

    Returns:
        Detached replay identity.
    """
    _draw(stream)
    return dict(stream)
