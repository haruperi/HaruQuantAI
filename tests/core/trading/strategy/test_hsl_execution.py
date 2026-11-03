"""Regression evidence for shared HSL semantics and capability rejection.

Description:
    Verify declared strategy behavior and explicit rejection of unavailable inputs.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Regression evidence for shared strategy execution.
Key Capabilities:
    - FR-hsl-regression-evidence: Assert observable results and failure boundaries.
Python API Usage:
    Run this module through pytest.
CLI Usage:
    uv run pytest tests/core/trading/strategy --no-cov
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np
import pytest
from app.core.data.contracts import MarketBar, PositionInfo
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError
from app.core.trading.backtest.contracts import BacktestSettings
from app.core.trading.blocks.series import BarData
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    InstrumentEconomics,
    LifecycleEvent,
    StrategyContext,
)
from app.core.trading.strategy.hsl.compiler import StrategyCompiler
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.core.trading.strategy.runtime import StrategyRuntime

TIME = 1704110400
ECONOMICS = InstrumentEconomics(0.0001, 0.00001, 10.0, 100000.0, 0.01, 100.0, 0.01)


def document(
    *, rules: list[dict[str, Any]] | None = None, **settings: Any
) -> HSLStrategyDocument:
    """Construct an isolated executable strategy."""
    return HSLStrategyDocument.model_validate(
        {
            "strategy": {
                "id": "audit",
                "name": "Audit",
                "rules": rules or [rule()],
                **settings,
            }
        }
    )


def rule(**settings: Any) -> dict[str, Any]:
    """Provide a simple entry rule, overridden by each scenario."""
    return {
        "id": "entry",
        "when": {"type": "state", "state": "always_true"},
        "then": [{"action": "enter_market", "side": "long"}],
        **settings,
    }


def event(price: float = 1.1, index: int = 0) -> BarUpdateEvent:
    """Build a closed primary bar with explicit time."""
    bar = MarketBar(
        time=TIME + index * 3600,
        open=price,
        high=price + 0.001,
        low=price - 0.001,
        close=price,
        tick_volume=10,
    )
    return BarUpdateEvent("EURUSD", Timeframe.PERIOD_H1, bar)


def evaluate(
    doc: HSLStrategyDocument, context: StrategyContext | None = None, update: Any = None
) -> Any:
    """Compile and use the core runtime directly, without a special bridge."""
    compiler = StrategyCompiler()
    return StrategyRuntime(compiler.library.registry).evaluate(
        compiler.compile_to_runtime(doc),
        context or StrategyContext(),
        update or event(),
    )


def test_enablement_events_else_and_filters() -> None:
    """No implicit ALL lifecycle mapping, dropped else, or ignored enablement."""
    assert not evaluate(document(enabled=False)).orders_to_open
    start = document(rules=[rule(event="on_start")])
    assert not evaluate(start).orders_to_open
    # A lifecycle event with no market price cannot fabricate an entry price.
    with pytest.raises(DomainError, match="Market feed"):
        evaluate(start, update=LifecycleEvent("on_start", "EURUSD", TIME, "H1"))
    other = document(
        rules=[
            rule(event={"type": "on_bar_close", "symbol": "GBPUSD", "timeframe": "H4"})
        ],
        universe={"symbols": ["EURUSD", "GBPUSD"]},
        timeframe={"primary": "H1", "additional": ["H4"]},
    )
    assert not evaluate(other).orders_to_open
    otherwise = document(
        rules=[
            rule(
                when={"type": "state", "state": "always_false"},
                then=[{"action": "emit_alert", "message": "wrong"}],
                else_then=[{"action": "enter_market", "side": "long"}],
            )
        ]
    )
    assert len(evaluate(otherwise).orders_to_open) == 1


def test_ordered_state_and_instance_isolation() -> None:
    """Earlier assignments affect later rules in the same event only."""
    doc = document(
        variables={"signal": {"type": "bool", "initial": False}},
        rules=[
            rule(
                id="set",
                priority=1,
                then=[{"action": "set_variable", "name": "signal", "value": True}],
            ),
            rule(
                id="use",
                priority=2,
                when={
                    "type": "comparison",
                    "operator": "equal",
                    "left": {"type": "variable", "name": "signal"},
                    "right": True,
                },
            ),
        ],
    )
    source = StrategyContext()
    result = evaluate(doc, source)
    assert len(result.orders_to_open) == 1
    assert not source.state
    assert result.state_updates["variables"]["signal"] is True


def test_absolute_pending_price_and_magic() -> None:
    """Pending prices remain absolute and magic numbers survive compilation."""
    doc = document(
        rules=[
            rule(
                then=[
                    {
                        "action": "enter_stop",
                        "side": "long",
                        "entry_price": 1.25,
                        "magic_number": 42,
                    }
                ]
            )
        ]
    )
    order = evaluate(doc).orders_to_open[0]
    assert order.price == 1.25
    assert order.magic == 42


def test_real_risk_sizing_and_default_stops() -> None:
    """Risk depends on equity and stop economics, with no lot-size fallback."""
    doc = document(
        money_management={"type": "risk_percent", "risk_pct": 1.0},
        risk_management={"default_stop_loss": {"type": "fixed_pips", "value": 20.0}},
    )
    context = StrategyContext(account_equity=10000.0, economics={"EURUSD": ECONOMICS})
    order = evaluate(doc, context).orders_to_open[0]
    assert order.sl == pytest.approx(1.098)
    assert order.volume == pytest.approx(0.5)
    with pytest.raises(DomainError, match="economics"):
        evaluate(doc)


def test_typed_values_and_missing_feeds() -> None:
    """String equality works; undeclared data is never replaced by primary bars."""
    string = document(
        rules=[
            rule(
                when={
                    "type": "comparison",
                    "operator": "equal",
                    "left": "x",
                    "right": "x",
                }
            )
        ]
    )
    assert evaluate(string).orders_to_open
    foreign = document(
        universe={"symbols": ["EURUSD", "GBPUSD"]},
        rules=[
            rule(
                when={
                    "type": "comparison",
                    "operator": "greater_than",
                    "left": {"type": "price", "context": {"symbol": "GBPUSD"}},
                    "right": 0,
                }
            )
        ],
    )
    with pytest.raises(DomainError, match="GBPUSD"):
        evaluate(foreign)


def test_unknown_output_and_noncausal_blocks_fail_compilation() -> None:
    """A registry declaration does not imply causal executable support."""
    compiler = StrategyCompiler()
    for name, output in (("indicator.rsi", "missing"), ("indicator.zigzag", "zigzag")):
        doc = document(
            rules=[
                rule(
                    when={
                        "type": "comparison",
                        "operator": "greater_than",
                        "left": {"type": "indicator", "name": name, "output": output},
                        "right": 0,
                    }
                )
            ]
        )
        with pytest.raises(DomainError):
            compiler.compile_to_runtime(doc)


def test_rsi_executes_in_core_runtime_and_ignores_future_rows() -> None:
    """A compiled indicator plan is executable and bounded by event availability."""
    doc = document(
        rules=[
            rule(
                when={
                    "type": "comparison",
                    "operator": "greater_than",
                    "left": {
                        "type": "indicator",
                        "name": "indicator.rsi",
                        "params": {"period": 2},
                        "output": "value",
                    },
                    "right": 50,
                }
            )
        ]
    )
    data = BarData.from_arrays(
        close=np.array([1.0, 2.0, 3.0, 100.0]),
        timestamps=np.array([TIME + i * 3600 for i in range(4)]),
    )
    context = StrategyContext(bars=data)
    first = evaluate(doc, context, event(3.0, 2))
    changed = BarData.from_arrays(
        close=np.array([1.0, 2.0, 3.0, -100.0]), timestamps=data.timestamps
    )
    second = evaluate(doc, replace(context, bars=changed), event(3.0, 2))
    assert first.orders_to_open == second.orders_to_open
    assert len(first.orders_to_open) == 1


def test_partial_close_is_an_absolute_quantity() -> None:
    """Partial exits preserve the selected position's quantity."""
    doc = document(
        rules=[rule(then=[{"action": "exit_position", "quantity_pct": 25.0}])]
    )
    position = PositionInfo(ticket=7, symbol="EURUSD", volume=2.0, magic=1000)
    result = evaluate(doc, StrategyContext(positions=(position,)))
    assert result.positions_to_close[0].volume == 0.5


def test_shared_backtester_has_no_fabricated_financial_defaults() -> None:
    """The preview adapter uses the real matcher and rejects missing economics."""
    compiler = StrategyCompiler()
    doc = document()
    effects = compiler.evaluate_hsl_on_bars(
        doc, [event().bar, event(index=1).bar], settings=BacktestSettings()
    )
    assert [len(item.orders_to_open) for item in effects] == [1, 0]


@pytest.mark.parametrize(
    "kind",
    [
        "on_start",
        "on_stop",
        "on_timer",
        "on_order_submitted",
        "on_order_filled",
        "on_order_cancelled",
        "on_position_opened",
        "on_position_closed",
        "on_session_open",
        "on_session_close",
        "on_order_rejected",
    ],
)
def test_lifecycle_dispatch_is_exact(kind: str) -> None:
    """An explicit host lifecycle event executes only its matching rule."""
    from typing import get_args

    from app.core.trading.strategy.hsl.models import LifecycleEventType

    assert kind in get_args(LifecycleEventType)
    doc = document(
        rules=[rule(event=kind, then=[{"action": "emit_alert", "message": kind}])]
    )
    update = LifecycleEvent(kind, "EURUSD", TIME, "H1")
    effects = evaluate(doc, update=update)
    assert effects.alerts[0]["message"] == kind
    if kind in ("on_start", "on_stop"):
        assert not evaluate(
            doc, StrategyContext(state=effects.state_updates), update
        ).alerts


def test_unknown_event_and_changed_plan_fail_closed() -> None:
    """Unknown events and modified registry bindings cannot silently execute."""
    with pytest.raises(DomainError) as error:
        evaluate(document(), update=LifecycleEvent("invented", "EURUSD", TIME, "H1"))
    assert error.value.code == "HSL_UNKNOWN_EVENT"
    compiler = StrategyCompiler()
    plan = compiler.compile_to_runtime(document())
    with pytest.raises(DomainError) as error:
        StrategyRuntime().evaluate(
            replace(plan, block_fingerprints={"unknown": "stale"}),
            StrategyContext(),
            event(),
        )
    assert error.value.code == "HSL_STALE_PLAN"


@pytest.mark.parametrize(
    ("mode", "value", "expected"),
    [
        ("fixed_pips", 20.0, 1.098),
        ("fixed_points", 20.0, 1.0998),
        ("percent", 1.0, 1.089),
        ("expression", 1.095, 1.095),
    ],
)
def test_protection_modes(mode: str, value: float, expected: float) -> None:
    """Declared protection units produce independently known absolute levels."""
    spec = {"type": mode, "expression" if mode == "expression" else "value": value}
    doc = document(
        risk_management={
            "default_stop_loss": spec,
            "default_take_profit": {"type": "risk_multiple", "multiple": 2.0},
        }
    )
    order = evaluate(
        doc, StrategyContext(economics={"EURUSD": ECONOMICS})
    ).orders_to_open[0]
    assert order.sl == pytest.approx(expected)
    assert order.tp == pytest.approx(1.1 + 2 * (1.1 - expected))


@pytest.mark.parametrize(
    ("sizing", "expected"),
    [
        ({"type": "fixed_cash", "amount": 110000.0}, 1.0),
        ({"type": "percent_equity", "percent": 11.0}, 0.01),
        ({"type": "fixed_size", "size": 0.257}, 0.25),
    ],
)
def test_sizing_conversions(sizing: dict[str, Any], expected: float) -> None:
    """Cash and equity sizing use contract economics and floor to the lot grid."""
    effects = evaluate(
        document(money_management=sizing),
        StrategyContext(account_equity=10000.0, economics={"EURUSD": ECONOMICS}),
    )
    assert effects.orders_to_open[0].volume == pytest.approx(expected)


def test_owned_position_management_and_once_only_partials() -> None:
    """Breakeven/trailing tighten owned stops and partial effects are one-time."""
    position = PositionInfo(
        ticket=1,
        symbol="EURUSD",
        volume=2.0,
        position_type=0,
        price_open=1.1,
        sl=1.095,
        magic=1000,
        time=TIME,
    )
    doc = document(
        rules=[rule(then=[{"action": "emit_alert", "message": "manage"}])],
        trade_management={
            "breakeven": {"trigger_pips": 10.0, "lock_pips": 2.0},
            "trailing_stop": {"type": "fixed_pips", "distance": 5.0},
            "partial_exits": [{"trigger_pips": 10.0, "close_pct": 25.0}],
        },
    )
    context = StrategyContext(positions=(position,), economics={"EURUSD": ECONOMICS})
    effects = evaluate(doc, context, event(1.102, 1))
    assert effects.orders_to_modify[0].sl == pytest.approx(1.1015)
    assert effects.positions_to_close[0].volume == 0.5
    repeated = evaluate(
        doc, replace(context, state=effects.state_updates), event(1.102, 2)
    )
    assert not repeated.positions_to_close
    foreign = replace(context, positions=(replace(position, magic=7),))
    assert not evaluate(doc, foreign, event(1.102, 1)).orders_to_modify


def test_temporal_histories_observe_actual_prior_events() -> None:
    """Temporal rules require observed prior bars and retain their boolean history."""
    doc = document(
        rules=[
            rule(
                when={
                    "type": "temporal",
                    "operator": "remains_true_for",
                    "bars": 2,
                    "condition": {"type": "state", "state": "always_true"},
                }
            )
        ]
    )
    first = evaluate(doc)
    assert not first.orders_to_open
    second = evaluate(doc, StrategyContext(state=first.state_updates), event(index=1))
    assert len(second.orders_to_open) == 1


def test_time_and_equity_policy_constraints() -> None:
    """Time windows and drawdown limits block entries using explicit snapshots."""
    # TIME is 12:00 UTC; the event closes at 13:00.
    doc = document(
        trading_options={
            "limit_time_range": True,
            "time_range_start": "14:00",
            "time_range_end": "15:00",
        }
    )
    assert not evaluate(doc).orders_to_open
    doc = document(risk_management={"max_daily_loss_pct": 1.0, "max_drawdown_pct": 5.0})
    initial = evaluate(doc, StrategyContext(account_equity=10000.0))
    fallen = evaluate(
        doc,
        StrategyContext(account_equity=9800.0, state=initial.state_updates),
        event(index=1),
    )
    assert not fallen.orders_to_open
    with pytest.raises(DomainError, match="equity"):
        evaluate(doc)


def test_reference_feed_uses_only_closed_rows() -> None:
    """An H4 reference row closing after the H1 event cannot influence a signal."""
    reference = BarData.from_arrays(
        close=np.array([1.0, 100.0]), timestamps=np.array([TIME - 4 * 3600, TIME])
    )
    doc = document(
        timeframe={"primary": "H1", "additional": ["H4"]},
        rules=[
            rule(
                when={
                    "type": "comparison",
                    "operator": "less_than",
                    "left": {
                        "type": "price",
                        "field": "close",
                        "context": {"timeframe": "H4"},
                    },
                    "right": 2.0,
                }
            )
        ],
    )
    effects = evaluate(
        doc, StrategyContext(bars_by_context={("EURUSD", "H4"): reference})
    )
    assert len(effects.orders_to_open) == 1


def test_daily_limit_requires_confirmed_fills() -> None:
    """Unfilled pending submissions do not count as executed trades."""
    doc = document(trading_options={"max_trades_per_day": 2})
    with pytest.raises(DomainError) as error:
        evaluate(doc)
    assert error.value.code == "HSL_MISSING_TRADE_COUNT"
    assert evaluate(doc, StrategyContext(entries_today=1)).orders_to_open
    assert not evaluate(doc, StrategyContext(entries_today=2)).orders_to_open


def test_historical_host_counts_fills_for_daily_limits() -> None:
    """The historical adapter supplies actual entries across successive events."""
    doc = document(
        trading_options={"max_trades_per_day": 2},
        risk_management={"max_open_positions": 10},
    )
    bars = [event(index=index).bar for index in range(5)]
    effects = StrategyCompiler().evaluate_hsl_on_bars(doc, bars)
    assert sum(len(effect.orders_to_open) for effect in effects) == 2
    assert effects[-1].state_updates["trades_today"] == 2


def test_unavailable_assignment_never_publishes_nan() -> None:
    """An undefined numeric sample leaves the last finite variable value intact."""
    doc = document(
        variables={"value": {"type": "float", "initial": 1.0}},
        rules=[
            rule(
                then=[
                    {
                        "action": "set_variable",
                        "name": "value",
                        "value": {
                            "type": "math",
                            "operator": "divide",
                            "left": {"type": "value", "value": 1.0},
                            "right": {"type": "value", "value": 0.0},
                        },
                    }
                ]
            )
        ],
    )
    effects = evaluate(doc)
    assert effects.state_updates["variables"]["value"] == 1.0


def test_declared_scalar_type_is_checked_before_compilation() -> None:
    """A typed declaration cannot carry an unrelated scalar value."""
    with pytest.raises(DomainError) as error:
        StrategyCompiler().compile_to_runtime(
            document(parameters={"bad": {"type": "int", "default": "text"}})
        )
    assert error.value.code in (
        "WIZARD_INVALID_PARAMETER_BOUNDS",
        "HSL_INVALID_DECLARATION",
    )


def test_authoring_template_cannot_be_selected_for_generation() -> None:
    """Manual discovery does not grant generation eligibility to templates."""
    from app.core.trading.generation.engine import GenerationEngine, GenerationSpec

    StrategyCompiler()  # Populate the application registry through its normal owner.
    with pytest.raises(DomainError) as error:
        GenerationEngine(
            GenerationSpec(allowed_blocks=("indicator.custom.indicator_template",))
        ).generate_hsl_strategy()
    assert error.value.code == "HSL_GENERATION_BLOCK_UNAVAILABLE"


def test_fresh_library_loads_recipes_once_and_binds_alias_parameters() -> None:
    """A fresh registry supports real signal recipes and configured alias calls."""
    from app.core.trading.blocks.registry import BlockRegistry
    from app.core.trading.strategy.hsl.library import WizardBlockLibrary

    registry = BlockRegistry()
    library = WizardBlockLibrary(registry=registry, seed_defaults=True)
    revision = registry.revision
    WizardBlockLibrary(registry=registry, seed_defaults=True)
    assert registry.revision == revision
    entry = library.require("adx_changes_up")
    descriptor = registry.require(entry.registry_id)
    parameters = descriptor.target.config_model().model_dump()
    bars = BarData.from_arrays(
        open=np.linspace(1.0, 2.0, 40),
        high=np.linspace(1.001, 2.001, 40),
        low=np.linspace(0.999, 1.999, 40),
        close=np.linspace(1.0, 2.0, 40),
        volume=np.ones(40),
        timestamps=np.array([TIME + i * 3600 for i in range(40)]),
    )
    expected = bool(descriptor.target(bars, **parameters))
    doc = document(
        rules=[
            rule(
                when={
                    "type": "block_condition",
                    "block_id": "adx_changes_up",
                    "params": parameters,
                },
                then=[{"action": "emit_alert", "message": "then"}],
                else_then=[{"action": "emit_alert", "message": "else"}],
            )
        ]
    )
    plan = StrategyCompiler(library=library).compile_to_runtime(doc)
    effects = StrategyRuntime(registry).evaluate(
        plan, StrategyContext(bars=bars), event(2.0, 39)
    )
    assert effects.alerts[0]["message"] == ("then" if expected else "else")
