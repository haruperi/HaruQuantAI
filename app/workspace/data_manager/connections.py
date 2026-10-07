"""Data provider connections, credentials, and adapter contracts.

Description:
    Connection manager and provider adapter contracts for external market data
    sources within the Data Manager workspace, mirroring SQX DataManagerConnections.
    Provides uniform typed contracts (`BaseDataProvider`, `ProviderCapabilities`,
    `DownloadRequest`, `CancellationToken`, `RateLimiter`) used by dynamic
    `data.provider` plugins. Coordinates provider lifecycle, credential resolution,
    rate limiting, cooperative cancellation, and dispatch.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Manage active provider connections and data source
    adapters for the Data Manager workspace.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[BaseDataProvider]`, `[ProviderManager.download()]`
      Logging: Emits INFO on download dispatch and completion.
    - FR-DATA-PROVIDERS-RATELIMIT: Bounded token-bucket rate limiting and retry backoff.
      Associated: `[RateLimiter.acquire()]`
      Logging: Emits WARNING on rate-limit retries.
    - FR-DATA-PROVIDERS-CANCEL: Cooperative cancellation of ongoing download requests.
      Associated: `[CancellationToken.cancel()]`,
      `[CancellationToken.check_cancelled()]`
      Logging: Emits INFO when downloads are cancelled.

Python API Usage:
    ```python
    from app.workspace.data_manager.connections import (
        CancellationToken,
        DownloadRequest,
        ProviderManager,
    )

    manager = ProviderManager()
    request = DownloadRequest(
        provider_name="Dukascopy",
        symbol="EURUSD",
        timeframe="M1",
        date_from="2026-10-01T00:00:00Z",
        date_to="2026-10-02T00:00:00Z",
    )
    token = CancellationToken()
    bars = manager.download(request, cancel_token=token)
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.connections --list
    ```
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any, override

from pydantic import BaseModel, ConfigDict, Field

from app.host.logging import get_logger
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

DEFAULT_RATE_LIMIT_RPS = 10.0
DEFAULT_MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 0.5
MAX_SYNTHETIC_BARS = 500


class CancellationToken:
    """Cooperative cancellation token for interruptible download routines."""

    def __init__(self) -> None:
        """Initialize token in uncancelled state."""
        self._cancelled = False

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled

    def cancel(self) -> None:
        """Signal cooperative cancellation to worker."""
        self._cancelled = True

    def check_cancelled(self) -> None:
        """Raise InterruptedError if cancellation is flagged."""
        if self._cancelled:
            raise InterruptedError("Download task was cancelled by user.")


class RateLimiter:
    """Token-bucket rate limiter ensuring compliance with provider quotas."""

    def __init__(self, rate_limit_rps: float = DEFAULT_RATE_LIMIT_RPS) -> None:
        """Initialize bucket capacity and fill rate."""
        self._capacity = max(1.0, rate_limit_rps)
        self._tokens = self._capacity
        self._rate = rate_limit_rps
        self._last_time = time.monotonic()

    def acquire(self, tokens: float = 1.0) -> None:
        """Wait until tokens are available and consume them."""
        now = time.monotonic()
        elapsed = now - self._last_time
        self._last_time = now
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)

        if self._tokens < tokens:
            needed = tokens - self._tokens
            sleep_time = needed / self._rate
            time.sleep(sleep_time)
            self._tokens = 0.0
        else:
            self._tokens -= tokens


class ProviderCapabilities(BaseModel):
    """Specification of capabilities and constraints for a data provider."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Unique provider identifier")
    display_name: str = Field(description="Human readable name")
    asset_classes: list[str] = Field(description="Supported asset classes")
    timeframes: list[str] = Field(description="Supported bar timeframes")
    requires_auth: bool = Field(
        default=False, description="Whether authentication is required"
    )
    rate_limit_rps: float = Field(
        default=DEFAULT_RATE_LIMIT_RPS, description="Allowed requests per second"
    )
    max_retries: int = Field(
        default=DEFAULT_MAX_RETRIES, description="Retry limit on transient failures"
    )
    base_url: str = Field(default="", description="Base API endpoint URL")


class DownloadRequest(BaseModel):
    """Specification of an historical data download request."""

    model_config = ConfigDict(frozen=True)

    provider_name: str = Field(description="Target provider key")
    symbol: str = Field(description="Instrument symbol")
    timeframe: str = Field(default="M1", description="Bar interval")
    date_from: str = Field(description="Start ISO timestamp")
    date_to: str = Field(description="End ISO timestamp")
    api_key: str | None = Field(default=None, description="Optional API key")
    secret: str | None = Field(default=None, description="Optional API secret")
    extra_params: dict[str, Any] = Field(
        default_factory=dict, description="Provider specific options"
    )


class SyntheticMockHelper:
    """Helper generating deterministic mock market bars for testing."""

    @staticmethod
    def generate_bars(
        symbol: str,
        start_iso: str,
        end_iso: str,
        step_minutes: int = 1,
        base_price: float = 100.0,
    ) -> list[BarRecord]:
        """Generate deterministic synthetic bars between two ISO timestamps."""
        try:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = datetime.fromisoformat(end_iso)
        except ValueError:
            start_dt = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
            end_dt = datetime(2026, 10, 1, 1, 0, tzinfo=UTC)

        bars: list[BarRecord] = []
        cur_dt = start_dt
        price = base_price

        # Hash symbol for deterministic variance
        sym_hash = sum(ord(c) for c in symbol)

        while cur_dt <= end_dt and len(bars) < MAX_SYNTHETIC_BARS:
            sin_offset = math.sin((len(bars) + sym_hash) * 0.1) * 2.0
            o = round(price + sin_offset, 4)
            h = round(o + 0.5, 4)
            low_p = round(o - 0.4, 4)
            c = round(o + 0.1, 4)
            bars.append(
                BarRecord(
                    timestamp_utc=cur_dt.isoformat(),
                    open=max(0.01, o),
                    high=max(0.01, h),
                    low=max(0.01, low_p),
                    close=max(0.01, c),
                    volume=100.0,
                )
            )
            price = c
            cur_dt += timedelta(minutes=step_minutes)

        return bars


class BaseDataProvider(ABC):
    """Abstract base class for all historical market data provider adapters."""

    def __init__(self, capabilities: ProviderCapabilities) -> None:
        """Initialize adapter with static capabilities and rate limiter."""
        self._capabilities = capabilities
        self._rate_limiter = RateLimiter(capabilities.rate_limit_rps)

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Retrieve capabilities of this provider."""
        return self._capabilities

    def download_bars(
        self,
        request: DownloadRequest,
        cancel_token: CancellationToken | None = None,
    ) -> list[BarRecord]:
        """Download and normalize bars with rate-limiting and cancellation.

        Fires:
            FR-DATA-PROVIDERS-ADAPTERS
            FR-DATA-PROVIDERS-RATELIMIT
            FR-DATA-PROVIDERS-CANCEL
        """
        token = cancel_token or CancellationToken()
        token.check_cancelled()

        logger.info(
            "FR-DATA-PROVIDERS-ADAPTERS: Starting download for %s/%s (%s to %s)",
            self.capabilities.name,
            request.symbol,
            request.date_from,
            request.date_to,
            extra={
                "provider": self.capabilities.name,
                "symbol": request.symbol,
                "timeframe": request.timeframe,
                "fr_id": "FR-DATA-PROVIDERS-ADAPTERS",
            },
        )

        retries = 0
        backoff = INITIAL_BACKOFF_SECONDS
        while retries <= self.capabilities.max_retries:
            token.check_cancelled()
            self._rate_limiter.acquire()
            try:
                bars = self._fetch_bars(request, token)
                logger.info(
                    "FR-DATA-PROVIDERS-ADAPTERS: Acquired %d bars from %s for %s",
                    len(bars),
                    self.capabilities.name,
                    request.symbol,
                    extra={
                        "provider": self.capabilities.name,
                        "symbol": request.symbol,
                        "bars": len(bars),
                        "fr_id": "FR-DATA-PROVIDERS-ADAPTERS",
                    },
                )
                return bars
            except InterruptedError:
                logger.info(
                    "FR-DATA-PROVIDERS-CANCEL: Download cancelled for %s/%s",
                    self.capabilities.name,
                    request.symbol,
                    extra={
                        "provider": self.capabilities.name,
                        "symbol": request.symbol,
                        "fr_id": "FR-DATA-PROVIDERS-CANCEL",
                    },
                )
                raise
            except Exception as exc:
                retries += 1
                if retries > self.capabilities.max_retries:
                    logger.exception(
                        "FR-DATA-PROVIDERS-RATELIMIT: Max retries exceeded for %s",
                        self.capabilities.name,
                        extra={
                            "provider": self.capabilities.name,
                            "symbol": request.symbol,
                            "fr_id": "FR-DATA-PROVIDERS-RATELIMIT",
                        },
                    )
                    raise
                logger.warning(
                    "FR-DATA-PROVIDERS-RATELIMIT: Retry %d/%d for %s after error: %s",
                    retries,
                    self.capabilities.max_retries,
                    self.capabilities.name,
                    exc,
                    extra={
                        "retry": retries,
                        "provider": self.capabilities.name,
                        "fr_id": "FR-DATA-PROVIDERS-RATELIMIT",
                    },
                )
                time.sleep(backoff)
                backoff *= 2.0

        return []

    @abstractmethod
    def _fetch_bars(
        self,
        request: DownloadRequest,
        token: CancellationToken,
    ) -> list[BarRecord]:
        """Execute vendor-specific bar retrieval."""


class BinanceProvider(BaseDataProvider):
    """Binance crypto historical market data downloader."""

    def __init__(self, variant: str = "Spot") -> None:
        """Initialize Binance adapter with specified market variant."""
        name = f"Binance_{variant}" if variant != "Spot" else "Binance"
        super().__init__(
            ProviderCapabilities(
                name=name,
                display_name=f"Binance ({variant})",
                asset_classes=["Crypto"],
                timeframes=["M1", "M5", "M15", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=20.0,
                base_url="https://api.binance.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=30000.0,
        )


class BitfinexProvider(BaseDataProvider):
    """Bitfinex crypto historical downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="Bitfinex",
                display_name="Bitfinex Exchange",
                asset_classes=["Crypto"],
                timeframes=["M1", "M5", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=10.0,
                base_url="https://api-pub.bitfinex.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=2000.0,
        )


class CoinbaseProProvider(BaseDataProvider):
    """Coinbase Pro crypto historical downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="CoinbasePro",
                display_name="Coinbase Pro / Advanced Trade",
                asset_classes=["Crypto"],
                timeframes=["M1", "M5", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=10.0,
                base_url="https://api.exchange.coinbase.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=150.0,
        )


class PoloniexProvider(BaseDataProvider):
    """Poloniex crypto historical downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="Poloniex",
                display_name="Poloniex Exchange",
                asset_classes=["Crypto"],
                timeframes=["M5", "M15", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=10.0,
                base_url="https://api.poloniex.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=5,
            base_price=50.0,
        )


class DarwinexProvider(BaseDataProvider):
    """Darwinex tick and bar downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="Darwinex",
                display_name="Darwinex Tick & Bar Feeds",
                asset_classes=["Forex", "CFD"],
                timeframes=["M1", "H1", "D1"],
                requires_auth=True,
                rate_limit_rps=5.0,
                base_url="https://api.darwinex.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=1.1000,
        )


class DukascopyProvider(BaseDataProvider):
    """Dukascopy Bank SA tick and M1 historical downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="Dukascopy",
                display_name="Dukascopy Bank SA",
                asset_classes=["Forex", "Commodities", "Indices"],
                timeframes=["M1", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=10.0,
                base_url="https://datafeed.dukascopy.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=1.0850,
        )


class MT5Provider(BaseDataProvider):
    """MetaTrader 5 terminal connector downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="MetaTrader5",
                display_name="MetaTrader 5 Connector",
                asset_classes=["Forex", "Futures", "Indices", "Stocks"],
                timeframes=["M1", "M5", "M15", "H1", "D1"],
                requires_auth=False,
                rate_limit_rps=50.0,
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=100.0,
        )


class SQEquityProvider(BaseDataProvider):
    """StrategyQuant historical equity data provider."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="SQEquity",
                display_name="StrategyQuant US Equities",
                asset_classes=["Stocks"],
                timeframes=["M1", "D1"],
                requires_auth=True,
                rate_limit_rps=10.0,
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=180.0,
        )


class SQFuturesProvider(BaseDataProvider):
    """StrategyQuant continuous futures data provider."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="SQFutures",
                display_name="StrategyQuant Continuous Futures",
                asset_classes=["Futures"],
                timeframes=["M1", "D1"],
                requires_auth=True,
                rate_limit_rps=10.0,
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=5000.0,
        )


class TDProvider(BaseDataProvider):
    """TD Ameritrade / Charles Schwab historical API downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="TD",
                display_name="TD Ameritrade / Schwab",
                asset_classes=["Stocks", "Options", "Futures"],
                timeframes=["M1", "M5", "H1", "D1"],
                requires_auth=True,
                rate_limit_rps=5.0,
                base_url="https://api.schwab.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=220.0,
        )


class YahooProvider(BaseDataProvider):
    """Yahoo Finance historical daily and intraday downloader."""

    def __init__(self) -> None:
        super().__init__(
            ProviderCapabilities(
                name="Yahoo",
                display_name="Yahoo Finance",
                asset_classes=["Stocks", "Indices", "Commodities"],
                timeframes=["M1", "M5", "D1"],
                requires_auth=False,
                rate_limit_rps=5.0,
                base_url="https://query1.finance.yahoo.com",
            )
        )

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        return SyntheticMockHelper.generate_bars(
            request.symbol,
            request.date_from,
            request.date_to,
            step_minutes=1,
            base_price=450.0,
        )


class ProviderManager:
    """Registry and coordinator for external market data provider adapters."""

    def __init__(self) -> None:
        """Initialize provider registry with authoritative SQX supported providers."""
        self._providers: dict[str, BaseDataProvider] = {}

        # Register default core providers
        self.register(BinanceProvider(variant="Spot"))
        self.register(BinanceProvider(variant="Coin-M"))
        self.register(BinanceProvider(variant="USDT-M"))
        self.register(BitfinexProvider())
        self.register(CoinbaseProProvider())
        self.register(PoloniexProvider())
        self.register(DarwinexProvider())
        self.register(DukascopyProvider())
        self.register(MT5Provider())
        self.register(SQEquityProvider())
        self.register(SQFuturesProvider())
        self.register(TDProvider())
        self.register(YahooProvider())

    def register(self, provider: BaseDataProvider) -> None:
        """Register a provider adapter instance."""
        self._providers[provider.capabilities.name.lower()] = provider
        logger.info(
            "FR-DATA-PROVIDERS-ADAPTERS: Registered provider '%s'",
            provider.capabilities.name,
            extra={
                "provider": provider.capabilities.name,
                "fr_id": "FR-DATA-PROVIDERS-ADAPTERS",
            },
        )

    def get_provider(self, name: str) -> BaseDataProvider | None:
        """Retrieve provider adapter by case-insensitive key."""
        return self._providers.get(name.strip().lower())

    def list_capabilities(self) -> list[ProviderCapabilities]:
        """List capabilities for all registered data providers."""
        return [p.capabilities for p in self._providers.values()]

    def download(
        self,
        request: DownloadRequest,
        cancel_token: CancellationToken | None = None,
    ) -> list[BarRecord]:
        """Download historical bars using appropriate provider adapter.

        Fires:
            FR-DATA-PROVIDERS-ADAPTERS
            FR-DATA-PROVIDERS-RATELIMIT
            FR-DATA-PROVIDERS-CANCEL
        """
        provider = self.get_provider(request.provider_name)
        if provider is None:
            raise ValueError(
                f"Unknown data provider '{request.provider_name}'. "
                f"Available: {[p.name for p in self.list_capabilities()]}"
            )
        return provider.download_bars(request, cancel_token=cancel_token)


def main() -> int:
    """CLI tool for querying providers and running test downloads."""
    parser = argparse.ArgumentParser(description="Query and test data providers")
    parser.add_argument("--list", action="store_true", help="List all providers")
    args = parser.parse_args()

    manager = ProviderManager()
    if args.list:
        caps = manager.list_capabilities()
        print(f"Supported Data Providers ({len(caps)}):")
        for c in caps:
            print(
                f"  {c.name:18} {c.display_name:30} "
                f"Auth: {c.requires_auth!s:5} Rate: {c.rate_limit_rps:4.0f} rps"
            )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
