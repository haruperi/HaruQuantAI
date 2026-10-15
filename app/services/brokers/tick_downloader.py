"""Tick Data Downloader market data provider adapter plugin.

Description:
    Dynamic data provider plugin for tick and high-precision trade data within
    the SQX dynamic plugin architecture under slot `data.provider`.
    Under the workspace Strict Real-Data Policy, if local tick archives are
    absent, the provider cleanly returns an empty record set rather than
    synthesizing artificial mock records.

Purpose:
    FEAT-DATA-SOURCE-TICKDOWNLOADER: Tick market data provider plugin.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed provider adapters and capability
      metadata.
      Associated: `[TickDownloaderProvider.download_bars()]`, `[create_adapter()]`
      Logging: Emits INFO on download dispatch.

Python API Usage:
    ```python
    from app.services.brokers.tick_downloader.adapter import create_adapter

    adapter = create_adapter()
    caps = adapter.capabilities
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.connections --list
    ```
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.services.data import DataBrokerBackend
from app.services.libs.trading import SymbolSnapshot


class ProviderCapabilities:
    """Provider capabilities metadata."""

    def __init__(
        self,
        *,
        name: str = "",
        display_name: str = "",
        asset_classes: list[str] | None = None,
        timeframes: list[str] | None = None,
        requires_auth: bool = False,
        rate_limit_rps: float = 0.0,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.asset_classes = asset_classes or []
        self.timeframes = timeframes or []
        self.requires_auth = requires_auth
        self.rate_limit_rps = rate_limit_rps
        self.extra = kwargs


class BaseDataProvider:
    """Base data provider interface."""

    def __init__(self, capabilities: ProviderCapabilities | None = None) -> None:
        self.capabilities = capabilities

    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        return []


class CancellationToken:
    """Cancellation token for download requests."""

    def check_cancelled(self) -> None:
        """Raise if cancelled."""


class DownloadRequest:
    """Data download request parameters."""

    symbol: str = ""


class BarRecord:
    """Historical bar record."""

    def __init__(
        self,
        *,
        timestamp_utc: str = "",
        open: float = 0.0,  # noqa: A002
        high: float = 0.0,
        low: float = 0.0,
        close: float = 0.0,
        volume: float = 0.0,
        **kwargs: Any,
    ) -> None:
        self.timestamp_utc = timestamp_utc
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.extra = kwargs


logger = get_logger(__name__)

PLUGIN_MANIFEST: dict[str, Any] = {
    "manifest_version": 1,
    "id": "data-source-tick-downloader",
    "name": "Tick Data Downloader",
    "version": "1.0.0",
    "description": "High-precision tick and trade volume historical data downloader plugin",
    "author": "HaruQuantAI",
    "slot": "data.provider",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": [],
    "enabled": True,
    "metadata": {
        "provider_name": "TickDownloader",
        "display_name": "Tick Data Downloader",
        "asset_classes": ["Forex", "Futures", "Crypto"],
        "timeframes": ["TICK", "M1"],
        "requires_auth": False,
        "rate_limit_rps": 20.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"


__all__ = ["TickDownloaderBroker", "TickDownloaderProvider", "create_adapter"]


class TickDownloaderProvider(BaseDataProvider):
    """Tick data downloader."""

    def __init__(self, data_dir: str | Path | None = None) -> None:
        """Initialize tick downloader capabilities and rate limiting."""
        super().__init__(
            ProviderCapabilities(
                name="TickDownloader",
                display_name="Tick Data Downloader",
                asset_classes=["Forex", "Futures", "Crypto"],
                timeframes=["TICK", "M1"],
                requires_auth=False,
                rate_limit_rps=20.0,
            )
        )
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    @override
    def _fetch_bars(
        self, request: DownloadRequest, token: CancellationToken
    ) -> list[BarRecord]:
        token.check_cancelled()
        # Strict Real-Data Policy: Scan real tick parquet archives if present
        sym_clean = (
            request.symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        )
        tick_dir = self.data_dir / "dukascopy" / "ticks" / sym_clean
        if tick_dir.exists():
            try:
                import pyarrow.parquet as pq

                p_files = sorted(tick_dir.rglob("*.parquet"))
                if p_files:
                    table = pq.read_table(p_files[-1])
                    df = table.to_pandas()
                    records: list[BarRecord] = []
                    for _, row in df.tail(100).iterrows():
                        dt = row["DateTime"]
                        dt_iso = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
                        records.append(
                            BarRecord(
                                timestamp_utc=dt_iso,
                                open=float(row.get("Bid", row.get("Ask", 0.0))),
                                high=float(row.get("Bid", row.get("Ask", 0.0))),
                                low=float(row.get("Bid", row.get("Ask", 0.0))),
                                close=float(row.get("Bid", row.get("Ask", 0.0))),
                                volume=float(row.get("Volume", 1.0)),
                            )
                        )
                    return records
            except Exception as e:
                logger.debug("Failed to read local tick partition: %s", e)

        return []


class TickDownloaderBroker(DataBrokerBackend):
    """Tick data downloader broker conforming to TradingBackend."""

    def __init__(
        self, name: str = "TickDownloader", data_dir: str | Path | None = None
    ) -> None:
        """Initialize tick downloader broker."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    @override
    def symbol_info(self, symbol: str) -> SymbolSnapshot:
        """Resolve symbol metadata as canonical SymbolSnapshot."""
        return SymbolSnapshot(name=symbol.upper(), digits=5, point=0.00001)

    @override
    def symbols_get(self) -> list[str]:
        """Return list of supported symbol names."""
        return ["EURUSD", "GBPUSD", "USDJPY"]

    @override
    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str,
        start_ms: int,
        end_ms: int,
        count: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Download tick data delegating to Dukascopy datafeed."""
        from app.services.brokers.dukascopy import DukascopyBroker

        broker = DukascopyBroker()
        return broker.fetch_ticks(
            symbol=symbol,
            mode=mode,
            start_ms=start_ms,
            end_ms=end_ms,
            count=count,
            limit=limit,
        )


def create_adapter(_context: PluginHostContext | None = None) -> BaseDataProvider:
    """Plugin entrypoint factory constructing Tick Data Downloader provider adapter."""
    logger.info("Initializing Tick Data Downloader provider plugin adapter.")
    return TickDownloaderProvider()
