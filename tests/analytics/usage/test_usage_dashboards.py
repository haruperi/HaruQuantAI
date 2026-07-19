"""Runnable usage evidence for Analytics dashboard operations."""

from datetime import UTC, datetime, timedelta

from app.services.analytics.dashboards import (
    build_dashboard_payload,
    truncate_series,
)
from app.utils import logger
from tests.analytics.usage.test_usage_reports import _report


def test_usage_truncation_truncate_series() -> None:
    """FR-ANLT-045 bounds one deterministic presentation series."""
    logger.info("Running Analytics dashboard truncation usage")
    start = datetime(2026, 7, 19, tzinfo=UTC)
    points = tuple(
        {"timestamp": start + timedelta(minutes=index), "value": float(index % 5)}
        for index in range(20)
    )
    selected, metadata = truncate_series(points, max_points=6)
    assert len(selected) <= 6
    assert metadata["truncated"] is True


def test_usage_payloads_build_dashboard_payload() -> None:
    """FR-ANLT-046 projects one report without calculating new metrics."""
    logger.info("Running Analytics dashboard payload usage")
    report, _ = _report()
    payload = build_dashboard_payload(report)
    assert payload.schema_id == "analytics.dashboard_payload.v1"
    assert payload.non_binding is True
