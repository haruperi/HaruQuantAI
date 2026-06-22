# ruff: noqa: E501, BLE001, E402
"""Usage example demonstrating both vectorized and event-driven strategy execution.

Example 1 runs TrendFollowingStrategy in vectorized mode on 2025 EURUSD H1 data
and prints the transactions (rows where entry_signal or exit_signal is non-zero).
Example 2 simulates a live/replay environment by iterating bar-by-bar,
passing historical snapshots, and logging any emitted trade intents.
"""

import sys
from pathlib import Path

import pandas as pd

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[4])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.data import get_data
from app.services.strategy import (
    PortfolioState,
    StrategyConfig,
    StrategyContext,
    StrategyService,
    TrendFollowingStrategy,
)
from app.utils.logger import logger


def example_01_vectorized_execution() -> pd.DataFrame:
    """Run vectorized execution of TrendFollowingStrategy on EURUSD H1 2025 data.

    Returns:
        pd.DataFrame: The resulting DataFrame with signals and standard columns.
    """
    logger.info("\n" + "=" * 100)
    logger.info("--- Example 1: Vectorized Strategy Execution (EURUSD H1 2025) ---")
    logger.info("=" * 100)

    # 1. Fetch 2025 EURUSD H1 bars from MT5 (falling back to local CSV/Parquet)
    start_time = "2025-01-01T00:00:00Z"
    end_time = "2025-12-31T23:59:59Z"

    logger.info(f"Fetching EURUSD H1 data from {start_time} to {end_time}...")
    records = get_data(
        symbol="EURUSD",
        timeframe="H1",
        data_kind="ohlcv",
        source="mt5",
        start_time=start_time,
        end_time=end_time,
        fallback_sources=["csv", "parquet"],
    )
    logger.info(f"Retrieved {len(records)} bars.")

    if not records:
        logger.error("No data retrieved! Vectorized execution cannot run.")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()

    # 2. Configure and instantiate strategy
    config = StrategyConfig(
        strategy_id="trend_following",
        strategy_version="1.0.0",
        parameters={
            "symbol": "EURUSD",
            "fast_period": 20,
            "slow_period": 50,
            "filter_period": 200,
        },
    )
    strategy = TrendFollowingStrategy(config)
    service = StrategyService()

    # 3. Process vectorized signals
    logger.info("Running vectorized signal calculations...")
    df_signals, intents = service.process_vectorized(strategy, df)
    logger.info(f"Vectorized execution complete. Emitted {len(intents)} intents.")

    # 4. Print transaction details where entry or exit signals are active
    tx_df = df_signals[
        (df_signals["entry_signal"] != 0) | (df_signals["exit_signal"] != 0)
    ]
    logger.info(f"Transactions detected (total: {len(tx_df)} rows):")
    cols_to_show = [
        "symbol",
        "close",
        "fast_ma",
        "slow_ma",
        "filter_ma",
        "entry_signal",
        "exit_signal",
        "price",
        "reason",
    ]
    valid_cols = [c for c in cols_to_show if c in tx_df.columns]
    print(tx_df[valid_cols].to_string())

    return df_signals


def example_02_event_driven_simulation(df: pd.DataFrame) -> None:
    """Simulate a live/replay loop bar-by-bar using historical data from Example 1.

    Args:
        df: The base historical data DataFrame.
    """
    logger.info("\n" + "=" * 100)
    logger.info("--- Example 2: Event-Driven Bar-by-Bar Replay Simulation ---")
    logger.info("=" * 100)

    if df.empty:
        logger.error("Empty DataFrame passed. Replay simulation cannot run.")
        return

    # 1. Initialize Strategy
    config = StrategyConfig(
        strategy_id="trend_following",
        strategy_version="1.0.0",
        parameters={
            "symbol": "EURUSD",
            "fast_period": 20,
            "slow_period": 50,
            "filter_period": 200,
        },
    )
    strategy = TrendFollowingStrategy(config)
    state = strategy.on_init()
    service = StrategyService()

    # 2. Replay simulation loop
    # Minimum warm-up period is filter_period + 5 (205 bars)
    warmup_bars = 205
    total_bars = len(df)
    if total_bars <= warmup_bars:
        logger.error(
            f"Insufficient data for replay. Need > {warmup_bars} bars, got {total_bars}."
        )
        return

    portfolio = PortfolioState(
        cash=100000.0,
        positions={"EURUSD": 0.0},
        equity=100000.0,
    )

    logger.info(
        f"Starting bar loop from bar {warmup_bars} to {total_bars}..."
    )

    intent_count = 0
    current_state = state

    # To avoid flooding output, we will run the entire loop, but log only when intents are generated
    for i in range(warmup_bars, total_bars):
        current_time = df.index[i]

        # In a real live environment, the database context snapshot contains the history
        # leading up to and including the current bar.
        history_snapshot = df.iloc[: i + 1]

        context = StrategyContext(
            current_time=current_time,
            portfolio=portfolio,
            market_snapshot={"EURUSD": history_snapshot},
        )

        bar_data = {
            "open": float(df["open"].iloc[i]),
            "high": float(df["high"].iloc[i]),
            "low": float(df["low"].iloc[i]),
            "close": float(df["close"].iloc[i]),
            "volume": float(df["volume"].iloc[i]),
        }

        # Process the bar event
        current_state, intents = service.process_bar(
            strategy=strategy,
            state=current_state,
            bar_data=bar_data,
            context=context,
        )

        if intents:
            intent_count += len(intents)
            for intent in intents:
                logger.info(
                    f"[Replay Time: {current_time}] Emitted Intent: "
                    f"Side={intent.side}, Qty={intent.quantity}, "
                    f"Reason='{intent.rationale}'"
                )

    logger.info(f"Replay loop completed. Emitted {intent_count} trade intents.")


if __name__ == "__main__":
    try:
        processed_df = example_01_vectorized_execution()
        example_02_event_driven_simulation(processed_df)
    except Exception as exc:
        logger.exception("Strategy usage example execution failed: {}", exc)
        sys.exit(1)
