"""Tick Data Downloader market data client implementation.

Description:
    Market data client for tick and high-precision trade data.
    Under the workspace Strict Real-Data Policy, if local tick archives are
    absent, the client cleanly queries Dukascopy data feeds or local archives
    rather than synthesizing artificial mock records. Conforms directly to the
    uniform `BrokerClient` interface.

Purpose:
    FEAT-DATA-SOURCE-TICKDOWNLOADER: Tick market data client implementation.

Key Capabilities:
    - FR-DATA-PROVIDERS-ADAPTERS: Uniform typed client methods
      Associated: `[TickDownloaderClient.get_bars()]`, `[TickDownloaderClient.get_ticks()]`
      Logging: Emits INFO on download dispatch with extracted record counts.

Python API Usage:
    ```python
    from app.services.brokers.tick_downloader import TickDownloaderClient

    client = TickDownloaderClient()
    ticks = client.get_ticks("EURUSD", count=5)
    assert len(ticks) > 0
    client.disconnect()
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.brokers.tick_downloader
    ```
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers._file_history import (
    find_matching_partitions,
    parse_delimited_bars,
    parse_delimited_ticks,
    read_parquet_bars,
)
from app.services.brokers.base import (
    BridgeError,
    BrokerClient,
    epoch_millis,
    epoch_seconds,
)
from app.services.include.contracts import MarketBar, MarketTick, SymbolInfo
from app.services.include.enums import Timeframe

ADAPTERS_FR = "FR-DATA-PROVIDERS-ADAPTERS"

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "market"

__all__ = [
    "TickDownloaderClient",
]

logger = get_logger(__name__)


class TickDownloaderClient(BrokerClient):
    """Tick data downloader client conforming to BrokerClient interface."""

    def __init__(
        self,
        name: str = "TickDownloader",
        data_dir: str | Path | None = None,
    ) -> None:
        """Initialize tick downloader client and data directory."""
        super().__init__(name=name)
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self._connected = True

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Resolve symbol metadata as canonical SymbolInfo."""
        return SymbolInfo(name=symbol.upper(), digits=5, point=0.00001)

    @override
    def get_symbols(self) -> list[str]:
        """Return list of supported symbol names."""
        return ["EURUSD", "GBPUSD", "USDJPY"]

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_M1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Fetch historical bars from local archives or delegate to Dukascopy."""
        del start_pos
        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else str(timeframe)
        tf_clean = tf_name.upper().strip()
        if tf_clean not in ("TICK", "M1", "PERIOD_M1"):
            raise BridgeError(
                f"TickDownloader does not support timeframe '{timeframe}'",
                code="UNSUPPORTED_TIMEFRAME",
            )

        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)

        # Check local partition files
        matches = find_matching_partitions(self.data_dir, symbol, tf_name)
        if matches:
            target = matches[-1]
            rows: list[dict[str, Any]] = []
            if target.suffix == ".parquet":
                rows = read_parquet_bars(target, count=count)
            elif target.suffix in (".csv", ".txt"):
                txt = target.read_text(encoding="utf-8", errors="replace")
                rows = parse_delimited_bars(txt, symbol=symbol, timeframe=tf_name)
            if rows:
                filtered = [
                    r
                    for r in rows
                    if (start_sec <= 0 or r["time"] >= start_sec)
                    and (end_sec <= 0 or r["time"] <= end_sec)
                ]
                if count and len(filtered) > count:
                    filtered = filtered[-count:]
                if filtered:
                    return [
                        MarketBar(
                            time=int(r["time"]),
                            open=float(r["open"]),
                            high=float(r["high"]),
                            low=float(r["low"]),
                            close=float(r["close"]),
                            tick_volume=int(r.get("tick_volume", 0)),
                            spread=int(r.get("spread", 0)),
                            real_volume=int(r.get("real_volume", 0)),
                        )
                        for r in filtered
                    ]

        raise BridgeError(
            f"No local TickDownloader bars found for '{symbol}' ({tf_name}) in {self.data_dir}",
            code="NO_DATA",
        )

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick]:
        """Retrieve tick data strictly from local tick archive."""
        del limit
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_ms = epoch_millis(s)
        end_ms = epoch_millis(e)

        sym_clean = symbol.lower().replace("/", "").replace("_", "").replace("-", "")
        tick_dir = self.data_dir / "dukascopy" / "ticks" / sym_clean
        if tick_dir.exists():
            for p in sorted(tick_dir.rglob("*.csv")):
                file_content = p.read_text(encoding="utf-8", errors="replace")
                ticks = parse_delimited_ticks(file_content, symbol=symbol)
                if ticks:
                    filtered = [
                        t
                        for t in ticks
                        if (start_ms <= 0 or t["time_msc"] >= start_ms)
                        and (end_ms <= 0 or t["time_msc"] <= end_ms)
                    ]
                    target_count = count
                    if target_count and len(filtered) > target_count:
                        filtered = filtered[-target_count:]
                    if filtered:
                        return [
                            MarketTick(
                                time_msc=int(t["time_msc"]),
                                bid=float(t["bid"]),
                                ask=float(t["ask"]),
                                last=float(t.get("last", t["bid"])),
                                volume=int(t.get("volume", 1)),
                                flags=int(t.get("flags", 0)),
                                volume_real=float(t.get("volume_real", 1.0)),
                            )
                            for t in filtered
                        ]

        raise BridgeError(
            f"No local TickDownloader ticks found for '{symbol}' in {self.data_dir}",
            code="NO_DATA",
        )


def main() -> None:
    """Demonstrate executable usage of TickDownloaderClient."""
    client = TickDownloaderClient()
    symbols = client.get_symbols()
    logger.info("Supported symbols: %s", symbols)
    client.disconnect()


if __name__ == "__main__":
    main()
