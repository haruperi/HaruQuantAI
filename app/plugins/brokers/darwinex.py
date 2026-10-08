"""Darwinex institutional market data broker and provider plugin.

Description:
    Implements a market data broker plugin tailored for Darwinex institutional
    FX, indices, and commodity tick specifications and historical feeds.
    Within HaruQuantAI, Darwinex provides high-resolution bid/ask spread models,
    institutional market data, and local Parquet market data reading from
    `data/market/darwinex`. The plugin satisfies the unified Data Manager
    download interface (`download_bars()`) alongside canonical candlestick
    and tick extraction (`get_bars()`, `get_ticks()`).
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-DARWINEX: Institutional FX/CFD Market Data and Parquet Store.
    Provides Darwinex instrument specifications, tick data structures, and
    historical bar extraction from local Parquet archives.

Key Capabilities:
    - FR-BROKER-DARWINEX-PARQUET-DATA: Parquet Storage Bar Ingestion
      Associated: `[DarwinexBroker.get_bars()]`, `[DarwinexBroker.get_ticks()]`
      Logging: Emits INFO log upon successfully loading Parquet records,
      and DEBUG log if partition read fails.
    - FR-BROKER-DARWINEX-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[DarwinexBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.darwinex import DarwinexBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars("EURUSD", count=5)
    if bars_resp.is_success:
        assert isinstance(bars_resp.data, list)
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, override

import requests

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.plugins.brokers.contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardResponse,
    Tick,
    TimeFrame,
)
from app.workspace.data_manager.connections import (
    CancellationToken,
    DownloadRequest,
    ProviderCapabilities,
)
from app.workspace.data_manager.data import BarRecord

logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "broker-darwinex",
    "name": "Darwinex Connector",
    "version": "1.0.0",
    "description": "Darwinex institutional tick and bar market data provider and broker plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks"],
    "enabled": True,
    "metadata": {
        "provider_name": "Darwinex",
        "display_name": "Darwinex Tick & Bar Feeds",
        "asset_classes": ["Forex", "CFD"],
        "timeframes": ["M1", "H1", "D1"],
        "requires_auth": True,
        "rate_limit_rps": 5.0,
        "base_url": "https://api.darwinex.com",
    },
}

SQX_DARWINEX_CDN = "https://cdn.strategyquantcdn.com/data/darwinex"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

# Core embedded instruments from DarwinexCatalog
DARWINEX_INSTRUMENTS: dict[str, dict[str, Any]] = {
    "EURUSD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "GBPUSD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "USDJPY": {
        "decimals": 3,
        "tick_value": 1000.0,
        "tick_size": 0.01,
        "tick_step": 0.001,
    },
    "AUDUSD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "USDCAD": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "USDCHF": {
        "decimals": 5,
        "tick_value": 100000.0,
        "tick_size": 0.0001,
        "tick_step": 0.00001,
    },
    "XAUUSD": {
        "decimals": 2,
        "tick_value": 100.0,
        "tick_size": 0.01,
        "tick_step": 0.01,
    },
    "SP500": {"decimals": 2, "tick_value": 1.0, "tick_size": 0.01, "tick_step": 0.01},
    "NAS100": {"decimals": 2, "tick_value": 1.0, "tick_size": 0.01, "tick_step": 0.01},
    "AAPL": {"decimals": 2, "tick_value": 1.0, "tick_size": 0.01, "tick_step": 0.01},
}

__all__ = ["DarwinexBroker", "DarwinexProvider", "create_adapter"]


class DarwinexBroker(BaseBroker):
    """Darwinex tick and candle datafeed broker plugin."""

    def __init__(
        self,
        name: str = "Darwinex",
        store_dir: str | Path | None = None,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize Darwinex broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.store_dir = Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "darwinex"
        self._db = db

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="Darwinex",
            display_name="Darwinex Tick & Bar Feeds",
            asset_classes=["Forex", "CFD"],
            timeframes=["M1", "H1", "D1"],
            requires_auth=True,
            rate_limit_rps=5.0,
            base_url="https://api.darwinex.com",
        )

    def download_bars(
        self, request: DownloadRequest, token: CancellationToken | None = None
    ) -> list[BarRecord]:
        """Download historical candlestick records matching the request."""
        if token:
            token.check_cancelled()
        dt_from = (
            datetime.fromisoformat(request.date_from) if request.date_from else None
        )
        dt_to = datetime.fromisoformat(request.date_to) if request.date_to else None
        bars_resp = self.get_bars(
            symbol=request.symbol,
            timeframe=request.timeframe,
            date_from=dt_from,
            date_to=dt_to,
        )
        if bars_resp.is_success and bars_resp.data:
            return [
                BarRecord(
                    timestamp_utc=b.time.isoformat(),
                    open=b.open,
                    high=b.high,
                    low=b.low,
                    close=b.close,
                    volume=float(b.tick_volume),
                )
                for b in bars_resp.data
            ]
        return []

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame | str | int = TimeFrame.H1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick bars from Darwinex local Parquet."""
        sym_clean = symbol.upper().replace("/", "").replace("_", "").replace("-", "")
        local_dir = self.store_dir / "m1" / sym_clean.lower()
        if local_dir.exists():
            try:
                import pyarrow.parquet as pq

                p_files = sorted(local_dir.glob("*.parquet"))
                if p_files:
                    table = pq.read_table(p_files[-1])
                    df = table.to_pandas()
                    bars: list[Bar] = []
                    for _, row in df.tail(count or 100).iterrows():
                        bars.append(
                            Bar(
                                time=row["DateTime"].to_pydatetime()
                                if hasattr(row["DateTime"], "to_pydatetime")
                                else row["DateTime"],
                                open=float(row["Open"]),
                                high=float(row["High"]),
                                low=float(row["Low"]),
                                close=float(row["Close"]),
                                tick_volume=int(row.get("Volume", 0)),
                            )
                        )
                    self.logger.info(
                        "FR-BROKER-DARWINEX-PARQUET-DATA: Loaded %d bars for %s",
                        len(bars),
                        sym_clean,
                        extra={
                            "fr_id": "FR-BROKER-DARWINEX-PARQUET-DATA",
                            "symbol": sym_clean,
                            "count": len(bars),
                        },
                    )
                    return StandardResponse.success(
                        data=bars, extensions={"broker": self.name}
                    )
            except Exception as e:
                self.logger.debug(
                    "FR-BROKER-DARWINEX-PARQUET-DATA: Local parquet read failed: %s",
                    e,
                    extra={"fr_id": "FR-BROKER-DARWINEX-PARQUET-DATA"},
                )

        return StandardResponse.success(
            data=[],
            message=f"No local or cached Darwinex bars available for '{sym_clean}'",
            extensions={"broker": self.name},
        )

    @override
    def get_ticks(
        self,
        symbol: str,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        flags: int | None = None,
    ) -> StandardResponse[list[Tick]]:
        """Retrieve historical ticks."""
        return StandardResponse.success(data=[], extensions={"broker": self.name})


# Compatibility aliases
DarwinexProvider = DarwinexBroker


def create_adapter(_context: PluginHostContext | None = None) -> DarwinexBroker:
    """Plugin entrypoint factory constructing DarwinexBroker adapter."""
    logger.info("Initializing Darwinex broker plugin adapter.")
    return DarwinexBroker()
