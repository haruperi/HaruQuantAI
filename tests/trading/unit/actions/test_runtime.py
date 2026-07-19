"""Unit tests for the thin Trading live evaluation-cycle orchestrator."""

# ruff: noqa: INP001

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

import app.services.trading.actions.runtime as runtime_module
import pytest
from app.services.risk.contracts import (
    DecisionState,
    RiskApprovalToken,
    RiskDecisionPackage,
)
from app.services.strategy import TradeIntent
from app.services.trading.actions import run_live_evaluation_cycle
from app.services.trading.contracts import (
    StandardTradingEnvelope,
    TradingError,
    TradingRequest,
)
from app.services.trading.state import TradingProjection
from tests.trading.unit.actions.test_dependencies import (
    NOW,
    account_snapshot,
    dependencies,
)


@pytest.fixture
def anyio_backend() -> str:
    """Select the installed asyncio AnyIO backend."""
    return "asyncio"


def evidence() -> dict[str, object]:
    """Return complete JSON-safe workflow and lineage references."""
    return {
        "request_id": "request-001",
        "workflow_id": "workflow-001",
        "correlation_id": "correlation-001",
        "account_id": "account-001",
        "action_policy_verdict_id": "policy-001",
        "canonical_material_version": "v1",
    }


def trade_intent() -> TradeIntent:
    """Build one immutable Strategy proposal without executable sizing."""
    return TradeIntent(
        intent_id="intent-001",
        decision_id="strategy-decision-001",
        idempotency_key="idempotency-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        strategy_sequence=1,
        symbol="EURUSD",
        side="BUY",
        intent_type="OPEN",
        order_type="MARKET",
        limit_price=None,
        stop_price=None,
        time_in_force=None,
        requested_sizing_mode=None,
        quantity_hint=None,
        notional_hint=None,
        signal_timestamp=NOW - timedelta(seconds=1),
        decision_timestamp=NOW,
        parent_intent_id=None,
        stop_loss=None,
        take_profit=None,
        expiration=None,
        allow_partial_fills=False,
        min_fill_size=None,
        rationale_ref="rationale-001",
        lineage={"signal": "signal-001"},
    )


def risk_decision() -> RiskDecisionPackage:
    """Build one exact Risk approval carrying the only executable size."""
    token = RiskApprovalToken(
        token_id="token-001",
        decision_id="risk-001",
        config_hash="a" * 64,
        action="submit_order",
        scope={"account_id": "account-001"},
        approver_id="risk-policy",
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        nonce="nonce-001",
        signature="signature-001",
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
    )
    return RiskDecisionPackage(
        decision_id="risk-001",
        intent_id="intent-001",
        state=DecisionState.APPROVE,
        requested_size=Decimal("0.50"),
        approved_size=Decimal("0.50"),
        ordered_checks=(),
        primary_failure_limit=None,
        composite_breach_flags=(),
        evidence_refs={"account": "snapshot-001"},
        config_hash="a" * 64,
        concurrency_disclosure="serialized",
        recommendations=(),
        issued_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(minutes=5),
        token=token,
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
    )


def evaluation_dependencies(intent):
    """Build observable public domain evaluation ports."""
    calls: list[str] = []

    async def market(value):
        """Record the Data market read."""
        calls.append("data.market")
        return cast("object", object())

    async def account(value):
        """Record the Data account read."""
        calls.append("data.account")
        return account_snapshot()

    async def indicators(dataset, value):
        """Record the Indicators invocation."""
        calls.append("indicators")
        return cast("object", object())

    async def strategy(dataset, snapshot, series, value):
        """Record the Strategy invocation."""
        calls.append("strategy")
        return intent

    async def risk(proposal, snapshot, value):
        """Record the Risk invocation."""
        calls.append("risk")
        return risk_decision()

    session = cast(
        "object",
        SimpleNamespace(
            config=SimpleNamespace(
                execution_route="paper", live_workflow_timeout_seconds=Decimal(10)
            )
        ),
    )
    deps = replace(
        dependencies(),
        live_session=session,
        connection=cast(
            "object", SimpleNamespace(broker_id=SimpleNamespace(value="mt5"))
        ),
        market_data_source=market,
        evaluation_account_source=account,
        indicator_source=indicators,
        strategy_source=strategy,
        risk_source=risk,
    )
    return deps, calls


@pytest.mark.anyio
async def test_cycle_never_generates_or_sizes_signals(monkeypatch) -> None:
    """Cycle preserves public domain order and uses only Risk approved_size."""
    deps, calls = evaluation_dependencies(trade_intent())
    captured = {}

    async def execute(item, supplied_deps, supplied_evidence):
        """Capture the already-approved canonical request."""
        captured["quantity"] = item.quantity
        return StandardTradingEnvelope(
            status="sent",
            message="captured",
            data={"request_id": item.request_id},
            errors=(),
            warnings=(),
            audit_metadata={"operation": "test", "redaction_applied": True},
        )

    monkeypatch.setattr(runtime_module, "_execute_request", execute)
    outcome = await run_live_evaluation_cycle(deps, evidence())
    assert outcome.status == "sent"
    assert calls == ["data.market", "data.account", "indicators", "strategy", "risk"]
    assert captured["quantity"] == Decimal("0.50")


@pytest.mark.anyio
async def test_neutral_cycle_is_normal_no_mutation() -> None:
    """A neutral Strategy result returns success without calling Risk."""
    deps, calls = evaluation_dependencies(None)
    outcome = await run_live_evaluation_cycle(deps, evidence())
    assert outcome.status == "success"
    assert outcome.data == {"mutation_performed": False}
    assert calls == ["data.market", "data.account", "indicators", "strategy"]


def test_runtime_reads_modify_targets_only_from_trading_state() -> None:
    """Runtime resolves cancel and close targets from the local projection."""
    deps = dependencies()
    deps.store.projection = TradingProjection(
        route="sim",
        tenant_id="account-001",
        authority_id="simulation",
        version=3,
        orders={"local-order": {"symbol": "EURUSD", "broker_order_id": "broker-order"}},
        positions={
            "local-position": {
                "symbol": "EURUSD",
                "broker_position_id": "broker-position",
            }
        },
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    base = TradingRequest.model_validate(
        {
            **dependencies_request_data(),
            "action": "cancel_order",
            "order_id": "placeholder",
            "target_broker_order_id": "placeholder",
            "expected_version": 1,
        }
    )
    cancel = trade_intent().model_copy(update={"intent_type": "CANCEL"})
    assert runtime_module._state_target(base, deps, cancel) == (
        "broker-order",
        None,
        3,
    )
    close = trade_intent().model_copy(update={"intent_type": "CLOSE"})
    assert runtime_module._state_target(base, deps, close) == (
        None,
        "broker-position",
        3,
    )


def dependencies_request_data() -> dict[str, object]:
    """Return complete request data for runtime state-target tests."""
    return {
        "request_id": "request-001",
        "workflow_id": "workflow-001",
        "correlation_id": "correlation-001",
        "route": "sim",
        "action": "submit_order",
        "provider_id": None,
        "account_id": "account-001",
        "strategy_id": "strategy-001",
        "strategy_version": "v1",
        "intent_id": "intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "lots",
        "quantity": Decimal("0.50"),
        "risk_decision_id": "risk-001",
        "action_policy_verdict_id": "policy-001",
        "approval_token_ref": "token-001",
        "idempotency_key": "idempotency-001",
        "canonical_material_version": "v1",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=5),
        "instrument_min_quantity": Decimal("0.01"),
        "instrument_max_quantity": Decimal(10),
        "instrument_quantity_step": Decimal("0.01"),
    }


def test_runtime_timeout_emits_operational_evidence() -> None:
    """An exceeded exact cycle bound emits timeout evidence before mutation."""
    events = []
    session = cast(
        "object",
        SimpleNamespace(
            config=SimpleNamespace(live_workflow_timeout_seconds=Decimal(1))
        ),
    )
    deps = replace(
        dependencies(),
        live_session=session,
        clock=lambda: NOW + timedelta(seconds=2),
        event_sink=events.append,
    )
    with pytest.raises(TradingError, match="WORKFLOW_TIMEOUT"):
        runtime_module._check_timeout(deps, NOW, evidence())
    assert events[0].event_type == "WORKFLOW_TIMEOUT"
