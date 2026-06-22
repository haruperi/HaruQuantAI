"""Unit tests for the TrendFollowingStrategy robot."""

from datetime import UTC, datetime

import pandas as pd
from app.services.strategy import (
    OrderSide,
    PortfolioState,
    StrategyConfig,
    StrategyContext,
    StrategyService,
    TradeIntentInspector,
    TrendFollowingState,
    TrendFollowingStrategy,
)


def test_trend_following_config_schema() -> None:
    """Test configuration schema structure of TrendFollowingStrategy."""
    schema = TrendFollowingStrategy.config_strategy
    assert schema is not None
    assert schema["title"] == "TrendFollowingConfig"
    assert "symbol" in schema["properties"]
    assert "filter_period" in schema["properties"]


def test_trend_following_init_state() -> None:
    """Test initializing state for TrendFollowingStrategy."""
    config = StrategyConfig(
        strategy_id="trend_bot",
        strategy_version="1.0.0",
        parameters={
            "symbol": "BTCUSD",
            "fast_period": 5,
            "slow_period": 10,
            "filter_period": 20,
        },
    )
    strategy = TrendFollowingStrategy(config)
    state = strategy.on_init()
    assert isinstance(state, TrendFollowingState)
    assert state.position == "FLAT"


def test_trend_following_vectorized_signals() -> None:
    """Test vectorized signal generation and lookahead check."""
    config = StrategyConfig(
        strategy_id="trend_bot",
        strategy_version="1.0.0",
        parameters={
            "symbol": "BTCUSD",
            "fast_period": 2,
            "slow_period": 4,
            "filter_period": 6,
        },
    )
    strategy = TrendFollowingStrategy(config)

    # 15 periods to test crossover transitions
    # Close prices
    closes = [
        100.0,
        101.0,
        99.0,
        98.0,
        102.0,
        105.0,
        108.0,
        110.0,
        106.0,
        104.0,
        101.0,
        97.0,
        95.0,
        98.0,
        100.0,
    ]
    dates = pd.date_range(start="2026-06-01", periods=15, freq="h")
    df = pd.DataFrame(
        {
            "close": closes,
            "open": closes,
            "high": closes,
            "low": closes,
            "symbol": ["BTCUSD"] * 15,
        },
        index=dates,
    )

    df_signals = strategy.calculate_vectorized_signals(df)
    assert "fast_ma" in df_signals.columns
    assert "slow_ma" in df_signals.columns
    assert "filter_ma" in df_signals.columns
    assert "signal" in df_signals.columns

    # Verify that lookahead inspector is clean
    inspector = TradeIntentInspector()
    assert not inspector.check_lookahead_bias(strategy, df)


def test_trend_following_event_driven_bar_logic() -> None:
    """Test TrendFollowingStrategy event hooks for crossovers and filters."""
    config = StrategyConfig(
        strategy_id="trend_bot",
        strategy_version="1.0.0",
        parameters={
            "symbol": "BTCUSD",
            "fast_period": 2,
            "slow_period": 4,
            "filter_period": 6,
        },
    )
    strategy = TrendFollowingStrategy(config)
    state = strategy.on_init()

    # Generate a DataFrame with enough history to avoid NaNs.
    # fast=2, slow=4, filter=6, min required = 11. Let's make 15 rows.
    closes = [
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
        100.0,
    ]
    dates = pd.date_range(start="2026-06-01", periods=15, freq="h")
    df_history = pd.DataFrame(
        {
            "close": closes,
            "open": closes,
            "high": closes,
            "low": closes,
        },
        index=dates,
    )

    portfolio = PortfolioState(
        cash=10000.0, positions={"BTCUSD": 0.0}, equity=10000.0
    )

    # 1. Warmup / Flat scenario
    context = StrategyContext(
        current_time=datetime.now(UTC),
        portfolio=portfolio,
        market_snapshot={"BTCUSD": df_history},
    )
    state, intents = strategy.on_bar(state, {"close": 100.0}, context)
    assert state.position == "FLAT"
    assert len(intents) == 0

    # 2. Golden Cross (fast crosses above slow) + slow > filter
    # Let's override history to simulate the crossover:
    # fast EMA crosses above slow EMA, and slow EMA > filter EMA at index -2.
    # We can inject specific close prices to make this happen:
    # Let's make prices go up: [..., 100, 100, 100, 101, 105, 110, 112]
    closes_gc = [100.0] * 13 + [120.0, 120.0]
    df_gc = pd.DataFrame(
        {
            "close": closes_gc,
            "open": closes_gc,
            "high": closes_gc,
            "low": closes_gc,
        },
        index=dates,
    )
    context_gc = StrategyContext(
        current_time=datetime.now(UTC),
        portfolio=portfolio,
        market_snapshot={"BTCUSD": df_gc},
    )

    # At i = -2 (which corresponds to close 120.0):
    # fast EMA crosses above slow EMA and slow EMA > filter EMA.
    state, intents = strategy.on_bar(state, {"close": 120.0}, context_gc)
    assert state.position == "LONG"
    assert len(intents) == 1
    assert intents[0].side == OrderSide.BUY

    # 3. Exit Long (fast crosses below slow)
    closes_drop = [100.0] * 12 + [120.0, 80.0, 80.0]
    df_drop = pd.DataFrame(
        {
            "close": closes_drop,
            "open": closes_drop,
            "high": closes_drop,
            "low": closes_drop,
        },
        index=dates,
    )
    context_drop = StrategyContext(
        current_time=datetime.now(UTC),
        portfolio=portfolio,
        market_snapshot={"BTCUSD": df_drop},
    )

    state, intents = strategy.on_bar(state, {"close": 80.0}, context_drop)
    assert state.position == "FLAT"
    assert len(intents) == 1
    assert intents[0].side == OrderSide.SELL


def test_trend_following_service_integration() -> None:
    """Test full integration of TrendFollowingStrategy via StrategyService."""
    service = StrategyService()
    config = StrategyConfig(
        strategy_id="trend_bot",
        strategy_version="1.0.0",
        parameters={
            "symbol": "BTCUSD",
            "fast_period": 2,
            "slow_period": 4,
            "filter_period": 6,
        },
    )
    strategy = TrendFollowingStrategy(config)

    closes = [
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
        10.0,
    ]
    dates = pd.date_range(start="2026-06-01", periods=15, freq="h")
    df = pd.DataFrame(
        {
            "close": closes,
            "open": closes,
            "high": closes,
            "low": closes,
            "symbol": ["BTCUSD"] * 15,
        },
        index=dates,
    )

    df_res, intents = service.process_vectorized(strategy, df)
    assert isinstance(df_res, pd.DataFrame)
    assert isinstance(intents, list)
