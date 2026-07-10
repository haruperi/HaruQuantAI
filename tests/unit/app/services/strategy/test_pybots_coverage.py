# ruff: noqa: D, ANN, S101
"""Coverage expansion tests for the strategy pybots, templates, translation helpers, and registry."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from app.services.strategy.contracts import (
    AccountSnapshot,
    Bar,
    Direction,
    MarketContext,
    PositionSnapshot,
    QuoteSnapshot,
    RuntimeMode,
)
from app.services.strategy.pybots._template.rules import (
    long_entry_signal,
    long_exit_signal,
    short_entry_signal,
    short_exit_signal,
)
from app.services.strategy.pybots._template.strategy import TemplateStrategy
from app.services.strategy.pybots.mql5_translation_helpers import (
    average_entry,
    by_direction,
    entry_price,
    pip_value,
    require_quote,
)
from app.services.strategy.pybots.registry import (
    STRATEGY_TYPES,
    bundled_strategy_ids,
    load_bundled_strategy,
    strategy_from_config,
)


@pytest.fixture
def mock_market_context() -> MarketContext:
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
        for i in range(200, 0, -1)  # Provide 200 bars for indicators and warmups
    ]
    return MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=now,
        bars=bars,
        chart_bars={"H1": bars, "H4": bars, "D1": bars, "M15": bars, "M5": bars},
        quote=QuoteSnapshot(bid=1.1045, ask=1.1055, point_size=0.00001),
        account=AccountSnapshot(balance=10000.0),
        pending_orders=(),
    )


def test_registry_and_bundled_evaluations(mock_market_context: MarketContext) -> None:
    # Verify bundled IDs match Stras in STRATEGY_TYPES keys
    ids = bundled_strategy_ids()
    assert set(ids) == set(STRATEGY_TYPES.keys())

    # Verify KeyError on unknown strategy loading
    with pytest.raises(KeyError, match="Unknown bundled strategy"):
        load_bundled_strategy("non_existent_strategy")

    # Load and evaluate every strategy
    for strategy_id in ids:
        strategy = load_bundled_strategy(strategy_id)
        assert strategy.config.strategy_id == strategy_id

        # Strategy from config
        constructed = strategy_from_config(strategy.config)
        assert constructed.config.strategy_id == strategy_id

        # Evaluate strategy
        decision = strategy.evaluate(mock_market_context)
        assert decision.diagnostics is not None

    with pytest.raises(KeyError, match="No bundled implementation"):
        # Load a config and modify strategy_id to fail registry
        strategy = load_bundled_strategy("naive_ma_trend")
        strategy.config.raw["strategy_manifest"]["identity"]["strategy_id"] = (
            "non_existent_registry"
        )
        strategy_from_config(strategy.config)


def test_mql5_translation_helpers() -> None:
    # require_quote exception
    ctx_no_quote = MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=datetime.now(UTC),
        bars=[],
    )
    with pytest.raises(ValueError, match="requires MarketContext.quote"):
        require_quote(ctx_no_quote)

    # pip_val computation
    ctx_with_quote = MarketContext(
        runtime_mode=RuntimeMode.SIMULATOR,
        symbol="EURUSD",
        timeframe="H1",
        as_of=datetime.now(UTC),
        bars=[],
        quote=QuoteSnapshot(bid=1.10, ask=1.11, point_size=0.0001),
    )
    val = pip_value(ctx_with_quote, 10.0, 1.0)
    assert val == pytest.approx(0.001)

    # entry_price exception
    pos_no_price = PositionSnapshot(
        position_id="pos1",
        symbol="EURUSD",
        direction=Direction.LONG,
        quantity=1.0,
        strategy_id="strat",
    )
    with pytest.raises(ValueError, match="has no entry_price"):
        entry_price(pos_no_price)

    # average_entry exception
    with pytest.raises(ValueError, match="Cannot average an empty position set"):
        average_entry([])

    # average_entry success
    pos_with_price1 = PositionSnapshot(
        position_id="pos1",
        symbol="EURUSD",
        direction=Direction.LONG,
        quantity=1.0,
        strategy_id="strat",
        entry_price=1.1000,
    )
    pos_with_price2 = PositionSnapshot(
        position_id="pos2",
        symbol="EURUSD",
        direction=Direction.LONG,
        quantity=1.0,
        strategy_id="strat",
        entry_price=1.2000,
    )
    assert average_entry([pos_with_price1, pos_with_price2]) == 1.1500

    # by_direction filter
    res_long = by_direction([pos_with_price1], Direction.LONG)
    assert len(res_long) == 1
    res_short = by_direction([pos_with_price1], Direction.SHORT)
    assert len(res_short) == 0


def test_template_strategy_and_rules(mock_market_context: MarketContext) -> None:
    # Verify rules defaults
    assert long_entry_signal(mock_market_context, None) is False
    assert short_entry_signal(mock_market_context, None) is False
    assert long_exit_signal(mock_market_context, None) is False
    assert short_exit_signal(mock_market_context, None) is False

    # Instantiate template strategy and run calculate_signals
    # Set config manifest dict to construct template config
    config_dict = {
        "schema_version": "1.0.0",
        "strategy_manifest": {
            "identity": {
                "strategy_id": "template_strat",
                "strategy_type": "trend_following",
            },
            "version": "1.0.0",
            "chart_requirements": {
                "main": {"symbol": "EURUSD", "timeframe": "H1"},
                "other": {},
            },
            "supported_runtime_modes": ["SIMULATOR"],
            "strategy_capabilities": [],
            "permissions": {
                "lifecycle_status": "RESEARCH",
                "permitted_environments": ["SIMULATOR"],
            },
        },
        "trading_profile": {
            "symbols": {"main": {"symbol": "EURUSD", "timeframe": "H1"}}
        },
        "parameters": {},
        "trading_options": {},
        "action_rules": {},
        "risk_management": {},
        "protection_rules": {},
    }
    from app.services.strategy.config import StrategyConfig

    config = StrategyConfig(config_dict)
    strategy = TemplateStrategy(config)

    df = pd.DataFrame(index=[b.open_time for b in mock_market_context.bars])
    df_signals = strategy.calculate_signals(df, mock_market_context)
    assert "long_entry" in df_signals.columns
    assert bool(df_signals["long_entry"].iloc[0]) is False
    assert bool(df_signals["short_entry"].iloc[0]) is False
    assert bool(df_signals["long_exit"].iloc[0]) is False
    assert bool(df_signals["short_exit"].iloc[0]) is False
