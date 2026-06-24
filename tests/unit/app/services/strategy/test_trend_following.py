"""Unit tests for the NaiveMATrendStrategy robot."""

from datetime import UTC

import pandas as pd
from app.services.contracts.strategies import (
    AccountSnapshot,
    Bar,
    MarketContext,
    QuoteSnapshot,
    RuntimeMode,
)
from app.services.strategy.pybots import load_bundled_strategy
from app.services.strategy.pybots.naive_ma_trend.strategy import NaiveMATrendStrategy


def test_naive_ma_trend_load() -> None:
    """Verify loading bundled naive_ma_trend strategy works."""
    strategy = load_bundled_strategy("naive_ma_trend")
    assert isinstance(strategy, NaiveMATrendStrategy)
    assert strategy.config.strategy_id == "naive_ma_trend"


def test_naive_ma_trend_signals() -> None:
    """Test crossovers and trend filter logic on a DataFrame."""
    strategy = load_bundled_strategy("naive_ma_trend")

    # Construct a DataFrame with 210 rows to satisfy SMA 200 period requirements
    dates = pd.date_range(start="2026-01-01", periods=210, freq="h")

    # Generate closes:
    # 0 to 199: 100.0 (flat)
    # 200 to 209: rising prices to trigger golden cross
    closes = [100.0] * 200 + [
        101.0,
        105.0,
        110.0,
        115.0,
        120.0,
        125.0,
        130.0,
        135.0,
        140.0,
        145.0,
    ]
    df = pd.DataFrame(
        {
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [100.0] * 210,
        },
        index=dates,
    )

    bars = [
        Bar(
            open_time=dates[i].to_pydatetime().replace(tzinfo=UTC),
            open=df["open"].iloc[i],
            high=df["high"].iloc[i],
            low=df["low"].iloc[i],
            close=df["close"].iloc[i],
            volume=df["volume"].iloc[i],
        )
        for i in range(210)
    ]

    context = MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=dates[-1].to_pydatetime().replace(tzinfo=UTC),
        bars=bars,
        quote=QuoteSnapshot(bid=1.1000, ask=1.1010, point_size=0.00001),
        account=AccountSnapshot(balance=10000.0),
    )

    # Calculate signals
    df_signals = strategy.calculate_signals(df, context)

    # Ensure SMA columns are computed
    assert "sma_20" in df_signals.columns
    assert "sma_50" in df_signals.columns
    assert "sma_200" in df_signals.columns
    assert "long_entry" in df_signals.columns
    assert "short_entry" in df_signals.columns
    assert "long_exit" in df_signals.columns
    assert "short_exit" in df_signals.columns
