"""Unit tests for HSL 1.0 AST models, canonical serializer, and legacy document upgrade.

Description:
    Verifies the HaruQuant Strategy Language (HSL 1.0) Pydantic AST models
    across all five semantic families (VALUE, EXPRESSION, CONDITION, ACTION,
    RULE), typed domain sub-DSLs, prohibited raw code rejection, deterministic
    rule-ordered canonical JSON hashing, and lossless upgrading from legacy
    StrategyDocument and UI Draft payloads.

Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Gate G2 verification suite for Phase 5.2
    (WO-WZ-HSL-LANGUAGE).

Key Capabilities:
    - FR-test-hsl-ast-families: Exercises recursive VALUE, EXPRESSION,
      CONDITION, ACTION, and RULE AST nodes and typed sub-DSLs.
    - FR-test-hsl-security-and-hashing: Verifies WIZARD_RAW_CODE_PROHIBITED,
      WIZARD_SCHEMA_INVALID, and priority-invariant SHA-256 hashing.
    - FR-test-hsl-legacy-upgrade: Verifies lossless upgrade from Core
      StrategyDocument and UI AlgoWizard Draft structures.

Python API Usage:
    pytest tests/workspace/algo_wizard/test_hsl_documents.py

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_hsl_documents.py --no-cov -q
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from app.core.lib.errors import DomainError
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
from app.workspace.algo_wizard import (
    AlertActionNode,
    BreakevenSpec,
    ComparisonConditionNode,
    EvaluationContext,
    FunctionExpressionNode,
    HSLStrategyDocument,
    IndicatorExpressionNode,
    LogicalConditionNode,
    MarketPriceNode,
    MathExpressionNode,
    MoneyManagementSpec,
    OrderCancelActionNode,
    OrderMarketActionNode,
    OrderModifyActionNode,
    OrderPendingActionNode,
    ParameterRefNode,
    PartialExitSpec,
    PositionAttrNode,
    PositionCloseActionNode,
    StateConditionNode,
    StopLossSpec,
    TakeProfitSpec,
    TradeManagementSpec,
    TrailingStopSpec,
    ValueLiteralNode,
    VariableRefNode,
    VariableSetActionNode,
    canonical_hsl_bytes,
    compute_document_hash,
    parse_hsl_document,
    upgrade_legacy_wizard_document,
)
from pydantic import ValidationError


def _sample_canonical_dict() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "strategy": {
            "id": "ma-crossover-001",
            "name": "EMA Crossover",
            "description": "Buy when fast EMA crosses above slow EMA.",
            "enabled": True,
            "metadata": {"author": "haruquant", "tags": ["trend", "crossover"]},
            "universe": {"mode": "explicit", "symbols": ["EURUSD", "GBPUSD"]},
            "timeframe": {"primary": "H1", "additional": ["D1"]},
            "parameters": {
                "fast_period": {
                    "type": "int",
                    "default": 20,
                    "min": 2,
                    "max": 200,
                    "step": 1,
                    "optimize": True,
                },
                "slow_period": {
                    "type": "int",
                    "default": 50,
                    "min": 5,
                    "max": 500,
                    "optimize": True,
                },
            },
            "variables": {
                "consecutive_losses": {
                    "type": "int",
                    "initial": 0,
                    "scope": "strategy",
                }
            },
            "money_management": {
                "type": "risk_percent",
                "risk_pct": {"type": "value", "value": 1.5, "value_type": "float"},
                "max_lots": 10.0,
            },
            "risk_management": {
                "max_open_positions": 2,
                "max_daily_loss_pct": 3.0,
                "max_drawdown_pct": 10.0,
                "allow_opposite_signals": False,
                "default_stop_loss": {
                    "type": "atr",
                    "period": 14,
                    "multiplier": 2.0,
                },
                "default_take_profit": {
                    "type": "risk_multiple",
                    "multiple": 2.5,
                },
            },
            "trade_management": {
                "breakeven": {"enabled": True, "trigger_pips": 20.0, "lock_pips": 2.0},
                "trailing_stop": {
                    "enabled": True,
                    "type": "fixed_pips",
                    "distance": 25.0,
                    "activation_pips": 30.0,
                },
                "time_stop_bars": 48,
                "partial_exits": [{"trigger_pips": 35.0, "close_pct": 50.0}],
            },
            "trading_options": {
                "exit_at_end_of_day": True,
                "end_of_day_time": "21:55",
                "exit_on_friday": True,
                "friday_exit_time": "20:30",
                "limit_time_range": True,
                "time_range_start": "08:00",
                "time_range_end": "18:00",
                "max_trades_per_day": 5,
                "min_distance_from_market_pips": 1.5,
            },
            "rules": [
                {
                    "type": "rule",
                    "id": "long-entry",
                    "name": "Enter Long on Crossover",
                    "priority": 300,
                    "event": {"type": "on_bar_close", "timeframe": "H1"},
                    "when": {
                        "type": "logical",
                        "operator": "and",
                        "conditions": [
                            {
                                "type": "comparison",
                                "operator": "crosses_above",
                                "left": {
                                    "type": "indicator",
                                    "name": "indicator.ema",
                                    "inputs": {
                                        "source": {"type": "price", "field": "close"}
                                    },
                                    "params": {
                                        "period": {
                                            "type": "parameter",
                                            "name": "fast_period",
                                        }
                                    },
                                    "context": {
                                        "symbol": "EURUSD",
                                        "timeframe": "H1",
                                        "shift": 1,
                                    },
                                },
                                "right": {
                                    "type": "indicator",
                                    "name": "indicator.ema",
                                    "params": {
                                        "period": {
                                            "type": "parameter",
                                            "name": "slow_period",
                                        }
                                    },
                                },
                            },
                            {"type": "state", "state": "position.is_flat"},
                        ],
                    },
                    "then": [
                        {
                            "type": "action",
                            "action": "enter_market",
                            "side": "long",
                            "comment": "EMA cross long",
                            "magic_number": 1001,
                        }
                    ],
                },
                {
                    "type": "rule",
                    "id": "long-exit",
                    "name": "Exit Long on RSI Overbought",
                    "priority": 200,
                    "event": "on_bar_close",
                    "when": {
                        "type": "not",
                        "condition": {
                            "type": "temporal",
                            "operator": "remains_true_for",
                            "bars": 3,
                            "condition": {
                                "type": "comparison",
                                "operator": "less_than",
                                "left": {
                                    "type": "indicator",
                                    "name": "indicator.rsi",
                                    "params": {"period": 14},
                                },
                                "right": 70,
                            },
                        },
                    },
                    "then": [{"type": "exit_position", "target_side": "long"}],
                    "else_then": [
                        {
                            "type": "action",
                            "action": "set_variable",
                            "name": "consecutive_losses",
                            "value": {"type": "variable", "name": "consecutive_losses"},
                        }
                    ],
                },
            ],
        },
    }


def test_parse_hsl_document_from_dict_str_and_bytes() -> None:
    payload = _sample_canonical_dict()
    doc_from_dict = parse_hsl_document(payload)
    assert isinstance(doc_from_dict, HSLStrategyDocument)
    assert doc_from_dict.schema_version == "1.0.0"
    assert doc_from_dict.strategy.id == "ma-crossover-001"
    assert len(doc_from_dict.strategy.rules) == 2

    json_text = json.dumps(payload)
    doc_from_str = parse_hsl_document(json_text)
    doc_from_bytes = parse_hsl_document(json_text.encode("utf-8"))

    assert compute_document_hash(doc_from_dict) == compute_document_hash(doc_from_str)
    assert compute_document_hash(doc_from_dict) == compute_document_hash(doc_from_bytes)


def test_canonical_hash_sorts_rules_by_priority_and_id() -> None:
    payload_a = _sample_canonical_dict()
    payload_b = _sample_canonical_dict()
    payload_b["strategy"]["rules"] = list(reversed(payload_a["strategy"]["rules"]))

    doc_a = parse_hsl_document(payload_a)
    doc_b = parse_hsl_document(payload_b)

    bytes_a = canonical_hsl_bytes(doc_a)
    bytes_b = canonical_hsl_bytes(doc_b)
    assert bytes_a == bytes_b
    assert compute_document_hash(doc_a) == compute_document_hash(doc_b)

    decoded = json.loads(bytes_a.decode("utf-8"))
    assert [r["id"] for r in decoded["strategy"]["rules"]] == [
        "long-exit",
        "long-entry",
    ]


def test_expression_and_value_nodes_composition() -> None:
    stop_expr = MathExpressionNode(
        operator="subtract",
        left=MarketPriceNode(
            field="close",
            context=EvaluationContext(symbol="EURUSD", timeframe="H1", shift=1),
        ),
        right=MathExpressionNode(
            operator="multiply",
            left=IndicatorExpressionNode(
                name="indicator.atr",
                params={"period": ParameterRefNode(name="atr_period")},
            ),
            right=ValueLiteralNode(value=2.0),
        ),
    )
    abs_expr = MathExpressionNode(
        operator="abs",
        left=PositionAttrNode(field="unrealized_pnl"),
    )
    fn_expr = FunctionExpressionNode(
        name="math.max",
        args=(stop_expr, abs_expr, VariableRefNode(name="highest_equity")),
    )
    assert fn_expr.type == "function"
    assert len(fn_expr.args) == 3
    assert ValueLiteralNode(value=True).value_type == "bool"
    assert ValueLiteralNode(value=42).value_type == "int"
    assert ValueLiteralNode(value=3.14).value_type == "float"
    assert ValueLiteralNode(value="EURUSD").value_type == "str"


def test_math_expression_arity_validation() -> None:
    with pytest.raises(ValidationError, match="requires a 'right' operand"):
        MathExpressionNode(operator="add", left=ValueLiteralNode(value=1))

    with pytest.raises(ValidationError, match="must not specify a 'right' operand"):
        MathExpressionNode(
            operator="abs",
            left=ValueLiteralNode(value=-5),
            right=ValueLiteralNode(value=1),
        )


def test_typed_sub_dsl_variants_and_validation() -> None:
    sl_fixed = StopLossSpec.model_validate({"type": "fixed_pips", "value": 25})
    assert isinstance(sl_fixed.value, ValueLiteralNode)

    sl_ind = StopLossSpec(
        type="indicator",
        indicator=IndicatorExpressionNode(name="indicator.sma", params={"period": 50}),
    )
    assert sl_ind.indicator is not None

    sl_expr = StopLossSpec(type="expression", expression=MarketPriceNode(field="low"))
    assert sl_expr.expression is not None

    tp_atr = TakeProfitSpec(
        type="atr",
        period=ValueLiteralNode(value=14),
        multiplier=ValueLiteralNode(value=3.0),
    )
    assert tp_atr.period is not None and tp_atr.multiplier is not None

    tp_expr = TakeProfitSpec(
        type="expression", expression=MarketPriceNode(field="high")
    )
    assert tp_expr.expression is not None

    mm_default = MoneyManagementSpec()
    assert mm_default.type == "fixed_size"
    assert isinstance(mm_default.size, ValueLiteralNode)

    mm_cash = MoneyManagementSpec(
        type="fixed_cash", amount=ValueLiteralNode(value=10000.0)
    )
    assert isinstance(mm_cash.amount, ValueLiteralNode)

    mm_eq = MoneyManagementSpec(
        type="percent_equity", percent=ValueLiteralNode(value=5.0)
    )
    assert isinstance(mm_eq.percent, ValueLiteralNode)

    tm = TradeManagementSpec(
        breakeven=BreakevenSpec(
            trigger_pips=ValueLiteralNode(value=15),
            lock_pips=ValueLiteralNode(value=1),
        ),
        trailing_stop=TrailingStopSpec(
            distance=ValueLiteralNode(value=20),
            activation_pips=ValueLiteralNode(value=25),
        ),
        partial_exits=(
            PartialExitSpec(
                trigger_pips=ValueLiteralNode(value=30),
                close_pct=50.0,
            ),
        ),
    )
    assert len(tm.partial_exits) == 1

    with pytest.raises(ValidationError, match="requires 'value'"):
        StopLossSpec(type="fixed_pips")
    with pytest.raises(ValidationError, match="requires both 'period'"):
        StopLossSpec(type="atr", period=ValueLiteralNode(value=14))
    with pytest.raises(ValidationError, match="requires 'indicator'"):
        StopLossSpec(type="indicator")
    with pytest.raises(ValidationError, match="requires 'expression'"):
        StopLossSpec(type="expression")

    with pytest.raises(ValidationError, match="requires 'value'"):
        TakeProfitSpec(type="fixed_points")
    with pytest.raises(ValidationError, match="requires both 'period'"):
        TakeProfitSpec(type="atr", multiplier=ValueLiteralNode(value=2.0))
    with pytest.raises(ValidationError, match="requires 'multiple'"):
        TakeProfitSpec(type="risk_multiple")
    with pytest.raises(ValidationError, match="requires 'expression'"):
        TakeProfitSpec(type="expression")

    with pytest.raises(ValidationError, match="requires 'amount'"):
        MoneyManagementSpec(type="fixed_cash")
    with pytest.raises(ValidationError, match="requires 'percent'"):
        MoneyManagementSpec(type="percent_equity")
    with pytest.raises(ValidationError, match="requires 'risk_pct'"):
        MoneyManagementSpec(type="risk_percent")


def test_action_node_variants_and_validation() -> None:
    pending = OrderPendingActionNode.model_validate(
        {
            "action": "enter_limit",
            "side": "long",
            "entry_price": 1.0850,
            "expiration_bars": 12,
        }
    )
    assert isinstance(pending.entry_price, ValueLiteralNode)

    mod_sl = OrderModifyActionNode(
        action="modify_stop_loss",
        stop_loss=StopLossSpec(type="fixed_pips", value=ValueLiteralNode(value=15)),
    )
    assert mod_sl.stop_loss is not None

    mod_tp = OrderModifyActionNode(
        action="modify_take_profit",
        take_profit=TakeProfitSpec(type="fixed_pips", value=ValueLiteralNode(value=30)),
    )
    assert mod_tp.take_profit is not None

    cancel = OrderCancelActionNode(target_side="short")
    assert cancel.action == "cancel_orders"

    var_set = VariableSetActionNode.model_validate({"name": "streak", "value": 0})
    assert isinstance(var_set.value, ValueLiteralNode)

    alert = AlertActionNode(level="warning", message="Drawdown threshold near")
    assert alert.action == "emit_alert"

    with pytest.raises(ValidationError, match="requires 'stop_loss'"):
        OrderModifyActionNode(action="modify_stop_loss")
    with pytest.raises(ValidationError, match="requires 'take_profit'"):
        OrderModifyActionNode(action="modify_take_profit")


def test_prohibited_raw_code_nodes_rejected() -> None:
    bad_type = _sample_canonical_dict()
    bad_type["strategy"]["rules"][0]["when"] = {
        "type": "python",
        "code": "df['close'] > df['open']",
    }
    with pytest.raises(DomainError) as exc_info:
        parse_hsl_document(bad_type)
    assert exc_info.value.code == "WIZARD_RAW_CODE_PROHIBITED"

    bad_key = _sample_canonical_dict()
    bad_key["strategy"]["metadata"]["python_code"] = "import os"
    with pytest.raises(DomainError) as exc_info_key:
        parse_hsl_document(bad_key)
    assert exc_info_key.value.code == "WIZARD_RAW_CODE_PROHIBITED"


def test_invalid_schema_errors_rejected() -> None:
    with pytest.raises(DomainError) as bad_json:
        parse_hsl_document("{not valid json")
    assert bad_json.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as non_obj:
        parse_hsl_document("[1, 2, 3]")
    assert non_obj.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as bad_type:
        parse_hsl_document(12345)  # type: ignore[arg-type]
    assert bad_type.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as bad_ver:
        parse_hsl_document({"schema_version": "0.9.0", "strategy": {}})
    assert bad_ver.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as missing_fields:
        parse_hsl_document({"schema_version": "1.0.0", "strategy": {"id": ""}})
    assert missing_fields.value.code == "WIZARD_SCHEMA_INVALID"


def test_upgrade_legacy_core_strategy_document() -> None:
    core_dataclass = StrategyDocument(
        strategy_id="core-dataclass-01",
        params=(ParameterDefinition(name="fast", param_type="int", value=12),),
        variables=(VariableDefinition(name="streak", var_type="int", default_value=0),),
        trading_setup=TradingSetupConfig(max_open_positions=4, magic_number=2026),
        rules=(
            RuleDefinition(
                rule_id="r-enter",
                name="Enter Long",
                trigger=RuleTriggerKind.ON_BAR_CLOSE,
                conditions=(
                    ConditionDefinition(left="close", comparator=">", right=1.05),
                    ConditionDefinition(left="rsi", comparator="<", right=70.0),
                ),
                actions=(
                    RuleAction(
                        kind=ActionKind.ENTER,
                        direction=1,
                        sl_pips=20.0,
                        tp_pips=40.0,
                        comment="buy",
                    ),
                ),
            ),
            RuleDefinition(
                rule_id="r-exit",
                trigger=RuleTriggerKind.ON_BAR_OPEN,
                conditions=(
                    ConditionDefinition(left="close", comparator="<", right=1.02),
                ),
                actions=(
                    RuleAction(kind=ActionKind.EXIT, direction=-1, comment="exit"),
                    RuleAction(kind=ActionKind.CANCEL, direction=1),
                ),
            ),
            RuleDefinition(
                rule_id="r-empty",
                conditions=(),
                actions=(),
            ),
        ),
    )
    upgraded_dc = upgrade_legacy_wizard_document(core_dataclass)
    assert upgraded_dc.strategy.id == "core-dataclass-01"
    assert "fast" in upgraded_dc.strategy.parameters
    assert "streak" in upgraded_dc.strategy.variables
    assert upgraded_dc.strategy.risk_management.max_open_positions == 4
    assert len(upgraded_dc.strategy.rules) == 3

    legacy_dict: dict[str, Any] = {
        "strategy_id": "legacy-ema-1",
        "name": "Legacy EMA Strategy",
        "version": 3,
        "universe": ["EURUSD", "USDJPY"],
        "timeframe": "15m",
        "indicators": {
            "fast_ema": {"type": "ema", "period": 12, "source": "close"},
            "slow_ema": {"type": "ema", "period": 26},
        },
        "rules": [
            {
                "id": "entry-long",
                "direction": "LONG",
                "entry": True,
                "conditions": [
                    {"left": "fast_ema", "op": ">", "right": "slow_ema"},
                    {"left": "close", "op": ">=", "right": "1.0500"},
                ],
            },
            {
                "id": "exit-short",
                "direction": "SHORT",
                "entry": False,
                "conditions": [
                    {"left": "rsi", "op": "<", "right": 30},
                ],
            },
            {
                "id": "unconditional-exit",
                "direction": "LONG",
                "entry": False,
                "conditions": [],
            },
        ],
        "risk": {
            "sizing_mode": "percent_equity",
            "base_size": 2.5,
            "stop_loss_pct": 1.2,
            "take_profit_pct": 2.4,
            "max_open_positions": 3,
        },
        "metadata": {"source": "unit-test"},
    }

    upgraded = upgrade_legacy_wizard_document(legacy_dict)
    assert upgraded.schema_version == "1.0.0"
    assert upgraded.strategy.id == "legacy-ema-1"
    assert upgraded.strategy.universe.symbols == ("EURUSD", "USDJPY")
    assert upgraded.strategy.timeframe.primary == "15m"
    assert upgraded.strategy.money_management.type == "percent_equity"
    assert upgraded.strategy.risk_management.max_open_positions == 3
    assert upgraded.strategy.risk_management.default_stop_loss.type == "percent"
    assert upgraded.strategy.risk_management.default_take_profit.type == "percent"
    assert upgraded.strategy.metadata["legacy_version"] == 3
    assert len(upgraded.strategy.rules) == 3

    rule_0 = upgraded.strategy.rules[0]
    assert isinstance(rule_0.when, LogicalConditionNode)
    assert isinstance(rule_0.then[0], OrderMarketActionNode)
    assert isinstance(upgraded.strategy.rules[2].when, StateConditionNode)

    vol_dict = dict(legacy_dict)
    vol_dict["risk"] = dict(legacy_dict["risk"], sizing_mode="volatility_target")
    upgraded_vol = upgrade_legacy_wizard_document(vol_dict)
    assert upgraded_vol.strategy.money_management.type == "risk_percent"

    fixed_dict = dict(legacy_dict)
    fixed_dict["risk"] = dict(legacy_dict["risk"], sizing_mode="fixed")
    fixed_dict["rules"] = [
        {
            "id": "entry-long",
            "direction": "LONG",
            "entry": True,
            "conditions": [{"left": "fast_ema", "op": "==", "right": "10"}],
        }
    ]
    upgraded_fixed = upgrade_legacy_wizard_document(fixed_dict)
    assert upgraded_fixed.strategy.money_management.type == "fixed_size"


def test_upgrade_legacy_ui_draft_and_passthrough() -> None:
    ui_draft: dict[str, Any] = {
        "strategyId": "draft-rsi-01",
        "name": "RSI Reversal Draft",
        "description": "Draft created in AlgoWizard UI",
        "direction": "long",
        "quantity": 2.0,
        "stopLossPct": 1.5,
        "takeProfitPct": 3.0,
        "signals": [
            {
                "id": "s1",
                "label": "Oversold Entry",
                "indicator": "RSI",
                "period": 14,
                "comparator": "crosses_above",
                "threshold": 30,
                "action": "enter_long",
            },
            {
                "id": "s2",
                "label": "Overbought Short",
                "indicator": "indicator.rsi",
                "period": 14,
                "comparator": "crosses_below",
                "threshold": 70,
                "action": "enter_short",
            },
            {
                "id": "s3",
                "label": "Long Exit",
                "indicator": "EMA",
                "period": 20,
                "comparator": "<",
                "threshold": 100,
                "action": "exit_long",
            },
            {
                "id": "s4",
                "label": "Short Exit",
                "indicator": "EMA",
                "period": 20,
                "comparator": ">",
                "threshold": 100,
                "action": "exit_short",
            },
        ],
        "blocks": [{"id": "b1", "category": "indicator", "blockId": "rsi"}],
    }

    upgraded = upgrade_legacy_wizard_document(ui_draft)
    assert upgraded.strategy.id == "draft-rsi-01"
    assert len(upgraded.strategy.rules) == 4
    assert isinstance(upgraded.strategy.rules[0].when, ComparisonConditionNode)
    assert isinstance(upgraded.strategy.rules[0].then[0], OrderMarketActionNode)
    assert isinstance(upgraded.strategy.rules[2].then[0], PositionCloseActionNode)
    assert upgraded.strategy.metadata["legacy_blocks_count"] == 1

    passthrough = upgrade_legacy_wizard_document(_sample_canonical_dict())
    assert passthrough.strategy.id == "ma-crossover-001"


def test_upgrade_legacy_error_branches() -> None:
    with pytest.raises(DomainError) as bad_input:
        upgrade_legacy_wizard_document("not-a-dict")  # type: ignore[arg-type]
    assert bad_input.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as missing_core_id:
        upgrade_legacy_wizard_document({"strategy_id": "", "name": ""})
    assert missing_core_id.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as missing_ui_id:
        upgrade_legacy_wizard_document({"strategyId": "", "name": "", "signals": []})
    assert missing_ui_id.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as bad_op:
        upgrade_legacy_wizard_document(
            {
                "strategy_id": "s1",
                "name": "S1",
                "rules": [
                    {
                        "id": "r1",
                        "conditions": [{"left": "close", "op": "???", "right": 1}],
                    }
                ],
            }
        )
    assert bad_op.value.code == "WIZARD_SCHEMA_INVALID"

    with pytest.raises(DomainError) as bad_operand:
        upgrade_legacy_wizard_document(
            {
                "strategy_id": "s1",
                "name": "S1",
                "rules": [
                    {
                        "id": "r1",
                        "conditions": [{"left": ["invalid"], "op": ">", "right": 1}],
                    }
                ],
            }
        )
    assert bad_operand.value.code == "WIZARD_SCHEMA_INVALID"
