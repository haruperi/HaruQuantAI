"""Deterministic unit tests for BacktestRunner and SimulationEngine."""

from __future__ import annotations

import pytest
from app.core.data.contracts import MarketBar
from app.core.enums import OrderType, Timeframe
from app.core.trading.backtest import (
    BacktestRunner,
    BacktestSettings,
    PrecisionMode,
    RunResult,
    RunSpec,
    SameBarExecutionRule,
)
from app.core.trading.simulation.engine import SimulationEngine
from app.core.trading.strategy import (
    ActionKind,
    CloseRequest,
    ConditionDefinition,
    OrderRequest,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    StrategyDocument,
    StrategyEffects,
)


def _bar(
    time: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    *,
    volume: int = 100,
) -> MarketBar:
    return MarketBar(
        time=time,
        open=open_,
        high=high,
        low=low,
        close=close,
        tick_volume=volume,
    )


def test_gap_fill_buy_limit_at_open() -> None:
    """Buy limit pending order fills at bar Open when market gaps down below limit."""
    engine = SimulationEngine()
    # Emit a buy limit order at 1.1000
    effects = StrategyEffects(
        orders_to_open=(
            OrderRequest(
                symbol="EURUSD",
                direction=1,
                order_type=OrderType.BUY_LIMIT,
                price=1.1000,
                volume=1.0,
            ),
        )
    )
    bar1 = _bar(1000, 1.1020, 1.1030, 1.1010, 1.1025)
    engine.apply_effects(effects, bar1)
    assert len(engine.pending_orders) == 1

    # Bar 2 opens at 1.0950 (gap down below limit of 1.1000)
    bar2 = _bar(1060, 1.0950, 1.0980, 1.0940, 1.0970)
    engine.process_pre_bar(bar2)

    # Order must have triggered at Open price (1.0950), not at 1.1000
    assert len(engine.pending_orders) == 0
    assert len(engine.positions) == 1
    pos = next(iter(engine.positions.values()))
    assert pos.open_price == pytest.approx(1.0950)
    assert pos.direction == 1


def test_gap_fill_buy_stop_at_open() -> None:
    """Buy stop pending order fills at bar Open when market gaps up above trigger."""
    engine = SimulationEngine()
    effects = StrategyEffects(
        orders_to_open=(
            OrderRequest(
                symbol="EURUSD",
                direction=1,
                order_type=OrderType.BUY_STOP,
                price=1.1000,
                volume=1.0,
            ),
        )
    )
    bar1 = _bar(1000, 1.0950, 1.0960, 1.0940, 1.0955)
    engine.apply_effects(effects, bar1)

    # Bar 2 opens at 1.1050 (gap up above 1.1000)
    bar2 = _bar(1060, 1.1050, 1.1070, 1.1040, 1.1060)
    engine.process_pre_bar(bar2)

    assert len(engine.pending_orders) == 0
    assert len(engine.positions) == 1
    pos = next(iter(engine.positions.values()))
    assert pos.open_price == pytest.approx(1.1050)


def test_gap_fill_sell_limit_at_open() -> None:
    """Sell limit pending order fills at bar Open when market gaps up above limit."""
    engine = SimulationEngine()
    effects = StrategyEffects(
        orders_to_open=(
            OrderRequest(
                symbol="EURUSD",
                direction=-1,
                order_type=OrderType.SELL_LIMIT,
                price=1.1000,
                volume=1.0,
            ),
        )
    )
    bar1 = _bar(1000, 1.0980, 1.0990, 1.0970, 1.0985)
    engine.apply_effects(effects, bar1)

    # Bar 2 opens at 1.1040 (gap up above limit 1.1000)
    bar2 = _bar(1060, 1.1040, 1.1060, 1.1030, 1.1050)
    engine.process_pre_bar(bar2)

    assert len(engine.pending_orders) == 0
    assert len(engine.positions) == 1
    pos = next(iter(engine.positions.values()))
    assert pos.open_price == pytest.approx(1.1040)
    assert pos.direction == -1


def test_gap_fill_sell_stop_at_open() -> None:
    """Sell stop pending order fills at bar Open when market gaps down below trigger."""
    engine = SimulationEngine()
    effects = StrategyEffects(
        orders_to_open=(
            OrderRequest(
                symbol="EURUSD",
                direction=-1,
                order_type=OrderType.SELL_STOP,
                price=1.1000,
                volume=1.0,
            ),
        )
    )
    bar1 = _bar(1000, 1.1030, 1.1040, 1.1020, 1.1035)
    engine.apply_effects(effects, bar1)

    # Bar 2 opens at 1.0940 (gap down below 1.1000)
    bar2 = _bar(1060, 1.0940, 1.0950, 1.0920, 1.0930)
    engine.process_pre_bar(bar2)

    assert len(engine.pending_orders) == 0
    assert len(engine.positions) == 1
    pos = next(iter(engine.positions.values()))
    assert pos.open_price == pytest.approx(1.0940)
    assert pos.direction == -1


def test_same_bar_sl_tp_tie_breaking_worst_case() -> None:
    """When both SL and TP are breached in same bar, WORST_CASE executes SL first."""
    settings = BacktestSettings(same_bar_sl_tp_rule=SameBarExecutionRule.WORST_CASE)
    engine = SimulationEngine(settings)

    # Long position opened at 1.1000, SL=1.0950, TP=1.1050
    bar1 = _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000)
    effects = StrategyEffects(
        orders_to_open=(
            OrderRequest(
                symbol="EURUSD",
                direction=1,
                order_type=OrderType.BUY,
                volume=1.0,
                sl=1.0950,
                tp=1.1050,
            ),
        )
    )
    engine.apply_effects(effects, bar1)

    # Bar 2 breaches both: Low 1.0940 <= SL and High 1.1060 >= TP
    bar2 = _bar(1060, 1.1000, 1.1060, 1.0940, 1.1020)
    engine.process_intra_bar(bar2)

    assert len(engine.positions) == 0
    assert len(engine.completed_trades) == 1
    trade = engine.completed_trades[0]
    assert trade.close_reason == "SL"
    assert trade.close_price == pytest.approx(1.0950)
    assert trade.net_pnl < 0.0


def test_same_bar_sl_tp_tie_breaking_best_case() -> None:
    """When both SL and TP are breached in same bar, BEST_CASE executes TP first."""
    settings = BacktestSettings(same_bar_sl_tp_rule=SameBarExecutionRule.BEST_CASE)
    engine = SimulationEngine(settings)

    bar1 = _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000)
    effects = StrategyEffects(
        orders_to_open=(
            OrderRequest(
                symbol="EURUSD",
                direction=1,
                order_type=OrderType.BUY,
                volume=1.0,
                sl=1.0950,
                tp=1.1050,
            ),
        )
    )
    engine.apply_effects(effects, bar1)

    # Bar 2 breaches both
    bar2 = _bar(1060, 1.1000, 1.1060, 1.0940, 1.1020)
    engine.process_intra_bar(bar2)

    assert len(engine.positions) == 0
    assert len(engine.completed_trades) == 1
    trade = engine.completed_trades[0]
    assert trade.close_reason == "TP"
    assert trade.close_price == pytest.approx(1.1050)
    assert trade.net_pnl > 0.0


def test_same_bar_sl_tp_short_position() -> None:
    """Short position tie-breaking for worst-case and best-case."""
    # 1. Worst case
    engine_worst = SimulationEngine(
        BacktestSettings(same_bar_sl_tp_rule=SameBarExecutionRule.WORST_CASE)
    )
    bar1 = _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000)
    engine_worst.apply_effects(
        StrategyEffects(
            orders_to_open=(
                OrderRequest(
                    symbol="EURUSD",
                    direction=-1,
                    order_type=OrderType.SELL,
                    volume=1.0,
                    sl=1.1050,
                    tp=1.0950,
                ),
            )
        ),
        bar1,
    )
    bar2 = _bar(1060, 1.1000, 1.1060, 1.0940, 1.1020)
    engine_worst.process_intra_bar(bar2)
    assert engine_worst.completed_trades[0].close_reason == "SL"

    # 2. Best case
    engine_best = SimulationEngine(
        BacktestSettings(same_bar_sl_tp_rule=SameBarExecutionRule.BEST_CASE)
    )
    engine_best.apply_effects(
        StrategyEffects(
            orders_to_open=(
                OrderRequest(
                    symbol="EURUSD",
                    direction=-1,
                    order_type=OrderType.SELL,
                    volume=1.0,
                    sl=1.1050,
                    tp=1.0950,
                ),
            )
        ),
        bar1,
    )
    engine_best.process_intra_bar(bar2)
    assert engine_best.completed_trades[0].close_reason == "TP"


def test_slippage_and_commission_modeling() -> None:
    """Slippage points and commissions are deducted accurately on buy and sell."""
    settings = BacktestSettings(
        initial_capital=10000.0,
        slippage_points=0.0002,
        commission_per_order=5.0,
    )
    engine = SimulationEngine(settings)

    # Long order at bar close 1.1000 -> fill at 1.1002 (slippage + 0.0002)
    bar1 = _bar(1000, 1.0990, 1.1010, 1.0980, 1.1000)
    engine.apply_effects(
        StrategyEffects(
            orders_to_open=(
                OrderRequest(
                    symbol="EURUSD",
                    direction=1,
                    order_type=OrderType.BUY,
                    volume=1.0,
                ),
            )
        ),
        bar1,
    )
    assert engine.balance == pytest.approx(10000.0 - 5.0)  # Entry commission
    pos = next(iter(engine.positions.values()))
    assert pos.open_price == pytest.approx(1.1002)

    # Close at bar close 1.1050 -> exit fill at 1.1048 (slippage - 0.0002)
    bar2 = _bar(1060, 1.1010, 1.1060, 1.1005, 1.1050)
    engine.apply_effects(
        StrategyEffects(positions_to_close=(CloseRequest(ticket=""),)),
        bar2,
    )

    assert len(engine.completed_trades) == 1
    trade = engine.completed_trades[0]
    assert trade.open_price == pytest.approx(1.1002)
    assert trade.close_price == pytest.approx(1.1048)
    assert trade.commission == pytest.approx(10.0)  # 2 orders * 5.0
    assert trade.slippage == pytest.approx(0.0004)  # 2 * 0.0002

    # Gross pnl = (1.1048 - 1.1002) * 1.0 = 0.0046
    assert trade.pnl == pytest.approx(0.0046)
    assert trade.net_pnl == pytest.approx(0.0046 - 10.0)
    assert engine.balance == pytest.approx(10000.0 + trade.net_pnl)


def test_mae_mfe_tracking_multi_bar() -> None:
    """MAE and MFE excursions track peak adverse and favorable prices accurately."""
    engine = SimulationEngine()
    bar1 = _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000)
    engine.apply_effects(
        StrategyEffects(
            orders_to_open=(
                OrderRequest(
                    symbol="EURUSD",
                    direction=1,
                    order_type=OrderType.BUY,
                    volume=2.0,
                ),
            )
        ),
        bar1,
    )

    # Bar 2: Low reaches 1.0960 (adverse), High reaches 1.1030 (favorable)
    bar2 = _bar(1060, 1.1000, 1.1030, 1.0960, 1.1010)
    engine.process_intra_bar(bar2)

    # Bar 3: Low reaches 1.0970 (not worse), High reaches 1.1070 (better favorable)
    bar3 = _bar(1120, 1.1010, 1.1070, 1.0970, 1.1050)
    engine.process_intra_bar(bar3)

    # Bar 4: Close trade
    bar4 = _bar(1180, 1.1050, 1.1055, 1.1045, 1.1050)
    engine.process_intra_bar(bar4)
    engine.close_all_open_positions(bar4)

    assert len(engine.mae_mfe_records) == 1
    record = engine.mae_mfe_records[0]
    # Entry was 1.1000
    assert record.mae_price == pytest.approx(1.0960)
    assert record.mae_points == pytest.approx(0.0040)
    assert record.mae_pnl == pytest.approx(-0.0040 * 2.0)

    assert record.mfe_price == pytest.approx(1.1070)
    assert record.mfe_points == pytest.approx(0.0070)
    assert record.mfe_pnl == pytest.approx(0.0070 * 2.0)


def test_full_backtest_runner_run() -> None:
    """BacktestRunner orchestrates rule evaluation, fills, and metrics on bar sequence."""
    runner = BacktestRunner()

    # Strategy: Buy when close > 1.1010, exit when close > 1.1050
    rule_entry = RuleDefinition(
        rule_id="entry_long",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right=1.1010),),
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, volume=1.0),),
    )
    rule_exit = RuleDefinition(
        rule_id="exit_long",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right=1.1050),),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    strategy = StrategyDocument(
        strategy_id="strat-test-full",
        rules=(rule_entry, rule_exit),
    )

    bars = [
        _bar(1000, 1.0990, 1.1005, 1.0985, 1.1000),  # No entry
        _bar(1060, 1.1000, 1.1025, 1.0995, 1.1020),  # Triggers entry at close 1.1020
        _bar(1120, 1.1020, 1.1040, 1.1010, 1.1030),  # In position
        _bar(1180, 1.1030, 1.1065, 1.1025, 1.1060),  # Triggers exit at close 1.1060
        _bar(1240, 1.1005, 1.1010, 1.0995, 1.1000),  # Flat (close <= 1.1010)
    ]

    settings = BacktestSettings(
        initial_capital=50000.0,
        slippage_points=0.0,
        commission_per_order=2.0,
    )
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bars=bars,
        settings=settings,
    )

    result = runner.run(spec)

    assert isinstance(result, RunResult)
    assert result.strategy_id == "strat-test-full"
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.open_price == pytest.approx(1.1020)
    assert trade.close_price == pytest.approx(1.1060)
    assert trade.pnl == pytest.approx(0.0040)
    assert trade.commission == pytest.approx(4.0)
    assert trade.net_pnl == pytest.approx(0.0040 - 4.0)

    assert len(result.equity_curve) == 5
    assert result.metrics["trades_count"] == 1.0
    assert result.metrics["winning_trades"] == (1.0 if trade.net_pnl > 0 else 0.0)
    assert result.metrics["final_balance"] == pytest.approx(50000.0 + trade.net_pnl)
    assert len(result.mae_mfe) == 1


def test_empty_bars_backtest_run() -> None:
    """Empty bar series safely returns valid empty RunResult."""
    runner = BacktestRunner()
    strategy = StrategyDocument(strategy_id="empty-strat", rules=())
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_M1,
        bars=(),
    )
    result = runner.run(spec)
    assert result.strategy_id == "empty-strat"
    assert len(result.trades) == 0
    assert len(result.equity_curve) == 0
    assert result.metrics["trades_count"] == 0.0
    assert result.metrics["final_balance"] == 100000.0


def test_end_of_data_force_close() -> None:
    """Positions remaining open at end of data are closed on last bar."""
    runner = BacktestRunner()
    rule_entry = RuleDefinition(
        rule_id="entry_only",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, volume=1.0),),
    )
    strategy = StrategyDocument(strategy_id="open-only", rules=(rule_entry,))
    bars = [
        _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000),  # Enters at 1.1000
        _bar(1060, 1.1000, 1.1050, 1.0995, 1.1040),  # End of data: closes at 1.1040
    ]
    spec = RunSpec(
        strategy=strategy,
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_M1,
        bars=bars,
    )
    result = runner.run(spec)

    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.close_reason == "END_OF_DATA"
    assert trade.close_price == pytest.approx(1.1040)


def test_order_modification_and_cancellation() -> None:
    """Test modification of pending orders and SL/TP, and cancellation."""
    from app.core.trading.strategy import OrderModification

    engine = SimulationEngine()
    bar1 = _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000)

    # 1. Place a limit order
    engine.apply_effects(
        StrategyEffects(
            orders_to_open=(
                OrderRequest(
                    symbol="EURUSD",
                    direction=1,
                    order_type=OrderType.BUY_LIMIT,
                    price=1.0950,
                    volume=1.0,
                    sl=1.0900,
                    tp=1.1050,
                    comment="my_limit",
                ),
            )
        ),
        bar1,
    )
    assert len(engine.pending_orders) == 1
    ticket = next(iter(engine.pending_orders.keys()))

    # 2. Modify the limit order
    engine.apply_effects(
        StrategyEffects(
            orders_to_modify=(
                OrderModification(
                    ticket=ticket,
                    price=1.0960,
                    sl=1.0910,
                    tp=1.1060,
                ),
            )
        ),
        bar1,
    )
    po = engine.pending_orders[ticket]
    assert po.price == pytest.approx(1.0960)
    assert po.sl == pytest.approx(1.0910)
    assert po.tp == pytest.approx(1.1060)

    # 3. Cancel the order
    engine.apply_effects(
        StrategyEffects(orders_to_cancel=(str(ticket),)),
        bar1,
    )
    assert len(engine.pending_orders) == 0


def test_gap_sl_and_tp_execution_prices() -> None:
    """Gap beyond SL or TP fills at open price reflecting realistic gap slippage."""
    engine = SimulationEngine()
    bar1 = _bar(1000, 1.1000, 1.1010, 1.0990, 1.1000)
    engine.apply_effects(
        StrategyEffects(
            orders_to_open=(
                OrderRequest(
                    symbol="EURUSD",
                    direction=1,
                    order_type=OrderType.BUY,
                    volume=1.0,
                    sl=1.0950,
                    tp=1.1050,
                ),
            )
        ),
        bar1,
    )

    # Bar 2 opens with severe gap down below SL at 1.0900
    bar2 = _bar(1060, 1.0900, 1.0920, 1.0890, 1.0910)
    engine.process_intra_bar(bar2)

    assert len(engine.completed_trades) == 1
    trade = engine.completed_trades[0]
    assert trade.close_reason == "SL"
    # Fill price should be the gap open 1.0900, not 1.0950!
    assert trade.close_price == pytest.approx(1.0900)


def test_contracts_to_dict() -> None:
    """Verify contracts serialization to dictionaries."""
    settings = BacktestSettings(
        initial_capital=25000.0,
        precision_mode=PrecisionMode.OHLC,
        same_bar_sl_tp_rule=SameBarExecutionRule.WORST_CASE,
    )
    assert settings.initial_capital == 25000.0

    result = RunResult(
        strategy_id="strat-1",
        trades=(),
        equity_curve=(),
        metrics={"net_profit": 150.0},
        mae_mfe=(),
    )
    d = result.to_dict()
    assert d["strategy_id"] == "strat-1"
    assert d["metrics"]["net_profit"] == 150.0
