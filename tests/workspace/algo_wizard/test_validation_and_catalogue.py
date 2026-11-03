"""Unit tests for WizardBlockLibrary, 3-pass StrategyValidator, and WizardCatalogueService.

Description:
    Verifies the single BlockRegistry projection (WizardBlockLibrary), the
    three-pass HSL 1.0 static validator (StrategyValidator), and the
    ServletConstants catalogue service (WizardCatalogueService) for Gate G3
    (Phase 5.3, WO-WZ-HSL-VALIDATION).

Purpose:
    FEAT-WIZARD-VALIDATION: Gate G3 verification suite for block resolution,
    3-pass AST validation, and catalogue responses.

Key Capabilities:
    - FR-test-wizard-block-library: Tests BlockRegistry projection, semantic ID
      aliasing, parameter bound extraction, and custom block registration.
    - FR-test-strategy-validator: Tests Pass 1 (structural), Pass 2 (registry
      and reference integrity), and Pass 3 (static types and lookahead shift).
    - FR-test-wizard-catalogue: Tests get_all, list_commission_methods, and
      get_block_descriptor endpoints.

Python API Usage:
    pytest tests/workspace/algo_wizard/test_validation_and_catalogue.py

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_validation_and_catalogue.py --no-cov -q
"""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.registry import BlockRegistry
from app.core.trading.strategy.hsl.value_models import BreakevenSpec
from app.workspace.algo_wizard import (
    ComparisonConditionNode,
    EvaluationContext,
    FunctionExpressionNode,
    GetBlockDescriptorRequest,
    GetCatalogueRequest,
    HSLStrategyDocument,
    HSLStrategyPayload,
    IndicatorExpressionNode,
    LifecycleEventSpec,
    ListCommissionMethodsRequest,
    LogicalConditionNode,
    MarketPriceNode,
    MathExpressionNode,
    MoneyManagementSpec,
    NotConditionNode,
    OrderMarketActionNode,
    OrderModifyActionNode,
    OrderPendingActionNode,
    ParameterRefNode,
    ParameterSpec,
    PartialExitSpec,
    PositionAttrNode,
    RiskManagementSpec,
    RuleNode,
    StateConditionNode,
    StopLossSpec,
    StrategyValidator,
    TakeProfitSpec,
    TemporalConditionNode,
    TimeframeSpec,
    TradeManagementSpec,
    TrailingStopSpec,
    UniverseSpec,
    ValueLiteralNode,
    VariableRefNode,
    VariableSetActionNode,
    VariableSpec,
    WizardBlockLibrary,
    WizardCatalogueService,
)


def _build_valid_document() -> HSLStrategyDocument:
    return HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="valid-rsi-ema-01",
            name="Valid RSI EMA Strategy",
            universe=UniverseSpec(mode="explicit", symbols=("EURUSD", "GBPUSD")),
            timeframe=TimeframeSpec(primary="H1", additional=("D1",)),
            parameters={
                "rsi_period": ParameterSpec(
                    type="int", default=14, min=2, max=100, optimize=True
                ),
                "ema_period": ParameterSpec(
                    type="int", default=50, min=5, max=200, optimize=True
                ),
            },
            variables={
                "trade_count": VariableSpec(type="int", initial=0),
                "last_side": VariableSpec(type="str", initial="none"),
            },
            money_management=MoneyManagementSpec(
                type="risk_percent",
                risk_pct=ValueLiteralNode(value=1.0),
            ),
            risk_management=RiskManagementSpec(
                max_open_positions=2,
                default_stop_loss=StopLossSpec(
                    type="atr",
                    period=ValueLiteralNode(value=14),
                    multiplier=ValueLiteralNode(value=2.0),
                ),
                default_take_profit=TakeProfitSpec(
                    type="risk_multiple",
                    multiple=ValueLiteralNode(value=2.0),
                ),
            ),
            trade_management=TradeManagementSpec(
                breakeven=BreakevenSpec(
                    trigger_pips=ValueLiteralNode(value=20.0),
                    lock_pips=ValueLiteralNode(value=2.0),
                ),
                trailing_stop=TrailingStopSpec(
                    distance=ValueLiteralNode(value=25.0),
                    activation_pips=ValueLiteralNode(value=30.0),
                ),
                partial_exits=(
                    PartialExitSpec(
                        trigger_pips=ValueLiteralNode(value=40.0),
                        close_pct=50.0,
                    ),
                ),
            ),
            rules=(
                RuleNode(
                    id="long-entry",
                    name="Long Entry",
                    priority=100,
                    event=LifecycleEventSpec(
                        type="on_bar_close",
                        symbol="EURUSD",
                        timeframe="H1",
                    ),
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            ComparisonConditionNode(
                                operator="crosses_above",
                                left=IndicatorExpressionNode(
                                    name="indicator.rsi",
                                    inputs={"source": MarketPriceNode(field="close")},
                                    params={
                                        "period": ParameterRefNode(name="rsi_period")
                                    },
                                    context=EvaluationContext(
                                        symbol="EURUSD", timeframe="H1", shift=0
                                    ),
                                ),
                                right=ValueLiteralNode(value=30),
                            ),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=MarketPriceNode(field="close"),
                                right=IndicatorExpressionNode(
                                    name="indicator.ema",
                                    params={
                                        "period": ParameterRefNode(name="ema_period")
                                    },
                                    context=EvaluationContext(
                                        symbol="EURUSD", timeframe="D1", shift=1
                                    ),
                                ),
                            ),
                            NotConditionNode(
                                condition=TemporalConditionNode(
                                    operator="occurred_within",
                                    bars=3,
                                    condition=StateConditionNode(
                                        state="position.is_short"
                                    ),
                                )
                            ),
                            ComparisonConditionNode(
                                operator="equal",
                                left=PositionAttrNode(field="side"),
                                right=VariableRefNode(name="last_side"),
                            ),
                            ComparisonConditionNode(
                                operator="greater_or_equal",
                                left=PositionAttrNode(field="bars_held"),
                                right=VariableRefNode(name="trade_count"),
                            ),
                            ComparisonConditionNode(
                                operator="greater_or_equal",
                                left=MathExpressionNode(
                                    operator="add",
                                    left=PositionAttrNode(field="unrealized_pnl"),
                                    right=ValueLiteralNode(value=0.0),
                                ),
                                right=FunctionExpressionNode(
                                    name="math.min",
                                    args=(
                                        ValueLiteralNode(value=0.0),
                                        ValueLiteralNode(value=10.0),
                                    ),
                                ),
                            ),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            size=MoneyManagementSpec(
                                type="fixed_size",
                                size=ValueLiteralNode(value=1.0),
                            ),
                            stop_loss=StopLossSpec(
                                type="indicator",
                                indicator=IndicatorExpressionNode(
                                    name="indicator.sma",
                                    params={"period": ValueLiteralNode(value=20)},
                                ),
                            ),
                            take_profit=TakeProfitSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=50.0),
                            ),
                        ),
                        VariableSetActionNode(
                            name="trade_count",
                            value=ValueLiteralNode(value=1, value_type="int"),
                        ),
                    ),
                    else_then=(
                        OrderPendingActionNode(
                            action="enter_limit",
                            side="long",
                            entry_price=MarketPriceNode(field="low"),
                            size=ValueLiteralNode(value=0.5),
                        ),
                        OrderModifyActionNode(
                            action="modify_stop_loss",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=15.0),
                            ),
                        ),
                    ),
                ),
            ),
        )
    )


def test_wizard_block_library_semantic_resolution_and_custom_registry() -> None:
    lib = WizardBlockLibrary()
    assert isinstance(lib.registry, BlockRegistry)
    assert lib.revision.startswith("rev-")
    assert lib.resolve("   ") is None

    rsi_entry = lib.require("indicator.rsi")
    assert rsi_entry.semantic_id == "indicator.rsi"
    assert rsi_entry.family == "EXPRESSION"
    assert rsi_entry.return_type == "float"
    assert lib.require("rsi").semantic_id == "indicator.rsi"
    assert lib.require("indicator.momentum.rsi").semantic_id == "indicator.rsi"

    assert lib.require("indicator.ema").semantic_id == "indicator.ema"
    assert lib.require("indicator.highest").semantic_id == "indicator.highest"
    assert lib.require("indicator.lowest").semantic_id == "indicator.lowest"
    assert lib.require("comparison.crosses_above").family == "CONDITION"
    assert lib.require("math.subtract").family == "EXPRESSION"
    assert lib.require("market.close").family == "VALUE"
    assert lib.require("position.is_flat").family == "CONDITION"
    assert lib.require("order.enter_market").family == "ACTION"
    assert lib.require("stop_loss.atr").family == "EXPRESSION"
    assert lib.require("position_size.risk_percent").family == "EXPRESSION"

    with pytest.raises(DomainError) as exc_info:
        lib.require("indicator.non_existent_xyz")
    assert exc_info.value.code == "WIZARD_UNKNOWN_BLOCK_ID"

    custom_reg = BlockRegistry()

    @block(
        BlockSpec(
            id="custom.bool_signal",
            name="Custom Bool Signal",
            category="custom_signals",
            execution_kind=ExecutionKind.EXPRESSION,
            outputs=(OutputPort("flag", PortType.BOOLEAN),),
        )
    )
    def _bool_sig(threshold: int, label: str = "ok", active: bool = True) -> bool:
        return active and threshold > 0 and bool(label)

    @block(
        BlockSpec(
            id="custom.str_fn",
            name="Custom String Function",
            category="custom_signals",
            execution_kind=ExecutionKind.EXPRESSION,
            outputs=(OutputPort("text", PortType.STRING),),
        )
    )
    def _str_fn() -> str:
        return "tag"

    @block(
        BlockSpec(
            id="custom.cond_block",
            name="Custom Condition",
            category="custom_signals",
            execution_kind=ExecutionKind.CONDITION,
        )
    )
    def _cond_fn() -> bool:
        return True

    @block(
        BlockSpec(
            id="custom.act_block",
            name="Custom Action",
            category="custom_signals",
            execution_kind=ExecutionKind.ACTION,
        )
    )
    def _act_fn() -> None:
        return None

    custom_reg.register_block(_bool_sig)
    custom_reg.register_block(_str_fn)
    custom_reg.register_block(_cond_fn)
    custom_reg.register_block(_act_fn)

    custom_lib = WizardBlockLibrary(registry=custom_reg)
    b_entry = custom_lib.require("custom.bool_signal")
    assert b_entry.return_type == "bool"
    assert any(p.name == "threshold" and p.required for p in b_entry.parameters)

    s_entry = custom_lib.require("custom.str_fn")
    assert s_entry.return_type == "str"

    c_entry = custom_lib.require("custom.cond_block")
    assert c_entry.family == "CONDITION"

    a_entry = custom_lib.require("custom.act_block")
    assert a_entry.family == "ACTION"

    custom_items = custom_lib.list_entries(category="custom_signals")
    assert len(custom_items) == 4


def test_validator_valid_document_passes_all_three_passes() -> None:
    validator = StrategyValidator()
    assert isinstance(validator.library, WizardBlockLibrary)
    doc = _build_valid_document()
    report = validator.validate(doc, raise_on_error=True)
    assert report.valid is True
    assert len(report.issues) == 0


def test_validator_pass1_structural_and_schema_errors() -> None:
    validator = StrategyValidator()

    raw_code_report = validator.validate(
        {
            "schema_version": "1.0.0",
            "strategy": {
                "id": "s1",
                "name": "S1",
                "rules": [{"type": "python", "code": "1+1"}],
            },
        }
    )
    assert not raw_code_report.valid
    assert raw_code_report.issues[0].code == "WIZARD_RAW_CODE_PROHIBITED"

    with pytest.raises(DomainError) as exc_raw:
        validator.validate(
            {"schema_version": "0.1.0", "strategy": {}},
            raise_on_error=True,
        )
    assert exc_raw.value.code == "WIZARD_SCHEMA_INVALID"

    base_doc = _build_valid_document()
    dup_rule = base_doc.strategy.rules[0]
    bad_payload = base_doc.strategy.model_copy(
        update={
            "rules": (dup_rule, dup_rule),
            "parameters": {
                "bad_bool_default": ParameterSpec(type="int", default=True),
                "inverted_bounds": ParameterSpec(
                    type="float", default=10.0, min=20.0, max=5.0
                ),
                "below_min": ParameterSpec(type="int", default=1, min=5, max=10),
                "above_max": ParameterSpec(type="int", default=25, min=5, max=10),
            },
        }
    )
    report = validator.validate(HSLStrategyDocument(strategy=bad_payload))
    assert not report.valid
    codes = {issue.code for issue in report.issues}
    assert "WIZARD_DUPLICATE_RULE_ID" in codes
    assert "WIZARD_INVALID_PARAMETER_BOUNDS" in codes


def test_validator_pass2_registry_and_reference_errors() -> None:
    validator = StrategyValidator()
    doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="pass2-errors",
            name="Pass 2 Errors",
            parameters={
                "too_small": ParameterSpec(type="int", default=0),
                "too_large": ParameterSpec(type="int", default=9999),
            },
            rules=(
                RuleNode(
                    id="r1",
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=IndicatorExpressionNode(
                                    name="indicator.unknown_ind",
                                    params={
                                        "p": ParameterRefNode(name="missing_param")
                                    },
                                ),
                                right=FunctionExpressionNode(
                                    name="unknown.func",
                                    args=(VariableRefNode(name="missing_var"),),
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=IndicatorExpressionNode(
                                    name="indicator.rsi",
                                    params={
                                        "unknown_param": 10,
                                        "period": "wrong_type_str",
                                    },
                                ),
                                right=IndicatorExpressionNode(
                                    name="indicator.rsi",
                                    params={
                                        "period": ParameterRefNode(name="too_small")
                                    },
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=IndicatorExpressionNode(
                                    name="indicator.rsi",
                                    params={
                                        "period": ParameterRefNode(name="too_large")
                                    },
                                ),
                                right=ValueLiteralNode(value=50),
                            ),
                        ),
                    ),
                    then=(
                        VariableSetActionNode(
                            name="undeclared_target_var",
                            value=ValueLiteralNode(value=1),
                        ),
                    ),
                ),
            ),
        )
    )
    report = validator.validate(doc)
    assert not report.valid
    codes = {issue.code for issue in report.issues}
    assert "WIZARD_UNKNOWN_BLOCK_ID" in codes
    assert "WIZARD_INVALID_BLOCK_PARAM" in codes
    assert "WIZARD_UNKNOWN_PARAMETER_REF" in codes
    assert "WIZARD_UNKNOWN_VARIABLE_REF" in codes


def test_validator_pass3_type_and_lookahead_safety_errors() -> None:
    validator = StrategyValidator()
    doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="pass3-errors",
            name="Pass 3 Errors",
            universe=UniverseSpec(mode="explicit", symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="M15", additional=("H1",)),
            variables={"int_var": VariableSpec(type="int", initial=0)},
            money_management=MoneyManagementSpec(
                type="fixed_size",
                size=ValueLiteralNode(value="not_a_number", value_type="str"),
            ),
            rules=(
                RuleNode(
                    id="r-lookahead",
                    event=LifecycleEventSpec(
                        type="on_bar_open",
                        symbol="USDJPY",
                        timeframe="W1",
                    ),
                    when=LogicalConditionNode(
                        operator="or",
                        conditions=(
                            ComparisonConditionNode(
                                operator="greater_than",
                                left=MarketPriceNode(
                                    field="close",
                                    context=EvaluationContext(
                                        symbol="GBPUSD",
                                        timeframe="D1",
                                        shift=-1,
                                    ),
                                ),
                                right=IndicatorExpressionNode(
                                    name="indicator.ema",
                                    inputs={
                                        "source": ValueLiteralNode(
                                            value="bad_input", value_type="str"
                                        )
                                    },
                                    params={"period": 20},
                                    context=EvaluationContext(
                                        symbol="EURUSD",
                                        timeframe="H1",
                                        shift=0,
                                    ),
                                ),
                            ),
                            ComparisonConditionNode(
                                operator="equal",
                                left=ValueLiteralNode(value=True, value_type="bool"),
                                right=ValueLiteralNode(value=10, value_type="int"),
                            ),
                            ComparisonConditionNode(
                                operator="less_than",
                                left=MathExpressionNode(
                                    operator="add",
                                    left=ValueLiteralNode(
                                        value="bad_left", value_type="str"
                                    ),
                                    right=ValueLiteralNode(
                                        value=False, value_type="bool"
                                    ),
                                ),
                                right=ValueLiteralNode(
                                    value="bad_right", value_type="str"
                                ),
                            ),
                        ),
                    ),
                    then=(
                        VariableSetActionNode(
                            name="int_var",
                            value=ValueLiteralNode(value=3.14, value_type="float"),
                        ),
                    ),
                ),
            ),
        )
    )

    with pytest.raises(DomainError) as exc_info:
        validator.validate(doc, raise_on_error=True)
    assert "issue_count" in exc_info.value.details
    assert int(exc_info.value.details["issue_count"]) >= 6  # type: ignore[arg-type]

    report = validator.validate(doc, raise_on_error=False)
    codes = {issue.code for issue in report.issues}
    assert "WIZARD_LOOKAHEAD_SHIFT_INVALID" in codes
    assert "WIZARD_UNDECLARED_CONTEXT_REF" in codes
    assert "WIZARD_TYPE_MISMATCH" in codes


def test_wizard_catalogue_service_endpoints() -> None:
    svc = WizardCatalogueService()
    assert isinstance(svc.library, WizardBlockLibrary)

    all_resp = svc.get_all(GetCatalogueRequest(request_id="req-1"))
    assert all_resp.request_id == "req-1"
    assert all_resp.revision is not None and all_resp.revision >= 1
    assert len(all_resp.data.blocks) > 20
    assert len(all_resp.data.lifecycle_events) == 14
    assert len(all_resp.data.timeframes) >= 9

    cond_resp = svc.get_all(GetCatalogueRequest(request_id="req-2", family="CONDITION"))
    assert all(b.family == "CONDITION" for b in cond_resp.data.blocks)

    comm_resp = svc.list_commission_methods(
        ListCommissionMethodsRequest(request_id="req-comm")
    )
    assert comm_resp.request_id == "req-comm"
    assert len(comm_resp.data) == 4
    assert {m.method_id for m in comm_resp.data} == {
        "percentage",
        "money_per_lot",
        "money_per_trade",
        "money_per_share",
    }

    desc_resp = svc.get_block_descriptor(
        GetBlockDescriptorRequest(request_id="req-rsi", block_id="indicator.rsi")
    )
    assert desc_resp.data.semantic_id == "indicator.rsi"
    assert any(p.name == "period" for p in desc_resp.data.parameters)

    with pytest.raises(DomainError) as exc_info:
        svc.get_block_descriptor(
            GetBlockDescriptorRequest(request_id="req-bad", block_id="unknown.block")
        )
    assert exc_info.value.code == "WIZARD_UNKNOWN_BLOCK_ID"
