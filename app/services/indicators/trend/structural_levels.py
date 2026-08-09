"""Causal support, resistance, and structural-level projection."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import cast

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import get_logger

logger = get_logger(__name__)


@guard_public_boundary
def project_structural_levels(
    observations: Sequence[Mapping[str, object]], *, decision_time: datetime
) -> tuple[Mapping[str, object], ...]:
    """Validate and order causal structural-level observations.

    Args:
        observations: Level mappings containing kind, price, observed_at, and
            invalidation_price.
        decision_time: Point-in-time upper boundary.

    Returns:
        Timestamp- and kind-ordered detached level mappings.

    Raises:
        IndicatorError: If evidence is malformed, non-finite, or future-dated.
    """
    logger.info("Projecting structural levels")
    if decision_time.tzinfo is None or decision_time.utcoffset() != UTC.utcoffset(
        decision_time
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_TIMEZONE,
            "structural-level decision time must be aware UTC",
        )
    projected: list[Mapping[str, object]] = []
    for observation in observations:
        if set(observation) != {"kind", "price", "observed_at", "invalidation_price"}:
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA,
                "structural-level fields are invalid",
            )
        kind = observation["kind"]
        observed_at = observation["observed_at"]
        price = observation["price"]
        invalidation = observation["invalidation_price"]
        if not isinstance(kind, str) or not kind:
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA, "level kind is invalid"
            )
        if not isinstance(observed_at, datetime) or observed_at.tzinfo is None:
            raise IndicatorError(
                IndicatorErrorCode.IND_INVALID_TIMEZONE, "level time must be aware UTC"
            )
        if (
            observed_at.utcoffset() != UTC.utcoffset(observed_at)
            or observed_at > decision_time
        ):
            raise IndicatorError(
                IndicatorErrorCode.IND_LOOKAHEAD_RISK,
                "structural level is future-dated",
            )
        if any(
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(float(value))
            for value in (price, invalidation)
        ):
            raise IndicatorError(
                IndicatorErrorCode.IND_UNSUPPORTED_DTYPE, "level prices must be finite"
            )
        projected.append(
            {
                "kind": kind,
                "price": float(cast("float", price)),
                "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
                "invalidation_price": float(cast("float", invalidation)),
            }
        )
    return tuple(
        sorted(
            projected, key=lambda item: (str(item["observed_at"]), str(item["kind"]))
        )
    )


__all__ = ["project_structural_levels"]
