"""Unit tests for the Analytics boundaries subpackage."""

from __future__ import annotations

import pytest
from app.services.analytics.boundaries import (
    AnalyticsError,
    AnalyticsLimits,
    RedactionPolicy,
    WorkloadShape,
    enforce_limits,
    error_envelope,
    float64,
    redact,
    request_id,
    success_envelope,
    validate_request,
)
from app.services.analytics.contracts import (
    AnalyticsMetadata,
    MetricConfig,
    ToolEnvelope,
)
from app.utils.errors import ValidationError


def test_request_id_valid() -> None:
    """Test valid and invalid request ID validation."""
    cfg = MetricConfig()

    # Valid string
    res = request_id("test-req-123", cfg)
    assert res.value == "test-req-123"

    # None is allowed
    res_none = request_id(None, cfg)
    assert res_none.value is None

    # Empty string raises error
    with pytest.raises(ValidationError, match="request_id must be a non-empty string"):
        request_id("", cfg)

    # Whitespace raises error
    with pytest.raises(ValidationError, match="request_id must be a non-empty string"):
        request_id("   ", cfg)


def test_float64_casting() -> None:
    """Test float64 validation and casting."""
    cfg = MetricConfig()

    # Valid conversions
    assert float64(12.34, cfg).value == 12.34
    assert float64("1.23", cfg).value == 1.23
    assert float64(45, cfg).value == 45.0

    # Invalid conversions
    with pytest.raises(ValidationError, match="is not a valid float"):
        float64("invalid", cfg)

    with pytest.raises(ValidationError, match="is not a valid float"):
        float64([1, 2], cfg)


def test_validate_request() -> None:
    """Test validate_request constraints."""
    limits = AnalyticsLimits(max_trades=5, max_equity_points=10)

    # Valid requests
    validate_request({"trades": [1, 2], "equity_curve": [0.1, 0.2]}, "req-1", limits)

    # Invalid request ID
    with pytest.raises(ValidationError, match="request_id must be a non-empty string"):
        validate_request({}, "   ", limits)

    # Too many trades
    with pytest.raises(ValidationError, match="Trades count 6 exceeds limit 5"):
        validate_request({"trades": [1, 2, 3, 4, 5, 6]}, "req-1", limits)

    # Too many equity points
    with pytest.raises(
        ValidationError, match="Equity curve points 11 exceeds limit 10"
    ):
        validate_request(
            {"equity_curve": [0] * 11},
            "req-1",
            limits,
        )


def test_enforce_limits() -> None:
    """Test enforce_limits validation on workload shapes."""
    limits = AnalyticsLimits(
        max_trades=10,
        max_equity_points=20,
        max_benchmark_points=30,
        max_portfolio_components=2,
        max_dashboard_points=5,
        max_statistical_observations=100,
    )

    # OK shape
    ok_shape = WorkloadShape(
        trades_count=5,
        equity_points_count=15,
        benchmark_points_count=25,
        portfolio_components_count=1,
        dashboard_points_count=4,
        statistical_observations_count=50,
    )
    enforce_limits(ok_shape, limits)

    # Exceeding trades
    with pytest.raises(ValidationError, match="Trades count 11 exceeds limit 10"):
        enforce_limits(WorkloadShape(trades_count=11), limits)

    # Exceeding equity points
    with pytest.raises(
        ValidationError, match="Equity points count 21 exceeds limit 20"
    ):
        enforce_limits(WorkloadShape(equity_points_count=21), limits)

    # Exceeding benchmark points
    with pytest.raises(
        ValidationError, match="Benchmark points count 31 exceeds limit 30"
    ):
        enforce_limits(WorkloadShape(benchmark_points_count=31), limits)

    # Exceeding portfolio components
    with pytest.raises(
        ValidationError, match="Portfolio components count 3 exceeds limit 2"
    ):
        enforce_limits(WorkloadShape(portfolio_components_count=3), limits)

    # Exceeding dashboard points
    with pytest.raises(
        ValidationError, match="Dashboard points count 6 exceeds limit 5"
    ):
        enforce_limits(WorkloadShape(dashboard_points_count=6), limits)

    # Exceeding statistical observations
    with pytest.raises(
        ValidationError,
        match="Statistical observations count 101 exceeds limit 100",
    ):
        enforce_limits(WorkloadShape(statistical_observations_count=101), limits)


def test_tool_envelopes() -> None:
    """Test success and error envelopes wrappers."""
    meta = AnalyticsMetadata(request_id="req-123")

    # Success envelope
    success = success_envelope({"result": 42}, meta)
    assert isinstance(success, ToolEnvelope)
    assert success.status == "success"
    assert success.message == "Operation completed successfully."
    assert success.data == {"result": 42}
    assert success.metadata["tool_name"] == "analytics_tool"
    assert success.metadata["request_id"] == "req-123"

    # Error envelope
    err = AnalyticsError(code="INVALID_INPUT", details="Something was wrong.")
    error_res = error_envelope(err, meta)
    assert isinstance(error_res, ToolEnvelope)
    assert error_res.status == "error"
    assert error_res.data is None
    assert error_res.error is not None
    assert error_res.error.code == "INVALID_INPUT"
    assert error_res.error.message == "Something was wrong."
    assert error_res.metadata["tool_name"] == "analytics_tool"


def test_redact_secrets() -> None:
    """Test recursive secret redaction logic."""
    payload = {
        "strategy_id": "SMA_CROSS",
        "api_key": "secret-api-token-123",
        "nested": {
            "password": "my-secret-password",
            "normal_field": 123.45,
        },
        "list_items": [
            {"token": "broker-oauth-token"},
            {"safe_val": "hello"},
        ],
        "auth_header": "Bearer abcdef12345",
    }

    redacted = redact(payload, RedactionPolicy.STANDARD)
    assert isinstance(redacted, dict)
    assert redacted["strategy_id"] == "SMA_CROSS"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["password"] == "[REDACTED]"
    assert redacted["nested"]["normal_field"] == 123.45
    assert redacted["list_items"][0]["token"] == "[REDACTED]"
    assert redacted["list_items"][1]["safe_val"] == "hello"
    assert redacted["auth_header"] == "[REDACTED]"
