"""Unit tests for the SimpleBacktestEngine simulator and auxiliary search."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from app.services.contracts.strategies import (
    Bar,
    MarketContext,
    QuoteSnapshot,
)
from app.services.simulator import BacktestConfig, SimpleBacktestEngine
from app.services.strategy import BaseStrategy
from app.services.strategy.config import StrategyConfig


class MockSimulatorStrategy(BaseStrategy):
    """Mock strategy for testing the simulator engine."""

    def calculate_signals(
        self, df: pd.DataFrame, context: MarketContext
    ) -> pd.DataFrame:
        del context
        df = df.copy()
        df["long_entry"] = False
        df["short_entry"] = False
        df["long_exit"] = False
        df["short_exit"] = False

        # Trigger long entry on the second bar
        if len(df) >= 2:
            df.iloc[-1, df.columns.get_loc("long_entry")] = True
        return df


@pytest.fixture
def mock_config() -> StrategyConfig:
    """Fixture returning a valid Mock strategy config."""
    raw = {
        "schema_version": "1.0.0",
        "strategy_manifest": {
            "identity": {
                "strategy_id": "mock_sim_strategy",
                "strategy_type": "trend_following",
                "description": "Mock for simulator testing",
                "author": "HaruQuantAI",
                "created_at": "2026-06-23",
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
                "risk_profile": {"execution_authority": "Risk Governor"},
            },
        },
        "trading_profile": {
            "magic_number": 123456,
            "order_comment": "mock_sim",
            "symbols": {
                "main": {"symbol": "EURUSD", "timeframe": "M5"},
                "other": {},
            },
        },
        "parameters": {"definitions": {}, "values": {}},
        "trading_options": {
            "timezone": "UTC",
            "warmup_bars": 0,
            "max_trades_per_day": 10,
            "schedule": {"weekend": {"enabled": False}},
            "end_of_day_exit": {"enabled": False},
            "friday_exit": {"enabled": False},
            "signal_time_range": {"enabled": False},
            "session_restrictions": [],
            "trading_filters": {
                "allowed_directions": ["LONG", "SHORT"],
                "max_open_positions": 0,
            },
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
        "risk_management": {
            "strategy_sizing_hint": {
                "mode": "strategy_formula",
                "value": None,
                "authoritative": False,
                "note": "note",
            }
        },
        "protection_rules": {},
    }
    return StrategyConfig(raw)


def test_simulator_basic_run(mock_config: StrategyConfig) -> None:
    """Verify standard simulator run executes and collects result metrics."""
    strategy = MockSimulatorStrategy(mock_config)

    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    bars = [
        Bar(
            open_time=now,
            open=1.1000,
            high=1.1050,
            low=1.0990,
            close=1.1010,
            volume=100.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=5),
            open=1.1010,
            high=1.1060,
            low=1.1000,
            close=1.1020,
            volume=110.0,
        ),
        Bar(
            open_time=now + timedelta(minutes=10),
            open=1.1020,
            high=1.1070,
            low=1.1010,
            close=1.1030,
            volume=120.0,
        ),
    ]

    engine = SimpleBacktestEngine(
        BacktestConfig(
            initial_balance=10000.0,
            point_size=0.00001,
            spread_points=10.0,
            slippage_points=0.0,
            default_quantity=0.10,
            contract_size=100000.0,
        )
    )

    result = engine.run(strategy, bars, symbol="EURUSD", timeframe="M5")

    assert result.strategy_id == "mock_sim_strategy"
    assert result.symbol == "EURUSD"
    assert result.timeframe == "M5"
    assert len(result.equity_curve) == 3
    assert result.metrics.initial_balance == 10000.0


def test_simulator_auxiliary_bars_binary_search(mock_config: StrategyConfig) -> None:
    """Verify engine constructs context chart_bars correctly using binary search."""
    engine = SimpleBacktestEngine(BacktestConfig(initial_balance=10000.0))

    now = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
    history = [
        Bar(open_time=now, open=1.0, high=1.0, low=1.0, close=1.0, volume=1.0),
        Bar(
            open_time=now + timedelta(minutes=5),
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=1.0,
        ),
    ]

    # Auxiliary bars: H1 bars
    h1_bars = [
        Bar(
            open_time=now - timedelta(hours=1),
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=1.0,
        ),
        Bar(open_time=now, open=1.1, high=1.1, low=1.1, close=1.1, volume=1.0),
    ]

    auxiliary = {"H1": h1_bars}
    auxiliary_durations = {"H1": timedelta(hours=1)}

    # Test 1: at primary bar 1 open time + timeframe duration (12:05)
    # cutoff = 12:05 - H1 duration (1h) = 11:05.
    # Only H1 bar 1 (open_time 11:00) should be included.
    context1 = engine._make_context(
        history=history[:1],
        as_of=now + timedelta(minutes=5),
        symbol="EURUSD",
        timeframe="M5",
        quote=QuoteSnapshot(bid=1.0, ask=1.0, point_size=0.0001),
        positions=(),
        pending_orders=(),
        balance=10000.0,
        auxiliary=auxiliary,
        auxiliary_durations=auxiliary_durations,
        feature_provider=None,
        feature_index=0,
    )

    assert "H1" in context1.chart_bars
    assert len(context1.chart_bars["H1"]) == 1
    assert context1.chart_bars["H1"][0].open_time == now - timedelta(hours=1)

    # Test 2: at 13:05.
    # cutoff = 13:05 - 1h = 12:05.
    # Both H1 bars should be included since both opens (11:00 and 12:00) are <= 12:05.
    context2 = engine._make_context(
        history=history,
        as_of=now + timedelta(hours=1, minutes=5),
        symbol="EURUSD",
        timeframe="M5",
        quote=QuoteSnapshot(bid=1.0, ask=1.0, point_size=0.0001),
        positions=(),
        pending_orders=(),
        balance=10000.0,
        auxiliary=auxiliary,
        auxiliary_durations=auxiliary_durations,
        feature_provider=None,
        feature_index=1,
    )

    assert len(context2.chart_bars["H1"]) == 2
    assert context2.chart_bars["H1"][1].open_time == now
