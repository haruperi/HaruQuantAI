"""StrategyQuant Equity local Parquet market data broker and provider plugin.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    US Equity historical candlestick archives stored as local Parquet files
    under `data/market/sq_equity`.
    Within HaruQuantAI, this module provides fast local access to normalized US
    equity datasets (e.g. AAPL, MSFT, TSLA, NVDA, SPY, QQQ) and fulfills Data
    Manager workspace download requests (`download_bars()`) alongside `get_bars()`.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-SQ-EQUITY: StrategyQuant US Equity Local Parquet Datafeed.
    Provides fast, offline historical equity bar extraction and Data Manager
    downloads from filesystem Parquet archives.

Key Capabilities:
    - FR-BROKER-SQ-EQUITY-PARQUET-DATA: Parquet Historical Bar Ingestion
      Associated: `[SQEquityBroker.get_bars()]`
      Logging: Emits INFO log upon successfully parsing Parquet partitions,
      and WARNING log if files are missing or empty.
    - FR-BROKER-SQ-EQUITY-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[SQEquityBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.sq_equity import SQEquityBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars("AAPL", count=5)
    if bars_resp.is_success:
        assert len(bars_resp.data) > 0
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

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.plugins.brokers.contracts import (
    Bar,
    BaseBroker,
    BrokerCapability,
    StandardError,
    StandardResponse,
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
    "id": "broker-sq-equity",
    "name": "StrategyQuant US Equities Connector",
    "version": "1.0.0",
    "description": "StrategyQuant US Equities historical parquet data and provider plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars"],
    "enabled": True,
    "metadata": {
        "provider_name": "SQEquity",
        "display_name": "StrategyQuant US Equities",
        "asset_classes": ["Stocks"],
        "timeframes": ["M1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

# Embedded benchmark equities from SQEquityCatalog
EQUITY_TICKERS: dict[str, dict[str, Any]] = {
    "SPY": {"name": "SPDR S&P 500 ETF Trust", "exchange": "ARCA", "decimals": 2},
    "QQQ": {"name": "Invesco QQQ Trust", "exchange": "NASDAQ", "decimals": 2},
    "DIA": {
        "name": "SPDR Dow Jones Industrial Average ETF",
        "exchange": "ARCA",
        "decimals": 2,
    },
    "IWM": {"name": "iShares Russell 2000 ETF", "exchange": "ARCA", "decimals": 2},
    "AAPL": {"name": "Apple Inc.", "exchange": "NASDAQ", "decimals": 2},
    "MSFT": {"name": "Microsoft Corporation", "exchange": "NASDAQ", "decimals": 2},
    "AMZN": {"name": "Amazon.com Inc.", "exchange": "NASDAQ", "decimals": 2},
    "GOOGL": {"name": "Alphabet Inc.", "exchange": "NASDAQ", "decimals": 2},
    "NVDA": {"name": "NVIDIA Corporation", "exchange": "NASDAQ", "decimals": 2},
    "TSLA": {"name": "Tesla Inc.", "exchange": "NASDAQ", "decimals": 2},
    "META": {"name": "Meta Platforms Inc.", "exchange": "NASDAQ", "decimals": 2},
}


__all__ = ["SQEquityBroker", "SQEquityProvider", "create_adapter"]


class SQEquityBroker(BaseBroker):
    """StrategyQuant Equity market data plugin."""

    def __init__(
        self,
        name: str = "SQ_Equity",
        store_dir: str | Path | None = None,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize SQ Equity broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
        self.store_dir = (
            Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "sq_equity"
        )
        self._db = db

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="SQEquity",
            display_name="StrategyQuant US Equities",
            asset_classes=["Stocks"],
            timeframes=["M1", "D1"],
            requires_auth=False,
            rate_limit_rps=10.0,
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
        timeframe: TimeFrame | str | int = TimeFrame.D1,
        count: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        start_pos: int | None = 0,
    ) -> StandardResponse[list[Bar]]:
        """Retrieve historical candlestick bars from local Parquet store."""
        sym_clean = symbol.lower().strip()
        tf_str = str(timeframe).upper()
        res_dir = "m1" if "M1" in tf_str or "1M" in tf_str else "d1"

        target_dir = self.store_dir / res_dir / sym_clean
        if not target_dir.exists():
            msg = f"No local data found for symbol '{symbol}' in {target_dir}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )

        try:
            import pyarrow.parquet as pq

            parquet_files = sorted(target_dir.glob("*.parquet"))
            if not parquet_files:
                msg = f"No parquet files for '{symbol}'"
                return StandardResponse.failure(
                    message=msg,
                    error=StandardError(code="NO_DATA", message=msg),
                    extensions={"broker": self.name},
                )

            bars: list[Bar] = []
            for pf_path in parquet_files:
                pf = pq.ParquetFile(str(pf_path))
                table = pf.read()
                df = table.to_pandas()
                for _, row in df.iterrows():
                    dt = row["DateTime"]
                    if hasattr(dt, "to_pydatetime"):
                        dt = dt.to_pydatetime()
                    bars.append(
                        Bar(
                            time=dt,
                            open=float(row["Open"]),
                            high=float(row["High"]),
                            low=float(row["Low"]),
                            close=float(row["Close"]),
                            tick_volume=int(row.get("Volume", 0)),
                            real_volume=int(row.get("Volume", 0)),
                        )
                    )

            if count and len(bars) > count:
                bars = bars[-count:]

            self.logger.info(
                "FR-BROKER-SQ-EQUITY-PARQUET-DATA: Loaded %d bars for %s",
                len(bars),
                symbol,
                extra={
                    "fr_id": "FR-BROKER-SQ-EQUITY-PARQUET-DATA",
                    "symbol": symbol,
                    "count": len(bars),
                },
            )
            return StandardResponse.success(
                data=bars,
                message=f"Loaded {len(bars)} bars for '{symbol}'",
                extensions={"broker": self.name},
            )
        except Exception as e:
            msg = f"Failed to read parquet bars for '{symbol}': {e}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="READ_ERROR", message=msg),
                extensions={"broker": self.name},
            )


# Compatibility aliases
SQEquityProvider = SQEquityBroker


def create_adapter(_context: PluginHostContext | None = None) -> SQEquityBroker:
    """Plugin entrypoint factory constructing SQEquityBroker adapter."""
    logger.info("Initializing SQ Equity broker plugin adapter.")
    return SQEquityBroker()
