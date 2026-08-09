"""Validated JSON-safe LiquiditySnapshot v1 transport."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)

_SCHEMA = "indicators.liquidity_snapshot.v1"
_FIELDS = {
    "schema",
    "observed_at",
    "spread",
    "executable_depth",
    "imbalance",
    "volume",
    "fill_probability",
    "regime",
    "complete",
}


def _validate_timestamp(value: object) -> None:
    """Validate canonical UTC liquidity time.

    Args:
        value: Candidate timestamp text.

    Raises:
        IndicatorError: If the timestamp is invalid or not UTC.
    """
    if not isinstance(value, str) or not value.endswith("Z"):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT, "liquidity time is invalid"
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT, "liquidity time is invalid"
        ) from error
    if parsed.utcoffset() != UTC.utcoffset(parsed):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_TIMEZONE, "liquidity time must be UTC"
        )


def _validate_numeric(value: Mapping[str, object]) -> None:
    """Validate liquidity numeric fields.

    Args:
        value: Candidate snapshot mapping.

    Raises:
        IndicatorError: If a numeric field violates its bounds.
    """
    numeric = ("spread", "executable_depth", "imbalance", "volume")
    for field in numeric:
        number = value[field]
        if (
            isinstance(number, bool)
            or not isinstance(number, int | float)
            or not math.isfinite(float(number))
        ):
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_SNAPSHOT,
                "liquidity value is invalid",
                {"field": field},
            )
    if any(
        float(cast("float", value[field])) < 0.0
        for field in ("spread", "executable_depth", "volume")
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "liquidity values must be non-negative",
        )
    if not -1.0 <= float(cast("float", value["imbalance"])) <= 1.0:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "liquidity imbalance is out of bounds",
        )


def _validate_optional(value: Mapping[str, object]) -> None:
    """Validate optional probability and state fields.

    Args:
        value: Candidate snapshot mapping.

    Raises:
        IndicatorError: If an optional or state field is invalid.
    """
    probability = value["fill_probability"]
    if probability is not None and (
        isinstance(probability, bool)
        or not isinstance(probability, int | float)
        or not math.isfinite(float(probability))
        or not 0.0 <= float(probability) <= 1.0
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT, "fill probability is invalid"
        )
    if not isinstance(value["regime"], str) or not value["regime"]:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT, "liquidity regime is invalid"
        )
    if not isinstance(value["complete"], bool):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT, "liquidity completeness is invalid"
        )


def _validated(value: Mapping[str, object]) -> dict[str, Any]:
    """Validate and detach one liquidity snapshot.

    Args:
        value: Candidate snapshot mapping.

    Returns:
        Detached JSON-safe mapping.

    Raises:
        IndicatorError: If fields, values, or time are invalid.
    """
    if set(value) != _FIELDS or value.get("schema") != _SCHEMA:
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_SNAPSHOT,
            "liquidity snapshot fields or schema are invalid",
        )
    _validate_timestamp(value["observed_at"])
    _validate_numeric(value)
    _validate_optional(value)
    numeric = ("spread", "executable_depth", "imbalance", "volume")
    probability = value["fill_probability"]
    detached = dict(value)
    for field in numeric:
        detached[field] = float(cast("float", value[field]))
    detached["fill_probability"] = (
        None if probability is None else float(cast("float", probability))
    )
    canonical_json(detached, max_items=None)
    return detached


@guard_public_boundary
def build_liquidity_snapshot(
    *,
    observed_at: datetime,
    spread: float,
    executable_depth: float,
    imbalance: float,
    volume: float,
    fill_probability: float | None,
    regime: str,
    complete: bool,
) -> Mapping[str, Any]:
    """Build a validated LiquiditySnapshot v1 mapping.

    Args:
        observed_at: Observation time in aware UTC.
        spread: Supplied non-negative spread.
        executable_depth: Supplied non-negative executable depth.
        imbalance: Supplied bounded imbalance from minus one to one.
        volume: Supplied non-negative volume.
        fill_probability: Supplied probability, or null when unavailable.
        regime: Caller-derived explicit liquidity regime.
        complete: Whether every required input was available.

    Returns:
        Validated detached JSON-safe mapping.

    Raises:
        IndicatorError: If the supplied evidence is invalid.
    """
    logger.info("Building LiquiditySnapshot v1")
    if observed_at.tzinfo is None or observed_at.utcoffset() != UTC.utcoffset(
        observed_at
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_TIMEZONE, "liquidity time must be aware UTC"
        )
    return _validated(
        {
            "schema": _SCHEMA,
            "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
            "spread": spread,
            "executable_depth": executable_depth,
            "imbalance": imbalance,
            "volume": volume,
            "fill_probability": fill_probability,
            "regime": regime,
            "complete": complete,
        }
    )


@guard_public_boundary
def parse_liquidity_snapshot(value: Mapping[str, object]) -> Mapping[str, Any]:
    """Parse one LiquiditySnapshot v1 mapping.

    Args:
        value: Candidate JSON-safe mapping.

    Returns:
        Validated detached JSON-safe mapping.

    Raises:
        IndicatorError: If the supplied evidence is invalid.
    """
    logger.info("Parsing LiquiditySnapshot v1")
    return _validated(value)


__all__ = ["build_liquidity_snapshot", "parse_liquidity_snapshot"]
