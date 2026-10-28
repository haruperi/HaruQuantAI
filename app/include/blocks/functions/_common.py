"""Shared constants, registries, and numerical helpers for function building blocks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.host.logging import get_logger
from app.include.blocks.series import resolve_shift_value

logger = get_logger(__name__)

__all__ = [
    "DATE_MONTH_MULTIPLIER",
    "DATE_YEAR_MULTIPLIER",
    "DEFAULT_PIP_SIZE",
    "FLOAT_MAX_VALUE",
    "MIN_RANK_PERIOD",
    "POINT_3_DIGIT",
    "POINT_5_DIGIT",
    "POINT_TOLERANCE",
    "POINT_TO_PIP_MULTIPLIER",
    "TIME_HOUR_MULTIPLIER",
    "TIME_MINUTE_MULTIPLIER",
    "_CUSTOM_REGISTRY",
    "register_custom_function",
    "resolve_pip_size",
    "resolve_shift_value",
]

FLOAT_MAX_VALUE: float = 1.7976931348623157e308
DEFAULT_PIP_SIZE: float = 0.0001
MIN_RANK_PERIOD: int = 2
DATE_YEAR_MULTIPLIER: int = 10000
DATE_MONTH_MULTIPLIER: int = 100
TIME_HOUR_MULTIPLIER: int = 10000
TIME_MINUTE_MULTIPLIER: int = 100
POINT_TO_PIP_MULTIPLIER: float = 10.0
POINT_TOLERANCE: float = 1e-9
POINT_5_DIGIT: float = 1e-5
POINT_3_DIGIT: float = 1e-3

_CUSTOM_REGISTRY: dict[str, Callable[..., Any]] = {}


def resolve_pip_size(
    point: float | None = None,
    digits: int | None = None,
    pip_size: float | None = None,
) -> float:
    """Resolve effective pip size from point, digits, or explicit pip size.

    Scaling logic:
    - If pip_size > 0 is provided, uses it directly.
    - If point is provided: for 3-digit and 5-digit broker quotes,
      pip size = point * 10.0; for others, pip size = point.
    - Defaults to standard Forex pip size 0.0001.

    Args:
        point: Instrument minimum price point (e.g. from symbol.Point()).
        digits: Quote precision digits (e.g. from symbol.Digits()).
        pip_size: Explicit override pip size.

    Returns:
        Effective pip size as float.
    """
    if pip_size is not None and pip_size > 0.0:
        return float(pip_size)

    if point is not None and point > 0.0:
        is_scaled_digits = digits in (3, 5)
        is_scaled_point = (
            abs(point - POINT_5_DIGIT) < POINT_TOLERANCE
            or abs(point - POINT_3_DIGIT) < POINT_TOLERANCE
        )
        if is_scaled_digits or (digits is None and is_scaled_point):
            return float(point * POINT_TO_PIP_MULTIPLIER)
        return float(point)

    return DEFAULT_PIP_SIZE


def register_custom_function(name: str, handler: Callable[..., Any]) -> None:
    """Register custom function handler for CustomFunction block evaluation.

    Args:
        name: Unique function identifier.
        handler: Callable implementing the function.
    """
    _CUSTOM_REGISTRY[name] = handler
    logger.debug("FR-SERVICES-FUNCTION-CUSTOM: registered '%s'", name)
