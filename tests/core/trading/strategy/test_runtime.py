"""Unit tests for StrategyRuntime pure event-driven evaluation."""

from __future__ import annotations

from app.core.data.contracts import MarketBar, MarketTick
from app.core.enums import OrderType, Timeframe
from app.core.trading.connection.contracts import OrderInfo, PositionInfo
from app.core.trading.strategy import (
    ActionKind,
    BarUpdateEvent,
    ConditionDefinition,
    OrderRequest,
    ParameterDefinition,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    SignalConflictPolicy,
    StrategyContext,
    StrategyDocument,
    StrategyEffects,
    StrategyRuntime,
    TickUpdateEvent,
    TradingSetupConfig,
    VariableDefinition,
)


def _make_bar(close: float = 1.1050, open_: float = 1.1000) -> MarketBar:
    return MarketBar(
        time=1700000000,
        open=open_,
        high=max(open_, close) + 0.0010,
        low=min(open_, close) - 0.0010,
        close=close,
        tick_volume=150,
    )


def _make_tick(
    bid: float = 1.1050, ask: float = 1.1052, last: float = 1.1051
) -> MarketTick:
    return MarketTick(
        time_msc=1700000000000,
        bid=bid,
        ask=ask,
        last=last,
        volume=10,
    )


def test_pure_execution_no_mutation() -> None:
    """Verify runtime evaluation does not mutate strategy document or context."""
    runtime = StrategyRuntime()
    rule = RuleDefinition(
        rule_id="r1",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right=1.1000),),
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, volume=1.0),),
    )
    strategy = StrategyDocument(strategy_id="strat-1", rules=(rule,))
    context = StrategyContext(account_balance=10000.0, variables={"x": 5.0})
    event = BarUpdateEvent(
        symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=_make_bar(1.1050)
    )

    effects = runtime.evaluate(strategy, context, event)

    assert isinstance(effects, StrategyEffects)
    assert len(effects.orders_to_open) == 1
    assert strategy.strategy_id == "strat-1"
    assert context.account_balance == 10000.0
    assert context.variables == {"x": 5.0}


def test_trigger_kind_filtering() -> None:
    """Verify rules execute only on matching event triggers."""
    runtime = StrategyRuntime()
    rule_close = RuleDefinition(
        rule_id="r_close",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, comment="close_rule"),),
    )
    rule_open = RuleDefinition(
        rule_id="r_open",
        trigger=RuleTriggerKind.ON_BAR_OPEN,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, comment="open_rule"),),
    )
    rule_tick = RuleDefinition(
        rule_id="r_tick",
        trigger=RuleTriggerKind.ON_TICK,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=-1, comment="tick_rule"),),
    )
    strategy = StrategyDocument(
        strategy_id="strat-triggers", rules=(rule_close, rule_open, rule_tick)
    )
    context = StrategyContext()

    # 1. Bar close event triggers only rule_close
    ev_close = BarUpdateEvent(
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bar=_make_bar(),
        is_bar_close=True,
    )
    eff_close = runtime.evaluate(strategy, context, ev_close)
    assert len(eff_close.orders_to_open) == 1
    assert eff_close.orders_to_open[0].comment == "close_rule"

    # 2. Bar open event triggers only rule_open
    ev_open = BarUpdateEvent(
        symbol="EURUSD",
        timeframe=Timeframe.PERIOD_H1,
        bar=_make_bar(),
        is_bar_close=False,
    )
    eff_open = runtime.evaluate(strategy, context, ev_open)
    assert len(eff_open.orders_to_open) == 1
    assert eff_open.orders_to_open[0].comment == "open_rule"

    # 3. Tick event triggers only rule_tick
    ev_tick = TickUpdateEvent(symbol="EURUSD", tick=_make_tick())
    eff_tick = runtime.evaluate(strategy, context, ev_tick)
    assert len(eff_tick.orders_to_open) == 1
    assert eff_tick.orders_to_open[0].comment == "tick_rule"


def test_condition_evaluation_and_sl_tp_calculation() -> None:
    """Verify scalar conditions, parameters, variables, and SL/TP calculation."""
    runtime = StrategyRuntime()
    rule = RuleDefinition(
        rule_id="r_long",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(left="close", comparator=">", right="threshold"),
            ConditionDefinition(left="var_factor", comparator="=", right=1.0),
        ),
        actions=(
            RuleAction(
                kind=ActionKind.ENTER,
                direction=1,
                order_type=OrderType.BUY,
                volume=2.0,
                sl_pips=20.0,
                tp_pips=40.0,
                comment="breakout",
                atm_rules={"trailing_stop_pips": 10.0},
            ),
        ),
    )
    strategy = StrategyDocument(
        strategy_id="strat-sltp",
        rules=(rule,),
        params=(ParameterDefinition(name="threshold", value=1.1000),),
        variables=(VariableDefinition(name="var_factor", default_value=1.0),),
        trading_setup=TradingSetupConfig(pip_size=0.0001, magic_number=555),
    )
    context = StrategyContext(variables={"var_factor": 1.0})
    bar = _make_bar(close=1.1050)
    event = BarUpdateEvent(symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=bar)

    effects = runtime.evaluate(strategy, context, event)
    assert len(effects.orders_to_open) == 1
    order: OrderRequest = effects.orders_to_open[0]
    assert order.symbol == "EURUSD"
    assert order.direction == 1
    assert order.order_type == OrderType.BUY
    assert order.volume == 2.0
    assert order.price == 1.1050
    # SL = 1.1050 - 20 * 0.0001 = 1.1030
    assert round(order.sl, 5) == 1.1030
    # TP = 1.1050 + 40 * 0.0001 = 1.1090
    assert round(order.tp, 5) == 1.1090
    assert order.magic == 555
    assert order.comment == "breakout"
    assert order.atm_rules == {"trailing_stop_pips": 10.0}


def test_exit_and_cancel_actions() -> None:
    """Verify position closing and order cancellation effects."""
    runtime = StrategyRuntime()
    rule_exit = RuleDefinition(
        rule_id="r_exit",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator="<", right=1.1000),),
        actions=(
            RuleAction(kind=ActionKind.EXIT, direction=1, comment="stop_out"),
            RuleAction(kind=ActionKind.CANCEL),
        ),
    )
    strategy = StrategyDocument(strategy_id="strat-exit", rules=(rule_exit,))
    pos1 = PositionInfo(ticket=101, symbol="EURUSD", position_type=0, volume=1.0)
    pos2 = PositionInfo(ticket=102, symbol="GBPUSD", position_type=0, volume=1.0)
    ord1 = OrderInfo(ticket=201, symbol="EURUSD", order_type=2, volume_initial=1.0)
    context = StrategyContext(positions=(pos1, pos2), orders=(ord1,))
    event = BarUpdateEvent(
        symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=_make_bar(close=1.0950)
    )

    effects = runtime.evaluate(strategy, context, event)
    # Only EURUSD position 101 should be closed
    assert len(effects.positions_to_close) == 1
    assert effects.positions_to_close[0].ticket == 101
    assert effects.positions_to_close[0].comment == "stop_out"
    # EURUSD order 201 should be cancelled
    assert effects.orders_to_cancel == ("201",)


def test_conflict_resolution_first_signal() -> None:
    """Verify SignalConflictPolicy.FIRST_SIGNAL keeps only the first signal."""
    runtime = StrategyRuntime()
    rule_long = RuleDefinition(
        rule_id="r1",
        trigger=RuleTriggerKind.ALL,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, comment="first_long"),),
    )
    rule_short = RuleDefinition(
        rule_id="r2",
        trigger=RuleTriggerKind.ALL,
        actions=(
            RuleAction(kind=ActionKind.ENTER, direction=-1, comment="second_short"),
        ),
    )
    strategy = StrategyDocument(
        strategy_id="strat-conflict",
        rules=(rule_long, rule_short),
        trading_setup=TradingSetupConfig(
            conflict_policy=SignalConflictPolicy.FIRST_SIGNAL
        ),
    )
    context = StrategyContext()
    event = BarUpdateEvent(
        symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=_make_bar()
    )

    effects = runtime.evaluate(strategy, context, event)
    assert len(effects.orders_to_open) == 1
    assert effects.orders_to_open[0].direction == 1
    assert effects.orders_to_open[0].comment == "first_long"


def test_conflict_resolution_cancel_both() -> None:
    """Verify SignalConflictPolicy.CANCEL_BOTH discards opposing signals."""
    runtime = StrategyRuntime()
    rule_long = RuleDefinition(
        rule_id="r1",
        trigger=RuleTriggerKind.ALL,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1),),
    )
    rule_short = RuleDefinition(
        rule_id="r2",
        trigger=RuleTriggerKind.ALL,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=-1),),
    )
    strategy = StrategyDocument(
        strategy_id="strat-conflict-cancel",
        rules=(rule_long, rule_short),
        trading_setup=TradingSetupConfig(
            conflict_policy=SignalConflictPolicy.CANCEL_BOTH
        ),
    )
    context = StrategyContext()
    event = BarUpdateEvent(
        symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=_make_bar()
    )

    effects = runtime.evaluate(strategy, context, event)
    assert len(effects.orders_to_open) == 0


def test_conflict_resolution_reverse() -> None:
    """Verify SignalConflictPolicy.REVERSE keeps the latest signal."""
    runtime = StrategyRuntime()
    rule_long = RuleDefinition(
        rule_id="r1",
        trigger=RuleTriggerKind.ALL,
        actions=(RuleAction(kind=ActionKind.ENTER, direction=1, comment="first_long"),),
    )
    rule_short = RuleDefinition(
        rule_id="r2",
        trigger=RuleTriggerKind.ALL,
        actions=(
            RuleAction(kind=ActionKind.ENTER, direction=-1, comment="second_short"),
        ),
    )
    strategy = StrategyDocument(
        strategy_id="strat-conflict-reverse",
        rules=(rule_long, rule_short),
        trading_setup=TradingSetupConfig(conflict_policy=SignalConflictPolicy.REVERSE),
    )
    context = StrategyContext()
    event = BarUpdateEvent(
        symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=_make_bar()
    )

    effects = runtime.evaluate(strategy, context, event)
    assert len(effects.orders_to_open) == 1
    assert effects.orders_to_open[0].direction == -1
    assert effects.orders_to_open[0].comment == "second_short"


def test_max_open_positions_enforcement() -> None:
    """Verify orders are trimmed when max open position capacity is reached."""
    runtime = StrategyRuntime()
    rule = RuleDefinition(
        rule_id="r1",
        trigger=RuleTriggerKind.ALL,
        actions=(
            RuleAction(kind=ActionKind.ENTER, direction=1, comment="order1"),
            RuleAction(kind=ActionKind.ENTER, direction=1, comment="order2"),
        ),
    )
    # Strategy allows max 1 open position, but context already has 1 open position for EURUSD
    strategy = StrategyDocument(
        strategy_id="strat-max-pos",
        rules=(rule,),
        trading_setup=TradingSetupConfig(max_open_positions=1),
    )
    pos = PositionInfo(ticket=101, symbol="EURUSD", position_type=0, volume=1.0)
    context = StrategyContext(positions=(pos,))
    event = BarUpdateEvent(
        symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=_make_bar()
    )

    effects = runtime.evaluate(strategy, context, event)
    # Capacity is 0 remaining, so no new orders to open
    assert len(effects.orders_to_open) == 0
