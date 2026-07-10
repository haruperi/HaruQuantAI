"""Unit tests to achieve 100% coverage on SimpleBacktestEngine models and edge cases."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from app.services.strategy.contracts import (
    Bar,
    Direction,
    EntryType,
    IntentAction,
    ProtectionRequest,
)
from app.services.simulator import (
    BacktestConfig,
    SimpleBacktestEngine,
)
from app.services.simulator.engine import (
    _gross_pnl,
    _timeframe_duration,
)
from app.services.strategy import BaseStrategy
from app.services.strategy.config import StrategyConfig


def test_timeframe_duration_mapping() -> None:
    """Verify that _timeframe_duration maps standard resolutions correctly."""
    assert _timeframe_duration("M1") == timedelta(minutes=1)
    assert _timeframe_duration("M5") == timedelta(minutes=5)
    assert _timeframe_duration("M15") == timedelta(minutes=15)
    assert _timeframe_duration("M30") == timedelta(minutes=30)
    assert _timeframe_duration("H1") == timedelta(hours=1)
    assert _timeframe_duration("H4") == timedelta(hours=4)
    assert _timeframe_duration("D1") == timedelta(days=1)
    assert _timeframe_duration("W1") == timedelta(weeks=1)

    with pytest.raises(ValueError, match="Unsupported timeframe"):
        _timeframe_duration("XYZ")


def test_backtest_config_validation() -> None:
    """Verify that BacktestConfig enforces valid numeric values during post-init."""
    with pytest.raises(ValueError, match="initial_balance cannot be negative"):
        BacktestConfig(initial_balance=-10.0)

    with pytest.raises(ValueError, match="point_size must be positive"):
        BacktestConfig(point_size=0.0)

    with pytest.raises(
        ValueError, match="spread_points and slippage_points cannot be negative"
    ):
        BacktestConfig(spread_points=-1.0)

    with pytest.raises(
        ValueError, match="spread_points and slippage_points cannot be negative"
    ):
        BacktestConfig(slippage_points=-1.0)

    with pytest.raises(
        ValueError, match="contract_size and default_quantity must be positive"
    ):
        BacktestConfig(contract_size=0.0)

    with pytest.raises(
        ValueError, match="contract_size and default_quantity must be positive"
    ):
        BacktestConfig(default_quantity=0.0)

    with pytest.raises(ValueError, match="Invalid volume constraints"):
        BacktestConfig(volume_min=0.0)

    with pytest.raises(ValueError, match="Invalid volume constraints"):
        BacktestConfig(volume_min=10.0, volume_max=5.0)

    with pytest.raises(ValueError, match="Invalid volume constraints"):
        BacktestConfig(volume_step=-1.0)


def test_quantity_resolution() -> None:
    """Verify that _quantity handles None by returning default quantity."""
    engine = SimpleBacktestEngine(BacktestConfig(default_quantity=0.5))
    assert engine._quantity(None) == 0.5
    assert engine._quantity(1.2) == 1.2


def test_gross_pnl_calc() -> None:
    """Verify standard gross profit/loss calculations for long and short directions."""
    assert _gross_pnl(Direction.LONG, 1.0, 1.1, 1.0, 100000.0) == pytest.approx(10000.0)
    assert _gross_pnl(Direction.SHORT, 1.1, 1.0, 1.0, 100000.0) == pytest.approx(
        10000.0
    )


def test_engine_missing_symbol_timeframe() -> None:
    """Verify engine raises ValueError if symbol or timeframe is not provided."""
    config = StrategyConfig(
        {
            "schema_version": "1.0.0",
            "strategy_manifest": {
                "identity": {
                    "strategy_id": "test_strat",
                    "strategy_type": "trend_following",
                },
                "version": "1.0.0",
                "chart_requirements": {
                    "main": {"symbol": "", "timeframe": ""},
                    "other": {},
                },
                "supported_runtime_modes": ["SIMULATOR"],
                "strategy_capabilities": [],
                "permissions": {
                    "lifecycle_status": "RESEARCH",
                    "permitted_environments": ["SIMULATOR"],
                },
            },
            "trading_profile": {"symbols": {"main": {"symbol": "", "timeframe": ""}}},
            "parameters": {},
            "trading_options": {},
            "action_rules": {},
            "risk_management": {},
            "protection_rules": {},
        }
    )

    class DummyStrategy(BaseStrategy):
        def calculate_signals(self, df, context):
            return df

    strategy = DummyStrategy(config)
    engine = SimpleBacktestEngine()

    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    bars = [Bar(open_time=now, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0)]

    with pytest.raises(ValueError, match="symbol and timeframe must be supplied"):
        engine.run(strategy, bars)


def test_time_exit_trigger() -> None:
    """Verify that a time exit closes a position after the specified number of bars."""
    config_dict = {
        "schema_version": "1.0.0",
        "strategy_manifest": {
            "identity": {
                "strategy_id": "time_exit_strat",
                "strategy_type": "trend_following",
            },
            "version": "1.0.0",
            "chart_requirements": {
                "main": {"symbol": "EURUSD", "timeframe": "M5"},
                "other": {},
            },
            "supported_runtime_modes": ["SIMULATOR"],
            "strategy_capabilities": ["market_entry"],
            "permissions": {
                "lifecycle_status": "RESEARCH",
                "permitted_environments": ["SIMULATOR"],
            },
        },
        "trading_profile": {
            "symbols": {"main": {"symbol": "EURUSD", "timeframe": "M5"}},
            "magic_number": 111,
            "order_comment": "time_exit",
        },
        "parameters": {},
        "trading_options": {
            "timezone": "UTC",
            "warmup_bars": 0,
        },
        "action_rules": {
            "long_entry_action": {
                "enabled": True,
                "action": "OPEN",
                "entry_type": "MARKET",
            },
            "short_entry_action": {
                "enabled": True,
                "action": "OPEN",
                "entry_type": "MARKET",
            },
            "long_exit_action": {"enabled": True, "action": "CLOSE"},
            "short_exit_action": {"enabled": True, "action": "CLOSE"},
            "direction_conflict_policy": "REJECT_BOTH",
            "entry_exit_conflict_policy": "EXIT_PRIORITY",
            "duplicate_trade_policy": "BLOCK_SAME_DIRECTION",
        },
        "risk_management": {},
        "protection_rules": {},
    }
    config = StrategyConfig(config_dict)

    class TimeExitStrategy(BaseStrategy):
        def calculate_signals(self, df, context):
            df = df.copy()
            df["long_entry"] = False
            df["short_entry"] = False
            df["long_exit"] = False
            df["short_exit"] = False
            if len(df) > 0:
                df.iloc[0, df.columns.get_loc("long_entry")] = True
            return df

        def evaluate(self, context):
            decision = super().evaluate(context)
            if decision.intents:
                intent = decision.intents[0]
                if intent.action == IntentAction.OPEN:
                    mocker_req = ProtectionRequest(time_exit_bars=2)
                    decision = replace(
                        decision, intents=(replace(intent, protection=mocker_req),)
                    )
            return decision

    strategy = TimeExitStrategy(config)
    engine = SimpleBacktestEngine(BacktestConfig(initial_balance=10000.0))

    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    bars = [
        Bar(
            open_time=now,
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=5),
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=10),
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=15),
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
    ]

    result = engine.run(strategy, bars)
    assert len(result.closed_trades) == 1
    assert result.closed_trades[0].reason == "TIME_EXIT"
    assert result.to_dict()["open_position_count"] == 0


def test_pending_order_activation() -> None:
    """Verify that pending stop/limit orders are activated and filled by bar path."""
    config_dict = {
        "schema_version": "1.0.0",
        "strategy_manifest": {
            "identity": {
                "strategy_id": "pending_strat",
                "strategy_type": "trend_following",
            },
            "version": "1.0.0",
            "chart_requirements": {
                "main": {"symbol": "EURUSD", "timeframe": "M5"},
                "other": {},
            },
            "supported_runtime_modes": ["SIMULATOR"],
            "strategy_capabilities": ["market_entry"],
            "permissions": {
                "lifecycle_status": "RESEARCH",
                "permitted_environments": ["SIMULATOR"],
            },
        },
        "trading_profile": {
            "symbols": {"main": {"symbol": "EURUSD", "timeframe": "M5"}},
            "magic_number": 111,
            "comment": "pending",
        },
        "parameters": {},
        "trading_options": {
            "timezone": "UTC",
            "warmup_bars": 0,
        },
        "action_rules": {
            "long_entry_action": {
                "enabled": True,
                "action": "OPEN",
                "entry_type": "LIMIT",
            },
            "short_entry_action": {
                "enabled": True,
                "action": "OPEN",
                "entry_type": "LIMIT",
            },
            "long_exit_action": {"enabled": True, "action": "CLOSE"},
            "short_exit_action": {"enabled": True, "action": "CLOSE"},
            "direction_conflict_policy": "REJECT_BOTH",
            "entry_exit_conflict_policy": "EXIT_PRIORITY",
            "duplicate_trade_policy": "BLOCK_SAME_DIRECTION",
        },
        "risk_management": {},
        "protection_rules": {},
    }
    config = StrategyConfig(config_dict)

    class PendingStrategy(BaseStrategy):
        def calculate_signals(self, df, context):
            df = df.copy()
            df["long_entry"] = False
            df["short_entry"] = False
            df["long_exit"] = False
            df["short_exit"] = False
            if len(df) > 0:
                df.iloc[0, df.columns.get_loc("long_entry")] = True
            return df

        def evaluate(self, context):
            decision = super().evaluate(context)
            if decision.intents:
                intent = decision.intents[0]
                limit_intent = replace(
                    intent, entry_type=EntryType.LIMIT, limit_price=1.0900
                )
                decision = replace(decision, intents=(limit_intent,))
            return decision

    strategy = PendingStrategy(config)
    engine = SimpleBacktestEngine(
        BacktestConfig(
            initial_balance=10000.0,
            point_size=0.0001,
            spread_points=0.0,
            close_open_positions_at_end=False,
        )
    )

    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    bars = [
        Bar(
            open_time=now,
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=5),
            open=1.1000,
            high=1.1050,
            low=1.0850,
            close=1.1000,
            volume=100.0,
        ),
    ]

    result = engine.run(strategy, bars)
    assert len(result.open_positions) == 1
    assert result.open_positions[0].entry_price == 1.0900


def test_pending_stop_order() -> None:
    """Verify that a pending stop order is triggered when price moves above stop price."""
    config_dict = {
        "schema_version": "1.0.0",
        "strategy_manifest": {
            "identity": {
                "strategy_id": "stop_strat",
                "strategy_type": "trend_following",
            },
            "version": "1.0.0",
            "chart_requirements": {
                "main": {"symbol": "EURUSD", "timeframe": "M5"},
                "other": {},
            },
            "supported_runtime_modes": ["SIMULATOR"],
            "strategy_capabilities": ["market_entry"],
            "permissions": {
                "lifecycle_status": "RESEARCH",
                "permitted_environments": ["SIMULATOR"],
            },
        },
        "trading_profile": {
            "symbols": {"main": {"symbol": "EURUSD", "timeframe": "M5"}},
            "magic_number": 111,
            "comment": "pending_stop",
        },
        "parameters": {},
        "trading_options": {
            "timezone": "UTC",
            "warmup_bars": 0,
        },
        "action_rules": {
            "long_entry_action": {
                "enabled": True,
                "action": "OPEN",
                "entry_type": "STOP",
            },
            "short_entry_action": {
                "enabled": True,
                "action": "OPEN",
                "entry_type": "STOP",
            },
            "long_exit_action": {"enabled": True, "action": "CLOSE"},
            "short_exit_action": {"enabled": True, "action": "CLOSE"},
            "direction_conflict_policy": "REJECT_BOTH",
            "entry_exit_conflict_policy": "EXIT_PRIORITY",
            "duplicate_trade_policy": "BLOCK_SAME_DIRECTION",
        },
        "risk_management": {},
        "protection_rules": {},
    }
    config = StrategyConfig(config_dict)

    class StopStrategy(BaseStrategy):
        def calculate_signals(self, df, context):
            df = df.copy()
            df["long_entry"] = False
            df["short_entry"] = False
            df["long_exit"] = False
            df["short_exit"] = False
            if len(df) > 0:
                df.iloc[0, df.columns.get_loc("long_entry")] = True
            return df

        def evaluate(self, context):
            decision = super().evaluate(context)
            if decision.intents:
                intent = decision.intents[0]
                stop_intent = replace(
                    intent, entry_type=EntryType.STOP, stop_price=1.1100
                )
                decision = replace(decision, intents=(stop_intent,))
            return decision

    strategy = StopStrategy(config)
    engine = SimpleBacktestEngine(
        BacktestConfig(
            initial_balance=10000.0,
            point_size=0.0001,
            spread_points=0.0,
            close_open_positions_at_end=False,
        )
    )

    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    bars = [
        Bar(
            open_time=now,
            open=1.1000,
            high=1.1050,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=5),
            open=1.1000,
            high=1.1200,
            low=1.0950,
            close=1.1000,
            volume=100.0,
        ),
    ]

    result = engine.run(strategy, bars)
    assert len(result.open_positions) == 1
    assert result.open_positions[0].entry_price == 1.1100
