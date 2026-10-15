"""Unit tests for typed data provider capabilities, request models, and error contracts.

Description:
    Tests the core data provider contracts: `HistoryRequest` validation and timestamp
    normalization, `HistoryPage` container semantics, `ProviderCapabilities` query
    methods, `ProviderHealth` reporting, `CancellationToken` cooperative interruption,
    the complete `ProviderError` exception hierarchy, and strict zero-synthetic fallback
    enforcement across all market data providers.

Purpose:
    FEAT-BROKER-CONTRACTS-TEST: Verification of data provider contracts and invariants.

Key Capabilities:
    - FR-TEST-CONTRACTS-MODELS: Assert typed request validation and page semantics.
      Associated: `test_history_request_validation()`, `test_history_page_container()`
      Logging: Validates request validation debug messages and page reporting.
    - FR-TEST-CONTRACTS-HEALTH: Assert health reporting and cancellation semantics.
      Associated: `test_cancellation_token()`, `test_provider_health_reporting()`
      Logging: Validates cancellation token logging and health status output.
    - FR-TEST-CONTRACTS-ZERO-SYNTHETIC: Assert no synthetic fallback across providers.
      Associated: `test_zero_synthetic_fallback_invariant()`
      Logging: Validates that empty upstream data never triggers synthetic bar generation.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_history_contracts.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_history_contracts.py --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.brokers.capabilities import (
    CancellationToken,
    HistoryPage,
    HistoryRequest,
    ProviderAuthError,
    ProviderCancelledError,
    ProviderCapabilities,
    ProviderDisabledError,
    ProviderHealth,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnsupportedError,
    ProviderValidationError,
)
from app.services.brokers.registry import BrokerKey, BrokerRegistry

# ============================================================================
# HistoryRequest Tests
# ============================================================================


def test_history_request_valid() -> None:
    """Verify HistoryRequest validates cleanly with proper parameters."""
    req = HistoryRequest(
        provider="dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        kind="bars",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
        count=50,
        limit=100,
    )
    req.validate()
    assert req.start_epoch() == int(datetime(2026, 1, 1, tzinfo=UTC).timestamp())
    assert req.end_epoch() == int(datetime(2026, 1, 2, tzinfo=UTC).timestamp())


def test_history_request_epoch_and_datetime_conversion() -> None:
    """Verify HistoryRequest epoch conversion across int, float, and datetime."""
    now = datetime.now(tz=UTC)
    now_ts = int(now.timestamp())

    req1 = HistoryRequest(provider="p", symbol="s", start=now_ts, end=now_ts + 60)
    assert req1.start_epoch() == now_ts
    assert req1.end_epoch() == now_ts + 60

    # Test millisecond conversion
    req2 = HistoryRequest(provider="p", symbol="s", start=now_ts * 1000)
    assert req2.start_epoch() == now_ts


@pytest.mark.parametrize(
    "case",
    [
        (
            "",
            "EURUSD",
            10,
            10,
            "bars",
            None,
            None,
            "Provider identifier must not be empty",
        ),
        ("dukascopy", "", 10, 10, "bars", None, None, "Symbol must not be empty"),
        (
            "dukascopy",
            "EURUSD",
            0,
            0,
            "bars",
            None,
            None,
            "Request count or limit must be greater than zero",
        ),
        (
            "dukascopy",
            "EURUSD",
            10,
            10,
            "invalid_kind",
            None,
            None,
            "Unsupported history kind",
        ),
        (
            "dukascopy",
            "EURUSD",
            10,
            10,
            "bars",
            1000,
            500,
            "cannot be greater than end date",
        ),
    ],
)
def test_history_request_validation_failures(
    case: tuple[str, str, int, int, str, int | None, int | None, str],
) -> None:
    """Verify HistoryRequest invalid invariants raise ProviderValidationError."""
    provider, symbol, count, limit, kind, start, end, error_match = case
    req = HistoryRequest(
        provider=provider,
        symbol=symbol,
        count=count,
        limit=limit,
        kind=kind,
        start=start,
        end=end,
    )
    with pytest.raises(ProviderValidationError, match=error_match):
        req.validate()


# ============================================================================
# HistoryPage Tests
# ============================================================================


def test_history_page_container() -> None:
    """Verify HistoryPage row counting and serialization."""
    rows = [{"time": 1000, "open": 1.0, "close": 1.1}]
    page = HistoryPage(
        provider="metatrader",
        symbol="EURUSD",
        timeframe="M1",
        kind="bars",
        rows=rows,
        cursor="cursor_abc",
        is_complete=False,
        provenance={"source": "cache"},
    )
    assert page.row_count == 1
    d = page.to_dict()
    assert d["provider"] == "metatrader"
    assert d["row_count"] == 1
    assert d["cursor"] == "cursor_abc"
    assert d["is_complete"] is False


# ============================================================================
# ProviderCapabilities Tests
# ============================================================================


def test_provider_capabilities_queries() -> None:
    """Verify ProviderCapabilities query methods."""
    caps = ProviderCapabilities(
        provider_id="test_provider",
        display_name="Test Provider",
        supported_timeframes=("M1", "H1", "D1"),
        supported_modes=("bars", "ticks"),
    )
    assert caps.supports_timeframe("m1")
    assert caps.supports_timeframe("D1")
    assert not caps.supports_timeframe("M5")
    assert caps.supports_kind("bars")
    assert caps.supports_kind("TICKS")
    assert not caps.supports_kind("orderbook")

    d = caps.to_dict()
    assert d["provider_id"] == "test_provider"
    assert "M1" in d["supported_timeframes"]


# ============================================================================
# ProviderHealth Tests
# ============================================================================


def test_provider_health_reporting() -> None:
    """Verify ProviderHealth representation and dictionary serialization."""
    health = ProviderHealth(
        provider_id="yahoo",
        status="HEALTHY",
        connected=True,
        message="Endpoint operational",
        latency_ms=12.5,
    )
    assert health.connected is True
    d = health.to_dict()
    assert d["provider_id"] == "yahoo"
    assert d["status"] == "HEALTHY"
    assert d["latency_ms"] == 12.5


# ============================================================================
# CancellationToken Tests
# ============================================================================


def test_cancellation_token() -> None:
    """Verify CancellationToken cooperative cancellation and exception raising."""
    # Check does not raise when not cancelled
    t1 = CancellationToken()
    assert not t1.is_cancelled
    t1.check_cancelled()

    # Trigger cancellation on separate token to prevent literal narrowing
    t2 = CancellationToken()
    t2.cancel(reason="Client disconnected")
    assert t2.is_cancelled

    with pytest.raises(ProviderCancelledError, match="Client disconnected") as exc_info:
        t2.check_cancelled()
    assert exc_info.value.status_code == 499
    assert exc_info.value.code == "OPERATION_CANCELLED"


# ============================================================================
# ProviderError Exception Hierarchy
# ============================================================================


def test_provider_error_hierarchy() -> None:
    """Verify status codes and error codes across the ProviderError exception tree."""
    err_404 = ProviderNotFoundError("Not found", provider="dukascopy")
    assert err_404.status_code == 404
    assert err_404.code == "PROVIDER_NOT_FOUND"
    assert err_404.provider == "dukascopy"

    err_422 = ProviderValidationError("Invalid symbol", provider="dukascopy")
    assert err_422.status_code == 422
    assert err_422.code == "VALIDATION_ERROR"

    err_unsupported = ProviderUnsupportedError("Ticks not supported", provider="yahoo")
    assert err_unsupported.status_code == 422
    assert err_unsupported.code == "UNSUPPORTED_CAPABILITY"

    err_503 = ProviderDisabledError("Disabled", provider="crypto")
    assert err_503.status_code == 503
    assert err_503.code == "PROVIDER_DISABLED"

    err_502 = ProviderAuthError("Bad API key", provider="binance")
    assert err_502.status_code == 502
    assert err_502.code == "UPSTREAM_AUTH_FAILED"

    err_429 = ProviderRateLimitError(
        "Too many requests", provider="darwinex", retry_after=5.0
    )
    assert err_429.status_code == 429
    assert err_429.code == "RATE_LIMITED"
    assert err_429.retry_after == 5.0

    err_504 = ProviderTimeoutError("Deadline exceeded", provider="yahoo")
    assert err_504.status_code == 504
    assert err_504.code == "UPSTREAM_TIMEOUT"

    err_cancelled = ProviderCancelledError("Aborted", provider="metatrader")
    assert err_cancelled.status_code == 499
    assert err_cancelled.code == "OPERATION_CANCELLED"


# ============================================================================
# Strict Zero-Synthetic-Fallback Invariant
# ============================================================================


@pytest.mark.parametrize(
    "provider_id",
    [
        "dukascopy",
        "darwinex",
        "metatrader",
        "sq_equity",
        "sq_futures",
        "crypto",
        "files",
        "yahoo",
        "tick_downloader",
    ],
)
def test_zero_synthetic_fallback_invariant(provider_id: str) -> None:
    """Verify that empty or failed upstream queries NEVER produce synthetic data."""
    registry = BrokerRegistry()
    broker = registry.acquire(BrokerKey(provider=provider_id))

    try:
        # Check read_history contract
        read_history_fn = getattr(broker, "read_history", None)
        if callable(read_history_fn):
            req = HistoryRequest(
                provider=provider_id,
                symbol="NONEXISTENT_9999",
                timeframe="M1",
                count=10,
                start=datetime(1975, 1, 1, tzinfo=UTC),
                end=datetime(1975, 1, 2, tzinfo=UTC),
            )
            try:
                page = read_history_fn(req)
                assert page.row_count == 0, (
                    f"Provider {provider_id} returned synthetic bars in read_history!"
                )
            except Exception as exc:
                assert not isinstance(exc, AssertionError)

        # Check fetch_bars contract with keyword args
        fetch_bars_fn = getattr(broker, "fetch_bars", None)
        if callable(fetch_bars_fn):
            try:
                bars = fetch_bars_fn(
                    symbol="NONEXISTENT_9999",
                    timeframe="M1",
                    mode="range",
                    start=0,
                    end=0,
                    count=10,
                    limit=10,
                )
                assert len(bars) == 0, (
                    f"Provider {provider_id} returned synthetic bars in fetch_bars!"
                )
            except Exception as exc:
                assert not isinstance(exc, AssertionError)

        # Check fetch_ticks contract with keyword args
        fetch_ticks_fn = getattr(broker, "fetch_ticks", None)
        if callable(fetch_ticks_fn):
            try:
                ticks = fetch_ticks_fn(
                    symbol="NONEXISTENT_9999",
                    mode="range",
                    start_ms=0,
                    end_ms=0,
                    count=10,
                    limit=10,
                )
                assert len(ticks) == 0, (
                    f"Provider {provider_id} returned synthetic ticks in fetch_ticks!"
                )
            except Exception as exc:
                assert not isinstance(exc, AssertionError)
    finally:
        registry.close()
