"""Market data download examples for all supported data brokers in HaruQuantAI.

Description:
    Demonstrates downloading real historical candlestick bars and ticks from all
    available data providers via the canonical quantitative data API in
    `app.workspace.data_manager` (`get_historical_bars` and `get_ticks`).
    Each data broker implements the `TradingBackend` protocol, allowing callers to
    retrieve normalized, validated `MarketBar` and `MarketTick` sequences regardless
    of the underlying vendor transport (Yahoo REST, Binance REST, StrategyQuant CDN,
    local Parquet, or headless simulation).

Purpose:
    FEAT-BROKER-DATA-EXAMPLES: Universal broker data ingestion demonstration.

Key Capabilities:
    - FR-BROKER-DATA-DOWNLOADS: Download historical bars from all brokers via data lib.
      Associated: `download_all()`, `demo_yahoo()`, `demo_binance()`,
      `demo_dukascopy()`, `demo_darwinex()`, `demo_sq_equity()`,
      `demo_sq_futures()`, `demo_files()`, `demo_simulator()`
      Logging: INFO on download dispatches and bar summary output.

Python API Usage:
    ```python
    import asyncio
    from scripts.examples.brokers_data import download_all

    asyncio.run(download_all())
    ```

CLI Usage:
    ```bash
    uv run python -m scripts.examples.brokers_data
    uv run python -m scripts.examples.brokers_data --broker binance
    ```
"""

from __future__ import annotations

import argparse
import asyncio

import pandas as pd  # type: ignore[import-untyped]
from app.host.logging import get_logger
from app.services.brokers import (
    BinanceClient,
    DarwinexClient,
    DukascopyClient,
    FilesClient,
    SimulatorClient,
    SQEquityClient,
    SQFuturesClient,
    YahooClient,
)
from app.services.include.contracts import (
    MarketBar,
    SymbolInfo,
)
from app.services.include.data import (
    get_historical_bars,
    get_ticks,
)
from app.services.include.enums import Timeframe

logger = get_logger(__name__)


def _print_bars_table(name: str, symbol: str, bars: pd.DataFrame) -> None:
    """Print formatted summary table of retrieved DataFrame bar records."""
    sep = "=" * 80
    print(f"\n{sep}")
    print(f"  BROKER: {name:20s} | SYMBOL: {symbol:10s} | BARS: {len(bars)}")
    print(sep)
    print(
        f"{'TIMESTAMP (UTC)':22s} {'OPEN':>12s} {'HIGH':>12s} {'LOW':>12s} "
        f"{'CLOSE':>12s} {'VOLUME':>12s}"
    )
    print("-" * 80)
    for ts, row in bars.iterrows():
        dt_str = str(ts)
        o_val = float(row["Open"])
        h_val = float(row["High"])
        l_val = float(row["Low"])
        c_val = float(row["Close"])
        v = int(row.get("Volume", 0))
        print(
            f"{dt_str:22s} {o_val:12.4f} {h_val:12.4f} {l_val:12.4f} "
            f"{c_val:12.4f} {v:12d}"
        )
    print(sep)


def _print_ticks_table(name: str, symbol: str, ticks: pd.DataFrame) -> None:
    """Print formatted summary table of retrieved DataFrame tick records."""
    sep = "=" * 80
    print(f"\n{sep}")
    print(f"  BROKER: {name:20s} | SYMBOL: {symbol:10s} | TICKS: {len(ticks)}")
    print(sep)
    print(
        f"{'TIMESTAMP (UTC)':24s} {'BID':>12s} {'ASK':>12s} {'LAST':>12s} "
        f"{'VOLUME':>12s}"
    )
    print("-" * 80)
    for ts, row in ticks.iterrows():
        dt_str = str(ts)
        b = float(row["Bid"])
        a = float(row["Ask"])
        last = float(row.get("Last", 0.0))
        v = float(row.get("Volume", 0.0))
        print(f"{dt_str:24s} {b:12.4f} {a:12.4f} {last:12.4f} {v:12.2f}")
    print(sep)


async def demo_yahoo(count: int = 5) -> pd.DataFrame:
    """Download historical Daily bars for AAPL from Yahoo Finance."""
    broker = YahooClient()
    symbol = "AAPL"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_D1, count=count)
    _print_bars_table("Yahoo Finance", symbol, bars)
    assert len(bars) > 0, "Yahoo Finance returned no bars"
    return bars


async def demo_binance(count: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download historical 1H klines and live ticks for BTCUSDT from Binance."""
    broker = BinanceClient()
    symbol = "BTCUSDT"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_H1, count=count)
    _print_bars_table("Binance (Klines)", symbol, bars)
    assert len(bars) > 0, "Binance returned no bars"

    ticks = await get_ticks(broker, symbol, count=count)
    _print_ticks_table("Binance (Live Ticks)", symbol, ticks)
    assert len(ticks) > 0, "Binance returned no ticks"
    return bars, ticks


async def demo_dukascopy(count: int = 5) -> pd.DataFrame:
    """Download historical M1 bars for EURUSD from Dukascopy CDN."""
    broker = DukascopyClient()
    symbol = "EURUSD"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_M1, count=count)
    _print_bars_table("Dukascopy Bank", symbol, bars)
    assert len(bars) > 0, "Dukascopy returned no bars"
    return bars


async def demo_darwinex(count: int = 5) -> pd.DataFrame:
    """Download historical Daily bars for EURUSD from Darwinex CDN."""
    broker = DarwinexClient()
    symbol = "EURUSD"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_D1, count=count)
    _print_bars_table("Darwinex Institutional", symbol, bars)
    assert len(bars) > 0, "Darwinex returned no bars"
    return bars


async def demo_sq_equity(count: int = 5) -> pd.DataFrame:
    """Download historical Daily bars for AAPL from StrategyQuant US Equities."""
    broker = SQEquityClient()
    symbol = "AAPL"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_D1, count=count)
    _print_bars_table("SQ US Equities", symbol, bars)
    assert len(bars) > 0, "SQ US Equities returned no bars"
    return bars


async def demo_sq_futures(count: int = 5) -> pd.DataFrame:
    """Download historical Daily bars for @ES from StrategyQuant Continuous Futures."""
    broker = SQFuturesClient()
    symbol = "@ES"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_D1, count=count)
    _print_bars_table("SQ Continuous Futures", symbol, bars)
    assert len(bars) > 0, "SQ Continuous Futures returned no bars"
    return bars


async def demo_files(count: int = 5) -> pd.DataFrame:
    """Download historical M1 bars for EURUSD from local filesystem Parquet archives."""
    broker = FilesClient(data_dir="data/market/dukascopy/m1")
    symbol = "EURUSD"
    bars = await get_historical_bars(broker, symbol, Timeframe.PERIOD_M1, count=count)
    _print_bars_table("Local Filesystem", symbol, bars)
    assert len(bars) > 0, "FilesBroker returned no bars"
    return bars


async def demo_simulator(count: int = 5) -> pd.DataFrame:
    """Download seeded historical M1 bars for EURUSD from SimulationBackend."""
    sim = SimulatorClient()
    symbol = "EURUSD"
    sim.add_symbol(SymbolInfo(name=symbol))
    base_ts = 1704100000
    seed_bars = [
        MarketBar(
            time=base_ts + i * 60,
            open=1.0850 + i * 0.0001,
            high=1.0860 + i * 0.0001,
            low=1.0845 + i * 0.0001,
            close=1.0855 + i * 0.0001,
            tick_volume=100 + i * 10,
            spread=1,
            real_volume=100 + i * 10,
        )
        for i in range(10)
    ]
    sim.seed_bar_history(symbol, Timeframe.PERIOD_M1, seed_bars)
    bars = await get_historical_bars(sim, symbol, Timeframe.PERIOD_M1, count=count)
    _print_bars_table("Simulation Backend", symbol, bars)
    assert len(bars) > 0, "Simulator returned no bars"
    return bars


DEMOS = {
    "yahoo": demo_yahoo,
    "binance": demo_binance,
    "dukascopy": demo_dukascopy,
    "darwinex": demo_darwinex,
    "sq_equity": demo_sq_equity,
    "sq_futures": demo_sq_futures,
    "files": demo_files,
    "simulator": demo_simulator,
}


async def download_all(count: int = 5) -> None:
    """Execute historical data downloads across all supported brokers."""
    print("=" * 80)
    print("  HARU QUANT AI - UNIVERSAL BROKER DATA INGESTION SUITE")
    print("=" * 80)
    for name, demo_func in DEMOS.items():
        print(f"\n>>> Running {name.upper()} data extraction...")
        await demo_func(count=count)
    print("\n" + "=" * 80)
    print("  ALL BROKER DATA DOWNLOADS COMPLETED SUCCESSFULLY!")
    print("=" * 80)


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Download historical bars and ticks from all HaruQuantAI brokers."
    )
    parser.add_argument(
        "--broker",
        choices=["all", *DEMOS.keys()],
        default="all",
        help="Broker data feed to demonstrate (default: all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of bars/ticks to retrieve (default: 5)",
    )
    args = parser.parse_args()

    if args.broker == "all":
        asyncio.run(download_all(count=args.count))
    else:
        demo_func = DEMOS[args.broker]
        asyncio.run(demo_func(count=args.count))


if __name__ == "__main__":
    main()
