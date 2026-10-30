"""Unit and golden output tests for strategy rule transformation and export engine."""

from __future__ import annotations

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
    assert compiled is not None

    # Execute class creation in a fresh namespace
    ns: dict = {}
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
