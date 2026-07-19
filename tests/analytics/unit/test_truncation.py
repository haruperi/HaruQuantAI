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
