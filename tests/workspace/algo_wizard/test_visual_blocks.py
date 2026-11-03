"""Tests for Phase 5.6 VisualBlockService (ServletAlgoWizard / WO-WZ-VISUAL-BLOCKS).

Description:
    Verify declared strategy behavior and explicit rejection of unavailable inputs.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Regression evidence for shared strategy execution.
Key Capabilities:
    - FR-hsl-regression-evidence: Assert observable results and failure boundaries.
Python API Usage:
    Run this module through pytest.
CLI Usage:
    uv run pytest tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.backtest.contracts import BacktestSettings
from app.core.trading.blocks.composition import CompositionSpec
from app.core.trading.strategy.contracts import InstrumentEconomics
from app.workspace.algo_wizard import (
    AddTimeframeRequest,
    BlockGroupDefinition,
    CheckResourcesRequest,
    ComparisonConditionNode,
    ComparisonOperator,
    CustomBlockDefinition,
    EvaluationContext,
    FunctionExpressionNode,
    GetWizardBacktestRequest,
    GetWizardConfigRequest,
    HSLStrategyDocument,
    HSLStrategyPayload,
    IndicatorExpressionNode,
    LoadBlockGroupsRequest,
    LoadCustomBlocksRequest,
    LogicalConditionNode,
    MarketPriceNode,
    MathExpressionNode,
    NegateConditionRequest,
    NotConditionNode,
    OrderCancelActionNode,
    OrderMarketActionNode,
    OrderModifyActionNode,
    OrderPendingActionNode,
    ParameterRefNode,
    ParameterSpec,
    PositionCloseActionNode,
    RuleNode,
    SaveBlockGroupsRequest,
    SaveCustomBlocksRequest,
    StateConditionNode,
    StopLossSpec,
    StopWizardBacktestRequest,
    StrategyCompiler,
    StrategyValidator,
    TemporalConditionNode,
    TimeframeSpec,
    UniverseSpec,
    ValidateDocumentRequest,
    ValueLiteralNode,
    VariableSetActionNode,
    VariableSpec,
    VisualBlockService,
    WizardBacktestRequest,
    WizardBarInput,
    WizardBlockLibrary,
)


def _make_sample_document() -> HSLStrategyDocument:
    return HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="visual-strat-001",
            name="Visual Breakout Strategy",
            universe=UniverseSpec(mode="explicit", symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1", additional=("D1",)),
            parameters={
                "fast_len": ParameterSpec(type="int", default=5, min=2, max=50),
            },
            variables={
                "signal_val": VariableSpec(type="float", initial=0.0),
            },
            rules=(
                RuleNode(
                    id="r-entry",
                    priority=10,
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=MarketPriceNode(field="close"),
                        right=MarketPriceNode(
                            field="open",
                            context=EvaluationContext(shift=1),
                        ),
                    ),
                    then=(
                        OrderMarketActionNode(
                            side="long",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=15.0),
                            ),
                        ),
                        OrderPendingActionNode(
                            action="enter_stop",
                            side="long",
                            entry_price=MathExpressionNode(
                                operator="add",
                                left=MarketPriceNode(field="high"),
                                right=ValueLiteralNode(value=0.001),
                            ),
                        ),
                        VariableSetActionNode(
                            name="signal_val",
                            value=IndicatorExpressionNode(
                                name="indicator.ema",
                                inputs={"source": MarketPriceNode(field="close")},
                                params={"period": ParameterRefNode(name="fast_len")},
                            ),
                        ),
                    ),
                ),
                RuleNode(
                    id="r-exit",
                    priority=20,
                    when=StateConditionNode(state="position.is_long"),
                    then=(
                        OrderModifyActionNode(
                            action="modify_stop_loss",
                            stop_loss=StopLossSpec(
                                type="fixed_pips",
                                value=ValueLiteralNode(value=10.0),
                            ),
                        ),
                        OrderCancelActionNode(),
                        PositionCloseActionNode(
                            target_side="long",
                            quantity_pct=100.0,
                            reason="exit_long",
                        ),
                    ),
                ),
            ),
        )
    )


def test_get_config_and_validate_document() -> None:
    svc = VisualBlockService()
    assert isinstance(svc.library, WizardBlockLibrary)
    assert isinstance(svc.validator, StrategyValidator)
    assert isinstance(svc.compiler, StrategyCompiler)

    cfg_resp = svc.get_config(GetWizardConfigRequest(request_id="req-cfg"))
    assert cfg_resp.data.schema_version == "1.0.0"
    assert len(cfg_resp.data.supported_lifecycle_events) == 14
    assert cfg_resp.data.default_symbol == "EURUSD"
    assert cfg_resp.data.default_timeframe == "H1"
    assert "H1" in cfg_resp.data.supported_timeframes
    assert len(cfg_resp.data.custom_block_groups) >= 3
    assert cfg_resp.data.custom_blocks_count == 0

    doc = _make_sample_document()
    val_ok = svc.validate_document(
        ValidateDocumentRequest(request_id="req-val-ok", document=doc)
    )
    assert val_ok.data.valid is True
    assert len(val_ok.data.issues) == 0

    # Also validate raw HSL dict and legacy dict
    val_raw = svc.validate_document(
        ValidateDocumentRequest(document=doc.model_dump(mode="json"))
    )
    assert val_raw.data.valid is True

    val_legacy = svc.validate_document(
        ValidateDocumentRequest(document={"id": "leg-1", "name": "Legacy", "rules": []})
    )
    assert val_legacy.data.valid is True


def test_negate_condition_operators_double_negation_and_de_morgan() -> None:
    svc = VisualBlockService()
    pairs: tuple[tuple[ComparisonOperator, ComparisonOperator], ...] = (
        ("greater_than", "less_or_equal"),
        ("less_or_equal", "greater_than"),
        ("greater_or_equal", "less_than"),
        ("less_than", "greater_or_equal"),
        ("equal", "not_equal"),
        ("not_equal", "equal"),
        ("crosses_above", "crosses_below"),
        ("crosses_below", "crosses_above"),
    )
    for op, expected_inv in pairs:
        cond = ComparisonConditionNode(
            operator=op,
            left=MarketPriceNode(field="close"),
            right=ValueLiteralNode(value=100.0),
        )
        neg = svc.negate_condition(NegateConditionRequest(condition=cond)).data
        assert isinstance(neg, ComparisonConditionNode)
        assert neg.operator == expected_inv

    # Double negation unwraps NotConditionNode
    inner = StateConditionNode(state="position.is_flat")
    wrapped = svc.negate_condition(NegateConditionRequest(condition=inner)).data
    assert isinstance(wrapped, NotConditionNode)
    unwrapped = svc.negate_condition(NegateConditionRequest(condition=wrapped)).data
    assert unwrapped == inner

    # LogicalConditionNode with distribute_logical=False vs True (De Morgan's law)
    c1 = ComparisonConditionNode(
        operator="greater_than",
        left=MarketPriceNode(field="close"),
        right=ValueLiteralNode(value=10.0),
    )
    c2 = ComparisonConditionNode(
        operator="less_than",
        left=MarketPriceNode(field="open"),
        right=ValueLiteralNode(value=20.0),
    )
    log_and = LogicalConditionNode(operator="and", conditions=(c1, c2))
    neg_wrap = svc.negate_condition(
        NegateConditionRequest(condition=log_and, distribute_logical=False)
    ).data
    assert isinstance(neg_wrap, NotConditionNode)

    neg_dist = svc.negate_condition(
        NegateConditionRequest(condition=log_and, distribute_logical=True)
    ).data
    assert isinstance(neg_dist, LogicalConditionNode)
    assert neg_dist.operator == "or"
    assert isinstance(neg_dist.conditions[0], ComparisonConditionNode)
    assert neg_dist.conditions[0].operator == "less_or_equal"
    assert isinstance(neg_dist.conditions[1], ComparisonConditionNode)
    assert neg_dist.conditions[1].operator == "greater_or_equal"


def test_custom_blocks_and_block_groups_persistence() -> None:
    svc = VisualBlockService()
    cb1 = CustomBlockDefinition(
        block_id="custom.rsi_oversold",
        name="RSI Oversold Filter",
        category="momentum_custom",
        family="CONDITION",
        owner_id="rsi",
        parameters={
            "threshold": ParameterSpec(type="float", default=30.0, min=10.0, max=50.0),
            "period": ParameterSpec(type="int", default=14, min=2, max=100),
        },
        subtree=ComparisonConditionNode(
            operator="less_than",
            left=IndicatorExpressionNode(
                name="indicator.rsi",
                params={"period": ParameterRefNode(name="period")},
            ),
            right=ParameterRefNode(name="threshold"),
        ),
        generation_eligible=True,
    )
    comp = cb1.to_composition_spec()
    assert isinstance(comp, CompositionSpec)
    assert comp.id == "custom.rsi_oversold"
    assert comp.owner_id == "rsi"
    assert comp.generation_eligible is True
    assert comp.recipe["parameters"]["threshold"]["minimum"] == 10.0
    assert comp.recipe["parameters"]["threshold"]["maximum"] == 50.0

    saved_cb = svc.save_custom_blocks(
        SaveCustomBlocksRequest(blocks=(cb1,), replace_all=True)
    )
    assert len(saved_cb.data) == 1
    assert saved_cb.data[0].block_id == "custom.rsi_oversold"

    loaded_cb = svc.load_custom_blocks(
        LoadCustomBlocksRequest(category="momentum_custom")
    )
    assert len(loaded_cb.data) == 1
    assert (
        len(svc.load_custom_blocks(LoadCustomBlocksRequest(category="other")).data) == 0
    )

    # Block groups save and load
    g_enabled = BlockGroupDefinition(
        group_id="custom_group_a",
        name="Custom Group A",
        block_ids=("custom.rsi_oversold",),
        enabled=True,
    )
    g_disabled = BlockGroupDefinition(
        group_id="custom_group_b",
        name="Custom Group B",
        block_ids=("indicator.ema",),
        enabled=False,
    )
    saved_grps = svc.save_block_groups(
        SaveBlockGroupsRequest(
            groups=(g_enabled, g_disabled),
            replace_all=True,
        )
    )
    assert len(saved_grps.data) == 2

    only_enabled = svc.load_block_groups(LoadBlockGroupsRequest(enabled_only=True))
    assert [g.group_id for g in only_enabled.data] == ["custom_group_a"]


def test_add_timeframe_and_check_resources() -> None:
    svc = VisualBlockService()
    doc = _make_sample_document()

    # Add new timeframe M15
    added = svc.add_timeframe(AddTimeframeRequest(document=doc, timeframe="m15")).data
    assert added.strategy.timeframe.additional == ("D1", "M15")

    # Adding duplicate D1 or primary H1 does not duplicate
    dup = svc.add_timeframe(AddTimeframeRequest(document=added, timeframe="D1")).data
    assert dup.strategy.timeframe.additional == ("D1", "M15")
    prim = svc.add_timeframe(AddTimeframeRequest(document=dup, timeframe="H1")).data
    assert prim.strategy.timeframe.additional == ("D1", "M15")

    # Invalid timeframe raises WIZARD_INVALID_TIMEFRAME
    with pytest.raises(DomainError) as tf_exc:
        svc.add_timeframe(AddTimeframeRequest(document=doc, timeframe="H7"))
    assert tf_exc.value.code == "WIZARD_INVALID_TIMEFRAME"

    # Resource check on ready document
    chk_ok = svc.check_resources(
        CheckResourcesRequest(
            document=added,
            available_symbols=("EURUSD", "GBPUSD"),
            available_timeframes=("H1", "D1", "M15"),
        )
    ).data
    assert chk_ok.ready is True
    assert "EURUSD" in chk_ok.referenced_symbols
    assert "indicator.ema" in chk_ok.referenced_blocks
    assert len(chk_ok.missing_resources) == 0

    # Resource check with missing symbol, timeframe, and block across nested conditions
    missing_doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="missing-res-strat",
            name="Missing Resources Strategy",
            universe=UniverseSpec(mode="explicit", symbols=("EURUSD",)),
            timeframe=TimeframeSpec(primary="H1"),
            rules=(
                RuleNode(
                    id="r-nested",
                    when=LogicalConditionNode(
                        operator="and",
                        conditions=(
                            NotConditionNode(
                                condition=TemporalConditionNode(
                                    operator="remains_true_for",
                                    bars=3,
                                    condition=ComparisonConditionNode(
                                        operator="greater_than",
                                        left=MarketPriceNode(
                                            field="close",
                                            context=EvaluationContext(
                                                symbol="XAUUSD",
                                                timeframe="W1",
                                                shift=0,
                                            ),
                                        ),
                                        right=FunctionExpressionNode(
                                            name="custom.missing_fn",
                                            args=(
                                                MathExpressionNode(
                                                    operator="abs",
                                                    left=MarketPriceNode(field="low"),
                                                ),
                                            ),
                                        ),
                                    ),
                                )
                            ),
                        ),
                    ),
                    then=(OrderMarketActionNode(side="long"),),
                ),
            ),
        )
    )
    chk_miss = svc.check_resources(
        CheckResourcesRequest(
            document=missing_doc,
            available_symbols=("GBPUSD",),
            available_timeframes=("M5",),
        )
    ).data
    assert chk_miss.ready is False
    kinds = {m.resource_type for m in chk_miss.missing_resources}
    assert kinds == {"symbol", "timeframe", "block"}


def test_run_stop_and_get_backtest_results() -> None:
    svc = VisualBlockService()
    doc = _make_sample_document()
    bars = tuple(
        WizardBarInput(
            time=1_700_000_000 + i * 3600,
            open=100.0 + i * 0.5,
            high=101.0 + i * 0.8,
            low=99.5 + i * 0.4,
            close=100.4 + i * 0.7,
            volume=150.0,
        )
        for i in range(15)
    )
    bt_resp = svc.run_backtest(
        WizardBacktestRequest(
            request_id="req-bt-1",
            backtest_id="bt-001",
            document=doc,
            bars=bars,
            settings=BacktestSettings(
                economics=InstrumentEconomics(
                    0.0001, 0.00001, 10.0, 100000.0, 0.01, 100.0, 0.01
                )
            ),
            negate_signals=False,
        )
    )
    assert bt_resp.data.backtest_id == "bt-001"
    assert bt_resp.data.strategy_id == "visual-strat-001"
    assert bt_resp.data.status == "COMPLETED"
    assert bt_resp.data.bars_evaluated == 15
    assert bt_resp.data.total_orders_opened >= 1
    assert len(bt_resp.data.trade_log) >= 1

    with pytest.raises(DomainError) as missing:
        svc.run_backtest(
            WizardBacktestRequest(
                backtest_id="bt-002", document=doc, bars=(), negate_signals=True
            )
        )
    assert missing.value.code == "HSL_MISSING_FEED"

    # Retrieve and stop backtest
    fetched = svc.get_backtest_results(GetWizardBacktestRequest(backtest_id="bt-001"))
    assert fetched.data.backtest_id == "bt-001"

    stopped = svc.stop_backtest(StopWizardBacktestRequest(backtest_id="bt-001"))
    assert stopped.data.status == "STOPPED"
    assert stopped.data.stopped is True

    fetched_after = svc.get_backtest_results(
        GetWizardBacktestRequest(backtest_id="bt-001")
    )
    assert fetched_after.data.status == "STOPPED"

    # Invalid strategy backtest raises WIZARD_STRATEGY_INVALID
    bad_doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id="bad-bt",
            name="Bad Backtest",
            rules=(
                RuleNode(
                    id="r1",
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=ParameterRefNode(name="nonexistent"),
                        right=ValueLiteralNode(value=1.0),
                    ),
                    then=(OrderMarketActionNode(side="long"),),
                ),
            ),
        )
    )
    with pytest.raises(DomainError) as inv_exc:
        svc.run_backtest(WizardBacktestRequest(document=bad_doc))
    assert inv_exc.value.code == "WIZARD_STRATEGY_INVALID"

    # Missing backtest_id raises WIZARD_BACKTEST_NOT_FOUND
    with pytest.raises(DomainError) as nf1:
        svc.stop_backtest(StopWizardBacktestRequest(backtest_id="missing-bt"))
    assert nf1.value.code == "WIZARD_BACKTEST_NOT_FOUND"

    with pytest.raises(DomainError) as nf2:
        svc.get_backtest_results(GetWizardBacktestRequest(backtest_id="missing-bt"))
    assert nf2.value.code == "WIZARD_BACKTEST_NOT_FOUND"
