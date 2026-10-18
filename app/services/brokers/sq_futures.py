"""StrategyQuant Continuous Futures market data and symbol catalog client implementation.

Description:
    Implements a specialized market data client accessing StrategyQuant Continuous
    Futures historical data conforming to the uniform `BrokerClient` interface.
    Operates a resilient three-tier resolution architecture:
    1. Local native StrategyQuant 4.2 binary (.dat) archives.
    2. Local partitioned Parquet stores (D1 and M1).
    3. Direct remote streaming of Daily (EOD) historical bars from StrategyQuant CDN.
    Exposes canonical `SymbolInfo` objects and normalized historical bars.

Purpose:
    FEAT-BROKER-SQ-FUTURES: StrategyQuant Continuous Futures Market Data and Catalog Broker.

Key Capabilities:
    - FR-BROKER-SQ-FUTURES-SYMBOLS: Continuous Futures Symbol Catalog Resolution
      Associated: `[SQFuturesClient.get_symbol_info()]`, `[SQFuturesClient.get_symbols()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-FUTURES-MARKET-DATA: Historical Continuous Bar Ingestion
      Associated: `[SQFuturesClient.get_bars()]`
      Logging: Emits INFO log upon successfully parsing native SQ 4.2 dat,
      Parquet partitions, or remote StrategyQuant CDN stream.

Python API Usage:
    ```python
    from app.services.brokers.sq_futures import SQFuturesClient
    from app.services.include.enums import Timeframe

    client = SQFuturesClient()
    bars = client.get_bars("@ES", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    client.disconnect()
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker sq_futures`
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers._file_history import load_local_partition_bars
from app.services.brokers._http import execute_bounded_get
from app.services.brokers._native_history import decode_sq_dat_bytes
from app.services.brokers.base import (
    BridgeError,
    epoch_seconds,
)
from app.services.brokers.sq_equity import SQEquityClient
from app.services.include.contracts import MarketBar
from app.services.include.enums import Timeframe

logger = get_logger(__name__)

DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "market" / "sq_futures"
)
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "sq_futures.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = "HaruQuantAI-SQFuturesConnector/1.0"

__all__ = [
    "SQFuturesClient",
]


def _clean_symbol(sym: str) -> str:
    """Normalize continuous futures symbol."""
    s = sym.strip().upper()
    s = s.removesuffix(".D")
    s = s.removesuffix("_LIMITED")
    return s.removesuffix("_BENCHMARK")


def _find_sq_dat_file(base_dir: Path, symbol: str, timeframe: str) -> Path | None:
    """Locate the StrategyQuant .dat file for a symbol and timeframe."""
    if not base_dir.exists():
        return None

    clean = _clean_symbol(symbol).upper()
    if not clean:
        return None

    tf_str = timeframe.upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "M1" if is_m1 else "D1"

    for entry in base_dir.iterdir():
        if entry.is_dir():
            entry_clean = _clean_symbol(entry.name).upper()
            if entry_clean == clean:
                adj = entry / f"{entry.name}_{tf_tag}.dat"
                if adj.is_file():
                    return adj
                adj_clean = entry / f"{entry_clean}_{tf_tag}.dat"
                if adj_clean.is_file():
                    return adj_clean

    flat = base_dir / f"{clean}_{tf_tag}.dat"
    if flat.is_file():
        return flat

    return None


def _find_parquet_files(base_dir: Path, symbol: str, timeframe: str) -> list[Path]:
    """Locate local Parquet partition files for continuous futures."""
    if not base_dir.exists():
        return []

    clean = _clean_symbol(symbol).upper()
    tf_str = timeframe.upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "M1" if is_m1 else "D1"

    matches: list[Path] = []
    for entry in base_dir.iterdir():
        if entry.is_dir() and _clean_symbol(entry.name).upper() == clean:
            matches.extend(sorted(entry.glob(f"*{tf_tag}*.parquet")))

    if not matches:
        matches.extend(sorted(base_dir.glob(f"{clean}*{tf_tag}*.parquet")))

    return matches


class SQFuturesClient(SQEquityClient):
    """StrategyQuant Continuous Futures market data and symbol catalog client."""

    _provider_id = "sq_futures"
    _display_name = "SQ Futures Free Data"
    _health_label = "SQ Futures"
    _asset_label = "futures"
    _category = "Futures"
    _supported_timeframes: tuple[str, ...] = ("M1", "D1")
    _default_data_dir = DEFAULT_DATA_DIR
    _default_catalog_path = DEFAULT_CATALOG_PATH
    _default_contract_size = 50.0
    _user_agent = USER_AGENT
    _cdn_base_url = CDN_BASE_URL

    def __init__(
        self,
        name: str = "SQ_Futures",
        data_dir: str | Path | None = None,
        catalog_path: str | Path | None = None,
        sqx_history_dir: str | Path | None = None,
        enable_cdn_download: bool = True,
    ) -> None:
        """Initialize SQ Futures broker client."""
        super().__init__(
            name=name,
            data_dir=data_dir,
            catalog_path=catalog_path,
            sqx_history_dir=sqx_history_dir,
            enable_cdn_download=enable_cdn_download,
        )

    @override
    def _clean_sym(self, symbol: str) -> str:
        return _clean_symbol(symbol)

    @override
    def _find_dat(self, base_dir: Path, symbol: str, timeframe: str) -> Path | None:
        return _find_sq_dat_file(base_dir, symbol, timeframe)

    @override
    def _find_parquet(self, base_dir: Path, symbol: str, timeframe: str) -> list[Path]:
        return _find_parquet_files(base_dir, symbol, timeframe)

    @override
    def _http_get(self, url: str) -> Any:
        return execute_bounded_get(
            self.session, url, timeout=(5.0, 15.0), provider="sq_futures"
        )

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_D1,
        date_from: datetime | int | None = None,
        date_to: datetime | int | None = None,
        *,
        start: datetime | int | None = None,
        end: datetime | int | None = None,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar]:
        """Validate M1/D1 cadence and retrieve continuous futures bars."""
        del start_pos
        tf_name = timeframe.name if isinstance(timeframe, Timeframe) else str(timeframe)
        if tf_name.upper() not in (
            "M1",
            "PERIOD_M1",
            "1M",
            "D1",
            "PERIOD_D1",
            "1D",
            "DAY",
        ):
            raise BridgeError(
                f"StrategyQuant Continuous Futures only supports M1 and D1 timeframes, got '{timeframe}'",
                code="UNSUPPORTED_TIMEFRAME",
            )
        target_count = count or limit or 100
        s = date_from if date_from is not None else start
        e = date_to if date_to is not None else end
        start_sec = epoch_seconds(s)
        end_sec = epoch_seconds(e)
        date_from = (
            datetime.fromtimestamp(start_sec, tz=UTC) if 0 < start_sec < 2**40 else None
        )
        date_to = (
            datetime.fromtimestamp(end_sec, tz=UTC) if 0 < end_sec < 2**40 else None
        )

        parquet_files = self._find_parquet(self.data_dir, symbol, tf_name)
        if not parquet_files and self.sqx_history_dir:
            parquet_files = self._find_parquet(self.sqx_history_dir, symbol, tf_name)
        if parquet_files:
            parquet_bars = load_local_partition_bars(
                parquet_files,
                symbol=symbol,
                timeframe=tf_name,
                start=start_sec,
                end=end_sec,
                count=target_count,
            )
            if parquet_bars:
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
                    for r in parquet_bars
                ]

        dat_file = self._find_dat(self.data_dir, symbol, tf_name)
        if not dat_file and self.sqx_history_dir:
            dat_file = self._find_dat(self.sqx_history_dir, symbol, tf_name)
        if dat_file:
            rows = decode_sq_dat_bytes(
                dat_file.read_bytes(),
                count=target_count,
                date_from=date_from,
                date_to=date_to,
            )
            if rows:
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
                    for r in rows
                ]

        if self.enable_cdn_download and tf_name.upper() in ("D1", "1D", "PERIOD_D1"):
            cdn_bars = self._fetch_cdn_bars(
                symbol, count=target_count, date_from=date_from, date_to=date_to
            )
            if cdn_bars:
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
                    for r in cdn_bars
                ]

        raise BridgeError(
            f"No {self._asset_label} data found for symbol '{symbol}' ({tf_name})",
            code="NO_DATA",
        )


def main() -> None:
    """Demonstrate executable usage of SQFuturesClient."""
    client = SQFuturesClient()
    symbols = client.get_symbols()
    logger.info("SQ Futures symbols: %d available", len(symbols))
    client.disconnect()


if __name__ == "__main__":
    main()
