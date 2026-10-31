"""Tests for Phase 5.5 StrategyDocumentService (ServletStrategy / WO-WZ-STRATEGY-LIFECYCLE)."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.core.trading.strategy.runtime import StrategyRuntime
from app.workspace.algo_wizard import (
    AddStrategyRequest,
    ComparisonConditionNode,
    EvaluationContext,
    HSLStrategyDocument,
    HSLStrategyPayload,
    IndicatorExpressionNode,
    ListStrategiesRequest,
    MarketPriceNode,
    OrderMarketActionNode,
    ParameterRefNode,
    ParameterSpec,
    RemoveStrategyRequest,
    RuleNode,
    StartStrategyRequest,
    StopStrategyRequest,
    StrategyCompiler,
    StrategyDocumentService,
    StrategyIdRequest,
    StrategyValidator,
    TimeframeSpec,
    UniverseSpec,
)


def _make_valid_hsl_document(
    strategy_id: str = "ema-cross-001",
    name: str = "EMA Crossover",
    fast_period: int = 12,
) -> HSLStrategyDocument:
    """Create a valid canonical HSL 1.0 strategy document for testing."""
    return HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id=strategy_id,
            name=name,
            universe=UniverseSpec(mode="explicit", symbols=("GBPUSD",)),
            timeframe=TimeframeSpec(primary="M15"),
            parameters={
                "fast_period": ParameterSpec(
                    type="int", default=fast_period, min=2, max=100
                ),
            },
            rules=(
                RuleNode(
                    id="entry-long",
                    name="Enter Long",
                    priority=10,
                    when=ComparisonConditionNode(
                        operator="crosses_above",
                        left=IndicatorExpressionNode(
                            name="indicator.ema",
                            params={"period": ParameterRefNode(name="fast_period")},
                        ),
                        right=MarketPriceNode(field="close"),
                    ),
                    then=(OrderMarketActionNode(side="long"),),
                ),
            ),
        )
    )


def _make_invalid_hsl_document(
    strategy_id: str = "broken-strat",
) -> HSLStrategyDocument:
    """Create an HSL 1.0 document that fails Pass 2/3 validation (negative shift + unknown param)."""
    return HSLStrategyDocument(
        strategy=HSLStrategyPayload(
            id=strategy_id,
            name="Broken Strategy",
            rules=(
                RuleNode(
                    id="bad-rule",
                    when=ComparisonConditionNode(
                        operator="greater_than",
                        left=MarketPriceNode(
                            field="close",
                            context=EvaluationContext(shift=-1),
                        ),
                        right=ParameterRefNode(name="missing_param"),
                    ),
                    then=(OrderMarketActionNode(side="long"),),
                ),
            ),
        )
    )


def test_add_get_and_list_strategies_with_optimistic_revisions() -> None:
    svc = StrategyDocumentService()
    assert isinstance(svc.validator, StrategyValidator)
    assert isinstance(svc.compiler, StrategyCompiler)
    assert isinstance(svc.runtime, StrategyRuntime)

    doc_b = _make_valid_hsl_document(strategy_id="strat-b", name="Strategy B")
    resp_b = svc.add_strategy(
        AddStrategyRequest(
            request_id="req-add-b",
            document=doc_b,
            expected_revision=0,
            connection_name="paper-fx",
        )
    )
    assert resp_b.request_id == "req-add-b"
    assert resp_b.revision == 1
    assert resp_b.data.strategy_id == "strat-b"
    assert resp_b.data.revision == 1
    assert resp_b.data.status == "IDLE"
    assert resp_b.data.validation.valid is True
    assert resp_b.data.connection_name == "paper-fx"
    assert resp_b.data.symbol == "GBPUSD"
    assert resp_b.data.timeframe == "M15"
    assert len(resp_b.data.document_hash) == 64

    # Add a raw HSL dict and a legacy flat dict to verify coercion
    doc_a_raw = _make_valid_hsl_document(
        strategy_id="strat-a", name="Strategy A"
    ).model_dump(mode="json")
    resp_a = svc.add_strategy(
        AddStrategyRequest(request_id="req-add-a", document=doc_a_raw)
    )
    assert resp_a.data.strategy_id == "strat-a"
    assert resp_a.data.revision == 1

    legacy_raw = {
        "id": "strat-c",
        "name": "Legacy C",
        "rules": [],
    }
    resp_c = svc.add_strategy(
        AddStrategyRequest(request_id="req-add-c", document=legacy_raw)
    )
    assert resp_c.data.strategy_id == "strat-c"

    # Deterministic ordering by strategy_id
    listed = svc.list_strategies(ListStrategiesRequest(request_id="req-list"))
    assert [item.strategy_id for item in listed.data] == [
        "strat-a",
        "strat-b",
        "strat-c",
    ]

    # Optimistic revision update succeeds when expected_revision matches
    doc_b_v2 = _make_valid_hsl_document(
        strategy_id="strat-b", name="Strategy B v2", fast_period=20
    )
    resp_b2 = svc.add_strategy(
        AddStrategyRequest(
            request_id="req-upd-b",
            document=doc_b_v2,
            expected_revision=1,
        )
    )
    assert resp_b2.revision == 2
    assert resp_b2.data.revision == 2
    assert resp_b2.data.name == "Strategy B v2"
    assert resp_b2.data.document_hash != resp_b.data.document_hash

    # Stale expected_revision raises WIZARD_REVISION_CONFLICT
    with pytest.raises(DomainError) as exc_info:
        svc.add_strategy(
            AddStrategyRequest(
                request_id="req-stale-b",
                document=doc_b_v2,
                expected_revision=1,
            )
        )
    assert exc_info.value.code == "WIZARD_REVISION_CONFLICT"
    assert exc_info.value.details["expected_revision"] == 1
    assert exc_info.value.details["actual_revision"] == 2

    # Non-zero expected_revision on a new strategy raises WIZARD_REVISION_CONFLICT
    with pytest.raises(DomainError) as exc_new:
        svc.add_strategy(
            AddStrategyRequest(
                request_id="req-bad-new",
                document=_make_valid_hsl_document(strategy_id="strat-new"),
                expected_revision=1,
            )
        )
    assert exc_new.value.code == "WIZARD_REVISION_CONFLICT"

    # get_strategy retrieves the latest version
    fetched = svc.get_strategy(
        StrategyIdRequest(request_id="req-get-b", strategy_id="strat-b")
    )
    assert fetched.data.revision == 2
    assert fetched.data.name == "Strategy B v2"


def test_validation_gating_strict_and_non_strict_modes() -> None:
    svc = StrategyDocumentService()
    bad_doc = _make_invalid_hsl_document("bad-strat-1")

    with pytest.raises(DomainError) as exc_info:
        svc.add_strategy(
            AddStrategyRequest(
                request_id="req-strict-fail",
                document=bad_doc,
                strict=True,
            )
        )
    assert exc_info.value.code == "WIZARD_STRATEGY_INVALID"
    assert int(exc_info.value.details["issue_count"]) >= 2  # type: ignore[arg-type]

    # Non-strict mode stores draft with status="ERROR"
    draft_resp = svc.add_strategy(
        AddStrategyRequest(
            request_id="req-draft-save",
            document=bad_doc,
            strict=False,
        )
    )
    assert draft_resp.data.status == "ERROR"
    assert draft_resp.data.validation.valid is False

    # Attempting to start an invalid draft raises WIZARD_STRATEGY_INVALID and increments revision
    with pytest.raises(DomainError) as start_exc:
        svc.start_strategy(
            StartStrategyRequest(
                request_id="req-start-bad",
                strategy_id="bad-strat-1",
            )
        )
    assert start_exc.value.code == "WIZARD_STRATEGY_INVALID"
    after_fail = svc.get_strategy(StrategyIdRequest(strategy_id="bad-strat-1"))
    assert after_fail.data.status == "ERROR"
    assert after_fail.data.revision == 2


def test_runtime_lifecycle_start_stop_remove_and_not_found() -> None:
    svc = StrategyDocumentService()
    doc = _make_valid_hsl_document(strategy_id="live-ema", name="Live EMA")
    svc.add_strategy(AddStrategyRequest(document=doc))

    # Start compiles to StrategyDocument and transitions to RUNNING
    started = svc.start_strategy(
        StartStrategyRequest(request_id="req-start", strategy_id="live-ema")
    )
    assert started.data.status == "RUNNING"
    assert started.data.revision == 2
    compiled_plan = svc.get_compiled_runtime_document("live-ema")
    assert compiled_plan.strategy_id == "live-ema"
    assert len(compiled_plan.rules) == 1

    # Updating a RUNNING strategy with a valid document preserves RUNNING and recompiles
    doc_updated = _make_valid_hsl_document(
        strategy_id="live-ema", name="Live EMA Fast 8", fast_period=8
    )
    re_added = svc.add_strategy(
        AddStrategyRequest(document=doc_updated, expected_revision=2)
    )
    assert re_added.data.status == "RUNNING"
    assert re_added.data.revision == 3

    # Filter list_strategies by status
    running_list = svc.list_strategies(ListStrategiesRequest(status="RUNNING"))
    assert len(running_list.data) == 1
    assert running_list.data[0].strategy_id == "live-ema"

    idle_list = svc.list_strategies(ListStrategiesRequest(status="IDLE"))
    assert len(idle_list.data) == 0

    # Stop transitions to STOPPED
    stopped = svc.stop_strategy(
        StopStrategyRequest(request_id="req-stop", strategy_id="live-ema")
    )
    assert stopped.data.status == "STOPPED"
    assert stopped.data.revision == 4

    # get_compiled_runtime_document compiles on demand when cache was cleared by stop
    recompiled = svc.get_compiled_runtime_document("live-ema")
    assert recompiled.strategy_id == "live-ema"

    # Remove deletes the strategy record and returns RemoveStrategyResult
    removed = svc.remove_strategy(
        RemoveStrategyRequest(request_id="req-remove", strategy_id="live-ema")
    )
    assert removed.data.strategy_id == "live-ema"
    assert removed.data.removed is True
    assert removed.data.previous_status == "STOPPED"
    assert removed.data.final_revision == 4

    assert len(svc.list_strategies().data) == 0

    # Operations on missing strategy raise WIZARD_STRATEGY_NOT_FOUND
    for fn in (
        lambda: svc.get_strategy(StrategyIdRequest(strategy_id="live-ema")),
        lambda: svc.start_strategy(StartStrategyRequest(strategy_id="live-ema")),
        lambda: svc.stop_strategy(StopStrategyRequest(strategy_id="live-ema")),
        lambda: svc.remove_strategy(RemoveStrategyRequest(strategy_id="live-ema")),
    ):
        with pytest.raises(DomainError) as not_found_exc:
            fn()
        assert not_found_exc.value.code == "WIZARD_STRATEGY_NOT_FOUND"
