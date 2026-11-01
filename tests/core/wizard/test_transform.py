"""Unit and golden output tests for strategy rule transformation and export engine."""

from __future__ import annotations

import types
from typing import Any

from app.core.enums import OrderType
from app.core.trading.strategy.contracts import (
    ActionKind,
    ConditionDefinition,
    ParameterDefinition,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    StrategyDocument,
    TradingSetupConfig,
    VariableDefinition,
)
from app.core.wizard import ExportResult, StrategyTransformer


def _build_synthetic_strategy() -> StrategyDocument:
    """Construct a synthetic multi-rule strategy for golden output assertions."""
    params = (
        ParameterDefinition(name="fast_period", param_type="int", value=14),
        ParameterDefinition(name="slow_period", param_type="int", value=50),
        ParameterDefinition(name="stop_loss_pips", param_type="float", value=25.0),
        ParameterDefinition(name="take_profit_pips", param_type="float", value=50.0),
    )
    variables = (
        VariableDefinition(name="consecutive_losses", var_type="int", default_value=0),
    )
    entry_rule = RuleDefinition(
        rule_id="rule-entry-01",
        name="Entry Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right="open"),),
        actions=(
            RuleAction(
                kind=ActionKind.ENTER,
                direction=1,
                order_type=OrderType.BUY,
                volume=1.0,
                sl_pips=25.0,
                tp_pips=50.0,
                comment="GoldenEntry",
            ),
        ),
    )
    exit_rule = RuleDefinition(
        rule_id="rule-exit-01",
        name="Exit Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator="<", right="open"),),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    return StrategyDocument(
        strategy_id="TrendFollower_01",
        rules=(entry_rule, exit_rule),
        params=params,
        variables=variables,
        trading_setup=TradingSetupConfig(magic_number=123456, max_open_positions=1),
    )


def test_mql5_golden_output() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()
    res: ExportResult = transformer.transform(doc, "mql5")

    assert res.success is True
    assert res.platform == "mql5"
    assert len(res.errors) == 0

    code = res.source_code
    assert "#include <Trade\\Trade.mqh>" in code
    assert "CTrade trade;" in code
    assert "input ulong InpMagicNumber = 123456;" in code
    assert "input int fast_period = 14;" in code
    assert "input int slow_period = 50;" in code
    assert "input double stop_loss_pips = 25.0;" in code
    assert "input double take_profit_pips = 50.0;" in code
    assert "int consecutive_losses = 0;" in code
    assert "void OnTick()" in code
    assert "trade.SetExpertMagicNumber(InpMagicNumber);" in code
    assert "if(close > open)" in code
    assert "trade.Buy(" in code
    assert "1.0, _Symbol, 0," in code
    assert "trade.PositionClose(_Symbol);" in code


def test_easylanguage_golden_output() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()
    res: ExportResult = transformer.transform(doc, "easylanguage")

    assert res.success is True
    assert res.platform == "easylanguage"
    assert len(res.errors) == 0

    code = res.source_code
    assert "Inputs:" in code
    assert "fast_period(14)" in code
    assert "slow_period(50)" in code
    assert "Variables:" in code
    assert "consecutive_losses(0)" in code
    assert "If close > open Then" in code
    assert 'Buy ("Entry_Rule_LE") 1.0 Shares Next Bar at Market;' in code
    assert "SetStopLoss(25.0 * PointValue);" in code
    assert "SetProfitTarget(50.0 * PointValue);" in code
    assert 'Sell ("Exit_Rule_LX") Next Bar at Market;' in code
    assert 'BuyToCover ("Exit_Rule_SX") Next Bar at Market;' in code
    assert "End;" in code


def test_python_golden_output() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()
    res: ExportResult = transformer.transform(doc, "python")

    assert res.success is True
    assert res.platform == "python"
    assert len(res.errors) == 0

    code = res.source_code
    assert "class TrendFollower01:" in code
    assert "fast_period: int = 14" in code
    assert "slow_period: int = 50" in code
    assert "self.magic_number: int = 123456" in code
    assert (
        "def evaluate(self, bar: Any, context: Any = None) -> list[dict[str, Any]]:"
        in code
    )
    assert "if close_price > open_price:" in code
    assert '"kind": "enter"' in code
    assert '"kind": "exit"' in code

    # Verify generated Python code compiles cleanly without syntax errors
    compiled = compile(code, "<test-python-export>", "exec")
    assert isinstance(compiled, types.CodeType)

    # Execute class creation in a fresh namespace
    ns: dict[str, Any] = {}
    exec(compiled, ns)
    assert "TrendFollower01" in ns
    instance = ns["TrendFollower01"]()
    assert instance.fast_period == 14
    assert instance.magic_number == 123456


def test_ctrader_golden_output() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()
    res: ExportResult = transformer.transform(doc, "ctrader")

    assert res.success is True
    assert res.platform == "ctrader"
    assert len(res.errors) == 0

    code = res.source_code
    assert "using cAlgo.API;" in code
    assert "public class TrendFollower01 : Robot" in code
    assert '[Parameter("fast_period", DefaultValue = 14)]' in code
    assert "public int fast_period { get; set; }" in code
    assert "ExecuteMarketOrder(" in code
    assert "TradeType.Buy, SymbolName," in code
    assert "ClosePosition(position);" in code


def test_mql4_golden_output() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()
    res: ExportResult = transformer.transform(doc, "mql4")

    assert res.success is True
    assert res.platform == "mql4"
    assert len(res.errors) == 0

    code = res.source_code
    assert "#property strict" in code
    assert "extern int MagicNumber = 123456;" in code
    assert "extern int fast_period = 14;" in code
    assert "OrderSend(" in code
    assert "Symbol(), OP_BUY, 1.0, Ask, 3," in code
    assert "OrderClose(OrderTicket(), OrderLots()" in code


def test_unsupported_platform_returns_error() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()
    res = transformer.transform(doc, "ninjatrader8")

    assert res.success is False
    assert res.source_code == ""
    assert len(res.errors) == 1
    assert "Unsupported platform" in res.errors[0]


def test_unsupported_indicator_composition_block_returns_error() -> None:
    transformer = StrategyTransformer()

    # Add a rule with an unknown indicator block
    bad_rule = RuleDefinition(
        rule_id="bad-rule",
        name="Bad Indicator Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(
                left="close",
                comparator=">",
                right=0.0,
                composition_block_id="quantum_neural_unknown_block_99",
            ),
        ),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    doc_bad = StrategyDocument(
        strategy_id="BadStrategy",
        rules=(bad_rule,),
    )

    res = transformer.transform(doc_bad, "mql5")
    assert res.success is False
    assert res.source_code == ""
    assert len(res.errors) >= 1
    assert "Unsupported indicator composition block" in res.errors[0]
    assert "quantum_neural_unknown_block_99" in res.errors[0]


def test_disabled_rules_are_excluded() -> None:
    transformer = StrategyTransformer()
    doc = _build_synthetic_strategy()

    disabled_rule = RuleDefinition(
        rule_id="disabled-rule-01",
        name="DisabledSpecialRule",
        is_enabled=False,
        conditions=(ConditionDefinition(left="close", comparator=">", right=1.2345),),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    doc_with_disabled = StrategyDocument(
        strategy_id="TestDisabled",
        rules=(*doc.rules, disabled_rule),
    )

    res = transformer.transform(doc_with_disabled, "python")
    assert res.success is True
    assert "DisabledSpecialRule" not in res.source_code


def test_invalid_comparator_fails_closed() -> None:
    """Strategy export fails closed when rule specifies an unsupported comparator."""
    transformer = StrategyTransformer()
    bad_rule = RuleDefinition(
        rule_id="bad-comp-rule",
        name="Bad Comparator Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(
                left="close",
                comparator="INVALID_COMP",
                right="open",
            ),
        ),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    doc = StrategyDocument(strategy_id="BadCompStrategy", rules=(bad_rule,))
    res = transformer.transform(doc, "python")
    assert res.success is False
    assert res.source_code == ""
    assert any("comparator" in err.lower() for err in res.errors)


def test_undeclared_operand_fails_closed() -> None:
    """Strategy export fails closed when operand is not declared in parameters, variables, or market fields."""
    transformer = StrategyTransformer()
    bad_rule = RuleDefinition(
        rule_id="bad-operand-rule",
        name="Bad Operand Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(
                left="undefined_market_indicator_xyz",
                comparator=">",
                right=10.0,
            ),
        ),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    doc = StrategyDocument(strategy_id="BadOperandStrategy", rules=(bad_rule,))
    res = transformer.transform(doc, "python")
    assert res.success is False
    assert res.source_code == ""
    assert any("undefined_market_indicator_xyz" in err for err in res.errors)


def test_composition_block_without_indicator_definition_fails_closed() -> None:
    """Strategy export fails closed when an indicator composition block is specified but not emitted."""
    transformer = StrategyTransformer()
    bad_rule = RuleDefinition(
        rule_id="unrendered-block-rule",
        name="Unrendered Block Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(
                left="close",
                comparator=">",
                right=10.0,
                composition_block_id="sma.14",
            ),
        ),
        actions=(RuleAction(kind=ActionKind.EXIT),),
    )
    doc = StrategyDocument(strategy_id="UnrenderedBlockStrategy", rules=(bad_rule,))
    res = transformer.transform(doc, "python")
    assert res.success is False
    assert res.source_code == ""
    assert any("composition block" in err.lower() for err in res.errors)


def test_reserved_keyword_identifier_fails_closed() -> None:
    """Strategy export fails closed when parameter name is a Python reserved keyword."""
    transformer = StrategyTransformer()
    doc = StrategyDocument(
        strategy_id="BadIdentStrategy",
        rules=(),
        params=(ParameterDefinition(name="class", param_type="int", value=1),),
    )
    res = transformer.transform(doc, "python")
    assert res.success is False
    assert res.source_code == ""
    assert any("reserved" in err.lower() for err in res.errors)


def test_unsupported_action_kind_fails_closed() -> None:
    """Strategy export fails closed when rule specifies an unsupported action kind."""
    transformer = StrategyTransformer()
    bad_rule = RuleDefinition(
        rule_id="bad-action-rule",
        name="Bad Action Rule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(ConditionDefinition(left="close", comparator=">", right="open"),),
        actions=(RuleAction(kind="custom_unsupported_action"),),  # type: ignore[arg-type]
    )
    doc = StrategyDocument(strategy_id="BadActionStrategy", rules=(bad_rule,))
    res = transformer.transform(doc, "python")
    assert res.success is False
    assert res.source_code == ""
    assert any("unsupported action kind" in err.lower() for err in res.errors)


class _SimpleBar:
    """Lightweight market bar mock for strategy evaluate verification."""

    def __init__(
        self,
        open_val: float,
        high_val: float,
        low_val: float,
        close_val: float,
        volume: float = 100.0,
    ) -> None:
        self.open = open_val
        self.high = high_val
        self.low = low_val
        self.close = close_val
        self.volume = volume


def test_python_export_with_parameter_operand_executes_and_overrides() -> None:
    """Exported Python strategy resolves parameter references to instance attributes and evaluates correctly."""
    transformer = StrategyTransformer()
    rule = RuleDefinition(
        rule_id="param-threshold-rule",
        name="ParamThresholdRule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(left="close", comparator=">", right="Threshold"),
        ),
        actions=(
            RuleAction(
                kind=ActionKind.ENTER,
                direction=1,
                order_type=OrderType.BUY,
                volume=1.0,
            ),
        ),
    )
    doc = StrategyDocument(
        strategy_id="ParamStrategy",
        rules=(rule,),
        params=(
            ParameterDefinition(name="Threshold", param_type="float", value=1.1010),
        ),
    )

    res = transformer.transform(doc, "python")
    assert res.success is True
    assert "close_price > self.Threshold" in res.source_code

    compiled = compile(res.source_code, "<test-param-eval>", "exec")
    ns: dict[str, Any] = {}
    exec(compiled, ns)
    strategy_cls = ns["ParamStrategy"]

    # Instance with default parameter Threshold = 1.1010
    instance = strategy_cls(Threshold=1.1010)

    # Bar with close = 1.1000 -> condition false, no actions
    bar_low = _SimpleBar(
        open_val=1.1000, high_val=1.1005, low_val=1.0995, close_val=1.1000
    )
    actions = instance.evaluate(bar_low)
    assert len(actions) == 0

    # Bar with close = 1.1020 -> condition true, enter action triggered
    bar_high = _SimpleBar(
        open_val=1.1000, high_val=1.1025, low_val=1.0995, close_val=1.1020
    )
    actions = instance.evaluate(bar_high)
    assert len(actions) == 1
    assert actions[0]["kind"] == "enter"

    # Instance with overridden parameter Threshold = 1.1030
    instance_overridden = strategy_cls(Threshold=1.1030)
    # The same bar (close = 1.1020) should no longer trigger
    actions_overridden = instance_overridden.evaluate(bar_high)
    assert len(actions_overridden) == 0


def test_python_export_with_state_variable_condition_executes() -> None:
    """Exported Python strategy resolves state variable references to instance attributes and evaluates correctly."""
    transformer = StrategyTransformer()
    rule = RuleDefinition(
        rule_id="state-var-rule",
        name="StateVarRule",
        trigger=RuleTriggerKind.ON_BAR_CLOSE,
        conditions=(
            ConditionDefinition(left="consecutive_losses", comparator="<", right=3),
        ),
        actions=(
            RuleAction(
                kind=ActionKind.ENTER,
                direction=1,
                order_type=OrderType.BUY,
                volume=1.0,
            ),
        ),
    )
    doc = StrategyDocument(
        strategy_id="StateVarStrategy",
        rules=(rule,),
        variables=(
            VariableDefinition(
                name="consecutive_losses", var_type="int", default_value=0
            ),
        ),
    )

    res = transformer.transform(doc, "python")
    assert res.success is True
    assert "self.consecutive_losses < 3" in res.source_code

    compiled = compile(res.source_code, "<test-var-eval>", "exec")
    ns: dict[str, Any] = {}
    exec(compiled, ns)
    strategy_cls = ns["StateVarStrategy"]

    instance = strategy_cls()
    bar = _SimpleBar(open_val=1.1000, high_val=1.1010, low_val=1.0990, close_val=1.1005)

    # Initial state consecutive_losses = 0 < 3 -> action triggered
    actions = instance.evaluate(bar)
    assert len(actions) == 1

    # Mutate instance state consecutive_losses = 3 -> condition false, no action
    instance.consecutive_losses = 3
    actions = instance.evaluate(bar)
    assert len(actions) == 0
