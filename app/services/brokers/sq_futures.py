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

from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    execute_bounded_get,
)
from app.services.brokers.sq_equity import SQEquityClient
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
    def _validate_timeframe(self, timeframe: Timeframe | str, tf_name: str) -> None:
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


def main() -> None:
    """Demonstrate executable usage of SQFuturesClient."""
    client = SQFuturesClient()
    symbols = client.get_symbols()
    logger.info("SQ Futures symbols: %d available", len(symbols))
    client.disconnect()


if __name__ == "__main__":
    main()
