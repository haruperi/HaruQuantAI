"""Unit tests for the Strategy Module services and components."""

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from app.services.strategy import (
    BaseStrategy,
    OrderSide,
    OrderType,
    PortfolioState,
    StrategyConfig,
    StrategyContext,
    StrategyManifest,
    StrategyService,
    TradeIntent,
    TradeIntentInspector,
    TrendFollowingState,
    TrendFollowingStrategy,
)


class LookaheadBiasStrategy(BaseStrategy[StrategyConfig, None]):
    """Mock strategy introducing lookahead bias by using future data."""

    def on_init(self) -> None:
        """Init mock."""
        return

    def on_bar(
        self, state: None, bar_data: dict[str, Any], context: StrategyContext
    ) -> tuple[None, list[TradeIntent]]:
        """Hook mock."""
        return None, []

    def on_tick(
        self, state: None, tick_data: dict[str, Any], context: StrategyContext
    ) -> tuple[None, list[TradeIntent]]:
        """Hook mock."""
        return None, []

    def on_stop(
        self, state: None, context: StrategyContext
    ) -> tuple[None, list[TradeIntent]]:
        """Hook mock."""
        return None, []

    def on_exception(
        self, state: None, error: Exception, context: StrategyContext
    ) -> tuple[None, list[TradeIntent]]:
        """Hook mock."""
        return None, []

    def on_timer(
        self,
        state: None,
        timer_event: dict[str, Any],
        context: StrategyContext,
    ) -> tuple[None, list[TradeIntent]]:
        """Hook mock."""
        return None, []

    def calculate_vectorized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Vectorized signal calculation with intentional lookahead leakage."""
        df_out = df.copy()
        # Shifts backwards to use future close
        df_out["signal"] = df_out["close"].shift(-1)
        return df_out


def test_trade_intent_pydantic_validation() -> None:
    """Test validation of TradeIntent and related schemas."""
    now_utc = datetime.now(UTC)
    intent = TradeIntent(
        intent_id="id1",
        decision_id="dec1",
        idempotency_key="ikey1",
        strategy_id="strat1",
        strategy_version="1.0.0",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=1.5,
        signal_timestamp=now_utc,
    )
    assert intent.intent_id == "id1"
    assert intent.side == OrderSide.BUY
    assert intent.quantity == 1.5


def test_strategy_context_validation() -> None:
    """Test strategy context and portfolio state schemas."""
    portfolio = PortfolioState(
        cash=10000.0, positions={"BTCUSD": 0.0}, equity=10000.0
    )
    context = StrategyContext(
        current_time=datetime.now(UTC),
        portfolio=portfolio,
        market_snapshot={"BTCUSD": {}},
    )
    assert context.portfolio.cash == 10000.0


def test_strategy_manifest_validation() -> None:
    """Test validation of StrategyManifest fields."""
    manifest = StrategyManifest(
        strategy_id="trend_following",
        strategy_version="1.0.0",
        description="Trend following",
        required_symbols=["BTCUSD"],
        required_timeframes=["M5"],
        max_drawdown_limit=0.2,
        max_position_size=10.0,
    )
    assert manifest.strategy_id == "trend_following"
    assert manifest.max_drawdown_limit == 0.2


def test_trade_intent_inspector_rules() -> None:
    """Test the TradeIntentInspector timing and staleness warning checks."""
    inspector = TradeIntentInspector(stale_threshold_seconds=10.0)
    now_utc = datetime.now(UTC)

    # 1. Valid intent
    intent_valid = TradeIntent(
        intent_id="id1",
        decision_id="dec1",
        idempotency_key="ikey1",
        strategy_id="strat1",
        strategy_version="1.0.0",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        quantity=1.0,
        signal_timestamp=now_utc,
    )
    assert not inspector.inspect_intent(intent_valid, now_utc)

    # 2. Lookahead / Future timestamp intent
    intent_future = TradeIntent(
        intent_id="id2",
        decision_id="dec2",
        idempotency_key="ikey2",
        strategy_id="strat1",
        strategy_version="1.0.0",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        quantity=1.0,
        signal_timestamp=now_utc + timedelta(seconds=5),
    )
    issues_future = inspector.inspect_intent(intent_future, now_utc)
    assert len(issues_future) == 1
    assert "Lookahead Risk" in issues_future[0]

    # 3. Stale timestamp intent
    intent_stale = TradeIntent(
        intent_id="id3",
        decision_id="dec3",
        idempotency_key="ikey3",
        strategy_id="strat1",
        strategy_version="1.0.0",
        symbol="BTCUSD",
        side=OrderSide.BUY,
        quantity=1.0,
        signal_timestamp=now_utc - timedelta(seconds=15),
    )
    issues_stale = inspector.inspect_intent(intent_stale, now_utc)
    assert len(issues_stale) == 1
    assert "Stale Data" in issues_stale[0]


def test_lookahead_bias_detection() -> None:
    """Test the perturbation detector flags lookahead leakages correctly."""
    inspector = TradeIntentInspector()

    # Generate mock price DataFrame
    dates = pd.date_range(start="2026-06-01", periods=10, freq="h")
    df = pd.DataFrame(
        {
            "open": np.linspace(95, 105, 10),
            "high": np.linspace(96, 106, 10),
            "low": np.linspace(94, 104, 10),
            "close": np.linspace(95, 105, 10),
            "volume": [100.0] * 10,
        },
        index=dates,
    )

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

    # TrendFollowingStrategy shifts signals, so it has no lookahead bias
    clean_strat = TrendFollowingStrategy(config)
    assert not inspector.check_lookahead_bias(clean_strat, df)

    # LookaheadBiasStrategy does not shift signals, so bias is detected
    bias_strat = LookaheadBiasStrategy(config)
    assert inspector.check_lookahead_bias(bias_strat, df)


def test_strategy_service_event_hooks() -> None:
    """Test StrategyService handles and delegates all lifecycle hooks."""
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
    state = strategy.on_init()

    # Supply history to allow execution
    closes = [100.0] * 15
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
    context = StrategyContext(
        current_time=datetime.now(UTC),
        portfolio=portfolio,
        market_snapshot={"BTCUSD": df_history},
    )

    # 1. Bar execution
    state, intents = service.process_bar(
        strategy, state, {"close": 100.0}, context
    )
    assert isinstance(state, TrendFollowingState)
    assert isinstance(intents, list)

    # 2. Tick execution
    state, intents = service.process_tick(
        strategy, state, {"last": 100.0}, context
    )
    assert isinstance(state, TrendFollowingState)
    assert isinstance(intents, list)

    # 3. Stop hook
    state, intents = service.process_stop(strategy, state, context)
    assert isinstance(intents, list)

    # 4. Exception hook
    state, intents = service.process_exception(
        strategy, state, ValueError("test error"), context
    )
    assert isinstance(intents, list)

    # 5. Timer hook
    state, intents = service.process_timer(strategy, state, {}, context)
    assert isinstance(intents, list)


def test_strategy_service_vectorized_processing() -> None:
    """Test process_vectorized converts signals and normalizes standard cols."""
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

    dates = pd.date_range(start="2026-06-01", periods=15, freq="h")
    df = pd.DataFrame(
        {
            "close": [100.0] * 15,
            "open": [100.0] * 15,
            "high": [100.0] * 15,
            "low": [100.0] * 15,
            "symbol": ["BTCUSD"] * 15,
        },
        index=dates,
    )

    df_signals, intents = service.process_vectorized(strategy, df)
    assert isinstance(df_signals, pd.DataFrame)
    # Check standard columns are guaranteed to exist
    standard_cols = [
        "entry_signal",
        "exit_signal",
        "price",
        "reason",
        "setup_id",
        "group_id",
    ]
    for col in standard_cols:
        assert col in df_signals.columns

    assert isinstance(intents, list)
