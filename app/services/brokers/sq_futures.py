"""StrategyQuant Continuous Futures market data and symbol catalog broker implementation.

Description:
    Implements a specialized market data broker accessing StrategyQuant Continuous
    Futures historical data conforming to the `TradingBackend` protocol.
    Operates a resilient three-tier resolution architecture:
    1. Local native StrategyQuant 4.2 binary (.dat) archives.
    2. Local partitioned Parquet stores (D1 and M1).
    3. Direct remote streaming of Daily (EOD) historical bars from StrategyQuant CDN.
    Exposes canonical `SymbolInfo` objects and normalized historical bars.

Purpose:
    FEAT-BROKER-SQ-FUTURES: StrategyQuant Continuous Futures Market Data and Catalog Broker.

Key Capabilities:
    - FR-BROKER-SQ-FUTURES-SYMBOLS: Continuous Futures Symbol Catalog Resolution
      Associated: `[SQFuturesBroker.symbol_info()]`, `[SQFuturesBroker.symbols_get()]`
      Logging: Emits INFO log upon resolving symbol info or catalog count,
      and WARNING log if symbol is not found.
    - FR-BROKER-SQ-FUTURES-MARKET-DATA: Historical Continuous Bar Ingestion
      Associated: `[SQFuturesBroker.fetch_bars()]`
      Logging: Emits INFO log upon successfully parsing native SQ 4.2 dat,
      Parquet partitions, or remote StrategyQuant CDN stream.

Python API Usage:
    ```python
    from app.services.brokers.sq_futures import SQFuturesBroker
    from app.services.include.data import get_historical_bars
    from app.workspace.data_manager import Timeframe

    broker = SQFuturesBroker()
    bars = await get_historical_bars(broker, "@ES", Timeframe.PERIOD_D1, count=5)
    assert len(bars) > 0
    ```

CLI Usage:
    `uv run python -m scripts.examples.brokers_data --broker sq_futures`
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers._http import execute_bounded_get
from app.services.brokers.sq_equity import SQEquityBroker

logger = get_logger(__name__)

DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "market" / "sq_futures"
)
DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "symbols.csv"
CDN_BASE_URL = "https://cdn.strategyquantcdn.com/data/barchart_test/eod"
USER_AGENT = "HaruQuantAI-SQFuturesConnector/1.0"

PLUGIN_MANIFEST = {
    "id": "sq_futures",
    "name": "SQ Futures Free Data",
    "version": "1.0.0",
    "slot": "data.provider",
    "entry_point": "sq_futures:create_adapter",
    "description": "StrategyQuant Continuous Futures historical data provider",
    "capabilities": ["data.fetch"],
}

__all__ = [
    "CDN_BASE_URL",
    "PLUGIN_MANIFEST",
    "SQFuturesBroker",
    "create_adapter",
    "main",
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
                for f in entry.glob(f"*_{tf_tag}.dat"):
                    return f
        elif entry.is_file() and entry.name.endswith(".dat"):
            entry_clean = _clean_symbol(entry.stem).upper()
            if entry_clean == clean or entry_clean.startswith(clean):
                return entry

    return None


def _find_parquet_files(base_dir: Path, symbol: str, timeframe: str) -> list[Path]:
    """Find local Parquet partition files for a symbol and timeframe."""
    if not base_dir.exists():
        return []
    clean = _clean_symbol(symbol).lower()
    variants = [clean, clean.removeprefix("@"), f"@{clean.removeprefix('@')}"]
    tf_str = timeframe.upper()
    is_m1 = "M1" in tf_str or "1M" in tf_str
    tf_tag = "m1" if is_m1 else "d1"
    for var in variants:
        for cdir in (base_dir / tf_tag / var, base_dir / var / tf_tag):
            if cdir.is_dir():
                p_files = sorted(cdir.glob("*.parquet"))
                if p_files:
                    return p_files
    return []


class SQFuturesBroker(SQEquityBroker):
    """StrategyQuant Continuous Futures market data and symbol catalog broker."""

    _provider_id = "sq_futures"
    _display_name = "SQ Futures Free Data"
    _health_label = "SQ Futures"
    _asset_label = "futures"
    _category = "Futures"
    _supported_timeframes: tuple[str, ...] = ("M1", "D1")
    _allowed_history_timeframes: tuple[str, ...] = ("D1", "M1")
    _history_tf_error_prefix = (
        "StrategyQuant Futures only supports D1 and M1 timeframes"
    )
    _description = "StrategyQuant Continuous Futures historical data provider"
    _default_data_dir = DEFAULT_DATA_DIR
    _default_catalog_path = DEFAULT_CATALOG_PATH
    _alt_catalog_filename = "sq_futures.csv"
    _default_symbols: tuple[str, ...] = (
        "@ES",
        "@NQ",
        "@YM",
        "@RTY",
        "@CL",
        "@GC",
        "@SI",
        "@ZB",
    )
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
        """Initialize SQ Futures broker."""
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


def create_adapter(context: Any = None) -> SQFuturesBroker:
    """Plugin entrypoint factory constructing SQFuturesBroker adapter."""
    data_dir = getattr(context, "data_dir", None)
    return SQFuturesBroker(data_dir=data_dir)


def main() -> None:
    """Demonstrate executable usage of SQFuturesBroker."""
    broker = SQFuturesBroker()
    health = broker.check_health()
    logger.info("SQ Futures health: %s (connected=%s)", health.status, health.connected)


if __name__ == "__main__":
    main()
