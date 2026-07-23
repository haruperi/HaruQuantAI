"""Unit tests for direct and typed Data retrieval facade calls."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.services.data import (
    get_data_availability,
    get_historical_volume,
    get_market_data,
    get_market_hours,
    get_spread_data,
    get_symbol_metadata,
    get_tick_data,
    get_trading_sessions,
    list_symbols,
)
from app.services.data.contracts import DataError
from app.services.data.market_data.requests import MarketDataRequest


@pytest.fixture
def isolated_facade(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace runtime and downstream operations with request-capturing fakes."""
    from app.services.data.market_data import pipeline, symbol_discovery
    from app.services.data.time_sessions import schedule

    monkeypatch.setattr(pipeline, "fetch_market_dataset", lambda request: request)
    monkeypatch.setattr(
        symbol_discovery, "fetch_symbol_metadata", lambda request: request
    )
    monkeypatch.setattr(symbol_discovery, "discover_symbols", lambda request: request)
    monkeypatch.setattr(
        symbol_discovery, "inspect_availability", lambda request: request
    )
    monkeypatch.setattr(
        symbol_discovery, "fetch_historical_volume", lambda request: request
    )
    monkeypatch.setattr(schedule, "ensure_source", lambda *_args: None)
    monkeypatch.setattr(schedule, "resolve_calendar", lambda *_args: object())
    monkeypatch.setattr(
        schedule,
        "get_current_schedule",
        lambda request, _calendar: request,
    )
    monkeypatch.setattr(
        symbol_discovery,
        "fetch_historical_volume",
        lambda request: request,
    )


def test_get_market_data_supports_direct_keywords_and_defaults(
    isolated_facade: None,
) -> None:
    """Direct calls build the same immutable request used by the typed path."""
    del isolated_facade

    result = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M1",
    )

    assert isinstance(result, MarketDataRequest)
    assert result.data_kind == "bars"
    assert result.start is None
    assert result.end is None
    assert result.limit == 10
    assert result.use_cache is False
    assert result.quality_failure_behavior == "reject"
    assert result.workflow_context == "research"
    assert result.precision_policy == "decimal_string"
    assert result.request_id.startswith("req-")


def test_get_market_data_preserves_typed_request_form(
    isolated_facade: None,
) -> None:
    """The existing request-object form passes the exact request through."""
    del isolated_facade
    request = MarketDataRequest(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        limit=25,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id=(
            "req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880"
        ),
    )

    assert get_market_data(request) is request


def test_get_market_data_forwards_all_optional_direct_arguments(
    isolated_facade: None,
) -> None:
    """Explicit facade options are preserved in the constructed request."""
    del isolated_facade
    start = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    end = start + timedelta(minutes=10)
    request_id = "req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880"

    result = get_market_data(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M1",
        start=start,
        end=end,
        limit=25,
        use_cache=True,
        cache_ttl_seconds=60,
        quality_failure_behavior="warn",
        workflow_context="validation",
        precision_policy="decimal_string",
        fallback_sources=("backup",),
        source_timezone="UTC",
        request_id=request_id,
    )

    assert result.start == start
    assert result.end == end
    assert result.limit == 25
    assert result.use_cache is True
    assert result.cache_ttl_seconds == 60
    assert result.quality_failure_behavior == "warn"
    assert result.workflow_context == "validation"
    assert result.fallback_sources == ("backup",)
    assert result.source_timezone == "UTC"
    assert result.request_id == request_id


def test_all_retrieval_reference_exports_accept_direct_keywords(
    isolated_facade: None,
) -> None:
    """Every Retrieval and Reference export constructs its owned request."""
    del isolated_facade
    start = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    end = start + timedelta(minutes=10)

    tick = get_tick_data(source_id="mt5", symbol="EURUSD")
    spread = get_spread_data(source_id="mt5", symbol="EURUSD")
    metadata = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    symbols = list_symbols(source_id="mt5")
    availability = get_data_availability(
        source_id="mt5",
        symbol="EURUSD",
        timeframe="M1",
    )
    hours = get_market_hours(source_id="mt5", symbol="EURUSD")
    sessions = get_trading_sessions(source_id="mt5", symbol="EURUSD")
    volume = get_historical_volume(
        source_id="mt5",
        symbol="EURUSD",
        start=start,
        end=end,
    )

    assert tick.data_kind == "ticks"
    assert spread.data_kind == "spreads"
    assert metadata.symbol == "EURUSD"
    assert symbols.limit == 100
    assert availability.data_kind == "ohlcv"
    assert availability.max_probe_records == 1_000
    assert hours.view == "hours"
    assert hours.timezone == "UTC"
    assert sessions.view == "sessions"
    assert volume.mode == "summary"
    assert volume.limit == 10


def test_typed_request_cannot_be_mixed_with_direct_keywords(
    isolated_facade: None,
) -> None:
    """Mixed call styles fail instead of silently ignoring keyword values."""
    del isolated_facade
    request = MarketDataRequest(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe="M1",
        limit=10,
        use_cache=False,
        quality_failure_behavior="reject",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=(
            "req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880"
        ),
    )

    with pytest.raises(DataError) as error:
        get_market_data(request, symbol="GBPUSD")
    assert error.value.code == "VALIDATION_FAILED"


def test_market_data_request_rejects_removed_fail_behavior() -> None:
    """The quality behavior contract accepts only reject or warn."""
    with pytest.raises(DataError) as captured:
        MarketDataRequest(
            source_id="mt5",
            symbol="EURUSD",
            data_kind="bars",
            timeframe="M1",
            limit=10,
            use_cache=False,
            quality_failure_behavior="fail",  # type: ignore[arg-type]
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=(
                "req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880"
            ),
        )
    assert captured.value.code == "INVALID_INPUT"
