"""Bounded pattern-evidence projection."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import get_logger

logger = get_logger(__name__)
_MAX_PATTERNS = 16


@guard_public_boundary
def build_chart_pattern_evidence(
    patterns: Mapping[str, int], *, observed_at: datetime
) -> Mapping[str, object]:
    """Build bounded non-authorizing evidence from official pattern labels.

    Args:
        patterns: Official pattern names mapped to labels in minus one, zero,
            or one.
        observed_at: Aware UTC observation time.

    Returns:
        Ordered labels with explicit non-authorizing semantics.

    Raises:
        IndicatorError: If the timestamp or labels are invalid.
    """
    logger.info("Building chart-pattern evidence")
    if observed_at.tzinfo is None or observed_at.utcoffset() != UTC.utcoffset(
        observed_at
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_TIMEZONE, "pattern time must be aware UTC"
        )
    if (
        not patterns
        or len(patterns) > _MAX_PATTERNS
        or any(
            not isinstance(name, str)
            or not name
            or isinstance(label, bool)
            or label not in {-1, 0, 1}
            for name, label in patterns.items()
        )
    ):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA, "pattern evidence is invalid"
        )
    return {
        "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "patterns": dict(sorted(patterns.items())),
        "authorizes_trade": False,
    }


__all__ = ["build_chart_pattern_evidence"]
