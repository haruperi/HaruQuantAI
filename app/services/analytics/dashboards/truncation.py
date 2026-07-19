"""Deterministic bounded time-series projection for Analytics dashboards."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.utils import logger

DASHBOARD_MAX_POINTS = 5000
DASHBOARD_TRUNCATION_POLICY = "min_max_per_bucket"


def _point_value(point: Mapping[str, object]) -> float:
    """Extract the single finite numeric value from a dashboard point.

    Args:
        point: Candidate timestamped series point.

    Returns:
        Finite numeric value used only for selection.

    Raises:
        AnalyticsValidationError: If the point has no unambiguous finite value.
    """
    logger.debug("Extracting Analytics dashboard point value")
    value = next(
        (point[key] for key in ("value", "equity", "drawdown") if key in point),
        None,
    )
    if not isinstance(value, (int, float, Decimal)) or isinstance(value, bool):
        raise AnalyticsValidationError(
            "dashboard point requires a finite value, equity, or drawdown ordinate"
        )
    if isinstance(value, Decimal):
        finite = value.is_finite()
    else:
        finite = math.isfinite(float(value))
    if not finite:
        raise AnalyticsValidationError("dashboard point value must be finite")
    return float(value)


def _validated_points(
    points: object,
) -> tuple[tuple[Mapping[str, object], ...], tuple[float, ...]]:
    """Validate an ordered immutable UTC dashboard series.

    Args:
        points: Candidate timestamped points.

    Returns:
        Copied point mappings and their finite selection values.

    Raises:
        AnalyticsValidationError: If shape, timestamps, or ordering is invalid.
    """
    logger.debug("Validating Analytics dashboard series")
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes, bytearray)):
        raise AnalyticsValidationError("dashboard points must be a sequence")
    if not points:
        raise AnalyticsValidationError("dashboard points must not be empty")
    copied: list[Mapping[str, object]] = []
    values: list[float] = []
    previous: datetime | None = None
    for point in points:
        if not isinstance(point, Mapping):
            raise AnalyticsValidationError("dashboard point must be a mapping")
        timestamp = point.get("timestamp")
        if (
            not isinstance(timestamp, datetime)
            or timestamp.tzinfo is None
            or timestamp.utcoffset() != timedelta(0)
            or (previous is not None and timestamp <= previous)
        ):
            raise AnalyticsValidationError(
                "dashboard timestamps must be unique ordered UTC"
            )
        copied.append(dict(point))
        values.append(_point_value(point))
        previous = timestamp
    return tuple(copied), tuple(values)


def _bucket_candidates(
    available: tuple[int, ...],
    values: tuple[float, ...],
    slots: int,
) -> tuple[int, ...]:
    """Select deterministic per-bucket minima and maxima.

    Args:
        available: Unpreserved source indices.
        values: Values aligned with the complete source series.
        slots: Remaining output capacity.

    Returns:
        Priority-ordered additional source indices.
    """
    logger.debug("Selecting Analytics dashboard min/max buckets")
    if slots <= 0 or not available:
        return ()
    bucket_count = max(1, min(len(available), math.ceil(slots / 2)))
    selected: list[int] = []
    for bucket_index in range(bucket_count):
        start = bucket_index * len(available) // bucket_count
        end = (bucket_index + 1) * len(available) // bucket_count
        bucket = available[start:end]
        minimum = min(bucket, key=lambda index: (values[index], index))
        maximum = max(bucket, key=lambda index: (values[index], -index))
        for index in (minimum, maximum):
            if index not in selected and len(selected) < slots:
                selected.append(index)
    if len(selected) < slots:
        selected.extend(index for index in available if index not in selected)
    return tuple(selected[:slots])


def truncate_series(
    points: Sequence[Mapping[str, object]],
    *,
    max_points: int,
) -> tuple[tuple[Mapping[str, object], ...], Mapping[str, object]]:
    """Bound a series while preserving endpoints, extrema, and warning points.

    Args:
        points: Ordered UTC time-series points with one finite numeric value each.
        max_points: Positive output ceiling no greater than the approved maximum.

    Returns:
        Selected original points and complete truncation metadata.

    Raises:
        AnalyticsValidationError: If validation or mandatory preservation fails.
    """
    logger.info("Truncating Analytics dashboard series deterministically")
    if (
        isinstance(max_points, bool)
        or not isinstance(max_points, int)
        or not 0 < max_points <= DASHBOARD_MAX_POINTS
    ):
        raise AnalyticsValidationError("dashboard point limit is invalid")
    copied, values = _validated_points(points)
    original_count = len(copied)
    if original_count <= max_points:
        return copied, {
            "original_count": original_count,
            "returned_count": original_count,
            "method": DASHBOARD_TRUNCATION_POLICY,
            "reason": "within_limit",
            "truncated": False,
        }
    mandatory = {
        0,
        original_count - 1,
        min(range(original_count), key=lambda index: (values[index], index)),
        max(range(original_count), key=lambda index: (values[index], -index)),
        *(index for index, point in enumerate(copied) if point.get("warning") is True),
    }
    if len(mandatory) > max_points:
        raise AnalyticsValidationError(
            "dashboard point limit cannot preserve required points"
        )
    available = tuple(
        index for index in range(original_count) if index not in mandatory
    )
    selected = mandatory | set(
        _bucket_candidates(available, values, max_points - len(mandatory))
    )
    ordered = tuple(copied[index] for index in sorted(selected))
    if len(ordered) > max_points:
        raise AnalyticsValidationError("dashboard truncation exceeded point limit")
    return ordered, {
        "original_count": original_count,
        "returned_count": len(ordered),
        "method": DASHBOARD_TRUNCATION_POLICY,
        "reason": "approved_point_limit",
        "truncated": True,
    }


__all__ = [
    "DASHBOARD_MAX_POINTS",
    "DASHBOARD_TRUNCATION_POLICY",
    "truncate_series",
]
