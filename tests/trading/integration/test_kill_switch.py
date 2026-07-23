"""Workflow integration for kill switches and partial emergency results."""

# ruff: noqa: ARG005, INP001

from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers.contracts import BrokerAdapter, BrokerFeatureFlags
from app.services.data.evidence.account_contracts import (
    AccountOrder,
    AccountStateSnapshot,
)
from app.services.risk.contracts import ActionPolicyVerdict, RiskDecisionPackage
from app.services.trading.actions import cancel_all_orders, resume_strategy
from app.services.trading.contracts import TradingError
from app.services.trading.live import LiveSession
from app.services.trading.state import TradingProjection
from app.services.trading.validation import ReadinessAssessment
from tests.trading.conftest import (
    NOW,
    CountingAdapter,
    MemoryStore,
    account_snapshot,
    action_policy,
    broker_connection,
    emergency_dependencies,
    inactive_kill_switch,
    kill_switch,
    live_config,
    live_evidence,
    live_risk_decision,
    symbol_capability,
    trading_dependencies,
    trading_request,
    unknown_dispatch,
)


async def _passed() -> bool:
    """Return successful paper-session lifecycle evidence."""
    return True


def _child_risk(request) -> RiskDecisionPackage:
    """Build exact per-child Risk approval and token authority."""
    data = live_risk_decision().model_dump(mode="python")
    decision_id = f"risk-{request.request_id}"
    intent_id = f"intent-{request.request_id}"
    token = dict(data["token"])
    token.update(
        {
            "token_id": f"token-{request.request_id}",
            "decision_id": decision_id,
            "action": request.action,
            "scope": {"account_id": request.account_id},
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
            "issued_at": NOW - timedelta(minutes=1),
            "expires_at": NOW + timedelta(minutes=5),
        }
    )
    data.update(
        {
            "decision_id": decision_id,
            "intent_id": intent_id,
            "requested_size": request.quantity,
            "approved_size": request.quantity,
            "token": token,
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
            "issued_at": NOW - timedelta(minutes=1),
            "expires_at": NOW + timedelta(minutes=5),
        }
    )
    return RiskDecisionPackage.model_validate(data)


def _emergency_policy(request) -> ActionPolicyVerdict:
    """Build the parent ceiling or exact child action-policy authority."""
    if request.action == "cancel_all_orders":
        return action_policy("cancel_all_orders", max_children="3")
    risk = _child_risk(request)
    data = action_policy(request.action).model_dump(mode="python")
    data.update(
        {
            "verdict_id": f"policy-{request.request_id}",
            "action": request.action,
            "scope": {"account_id": request.account_id},
            "decision_id": risk.decision_id,
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
        }
    )
    return ActionPolicyVerdict.model_validate(data)


def _paper_account() -> AccountStateSnapshot:
    """Build account evidence with eligible, skipped, and state-missing orders."""
    data = account_snapshot().model_dump(mode="python")
    data["orders"] = (
        *data["orders"],
        AccountOrder(
            order_id="order-missing",
            symbol="EURUSD",
            side="BUY",
            state="PENDING",
            quantity=1,
        ),
    )
    return AccountStateSnapshot.model_validate(data)


def _paper_emergency_dependencies(adapter: CountingAdapter):
    """Build paper bulk dependencies with per-child Option A Risk authority."""
    store = MemoryStore()
    store.projection = TradingProjection(
        route="paper",
        tenant_id="account-001",
        authority_id="mt5",
        version=1,
        orders={
            "order-001": {"symbol": "EURUSD", "broker_order_id": "order-001"},
            "order-filled": {
                "symbol": "EURUSD",
                "broker_order_id": "order-filled",
            },
        },
        positions={},
        fills={},
        receipts={},
        authority_state={},
        updated_at=NOW,
    )
    connection = broker_connection()
    session = LiveSession(
        store=store,
        connection=connection,
        broker_adapter=cast("BrokerAdapter", adapter),
        feature_flags=cast(
            "BrokerFeatureFlags",
            SimpleNamespace(
                broker_id=connection.broker_id,
                environment=connection.environment,
            ),
        ),
        risk_decision_source=_child_risk,
        action_policy_source=_emergency_policy,
        kill_switch_source=lambda _request: (inactive_kill_switch(),),
        readiness_source=lambda request, _evidence: ReadinessAssessment(
            passed=True,
            failed_check_codes=(),
            evidence_refs={"data_authority_id": "data-authority-001"},
            assessed_at=request.system_time,
        ),
        adapter_capability_source=lambda request: symbol_capability(
            request.route, request.provider_id, request.symbol
        )[0],
        pre_audit_sink=lambda _evidence: None,
        event_sink=lambda _event: None,
        startup_reconcile=_passed,
        drain_in_flight=_passed,
        flush_evidence=_passed,
        shutdown_reconcile=_passed,
        clock=lambda: NOW,
    )
    deps = replace(
        trading_dependencies(store=store),
        connection=connection,
        broker_adapter=cast("BrokerAdapter", adapter),
        simulation_dispatch=None,
        live_session=session,
        account_state_source=lambda _request: _paper_account(),
        action_policy_source=_emergency_policy,
        kill_switch_state_source=lambda _request: (inactive_kill_switch(),),
        child_risk_decision_source=_child_risk,
    )
    return deps, session


@pytest.mark.anyio
async def test_kill_switch_blocks_and_reports_partial_emergency_results() -> None:
    """New admission blocks while emergency uncertainty remains explicit."""
    blocked = trading_dependencies(action_policy=action_policy("resume_strategy"))
    blocked = replace(
        blocked,
        kill_switch_state_source=lambda item: (kill_switch("global", "active"),),
    )
    with pytest.raises(TradingError, match="KILL_SWITCH_ACTIVE"):
        await resume_strategy(trading_request(action="resume_strategy"), blocked)
    emergency = replace(
        emergency_dependencies("cancel_all_orders"),
        simulation_dispatch=unknown_dispatch,
    )
    assert (
        await cancel_all_orders(trading_request(action="cancel_all_orders"), emergency)
    ).status == "partial"


@pytest.mark.anyio
async def test_paper_bulk_cancel_binds_each_child_risk_authority() -> None:
    """Paper bulk cancel reports success, skips, and state errors within its bound."""
    adapter = CountingAdapter()
    deps, session = _paper_emergency_dependencies(adapter)
    config = {
        **live_config(),
        "RUNTIME_PROFILE": "paper",
        "EXECUTION_ROUTE": "paper",
        "ALLOW_LIVE_MUTATIONS": True,
    }
    await session.start(config, live_evidence())
    item = trading_request(
        route="paper",
        provider_id="mt5",
        action="cancel_all_orders",
    )

    outcome = await cancel_all_orders(item, deps)

    assert outcome.status == "partial"
    assert adapter.calls == 1
    assert len(outcome.data["results"]) == 2
    assert outcome.data["results"][0]["status"] == "cancelled"
    assert outcome.data["results"][1] == {
        "order_id": "order-missing",
        "status": "error",
        "code": "RECONCILIATION_REQUIRED",
    }
    assert outcome.data["skipped"] == [{"order_id": "order-filled", "state": "FILLED"}]
