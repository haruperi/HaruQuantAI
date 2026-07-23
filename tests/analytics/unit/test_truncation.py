"""Unit tests for bounded Analytics dashboard series."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta

import pytest
from app.services.analytics.contracts import AnalyticsValidationError
from app.services.analytics.dashboards.truncation import truncate_series
from app.utils import logger


def _points() -> tuple[dict[str, object], ...]:
    """Build an ordered series with distinct extrema.

    Returns:
        Ten deterministic UTC value points.
    """
    logger.debug("Building Analytics truncation test points")
    values = (0.0, 4.0, -5.0, 2.0, 8.0, 3.0, -1.0, 6.0, 1.0, 2.0)
    start = datetime(2026, 7, 19, tzinfo=UTC)
    return tuple(
        {"timestamp": start + timedelta(minutes=index), "value": value}
        for index, value in enumerate(values)
    )


def test_truncation_never_exceeds_limit() -> None:
    """Endpoints and global extrema survive the exact output ceiling."""
    logger.debug("Testing Analytics dashboard truncation ceiling")
    points = _points()
    selected, metadata = truncate_series(points, max_points=4)
    assert len(selected) == 4
    assert selected[0] == points[0]
    assert selected[-1] == points[-1]
    assert points[2] in selected
    assert points[4] in selected
    assert metadata == {
        "original_count": 10,
        "returned_count": 4,
        "method": "min_max_per_bucket",
        "reason": "approved_point_limit",
        "truncated": True,
    }


def test_truncation_fails_when_warning_preservation_exceeds_limit() -> None:
    """A ceiling that cannot retain required warning points fails closed."""
    logger.debug("Testing Analytics warning-point preservation failure")
    points = tuple({**point, "warning": True} for point in _points())
    with pytest.raises(AnalyticsValidationError, match="preserve"):
        truncate_series(points, max_points=4)


def test_truncate_series_invalid_inputs() -> None:
    """Test various invalid arguments to truncate_series."""
    # points is not a sequence
    with pytest.raises(AnalyticsValidationError, match="must be a sequence"):
        truncate_series(123, max_points=5)  # type: ignore[arg-type]

    # points is empty
    with pytest.raises(AnalyticsValidationError, match="must not be empty"):
        truncate_series((), max_points=5)

    # point is not a mapping
    with pytest.raises(AnalyticsValidationError, match="must be a mapping"):
        truncate_series(([1, 2],), max_points=5)  # type: ignore[arg-type]

    # missing timestamp
    with pytest.raises(AnalyticsValidationError, match="timestamps must be unique"):
        truncate_series(({"value": 1.0},), max_points=5)

    # naive timestamp
    naive_ts = datetime(2026, 7, 19)  # noqa: DTZ001
    with pytest.raises(AnalyticsValidationError, match="timestamps must be unique"):
        truncate_series(({"timestamp": naive_ts, "value": 1.0},), max_points=5)

    # unordered timestamps
    ts1 = datetime(2026, 7, 19, tzinfo=UTC)
    ts2 = ts1 - timedelta(minutes=1)
    with pytest.raises(AnalyticsValidationError, match="timestamps must be unique"):
        truncate_series(
            (
                {"timestamp": ts1, "value": 1.0},
                {"timestamp": ts2, "value": 2.0},
            ),
            max_points=5,
        )

    # duplicate timestamps
    with pytest.raises(AnalyticsValidationError, match="timestamps must be unique"):
        truncate_series(
            (
                {"timestamp": ts1, "value": 1.0},
                {"timestamp": ts1, "value": 2.0},
            ),
            max_points=5,
        )


def test_truncate_series_invalid_values() -> None:
    """Test values validation inside truncate_series."""
    ts = datetime(2026, 7, 19, tzinfo=UTC)

    # value is not finite (string)
    with pytest.raises(AnalyticsValidationError, match="requires a finite value"):
        truncate_series(({"timestamp": ts, "value": "not-a-number"},), max_points=5)

    # value is boolean (which is subclass of int!)
    with pytest.raises(AnalyticsValidationError, match="requires a finite value"):
        truncate_series(({"timestamp": ts, "value": True},), max_points=5)

    # value is infinite float
    with pytest.raises(AnalyticsValidationError, match="value must be finite"):
        truncate_series(({"timestamp": ts, "value": float("inf")},), max_points=5)

    # value is infinite Decimal
    from decimal import Decimal

    with pytest.raises(AnalyticsValidationError, match="value must be finite"):
        truncate_series(
            ({"timestamp": ts, "value": Decimal("Infinity")},), max_points=5
        )


def test_truncate_series_no_truncation_needed() -> None:
    """Test when length of points is within the max_points limit."""
    points = _points()
    selected, metadata = truncate_series(points, max_points=20)
    assert len(selected) == len(points)
    assert metadata["truncated"] is False
    assert metadata["reason"] == "within_limit"


def test_truncate_series_extracts_drawdown_or_equity() -> None:
    """Test extraction of alternate values like equity or drawdown."""
    ts1 = datetime(2026, 7, 19, tzinfo=UTC)
    ts2 = ts1 + timedelta(minutes=1)

    points1 = (
        {"timestamp": ts1, "equity": 1000.0},
        {"timestamp": ts2, "equity": 1100.0},
    )
    selected, _ = truncate_series(points1, max_points=5)
    assert len(selected) == 2

    points2 = (
        {"timestamp": ts1, "drawdown": 0.05},
        {"timestamp": ts2, "drawdown": 0.02},
    )
    selected, _ = truncate_series(points2, max_points=5)
    assert len(selected) == 2


def test_truncate_series_invalid_max_points() -> None:
    """Test invalid max_points arguments."""
    points = _points()
    with pytest.raises(AnalyticsValidationError, match="point limit is invalid"):
        truncate_series(points, max_points=0)

    with pytest.raises(AnalyticsValidationError, match="point limit is invalid"):
        truncate_series(points, max_points=-5)

    with pytest.raises(AnalyticsValidationError, match="point limit is invalid"):
        truncate_series(points, max_points=100000)

    with pytest.raises(AnalyticsValidationError, match="point limit is invalid"):
        truncate_series(points, max_points=True)  # type: ignore[arg-type]
