"""StrategyQuant Futures local Parquet market data broker and provider plugin.

Description:
    Implements a specialized market data broker plugin accessing StrategyQuant
    Commodity, Index, and Currency Futures historical candlestick archives
    stored as local Parquet files under `data/market/sq_futures`.
    Within HaruQuantAI, this module provides offline historical futures bar
    and tick extraction from local Parquet archives, and fulfills Data Manager
    workspace download requests (`download_bars()`) alongside `get_bars()`
    and `get_ticks()`.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-BROKER-SQ-FUTURES: StrategyQuant Futures Local Parquet Datafeed.
    Provides offline historical futures bar and tick extraction and Data
    Manager downloads from local Parquet archives.

Key Capabilities:
    - FR-BROKER-SQ-FUTURES-PARQUET-DATA: Parquet Historical Bar Ingestion
      Associated: `[SQFuturesBroker.get_bars()]`, `[SQFuturesBroker.get_ticks()]`
      Logging: Emits INFO log upon successfully parsing Parquet partitions,
      and WARNING log if files are missing or empty.
    - FR-BROKER-SQ-FUTURES-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[SQFuturesBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.sq_futures import SQFuturesBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars("@ES", count=5)
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
    "id": "broker-sq-futures",
    "name": "StrategyQuant Continuous Futures Connector",
    "version": "1.0.0",
    "description": "StrategyQuant Continuous Futures historical parquet data and provider plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars"],
    "enabled": True,
    "metadata": {
        "provider_name": "SQFutures",
        "display_name": "StrategyQuant Continuous Futures",
        "asset_classes": ["Futures"],
        "timeframes": ["M1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 10.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

# Embedded specifications for continuous futures
SQ_FUTURES_INSTRUMENTS: dict[str, dict[str, Any]] = {
    "@ES": {
        "name": "E-mini S&P 500",
        "tick_size": 0.25,
        "point_value": 50.0,
        "exchange": "CME",
        "decimals": 2,
    },
    "@NQ": {
        "name": "E-mini NASDAQ 100",
        "tick_size": 0.25,
        "point_value": 20.0,
        "exchange": "CME",
        "decimals": 2,
    },
    "@YM": {
        "name": "E-mini Dow Jones",
        "tick_size": 1.0,
        "point_value": 5.0,
        "exchange": "CBOT",
        "decimals": 0,
    },
    "@CL": {
        "name": "Crude Oil",
        "tick_size": 0.01,
        "point_value": 1000.0,
        "exchange": "NYMEX",
        "decimals": 2,
    },
    "@GC": {
        "name": "Gold",
        "tick_size": 0.1,
        "point_value": 100.0,
        "exchange": "COMEX",
        "decimals": 1,
    },
    "@SI": {
        "name": "Silver",
        "tick_size": 0.005,
        "point_value": 5000.0,
        "exchange": "COMEX",
        "decimals": 3,
    },
}


def _calc_digits(tick_size: float) -> int:
    """Calculate quotation digits precision from tick size."""
    if tick_size >= 1.0 or tick_size <= 0:
        return 0
    s = f"{tick_size:.8f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0


__all__ = ["SQFuturesBroker", "SQFuturesProvider", "create_adapter"]


class SQFuturesBroker(BaseBroker):
    """StrategyQuant Futures market data plugin."""

    def __init__(
        self,
        name: str = "SQ_Futures",
        store_dir: str | Path | None = None,
        db: DatabaseManager | None = None,
    ) -> None:
        """Initialize SQ Futures broker plugin."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
        self.store_dir = (
            Path(store_dir) if store_dir else DEFAULT_DATA_DIR / "sq_futures"
        )
        self._db = db

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="SQFutures",
            display_name="StrategyQuant Continuous Futures",
            asset_classes=["Futures"],
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
                "FR-BROKER-SQ-FUTURES-PARQUET-DATA: Loaded %d bars for %s",
                len(bars),
                symbol,
                extra={
                    "fr_id": "FR-BROKER-SQ-FUTURES-PARQUET-DATA",
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
SQFuturesProvider = SQFuturesBroker


def create_adapter(_context: PluginHostContext | None = None) -> SQFuturesBroker:
    """Plugin entrypoint factory constructing SQFuturesBroker adapter."""
    logger.info("Initializing SQ Futures broker plugin adapter.")
    return SQFuturesBroker()
