"""Unit tests for the BaseStrategy lifecycle and common SQX handling."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from app.services.contracts.strategies import (
    AccountSnapshot,
    Bar,
    Direction,
    IntentAction,
    MarketContext,
    PositionSnapshot,
    ProtectionRequest,
    QuoteSnapshot,
    RuntimeMode,
    SignalSet,
)
from app.services.strategy import BaseStrategy, StrategyPermissionError
from app.services.strategy.config import StrategyConfig
from app.services.strategy.pybots import load_bundled_strategy


class MockCustomStrategy(BaseStrategy):
    """Mock strategy to test BaseStrategy standard execution flow."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        del context
        df = df.copy()
        df["long_entry"] = True
        df["short_entry"] = False
        df["long_exit"] = False
        df["short_exit"] = False
        return df


@pytest.fixture
def base_config() -> StrategyConfig:
    """Fixture returning a valid Naive MA Trend StrategyConfig with warmup=0."""
    strategy = load_bundled_strategy("naive_ma_trend")
    raw = dict(strategy.config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["warmup_bars"] = 0
    return StrategyConfig(raw)


@pytest.fixture
def market_context() -> MarketContext:
    """Fixture returning a standard dummy MarketContext."""
    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    bars = [
        Bar(
            open_time=now - timedelta(hours=i),
            open=1.1000,
            high=1.1100,
            low=1.0900,
            close=1.1050,
            volume=1000.0,
        )
        for i in range(10, 0, -1)
    ]
    return MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=now,
        bars=bars,
        quote=QuoteSnapshot(bid=1.1045, ask=1.1055, point_size=0.00001),
        account=AccountSnapshot(balance=10000.0),
    )


def test_strategy_permitted_environments(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify strategy raises permission error on unpermitted runtime modes."""
    strategy = MockCustomStrategy(base_config)

    # Mode SIMULATOR is permitted
    assert market_context.runtime_mode == RuntimeMode.SIMULATOR
    strategy.evaluate(market_context)  # Should not raise

    # Mode LIVE is not permitted
    live_context = MarketContext(
        runtime_mode=RuntimeMode.LIVE,
        symbol=market_context.symbol,
        timeframe=market_context.timeframe,
        as_of=market_context.as_of,
        bars=market_context.bars,
    )
    with pytest.raises(StrategyPermissionError):
        strategy.evaluate(live_context)


def test_strategy_warmup_requirements(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify strategy checks warmup bar requirements."""
    # Modify config to require 15 bars
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["warmup_bars"] = 15
    config = StrategyConfig(raw)

    strategy = MockCustomStrategy(config)
    decision = strategy.evaluate(market_context)

    assert decision.signals.long_entry is False
    assert any("Warm-up incomplete" in msg for msg in decision.diagnostics)


def test_strategy_cooldown(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify strategy skips evaluation when in cooldown."""
    strategy = MockCustomStrategy(base_config)
    strategy.state.cooldown_until = market_context.as_of + timedelta(minutes=30)

    decision = strategy.evaluate(market_context)
    assert decision.signals.long_entry is False
    assert any("cooldown is active" in msg for msg in decision.diagnostics)


def test_resolve_signal_conflicts(base_config: StrategyConfig) -> None:
    """Test direction and entry/exit signal conflict resolution policies."""
    raw = dict(base_config.raw)
    raw["action_rules"] = dict(raw["action_rules"])

    # Policy: REJECT_BOTH, EXIT_PRIORITY
    raw["action_rules"]["direction_conflict_policy"] = "REJECT_BOTH"
    raw["action_rules"]["entry_exit_conflict_policy"] = "EXIT_PRIORITY"
    strategy = MockCustomStrategy(StrategyConfig(raw))

    # Both entry triggers present
    signals = SignalSet(
        long_entry=True, short_entry=True, long_exit=True, short_exit=True
    )
    resolved = strategy._resolve_signal_conflicts(signals)
    assert resolved.long_entry is False
    assert resolved.short_entry is False
    assert resolved.long_exit is True
    assert resolved.short_exit is True


def test_incremental_caching(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify that signals are incrementally cached and updated correctly."""
    strategy = MockCustomStrategy(base_config)

    # First execution calculates signals
    strategy.evaluate(market_context)
    assert strategy.df_signals is not None
    assert len(strategy.df_signals) == len(market_context.bars)

    # Append a new bar
    new_time = market_context.as_of + timedelta(hours=1)
    new_bar = Bar(
        open_time=new_time,
        open=1.1050,
        high=1.1200,
        low=1.1000,
        close=1.1150,
        volume=1200.0,
    )
    new_bars = [*list(market_context.bars), new_bar]

    next_context = MarketContext(
        runtime_mode=market_context.runtime_mode,
        symbol=market_context.symbol,
        timeframe=market_context.timeframe,
        as_of=new_time,
        bars=new_bars,
        quote=market_context.quote,
        account=market_context.account,
    )

    # Evaluate next bar triggers incremental branch
    strategy.evaluate(next_context)
    assert len(strategy.df_signals) == len(new_bars)
    assert strategy.df_signals.index[-1] == new_time


def test_scheduled_exits(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify end of day and Friday exits trigger close intents."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["end_of_day_exit"] = {"enabled": True, "time": "18:00"}

    strategy = MockCustomStrategy(StrategyConfig(raw))

    # Add a mock open position matching strategy_id
    pos = PositionSnapshot(
        position_id="pos_1",
        symbol="EURUSD",
        direction=Direction.LONG,
        quantity=0.1,
        strategy_id="naive_ma_trend",
    )

    eod_context = MarketContext(
        runtime_mode=market_context.runtime_mode,
        symbol=market_context.symbol,
        timeframe=market_context.timeframe,
        as_of=datetime(2026, 6, 23, 18, 5, tzinfo=UTC),
        bars=market_context.bars,
        positions=(pos,),
    )

    decision = strategy.evaluate(eod_context)
    assert len(decision.intents) == 1
    assert decision.intents[0].action == IntentAction.CLOSE


def test_session_restrictions_invalid_type(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify strategy raises TypeError if session_restrictions is not a list."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["session_restrictions"] = "invalid_string_instead_of_list"

    strategy = MockCustomStrategy(StrategyConfig(raw))
    with pytest.raises(TypeError, match="session_restrictions must be a list"):
        strategy.evaluate(market_context)


def test_warmup_bars_validation(base_config: StrategyConfig) -> None:
    """Verify warmup_bars validation checks."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["warmup_bars"] = -5
    strategy = MockCustomStrategy(StrategyConfig(raw))
    with pytest.raises(ValueError, match="warmup_bars must be a non-negative integer"):
        _ = strategy.required_warmup_bars

    raw["trading_options"]["warmup_bars"] = True
    strategy = MockCustomStrategy(StrategyConfig(raw))
    with pytest.raises(ValueError, match="warmup_bars must be a non-negative integer"):
        _ = strategy.required_warmup_bars


def test_evaluate_no_bars(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify evaluation fails when no bars are supplied."""
    strategy = MockCustomStrategy(base_config)
    empty_context = MarketContext(
        runtime_mode=market_context.runtime_mode,
        symbol=market_context.symbol,
        timeframe=market_context.timeframe,
        as_of=market_context.as_of,
        bars=[],
    )
    decision = strategy.evaluate(empty_context)
    assert decision.signal_time is None
    assert any("No completed bars supplied" in msg for msg in decision.diagnostics)


def test_evaluate_already_processed(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify signal bar deduplication."""
    strategy = MockCustomStrategy(base_config)
    dec1 = strategy.evaluate(market_context)
    assert dec1.signal_time == market_context.signal_bar.open_time

    dec2 = strategy.evaluate(market_context)
    assert dec2.signal_time == market_context.signal_bar.open_time
    assert any("already processed" in msg for msg in dec2.diagnostics)


def test_evaluate_execution_event(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify execution event evaluation and deduplication."""
    strategy = MockCustomStrategy(base_config)

    with pytest.raises(ValueError, match="event_id cannot be empty"):
        strategy.evaluate_execution_event(market_context, "   ")

    dec = strategy.evaluate_execution_event(market_context, "event_123")
    assert dec.intents == ()
    assert "event_123" in strategy.state.processed_event_ids

    dec2 = strategy.evaluate_execution_event(market_context, "event_123")
    assert any("already processed" in msg for msg in dec2.diagnostics)


def test_on_order_update(base_config: StrategyConfig) -> None:
    """Verify order update tracking in state."""
    strategy = MockCustomStrategy(base_config)
    with pytest.raises(ValueError, match="cannot be empty"):
        strategy.on_order_update("", "broker_1", "FILLED")

    strategy.on_order_update("intent_1", "broker_1", "SUBMITTED")
    assert strategy.state.open_signal_order_identifiers["intent_1"] == "broker_1"

    strategy.on_order_update("intent_1", "broker_1", "FILLED")
    assert "intent_1" not in strategy.state.open_signal_order_identifiers


def test_weekend_block(base_config: StrategyConfig) -> None:
    """Verify weekend schedule blocking logic."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["schedule"] = {
        "weekend": {
            "enabled": True,
            "start": {"weekday": "SATURDAY", "time": "00:00"},
            "end": {"weekday": "SUNDAY", "time": "23:59"},
        }
    }
    strategy = MockCustomStrategy(StrategyConfig(raw))

    # June 27, 2026 is Saturday
    sat_datetime = datetime(2026, 6, 27, 12, 0, tzinfo=UTC)
    assert strategy._is_weekend_blocked(sat_datetime) is True

    # June 23, 2026 is Tuesday
    tue_datetime = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    assert strategy._is_weekend_blocked(tue_datetime) is False


def test_signal_time_range(base_config: StrategyConfig) -> None:
    """Verify signal time range filter."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["signal_time_range"] = {
        "enabled": True,
        "start": "08:00",
        "end": "18:00",
    }
    strategy = MockCustomStrategy(StrategyConfig(raw))

    assert (
        strategy._is_time_range_allowed(datetime(2026, 6, 23, 12, 0, tzinfo=UTC))
        is True
    )
    assert (
        strategy._is_time_range_allowed(datetime(2026, 6, 23, 20, 0, tzinfo=UTC))
        is False
    )


def test_session_restrictions(base_config: StrategyConfig) -> None:
    """Verify session restrictions filtering."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["session_restrictions"] = [
        {"weekdays": ["TUESDAY"], "start": "09:00", "end": "17:00"}
    ]
    strategy = MockCustomStrategy(StrategyConfig(raw))

    assert (
        strategy._is_session_allowed(datetime(2026, 6, 23, 12, 0, tzinfo=UTC)) is True
    )
    assert (
        strategy._is_session_allowed(datetime(2026, 6, 23, 18, 0, tzinfo=UTC)) is False
    )
    assert (
        strategy._is_session_allowed(datetime(2026, 6, 24, 12, 0, tzinfo=UTC)) is False
    )


def test_max_trades_per_day(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify daily trade limit gating."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["max_trades_per_day"] = 2
    strategy = MockCustomStrategy(StrategyConfig(raw))

    day = market_context.signal_bar.open_time.date().isoformat()
    assert strategy._can_open(market_context, Direction.LONG) is True

    strategy.state.increment_entry_count(day)
    assert strategy._can_open(market_context, Direction.LONG) is True

    strategy.state.increment_entry_count(day)
    assert strategy._can_open(market_context, Direction.LONG) is False


def test_duplicate_trade_policy(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify duplicate trade prevention policies."""
    raw = dict(base_config.raw)
    raw["action_rules"] = dict(raw["action_rules"])

    raw["action_rules"]["duplicate_trade_policy"] = "BLOCK_ANY_OWNED_POSITION"
    strategy = MockCustomStrategy(StrategyConfig(raw))

    assert strategy._duplicate_policy_allows(market_context, Direction.LONG) is True

    pos = PositionSnapshot(
        position_id="pos_1",
        symbol="EURUSD",
        direction=Direction.LONG,
        quantity=0.1,
        strategy_id="naive_ma_trend",
    )
    context_with_pos = MarketContext(
        runtime_mode=market_context.runtime_mode,
        symbol=market_context.symbol,
        timeframe=market_context.timeframe,
        as_of=market_context.as_of,
        bars=market_context.bars,
        positions=(pos,),
    )
    assert strategy._duplicate_policy_allows(context_with_pos, Direction.LONG) is False

    raw["action_rules"]["duplicate_trade_policy"] = "BLOCK_SAME_DIRECTION"
    strategy = MockCustomStrategy(StrategyConfig(raw))
    assert strategy._duplicate_policy_allows(context_with_pos, Direction.LONG) is False
    assert strategy._duplicate_policy_allows(context_with_pos, Direction.SHORT) is True


def test_other_intents(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify generation of partial close, modify, and cancel intents."""
    strategy = MockCustomStrategy(base_config)

    partial = strategy._make_partial_close_intent(
        market_context, Direction.LONG, ("pos_1",), 0.05, operation_key="partial"
    )
    assert partial.action == IntentAction.PARTIAL_CLOSE
    assert partial.requested_quantity == 0.05

    modify = strategy._make_modify_intent(
        market_context,
        Direction.LONG,
        ("pos_1",),
        ProtectionRequest(profit_target_price=1.1200),
        operation_key="modify",
    )
    assert modify.action == IntentAction.MODIFY
    assert modify.protection.profit_target_price == 1.1200

    cancel = strategy._make_cancel_pending_intent(
        market_context, Direction.LONG, ("ord_1",), operation_key="cancel"
    )
    assert cancel.action == IntentAction.CANCEL_PENDING
    assert cancel.target_pending_order_ids == ("ord_1",)


def test_precalculate_signals_no_bars(base_config: StrategyConfig) -> None:
    """Verify precalculate_signals handles empty bars context."""
    strategy = MockCustomStrategy(base_config)
    empty_context = MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        bars=[],
    )
    strategy.precalculate_signals(empty_context)
    assert strategy.df_signals is None


def test_entry_intent_disabled(
    base_config: StrategyConfig, market_context: MarketContext
) -> None:
    """Verify entry gating blocks signal evaluate if action is disabled."""
    raw = dict(base_config.raw)
    raw["action_rules"] = dict(raw["action_rules"])
    raw["action_rules"]["long_entry_action"] = {"enabled": False}
    strategy = MockCustomStrategy(StrategyConfig(raw))

    decision = strategy.evaluate(market_context)
    assert len(decision.intents) == 0


def test_weekend_block_wrap_around(base_config: StrategyConfig) -> None:
    """Verify weekend wrap-around scheduling (start > end weekday)."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["schedule"] = {
        "weekend": {
            "enabled": True,
            "start": {"weekday": "SUNDAY", "time": "23:00"},
            "end": {"weekday": "MONDAY", "time": "05:00"},
        }
    }
    strategy = MockCustomStrategy(StrategyConfig(raw))

    # Sunday 23:30 (value = 6 * 1440 + 23 * 60 + 30) -> start = 6*1440 + 23*60 = 10020
    sun_wrap = datetime(2026, 6, 28, 23, 30, tzinfo=UTC)
    assert strategy._is_weekend_blocked(sun_wrap) is True


def test_signal_time_range_wrap_around(base_config: StrategyConfig) -> None:
    """Verify daily time range wrap-around scheduling (start > end hour)."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["signal_time_range"] = {
        "enabled": True,
        "start": "22:00",
        "end": "04:00",
    }
    strategy = MockCustomStrategy(StrategyConfig(raw))

    assert (
        strategy._is_time_range_allowed(datetime(2026, 6, 23, 23, 0, tzinfo=UTC))
        is True
    )
    assert (
        strategy._is_time_range_allowed(datetime(2026, 6, 23, 12, 0, tzinfo=UTC))
        is False
    )


def test_session_restrictions_wrap_around(base_config: StrategyConfig) -> None:
    """Verify session restrictions wrap-around hours."""
    raw = dict(base_config.raw)
    raw["trading_options"] = dict(raw["trading_options"])
    raw["trading_options"]["session_restrictions"] = [
        {"weekdays": ["TUESDAY"], "start": "22:00", "end": "04:00"}
    ]
    strategy = MockCustomStrategy(StrategyConfig(raw))

    assert (
        strategy._is_session_allowed(datetime(2026, 6, 23, 23, 0, tzinfo=UTC)) is True
    )
    assert (
        strategy._is_session_allowed(datetime(2026, 6, 23, 12, 0, tzinfo=UTC)) is False
    )


def test_parse_time_non_string(base_config: StrategyConfig) -> None:
    """Verify _parse_time raises ValueError on non-string input."""
    from app.services.strategy.base import _parse_time

    with pytest.raises(ValueError, match="must be an HH:MM string"):
        _parse_time(123, "test_param")


def test_parse_time_invalid_format(base_config: StrategyConfig) -> None:
    """Verify _parse_time raises ValueError on malformed string."""
    from app.services.strategy.base import _parse_time

    with pytest.raises(ValueError, match="must be an HH:MM string"):
        _parse_time("invalid_format", "test_param")


def test_parse_weekly_point_errors() -> None:
    """Verify _parse_weekly_point validation error cases."""
    from app.services.strategy.base import _parse_weekly_point

    with pytest.raises(ValueError, match="must be an object with weekday and time"):
        _parse_weekly_point("not_a_mapping", "test_param")

    with pytest.raises(ValueError, match="weekday must be a weekday name"):
        _parse_weekly_point({"weekday": "INVALID_DAY", "time": "12:00"}, "test_param")


def test_strategy_state_coverage() -> None:
    """Verify StrategyState serialization and custom state access."""
    from app.services.strategy.state import StrategyState

    state = StrategyState()

    # Test entry count
    assert state.entry_count_for("2026-06-23") == 0
    state.increment_entry_count("2026-06-23")
    assert state.entry_count_for("2026-06-23") == 1

    # Test custom dictionary
    assert state.get_custom("foo") is None
    assert state.get_custom("foo", "default") == "default"
    state.set_custom("foo", "bar")
    assert state.get_custom("foo") == "bar"

    # Test to_dict / from_dict with cooldown
    state.cooldown_until = datetime(2026, 6, 23, 15, 0, tzinfo=UTC)
    state.emitted_intent_ids.add("i1")
    state.processed_event_ids.add("e1")

    serialized = state.to_dict()
    assert serialized["custom"]["foo"] == "bar"
    assert serialized["cooldown_until"] == "2026-06-23T15:00:00+00:00"

    restored = StrategyState.from_dict(serialized)
    assert restored.get_custom("foo") == "bar"
    assert restored.cooldown_until == state.cooldown_until
    assert restored.entry_count_for("2026-06-23") == 1
    assert "i1" in restored.emitted_intent_ids
    assert "e1" in restored.processed_event_ids

    # Test from_dict without cooldown
    serialized["cooldown_until"] = None
    restored_no_cooldown = StrategyState.from_dict(serialized)
    assert restored_no_cooldown.cooldown_until is None
