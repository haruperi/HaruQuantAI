"""Unit tests for the public API domain boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from app.services.data import (
    generate_synthetic_bars,
    generate_synthetic_ticks,
    get_market_hours,
    get_spread_data,
    get_tick_data,
    get_trading_sessions,
)
from app.services.data.contracts import (
    MarketDataRequest,
    ScheduleRequest,
    SyntheticRequest,
)
from app.services.data.contracts.errors import DataError


def test_public_api_exports_are_sorted_and_exact() -> None:
    """Verify that all public API operations are exported exactly as declared."""
    from app.services import data

    assert sorted(data.__all__) == data.__all__

    # 23 expected operations
    expected_exports = {
        "get_market_data",
        "get_tick_data",
        "get_spread_data",
        "get_symbol_metadata",
        "list_symbols",
        "get_data_availability",
        "get_market_hours",
        "get_trading_sessions",
        "get_historical_volume",
        "save_market_data",
        "load_local_dataset",
        "clear_data_cache",
        "resample_ohlcv",
        "align_multitimeframe_data",
        "generate_synthetic_ticks",
        "generate_synthetic_bars",
        "aggregate_ticks_to_bars",
        "create_data_update_job",
        "start_data_update_job",
        "stop_data_update_job",
        "run_data_update_job_once",
        "get_data_update_job_status",
        "get_feed_status",
    }
    assert set(data.__all__) == expected_exports


def test_get_tick_data_validates_data_kind() -> None:
    """Verify get_tick_data raises DataError if data_kind is invalid."""
    req = MarketDataRequest(
        source_id="local_csv",
        symbol="BTC/USD",
        data_kind="bars",  # Not tick
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        end=datetime(2026, 7, 1, 12, 5, tzinfo=UTC),
        limit=10,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc:
        get_tick_data(req)
    assert exc.value.args[0] == "VALIDATION_FAILED"
    assert "requires tick data_kind" in exc.value.safe_details["message"]


def test_get_spread_data_validates_data_kind() -> None:
    """Verify get_spread_data raises DataError if data_kind is invalid."""
    req = MarketDataRequest(
        source_id="local_csv",
        symbol="BTC/USD",
        data_kind="bars",  # Not spread
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        end=datetime(2026, 7, 1, 12, 5, tzinfo=UTC),
        limit=10,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc:
        get_spread_data(req)
    assert exc.value.args[0] == "VALIDATION_FAILED"
    assert "requires spread data_kind" in exc.value.safe_details["message"]


def test_get_market_hours_validates_view() -> None:
    """Verify get_market_hours raises DataError if view is invalid."""
    req = ScheduleRequest(
        source_id="live-src",
        symbol="BTC/USD",
        view="sessions",  # Not hours
        timezone="UTC",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc:
        get_market_hours(req, object())  # type: ignore[arg-type]
    assert exc.value.args[0] == "VALIDATION_FAILED"
    assert "requires hours view" in exc.value.safe_details["message"]


def test_get_trading_sessions_validates_view() -> None:
    """Verify get_trading_sessions raises DataError if view is invalid."""
    req = ScheduleRequest(
        source_id="live-src",
        symbol="BTC/USD",
        view="hours",  # Not sessions
        timezone="UTC",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc:
        get_trading_sessions(req, object())  # type: ignore[arg-type]
    assert exc.value.args[0] == "VALIDATION_FAILED"
    assert "requires sessions view" in exc.value.safe_details["message"]


def test_generate_synthetic_ticks_validates_data_kind() -> None:
    """Verify generate_synthetic_ticks raises DataError if data_kind is invalid."""
    req = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="bars",  # Not ticks
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        seed=123,
        parameters={
            "mu": Decimal("0.05"),
            "sigma": Decimal("0.2"),
            "start_val": Decimal("100.0"),
        },
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc:
        generate_synthetic_ticks(req)
    assert exc.value.args[0] == "VALIDATION_FAILED"
    assert "requires ticks data_kind" in exc.value.safe_details["message"]


def test_generate_synthetic_bars_validates_data_kind() -> None:
    """Verify generate_synthetic_bars raises DataError if data_kind is invalid."""
    req = SyntheticRequest(
        symbol="BTC/USD",
        data_kind="ticks",  # Not bars
        timeframe="M1",
        start=datetime(2026, 7, 1, 12, 0, tzinfo=UTC),
        record_count=10,
        method="gbm",
        seed=123,
        parameters={
            "mu": Decimal("0.05"),
            "sigma": Decimal("0.2"),
            "start_val": Decimal("100.0"),
        },
        precision_policy="decimal_string",
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )
    with pytest.raises(DataError) as exc:
        generate_synthetic_bars(req)
    assert exc.value.args[0] == "VALIDATION_FAILED"
    assert "requires bars data_kind" in exc.value.safe_details["message"]
