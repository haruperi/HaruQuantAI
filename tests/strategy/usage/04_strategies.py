# ruff: noqa: E501, BLE001, E402
"""Usage example demonstrating both vectorized and event-driven strategy execution.

Example 1 runs NaiveMATrendStrategy in vectorized mode on 2026 EURUSD H1 data
and prints the transactions (rows where entry or exit signals are True).
Example 2 simulates a live/replay environment by iterating bar-by-bar,
passing historical snapshots, and logging any emitted trade intents.
"""

import sys
from datetime import UTC
from pathlib import Path

import pandas as pd

# Add project root to sys.path to allow execution without PYTHONPATH issues
project_root = str(Path(__file__).resolve().parents[3])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.services.data import get_data
from app.services.strategy.contracts import (
    AccountSnapshot,
    Bar,
    MarketContext,
    QuoteSnapshot,
    RuntimeMode,
)
from app.services.strategy.pybots import load_bundled_strategy
from app.utils.logger import logger


def print_header(title: str) -> None:
    """Print the header for an example section."""
    print(f"\n{'=' * 100}")
    print(f"--- {title} ---")
    print(f"{'=' * 100}")


def example_01_vectorized_execution() -> pd.DataFrame:
    """Run vectorized execution of NaiveMATrendStrategy on EURUSD H1 2026 data.

    Returns:
        pd.DataFrame: The resulting DataFrame with signals and standard columns.
    """
    print_header("Example 1: Vectorized Strategy Execution (EURUSD H1 2026)")

    # 1. Fetch 2026 EURUSD H1 bars from the requested MT5 source.
    start_time = "2026-01-01T00:00:00Z"
    end_time = "2026-12-31T23:59:59Z"

    logger.info(f"Fetching EURUSD H1 data from {start_time} to {end_time}...")
    records = get_data(
        symbol="EURUSD",
        timeframe="H1",
        data_kind="ohlcv",
        source="mt5",
        start_time=start_time,
        end_time=end_time,
    )
    logger.info(f"Retrieved {len(records)} bars.")

    if not records:
        logger.error("No data retrieved! Vectorized execution cannot run.")
        return pd.DataFrame()

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp").sort_index()

    # 2. Load bundled strategy
    strategy = load_bundled_strategy("naive_ma_trend")

    # 3. Create dummy MarketContext for calculate_signals
    dummy_bars = [
        Bar(
            open_time=t.to_pydatetime().replace(tzinfo=UTC),
            open=float(r["open"]),
            high=float(r["high"]),
            low=float(r["low"]),
            close=float(r["close"]),
            volume=float(r.get("volume", 0.0)),
        )
        for t, r in zip(df.index, records, strict=True)
    ]
    dummy_context = MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=df.index[-1].to_pydatetime().replace(tzinfo=UTC),
        bars=dummy_bars,
        quote=QuoteSnapshot(
            bid=float(df["close"].iloc[-1]),
            ask=float(df["close"].iloc[-1]) + 0.0001,
            point_size=0.00001,
        ),
        account=AccountSnapshot(balance=10000.0),
    )

    # 4. Calculate signals
    logger.info("Running vectorized signal calculations...")
    df_signals = strategy.calculate_signals(df, dummy_context)
    logger.info("Vectorized signal calculation complete.")

    # 5. Print transaction details where entry or exit signals are active
    tx_df = df_signals[
        (df_signals["long_entry"] == 1)
        | (df_signals["short_entry"] == 1)
        | (df_signals["long_exit"] == 1)
        | (df_signals["short_exit"] == 1)
    ]
    logger.info(f"Transactions/Signals detected (total: {len(tx_df)} rows):")
    cols_to_show = [
        "close",
        "sma_20",
        "sma_50",
        "sma_200",
        "long_entry",
        "short_entry",
        "long_exit",
        "short_exit",
    ]
    valid_cols = [c for c in cols_to_show if c in tx_df.columns]
    print(tx_df[valid_cols].tail(20).to_string())

    return df_signals


def example_02_event_driven_simulation(df: pd.DataFrame) -> None:
    """Simulate a live/replay loop bar-by-bar using historical data from Example 1.

    Args:
        df: The base historical data DataFrame.
    """
    print_header("Example 2: Event-Driven Bar-by-Bar Replay Simulation")

    if df.empty:
        logger.error("Empty DataFrame passed. Replay simulation cannot run.")
        return

    # 1. Load bundled strategy
    strategy = load_bundled_strategy("naive_ma_trend")

    # 2. Replay simulation loop
    # Minimum warm-up period is filter_period + 5 (205 bars)
    warmup_bars = 205
    total_bars = len(df)
    if total_bars <= warmup_bars:
        logger.error(
            f"Insufficient data for replay. Need > {warmup_bars} bars, got {total_bars}."
        )
        return

    logger.info(f"Starting bar loop from bar {warmup_bars} to {total_bars}...")

    # Pre-construct all Bar objects to avoid millions of instantiations inside the loop
    all_bars = [
        Bar(
            open_time=df.index[j].to_pydatetime().replace(tzinfo=UTC),
            open=float(df["open"].iloc[j]),
            high=float(df["high"].iloc[j]),
            low=float(df["low"].iloc[j]),
            close=float(df["close"].iloc[j]),
            volume=float(df["volume"].iloc[j]),
        )
        for j in range(total_bars)
    ]

    intent_count = 0

    # To avoid flooding output, we will run the entire loop, but log only when intents are generated
    for i in range(warmup_bars, total_bars):
        current_time = df.index[i]
        current_bars = all_bars[: i + 1]

        context = MarketContext(
            runtime_mode=RuntimeMode.SIMULATOR,
            symbol="EURUSD",
            timeframe="H1",
            as_of=current_time.to_pydatetime().replace(tzinfo=UTC),
            bars=current_bars,
            quote=QuoteSnapshot(
                bid=float(df["close"].iloc[i]),
                ask=float(df["close"].iloc[i]) + 0.0001,
                point_size=0.00001,
            ),
            account=AccountSnapshot(balance=100000.0),
        )

        # Process the bar event
        decision = strategy.evaluate(context)

        if decision.intents:
            intent_count += len(decision.intents)
            for intent in decision.intents:
                logger.info(
                    f"[Replay Time: {current_time}] Emitted Intent: "
                    f"Action={intent.action}, Direction={intent.direction}, Qty={intent.requested_quantity}, "
                    f"Reason='{intent.order_comment}'"
                )

    logger.info(f"Replay loop completed. Emitted {intent_count} trade intents.")


if __name__ == "__main__":
    try:
        processed_df = example_01_vectorized_execution()
        if not processed_df.empty:
            example_02_event_driven_simulation(processed_df)
    except Exception as exc:
        logger.exception("Strategy usage example execution failed: {}", exc)
        sys.exit(1)
