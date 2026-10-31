"""Unit tests for Phase 5.4 HSL StrategyCompiler and StrategyRuntime bridge.
Description:
    Verifies StrategyCompiler lowering of HSL 1.0 ASTs to Core StrategyDocument
    (compile_to_runtime), causal bar-by-bar simulation (evaluate_hsl_on_bars),
    inclusive prior-bar crossing semantics (crosses_above / crosses_below), and
    NormalizedStrategy lowering (compile_to_normalized) for Gate G4.
Purpose:
    FEAT-WIZARD-COMPILER: Gate G4 verification suite for Phase 5.4
    (WO-WZ-HSL-COMPILER).
Key Capabilities:
    - FR-test-runtime-lowering: Verifies priority-ordered rule lowering and
      inclusive crossing condition lowering (>, <= and <, >=).
    - FR-test-causal-bar-evaluation: Verifies causal bar-by-bar evaluation over
      BarUpdateEvent and MarketBar sequences across indicators, math, functions,
      and actions.
    - FR-test-normalized-lowering: Verifies NormalizedStrategy rendering across
      all multi-platform Jinja2 templates.
Python API Usage:
    pytest tests/workspace/algo_wizard/test_compiler_and_runtime.py
CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_compiler_and_runtime.py --no-cov -q
"""

from __future__ import annotations

import pytest
from app.core.data.contracts import MarketBar
from app.core.enums import Timeframe
from app.core.lib.errors import DomainError
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.registry import BlockRegistry
from app.core.trading.strategy.contracts import (
    ActionKind,
    BarUpdateEvent,
    RuleTriggerKind,
    SignalConflictPolicy,
)
from app.core.wizard.transform import (
    CTRADER_TEMPLATE,
    EASYLANGUAGE_TEMPLATE,
    MQL4_TEMPLATE,
    MQL5_TEMPLATE,
    PYTHON_TEMPLATE,
)
from app.workspace.algo_wizard import (
    AlertActionNode,
    ComparisonConditionNode,
    EvaluationContext,
    FunctionExpressionNode,
    HSLStrategyDocument,
    HSLStrategyPayload,
    IndicatorExpressionNode,
    LifecycleEventSpec,
    LogicalConditionNode,
    MarketPriceNode,
    MathExpressionNode,
    MoneyManagementSpec,
    NotConditionNode,
    OrderCancelActionNode,
    OrderMarketActionNode,
    OrderModifyActionNode,
    OrderPendingActionNode,
    ParameterRefNode,
    ParameterSpec,
    PositionAttrNode,
    PositionCloseActionNode,
    RiskManagementSpec,
    RuleNode,
    StateConditionNode,
    StopLossSpec,
    StrategyCompiler,
    StrategyValidator,
    TakeProfitSpec,
    TemporalConditionNode,
    TimeframeSpec,
    UniverseSpec,
    ValueLiteralNode,
    VariableRefNode,
    VariableSetActionNode,
    VariableSpec,
    WizardBlockLibrary,
)
from jinja2 import Environment


def _make_bars(closes: list[float], base_time: int = 1704110400) -> list[MarketBar]:
    """Create a sequence of MarketBar instances from closing prices."""
    bars: list[MarketBar] = []
    for idx, c in enumerate(closes):
        bars.append(
            MarketBar(
                time=base_time + idx * 3600,
                open=c - 0.5,
                high=c + 1.0,
                low=c - 1.0,
                close=c,
                tick_volume=100 + idx * 10,
            )
        )
    return bars


def test_compile_to_runtime_rule_priority_and_crossing_lowering() -> None:
    compiler = StrategyCompiler()
    assert isinstance(compiler.library, WizardBlockLibrary)
    assert isinstance(compiler.validator, StrategyValidator)
    doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="strat-crossing-priority",
            name="Crossing Priority Strategy",
            parameters={
                "threshold": ParameterSpec(
                    type="float", default=100.0, min=10.0, max=500.0
                ),
                "fast_p": ParameterSpec(type="int", default=3, min=2, max=50),
            },
            variables={
                "signal_count": VariableSpec(type="int", initial=0),
            },
            risk_management=RiskManagementSpec(
                max_open_positions=2,
                allow_opposite_signals=True,
            ),
            money_management=MoneyManagementSpec(
                type="risk_percent",
                risk_pct=ValueLiteralNode(value=2.0),
                max_lots=0.5,
            ),
            rules=(
                RuleNode(
                    id="rule-b",
                    name="Crosses Below Exit",
                    priority=20,
                    event=LifecycleEventSpec(type="on_bar_open"),
                    when=ComparisonConditionNode(
                        operator="crosses_below",
                        left=MarketPriceNode(field="close"),
                        right=ParameterRefNode(name="threshold"),
                    ),
                    then=(
                        PositionCloseActionNode(
                            target_side="long",
                            quantity_pct=50.0,
                        ),
                    ),
                ),
                RuleNode(
                    id="rule-a",
                    name="Crosses Above Entry",
                    priority=10,
                    event=LifecycleEventSpec(type="on_bar_close"),
                    when=ComparisonConditionNode(
                        operator="crosses_above",
                        left=MarketPriceNode(field="close"),
                        right=ParameterRefNode(name="threshold"),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=20.0),
                            ),
                            take_profit=TakeProfitSpec(
                                type="risk_multiple",
                                multiple=ValueLiteralNode(value=2.0),
                            ),
                            comment="CrossAboveLong",
                        ),
                    ),
                ),
            ),
        )
    )
    runtime_doc = compiler.compile_to_runtime(doc)
    assert runtime_doc.strategy_id == "strat-crossing-priority"
    assert runtime_doc.trading_setup.conflict_policy == SignalConflictPolicy.REVERSE
    assert runtime_doc.trading_setup.max_open_positions == 2
    assert len(runtime_doc.rules) == 2
    r0, r1 = runtime_doc.rules
    assert r0.rule_id == "rule-a"
    assert r0.trigger == RuleTriggerKind.ON_BAR_CLOSE
    assert len(r0.conditions) == 2
    assert r0.conditions[0].comparator == ">"
    assert r0.conditions[1].comparator == "<="
    assert r0.actions[0].kind == ActionKind.ENTER
    assert r0.actions[0].sl_pips == 20.0
    assert r0.actions[0].tp_pips == 40.0
    assert r1.rule_id == "rule-b"
    assert r1.trigger == RuleTriggerKind.ON_BAR_OPEN
    assert len(r1.conditions) == 2
    assert r1.conditions[0].comparator == "<"
    assert r1.conditions[1].comparator == ">="
    assert r1.actions[0].kind == ActionKind.EXIT
    assert r1.actions[0].volume == 0.5


def test_evaluate_hsl_on_bars_causal_crossing_and_indicators() -> None:
    compiler = StrategyCompiler()
    bars = _make_bars([98.0, 100.0, 105.0, 100.0, 95.0])
    doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="causal-crossing-sim",
            name="Causal Crossing Simulation",
            universe=UniverseSpec(mode="explicit", symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1"),
            parameters={"level": ParameterSpec(type="float", default=100.0)},
            variables={"cross_events": VariableSpec(type="int", initial=0)},
            rules=(
                RuleNode(
                    id="entry-cross-up",
                    priority=1,
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_flat"),
                            ComparisonConditionNode(
                                operator="crosses_above",
                                left=MarketPriceNode(field="close"),
                                right=ParameterRefNode(name="level"),
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            size=ValueLiteralNode(value=1.0),
                            stop_loss=StopLossSpec(
                                type="atr",
                                period=ValueLiteralNode(value=14),
                                multiplier=ValueLiteralNode(value=1.5),
                            ),
                            take_profit=TakeProfitSpec(
                                type="atr",
                                period=ValueLiteralNode(value=14),
                                multiplier=ValueLiteralNode(value=3.0),
                            ),
                        ),
                        VariableSetActionNode(
                            name="cross_events",
                            value=ValueLiteralNode(value=1),
                        ),
                    ),
                ),
                RuleNode(
                    id="exit-cross-down",
                    priority=2,
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_long"),
                            ComparisonConditionNode(
                                operator="crosses_below",
                                left=MarketPriceNode(field="close"),
                                right=ParameterRefNode(name="level"),
                            ),
                        ),
                    ),
                    then=(PositionCloseActionNode(target_side="long"),),
                ),
            ),
        )
    )
    assert compiler.evaluate_hsl_on_bars(doc, ()) == ()
    effects = compiler.evaluate_hsl_on_bars(doc, bars)
    assert len(effects) == 5
    assert len(effects[0].orders_to_open) == 0
    assert len(effects[1].orders_to_open) == 0
    assert len(effects[2].orders_to_open) == 1
    assert effects[2].orders_to_open[0].direction == 1
    assert len(effects[3].positions_to_close) == 0
    assert len(effects[4].positions_to_close) == 1


def test_evaluate_hsl_on_bars_indicators_math_functions_and_all_actions() -> None:
    custom_reg = BlockRegistry()

    @block(
        BlockSpec(
            id="custom.scale_signal",
            name="Scale Signal",
            category="custom_signals",
            execution_kind=ExecutionKind.EXPRESSION,
            outputs=(OutputPort("val", PortType.NUMBER),),
        )
    )
    def _scale_signal(val: float, factor: float = 2.0) -> float:
        return float(val) * float(factor)

    custom_reg.register_block(_scale_signal)
    lib = WizardBlockLibrary(registry=custom_reg)
    default_compiler = StrategyCompiler()
    custom_compiler = StrategyCompiler(library=lib)
    bars = _make_bars([100.0 + i * 2.0 for i in range(20)])
    bar_events = [
        BarUpdateEvent(
            symbol="EURUSD", timeframe=Timeframe.PERIOD_H1, bar=b, is_bar_close=True
        )
        for b in bars
    ]
    fn_doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="custom-fn-strat",
            name="Custom Function Strategy",
            money_management=MoneyManagementSpec(
                type="percent_equity",
                percent=ValueLiteralNode(value=2.0),
            ),
            rules=(
                RuleNode(
                    id="r-fn",
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=FunctionExpressionNode(
                            name="custom.scale_signal",
                            args=(
                                MarketPriceNode(field="close"),
                                ValueLiteralNode(value=2.0),
                            ),
                        ),
                        right=ValueLiteralNode(value=200.0),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="short",
                            stop_loss=StopLossSpec(
                                type="expression",
                                expression=ValueLiteralNode(value=12.0),
                            ),
                            take_profit=TakeProfitSpec(
                                type="expression",
                                expression=ValueLiteralNode(value=24.0),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    fn_effects = custom_compiler.evaluate_hsl_on_bars(fn_doc, bar_events)
    assert len(fn_effects[1].orders_to_open) == 1
    assert fn_effects[1].orders_to_open[0].direction == -1
    ind_doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="comprehensive-sim",
            name="Comprehensive Simulation",
            timeframe=TimeframeSpec(primary="CUSTOM_TF"),
            risk_management=RiskManagementSpec(
                max_open_positions=5, allow_opposite_signals=True
            ),
            parameters={
                "period_p": ParameterSpec(type="int", default=5, min=5, max=20)
            },
            variables={"var_offset": VariableSpec(type="float", initial=10.0)},
            rules=(
                RuleNode(
                    id="r-disabled",
                    enabled=False,
                    when=StateConditionNode(state="position.is_flat"),
                    then=(PositionCloseActionNode(target_side="any"),),
                ),
                RuleNode(
                    id="r-open-short-and-pending",
                    priority=1,
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_flat"),
                            NotConditionNode(
                                condition=StateConditionNode(state="position.is_short")
                            ),
                            TemporalConditionNode(
                                operator="remains_true_for",
                                condition=StateConditionNode(state="always_true"),
                                bars=1,
                            ),
                            ComparisonConditionNode(
                                operator="greater_or_equal",
                                left=IndicatorExpressionNode(
                                    name="indicator.highest",
                                    inputs={"source": MarketPriceNode(field="typical")},
                                ),
                                right=IndicatorExpressionNode(
                                    name="indicator.lowest",
                                    inputs={"source": MarketPriceNode(field="median")},
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=IndicatorExpressionNode(
                                    name="indicator.ema",
                                    params={
                                        "period": ParameterRefNode(name="period_p")
                                    },
                                ),
                                right=ValueLiteralNode(value=0.0),
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="short",
                            stop_loss=StopLossSpec(
                                type="indicator",
                                indicator=IndicatorExpressionNode(
                                    name="indicator.sma",
                                    params={"period": 5},
                                ),
                            ),
                            take_profit=TakeProfitSpec(
                                type="fixed_pips",
                                value=VariableRefNode(name="var_offset"),
                            ),
                        ),
                        OrderPendingActionNode(
                            action="enter_stop",
                            side="short",
                            entry_price=MarketPriceNode(
                                field="weighted",
                                context=EvaluationContext(shift=1),
                            ),
                            expiration_bars=5,
                        ),
                        OrderPendingActionNode(
                            action="enter_limit",
                            side="short",
                            entry_price=MarketPriceNode(field="open"),
                        ),
                        AlertActionNode(message="Opened positions", level="info"),
                    ),
                ),
                RuleNode(
                    id="r-manage-active",
                    priority=2,
                    when=LogicalConditionNode(
                        operator="or",
                        conditions=(
                            TemporalConditionNode(
                                operator="occurred_within",
                                condition=StateConditionNode(state="position.is_short"),
                                bars=2,
                            ),
                            StateConditionNode(state="always_false"),
                        ),
                    ),
                    then=(
                        OrderModifyActionNode(
                            action="modify_stop_loss",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=MathExpressionNode(
                                    operator="max",
                                    left=MathExpressionNode(
                                        operator="min",
                                        left=MathExpressionNode(
                                            operator="multiply",
                                            left=MathExpressionNode(
                                                operator="divide",
                                                left=MathExpressionNode(
                                                    operator="add",
                                                    left=PositionAttrNode(field="size"),
                                                    right=PositionAttrNode(
                                                        field="bars_held"
                                                    ),
                                                ),
                                                right=ValueLiteralNode(value=1.0),
                                            ),
                                            right=ValueLiteralNode(value=2.0),
                                        ),
                                        right=ValueLiteralNode(value=50.0),
                                    ),
                                    right=MathExpressionNode(
                                        operator="abs",
                                        left=MathExpressionNode(
                                            operator="subtract",
                                            left=PositionAttrNode(field="open_price"),
                                            right=PositionAttrNode(
                                                field="unrealized_pnl"
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        OrderModifyActionNode(
                            action="modify_take_profit",
                            take_profit=TakeProfitSpec(
                                type="fixed_pips",
                                value=PositionAttrNode(field="bars_held"),
                            ),
                        ),
                        OrderCancelActionNode(target_side="any"),
                    ),
                ),
            ),
        )
    )
    sim_effects = default_compiler.evaluate_hsl_on_bars(ind_doc, bars)
    assert len(sim_effects) == 20
    assert any(len(e.orders_to_open) > 0 for e in sim_effects)
    assert any(len(e.orders_to_modify) > 0 for e in sim_effects)
    assert any(len(e.orders_to_cancel) > 0 for e in sim_effects)


def test_compile_to_normalized_and_platform_rendering() -> None:
    compiler = StrategyCompiler()
    doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="123-export-strat",
            name="123 Export Strategy",
            parameters={
                "rsi_len": ParameterSpec(type="int", default=14),
                "use_filter": ParameterSpec(type="bool", default=True),
                "tag": ParameterSpec(type="str", default="v1"),
                "ratio": ParameterSpec(type="float", default=1.5),
            },
            variables={
                "count_v": VariableSpec(type="int", initial=0),
                "flag_v": VariableSpec(type="bool", initial=False),
                "label_v": VariableSpec(type="str", initial="init"),
                "level_v": VariableSpec(type="float", initial=50.0),
            },
            rules=(
                RuleNode(
                    id="r-export",
                    name="Export Rule",
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            StateConditionNode(state="position.is_flat"),
                            NotConditionNode(
                                condition=StateConditionNode(state="position.is_short")
                            ),
                            LogicalConditionNode(
                                operator="or",
                                conditions=(
                                    StateConditionNode(state="position.is_long"),
                                    TemporalConditionNode(
                                        operator="remains_true_for",
                                        condition=StateConditionNode(
                                            state="session.is_open"
                                        ),
                                        bars=2,
                                    ),
                                    ComparisonConditionNode(
                                        operator="crosses_above",
                                        left=IndicatorExpressionNode(
                                            name="indicator.rsi",
                                            params={
                                                "period": ParameterRefNode(
                                                    name="rsi_len"
                                                )
                                            },
                                        ),
                                        right=MathExpressionNode(
                                            operator="add",
                                            left=VariableRefNode(name="level_v"),
                                            right=MathExpressionNode(
                                                operator="abs",
                                                left=PositionAttrNode(field="size"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="equal",
                                left=ParameterRefNode(name="use_filter"),
                                right=ValueLiteralNode(value=True, value_type="bool"),
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=15.0),
                            ),
                            take_profit=TakeProfitSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=30.0),
                            ),
                        ),
                        OrderMarketActionNode(
                            side="short",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=15.0),
                            ),
                            take_profit=TakeProfitSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=30.0),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )
    norm = compiler.compile_to_normalized(doc)
    assert norm.name.startswith("var_123")
    assert len(norm.parameters) == 4
    assert len(norm.variables) == 4
    assert len(norm.rules) == 1
    env = Environment(autoescape=False, trim_blocks=True, lstrip_blocks=True)
    for tpl_str in (
        MQL5_TEMPLATE,
        MQL4_TEMPLATE,
        EASYLANGUAGE_TEMPLATE,
        CTRADER_TEMPLATE,
        PYTHON_TEMPLATE,
    ):
        rendered = env.from_string(tpl_str).render(strategy=norm)
        assert norm.name in rendered or norm.class_name in rendered


def test_compiler_rejects_invalid_document() -> None:
    compiler = StrategyCompiler()
    invalid_doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="bad-strat",
            name="Bad Strategy",
            rules=(
                RuleNode(
                    id="r1",
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=ParameterRefNode(name="non_existent_param"),
                        right=ValueLiteralNode(value=0.0),
                    ),
                    then=(PositionCloseActionNode(target_side="any"),),
                ),
            ),
        )
    )
    with pytest.raises(DomainError) as exc_rt:
        compiler.compile_to_runtime(invalid_doc)
    assert exc_rt.value.code == "WIZARD_UNKNOWN_PARAMETER_REF"
    with pytest.raises(DomainError) as exc_norm:
        compiler.compile_to_normalized(invalid_doc)
    assert exc_norm.value.code == "WIZARD_UNKNOWN_PARAMETER_REF"
