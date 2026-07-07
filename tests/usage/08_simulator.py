# ruff: noqa: E402, I001, BLE001
"""Run the 20/50/200 naïve MA strategy against a canonical OHLCV CSV file."""

from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[2])
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from datetime import datetime
from app.services.data import get_data
from app.services.simulator import BacktestConfig, SimpleBacktestEngine
from app.services.strategy import Bar
from app.services.strategy.pybots import load_bundled_strategy


def example_01_basic_backtest() -> None:
    """Demonstrate simple backtest using OHLCV data from MT5."""
    print("\n" + "=" * 100)
    print("--- 1. Simple Backtest ---")
    print("=" * 100)
    try:
        print("Querying MT5 for EURUSD H1 bars...")
        records = get_data(
            symbol="EURUSD",
            timeframe="H1",
            data_kind="ohlcv",
            source="mt5",
            start_time="2026-01-01",
            end_time="2026-12-31",
        )
        print(f"Fetched {len(records)} bars from MT5.")
        if records:
            # Convert to sequence of canonical Bar objects for backtesting
            bars = [
                Bar(
                    open_time=datetime.fromisoformat(r["timestamp"]),
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    volume=r.get("volume", 0.0),
                )
                for r in records
            ]
            strategy = load_bundled_strategy("naive_ma_trend")
            engine = SimpleBacktestEngine(
                BacktestConfig(
                    initial_balance=10_000.0,
                    point_size=0.00001,
                    spread_points=10.0,
                    slippage_points=0.0,
                    default_quantity=0.10,
                    contract_size=100_000.0,
                )
            )
            result = engine.run(strategy, bars, symbol="EURUSD", timeframe="H1")
            print("\nBacktest Result Summary:")
            print(result.to_dict())

    except Exception as e:
        print(f"MT5 retrieval failed closed (expected in staging): {e}")


if __name__ == "__main__":
    example_01_basic_backtest()


