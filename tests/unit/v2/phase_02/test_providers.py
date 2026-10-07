"""Unit tests for ProviderManager, provider download adapters, rate limiting, and cancellation.

Description:
    Validates external market data provider registry, rate limiter, retry backoff,
    cooperative cancellation, and historical bar acquisition across supported
    adapters (Binance, Bitfinex, Coinbase, Darwinex, Dukascopy, MT5, SQ, TD, Yahoo)
    for Phase 2 Task 2.5.

Purpose:
    FEAT-DATA-PROVIDERS: Historical market data acquisition across external providers.

Key Capabilities:
    FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability metadata.
    FR-DATA-PROVIDERS-RATELIMIT: Bounded token-bucket rate limiting and retry backoff.
    FR-DATA-PROVIDERS-CANCEL: Cooperative cancellation of ongoing download requests.

Python API Usage:
    Run via pytest:
    `pytest tests/unit/v2/phase_02/test_providers.py -v --no-cov`
"""

from __future__ import annotations

import logging
import time
from typing import override

import pytest
from app.plugins.data.ingestion import BarRecord
from app.plugins.data.providers import (
    BaseDataProvider,
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
    ProviderManager,
    RateLimiter,
)


def test_provider_registry_enumeration() -> None:
    """Validate all required external providers are registered with capabilities."""
    manager = ProviderManager()
    capabilities = manager.list_capabilities()

    assert len(capabilities) >= 13
    provider_names = {c.name.lower() for c in capabilities}

    expected_names = {
        "binance",
        "binance_coin-m",
        "binance_usdt-m",
        "bitfinex",
        "coinbasepro",
        "poloniex",
        "darwinex",
        "dukascopy",
        "metatrader5",
        "sqequity",
        "sqfutures",
        "td",
        "yahoo",
    }
    assert expected_names.issubset(provider_names)

    # Test case-insensitive lookup
    assert manager.get_provider("binance") is not None
    assert manager.get_provider("BINANCE") is not None
    assert manager.get_provider("Dukascopy") is not None
    assert manager.get_provider("nonexistent") is None


def test_provider_download_execution(caplog: pytest.LogCaptureFixture) -> None:
    """Validate downloading bars across multiple provider adapters."""
    caplog.set_level(logging.DEBUG)
    manager = ProviderManager()

    # 1. Binance download
    req_binance = DownloadRequest(
        provider_name="Binance",
        symbol="BTCUSDT",
        timeframe="M1",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-01T01:00:00Z",
    )
    bars_binance = manager.download(req_binance)
    assert len(bars_binance) > 0
    assert bars_binance[0].open > 0.0

    # 2. Dukascopy download
    req_dukas = DownloadRequest(
        provider_name="Dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-01T00:30:00Z",
    )
    bars_dukas = manager.download(req_dukas)
    assert len(bars_dukas) > 0

    # 3. Yahoo download
    req_yahoo = DownloadRequest(
        provider_name="Yahoo",
        symbol="SPY",
        timeframe="D1",
        date_from="2026-09-01T00:00:00Z",
        date_to="2026-10-01T00:00:00Z",
    )
    bars_yahoo = manager.download(req_yahoo)
    assert len(bars_yahoo) > 0

    assert any("FR-DATA-PROVIDERS-ADAPTERS" in rec.message for rec in caplog.records)


def test_provider_unknown_error() -> None:
    """Validate error raised on unknown provider name."""
    manager = ProviderManager()
    req = DownloadRequest(
        provider_name="UnknownExchange",
        symbol="XYZ",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-01T01:00:00Z",
    )
    with pytest.raises(ValueError, match="Unknown data provider"):
        manager.download(req)


def test_cancellation_token(caplog: pytest.LogCaptureFixture) -> None:
    """Validate cooperative cancellation halts execution and fires log."""
    caplog.set_level(logging.DEBUG)
    manager = ProviderManager()

    token = CancellationToken()
    initially_cancelled: bool = token.is_cancelled
    assert not initially_cancelled
    token.cancel()
    assert token.is_cancelled

    req = DownloadRequest(
        provider_name="Binance",
        symbol="BTCUSDT",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-01T01:00:00Z",
    )

    with pytest.raises(InterruptedError, match="cancelled by user"):
        manager.download(req, cancel_token=token)


def test_rate_limiter() -> None:
    """Validate token-bucket rate limiter token acquisition."""
    limiter = RateLimiter(rate_limit_rps=100.0)
    # Fast acquire within capacity
    limiter.acquire(tokens=1.0)
    limiter.acquire(tokens=5.0)


class FlakyTestProvider(BaseDataProvider):
    """Test provider that fails twice before succeeding."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="FlakyTest",
                display_name="Flaky Test Provider",
                asset_classes=["Test"],
                timeframes=["M1"],
                max_retries=2,
                rate_limit_rps=100.0,
            )
        )
        self.call_count = 0

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        self.call_count += 1
        if self.call_count < 2:
            raise ConnectionError("Transient network failure")
        return [
            BarRecord(
                timestamp_utc="2026-10-01T00:00:00Z",
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=10.0,
            )
        ]


def test_retry_backoff(caplog: pytest.LogCaptureFixture) -> None:
    """Validate retry logic with backoff on transient provider failure."""
    caplog.set_level(logging.DEBUG)
    provider = FlakyTestProvider()

    req = DownloadRequest(
        provider_name="FlakyTest",
        symbol="TEST",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-01T01:00:00Z",
    )

    bars = provider.download_bars(req)
    assert len(bars) == 1
    assert provider.call_count == 2
    assert any("FR-DATA-PROVIDERS-RATELIMIT" in rec.message for rec in caplog.records)


def test_all_registered_providers_download() -> None:
    """Validate that every registered provider adapter executes download and returns bars."""
    manager = ProviderManager()
    caps = manager.list_capabilities()
    assert len(caps) >= 12

    for cap in caps:
        req = DownloadRequest(
            provider_name=cap.name,
            symbol="BTCUSD" if "Crypto" in cap.asset_classes else "EURUSD",
            date_from="2026-10-01T00:00:00Z",
            date_to="2026-10-01T00:05:00Z",
        )
        bars = manager.download(req)
        assert len(bars) > 0


def test_rate_limiter_sleep_when_exhausted() -> None:
    """Validate RateLimiter sleeps when requested tokens exceed capacity."""
    limiter = RateLimiter(rate_limit_rps=100.0)
    # Asking for 105 tokens when capacity is 100 will sleep ~0.05s
    start = time.monotonic()
    limiter.acquire(105.0)
    elapsed = time.monotonic() - start
    assert elapsed >= 0.02


def test_retry_exhaustion() -> None:
    """Validate exception raised when provider exhausts all retry attempts."""

    class FailingProvider(BaseDataProvider):
        def __init__(self) -> None:
            super().__init__(
                ProviderCapabilities(
                    name="FailAlways",
                    display_name="Fail Always",
                    asset_classes=["Forex"],
                    timeframes=["M1"],
                    max_retries=1,
                )
            )

        @override
        def _fetch_bars(
            self, request: DownloadRequest, token: CancellationToken
        ) -> list[BarRecord]:
            raise RuntimeError("Permanent failure")

    provider = FailingProvider()
    req = DownloadRequest(
        provider_name="FailAlways",
        symbol="EURUSD",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-01T00:05:00Z",
    )
    with pytest.raises(RuntimeError, match="Permanent failure"):
        provider.download_bars(req)
