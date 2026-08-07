"""Tests for the Analytics StandardResponse public boundary."""

from decimal import Decimal

from app.services.analytics import (
    AnalyticsRunConfig,
    build_performance_report,
    truncate_series,
)
from app.services.analytics.contracts.responses import ANALYTICS_ERROR_CATALOG

from tests.analytics._support import NOW, _config, _source, unwrap


def test_success_response_keeps_report_raw_in_data() -> None:
    """The report DTO is the direct response data value."""
    response = build_performance_report(
        _source(),
        source_contract="simulation.result",
        request_id="req-00000000-0000-4000-8000-000000000001",
        correlation_id="cor-00000000-0000-4000-8000-000000000001",
        created_at=NOW,
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=_config(),
    )
    report = unwrap(response)
    assert response.metadata.domain == "analytics"
    assert response.metadata.read_only is True
    assert response.data is report
    assert report.schema_id == "analytics.performance_report.v1"


def test_validation_failure_uses_analytics_catalog() -> None:
    """Invalid input is represented by the cataloged validation error."""
    response = build_performance_report(
        _source(),
        source_contract="simulation.result",
        request_id="req-00000000-0000-4000-8000-000000000001",
        correlation_id="cor-00000000-0000-4000-8000-000000000001",
        created_at=NOW,
        initial_balance=Decimal(0),
        account_currency="USD",
        config=_config(),
    )
    assert response.status == "error"
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "ANALYTICS_VALIDATION_FAILED"


def test_truncation_metadata_is_an_extension() -> None:
    """Truncation returns points in data and bounded metadata in extensions."""
    points = tuple(
        {"timestamp": NOW.replace(minute=index), "value": index} for index in range(4)
    )
    response = truncate_series(points, max_points=2)
    assert unwrap(response) == (points[0], points[3])
    assert response.metadata.extensions["truncation"]["original_count"] == 4
    assert response.metadata.extensions["truncation"]["returned_count"] == 2
    assert response.metadata.extensions["truncation"]["truncated"] is True
    assert set(ANALYTICS_ERROR_CATALOG) == {
        "ANALYTICS_VALIDATION_FAILED",
        "ANALYTICS_EXECUTION_FAILED",
    }


def test_response_helper_accepts_explicit_config_type() -> None:
    """The public response tests retain the Analytics configuration contract."""
    config: AnalyticsRunConfig = _config()
    assert config.max_response_bytes > 0
