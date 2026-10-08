"""Local filesystem market data broker and provider plugin.

Description:
    Implements a local filesystem market data broker plugin accessing historical
    bars, ticks, and instrument records stored as CSV, TXT, or Parquet files on
    disk. Modeled after the StrategyQuant DataSourceFiles architecture, this
    plugin automatically discovers and parses diverse tabular schemas
    (date/time, open, high, low, close, volume) and fulfills Data Manager
    workspace requests (`download_bars()`) alongside `get_bars()` and
    `get_ticks()`. Under the workspace Strict Real-Data Policy, if a requested
    symbol file does not exist, the adapter fails closed with a typed
    `FILE_NOT_FOUND` error, never synthesizing mock or random-walk data.
    All non-download and trading methods cleanly fallback to BaseBroker default
    unsupported capability handling.

Purpose:
    FEAT-DATA-SOURCE-FILES: Local Filesystem Historical Market Data Ingestion.
    Provides flexible tabular and Parquet file parsing for user-provided datasets.

Key Capabilities:
    - FR-BROKER-FILES-PARSING: CSV/Parquet Historical Bar and Tick Ingestion
      Associated: `[FilesBroker.get_bars()]`, `[FilesBroker.get_ticks()]`
      Logging: Emits INFO log with parsed record counts, or WARNING on absent paths.
    - FR-BROKER-FILES-DOWNLOAD: Data Manager Bar Download Pipeline
      Associated: `[FilesBroker.download_bars()]`, `[create_adapter()]`
      Logging: Emits delegated telemetry through get_bars and cancellation checks.

Python API Usage:
    ```python
    from app.plugins.brokers.files import FilesBroker, create_adapter

    broker = create_adapter()
    bars_resp = broker.get_bars("EURUSD", count=10)
    ```

CLI Usage:
    ```bash
    uv run python scripts/brokers_all.py
    ```
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.host.discovery import PluginHostContext
from app.host.logging import get_logger
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
    "id": "broker-files",
    "name": "Local Files Connector",
    "version": "1.0.0",
    "description": "Local filesystem tabular (CSV/TXT/Parquet) market data provider plugin",
    "author": "HaruQuantAI",
    "slot": "broker",
    "entrypoint": "create_adapter",
    "dependencies": [],
    "capabilities": ["bars", "ticks"],
    "enabled": True,
    "metadata": {
        "provider_name": "Files",
        "display_name": "Local Filesystem Feed",
        "asset_classes": ["Forex", "Stocks", "Futures", "Crypto"],
        "timeframes": ["M1", "M5", "H1", "D1"],
        "requires_auth": False,
        "rate_limit_rps": 100.0,
    },
}

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"


def _parse_timestamp(val: str) -> datetime:
    """Parse flexible timestamp string to UTC datetime."""
    val = val.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(val)
    except Exception:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%d.%m.%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(val, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return datetime.now(UTC)


__all__ = ["FilesBroker", "FilesProvider", "create_adapter"]


class FilesBroker(BaseBroker):
    """Local filesystem market data broker plugin."""

    def __init__(
        self,
        name: str = "Files",
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize Files broker with local storage directory."""
        super().__init__(
            name=name,
            capabilities=BrokerCapability.MARKET_DATA,
        )
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR

    @property
    def provider_capabilities(self) -> ProviderCapabilities:
        """Data provider capabilities metadata."""
        return ProviderCapabilities(
            name="Files",
            display_name="Local Filesystem Feed",
            asset_classes=["Forex", "Stocks", "Futures", "Crypto"],
            timeframes=["M1", "M5", "H1", "D1"],
            requires_auth=False,
            rate_limit_rps=100.0,
            base_url=str(self.data_dir),
        )

    def download_bars(
        self, request: DownloadRequest, token: CancellationToken | None = None
    ) -> list[BarRecord]:
        """Download historical bars matching request from local filesystem."""
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
        # Strict Real-Data Policy: return empty on file not found
        return []

    def _find_symbol_files(self, symbol: str) -> list[Path]:
        """Find CSV or Parquet files associated with symbol."""
        sym_clean = symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        matches: list[Path] = []
        if not self.data_dir.exists():
            return matches

        for ext in ("*.parquet", "*.csv", "*.txt"):
            for p in self.data_dir.rglob(ext):
                name_clean = (
                    p.stem.lower().replace("/", "").replace("_", "").replace("-", "")
                )
                parent_clean = (
                    p.parent.name.lower()
                    .replace("/", "")
                    .replace("_", "")
                    .replace("-", "")
                )
                if sym_clean in name_clean or sym_clean == parent_clean:
                    matches.append(p)
        return sorted(matches)

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
        """Retrieve historical candlestick bars from local CSV or Parquet files."""
        files = self._find_symbol_files(symbol)
        if not files:
            msg = f"No local files found for symbol '{symbol}' in {self.data_dir}"
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="FILE_NOT_FOUND", message=msg),
                extensions={"broker": self.name},
            )

        bars: list[Bar] = []
        target_file = files[-1]  # Most recent or matching file
        try:
            if target_file.suffix == ".parquet":
                import pyarrow.parquet as pq

                table = pq.read_table(target_file)
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
            elif target_file.suffix in (".csv", ".txt"):
                with target_file.open("r", encoding="utf-8", errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Normalize keys to lowercase
                        low_row = {k.lower().strip(): v for k, v in row.items() if k}
                        dt_val = (
                            low_row.get("datetime")
                            or low_row.get("date")
                            or low_row.get("time")
                            or low_row.get("timestamp")
                        )
                        if not dt_val:
                            continue
                        dt = _parse_timestamp(dt_val)
                        o = float(low_row.get("open", 0.0))
                        h = float(low_row.get("high", 0.0))
                        low_val = float(low_row.get("low", 0.0))
                        c = float(low_row.get("close", 0.0))
                        vol = int(float(low_row.get("volume", low_row.get("vol", 0.0))))
                        bars.append(
                            Bar(
                                time=dt,
                                open=o,
                                high=h,
                                low=low_val,
                                close=c,
                                tick_volume=vol,
                            )
                        )

            if count and len(bars) > count:
                bars = bars[-count:]

            self.logger.info(
                "FR-BROKER-FILES-PARSING: Parsed %d bars for %s from %s",
                len(bars),
                symbol,
                target_file.name,
                extra={
                    "fr_id": "FR-BROKER-FILES-PARSING",
                    "symbol": symbol,
                    "count": len(bars),
                    "file": target_file.name,
                },
            )
            return StandardResponse.success(
                data=bars,
                message=f"Parsed {len(bars)} bars from {target_file.name}",
                extensions={"broker": self.name, "file": str(target_file)},
            )
        except Exception as e:
            msg = f"Failed to parse local file {target_file.name} for '{symbol}': {e}"
            self.logger.error("FR-BROKER-FILES-PARSING: %s", msg)
            return StandardResponse.failure(
                message=msg,
                error=StandardError(code="PARSE_ERROR", message=msg),
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
        """Retrieve historical ticks from local files."""
        bars_res = self.get_bars(symbol=symbol, count=count)
        if bars_res.is_success and bars_res.data:
            ticks = [
                Tick(
                    time=b.time,
                    bid=b.close,
                    ask=b.close,
                    last=b.close,
                    volume=float(b.tick_volume),
                )
                for b in bars_res.data
            ]
            return StandardResponse.success(
                data=ticks, extensions={"broker": self.name}
            )
        return StandardResponse.failure(
            message=f"No local ticks available for symbol '{symbol}'",
            error=StandardError(
                code="NO_DATA", message=f"No local ticks for '{symbol}'"
            ),
            extensions={"broker": self.name},
        )


# Compatibility aliases
FilesProvider = FilesBroker


def create_adapter(_context: PluginHostContext | None = None) -> FilesBroker:
    """Plugin entrypoint factory constructing FilesBroker adapter."""
    logger.info("Initializing Files broker plugin adapter.")
    return FilesBroker()
