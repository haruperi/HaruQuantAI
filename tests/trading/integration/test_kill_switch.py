"""Workflow integration for kill switches and partial emergency results."""

# ruff: noqa: ARG005
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace
from typing import cast

import pytest
from app.services.brokers import get_broker_error_code
from app.services.data import build_account_order, build_account_state_snapshot
from app.services.risk import (
    create_action_policy_verdict,
    create_risk_decision_package,
)
from app.services.trading import (
    cancel_all_orders,
    create_live_session,
    create_readiness_assessment,
    create_trading_projection,
    resume_strategy,
    start_live_session,
)

from tests.trading.conftest import (
    NOW,
    CountingAdapter,
    MemoryStore,
    account_snapshot,
    action_policy,
    auth_context,
    broker_connection,
    emergency_dependencies,
    inactive_kill_switch_hierarchy,
    live_config,
    live_evidence,
    live_risk_decision,
    symbol_capability,
    trading_dependencies,
    trading_request,
)
from tests.trading.unit.routing.test_dispatcher import _ErrorAdapter

# Private type-only aliases; Risk exposes functions, not contract classes.
ActionPolicyVerdict = object
RiskDecisionPackage = object


async def _passed() -> bool:
    """Return successful demo-session lifecycle evidence."""
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
    return create_risk_decision_package(**data)


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
    return create_action_policy_verdict(**data)


def _demo_account() -> object:
    """Build account evidence with eligible, skipped, and state-missing orders."""
    data = account_snapshot().model_dump(mode="python")
    data["orders"] = (
        *data["orders"],
        build_account_order(
            order_id="order-missing",
            symbol="EURUSD",
            side="BUY",
            state="PENDING",
            quantity=1,
        ),
    )
    return build_account_state_snapshot(**data)


def _demo_emergency_dependencies(adapter: CountingAdapter):
    """Build demo bulk dependencies with per-child Option A Risk authority."""
    store = MemoryStore()
    store.projection = create_trading_projection(
        route="demo",
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
    session = create_live_session(
        store=store,
        connection=connection,
        broker_adapter=cast("object", adapter),
        feature_flags=SimpleNamespace(broker_id="mt5", environment="demo"),
        risk_decision_source=_child_risk,
        action_policy_source=_emergency_policy,
        kill_switch_source=inactive_kill_switch_hierarchy,
        readiness_source=lambda request, _evidence: create_readiness_assessment(
            passed=True,
            failed_check_codes=(),
            evidence_refs={"data_authority_id": "data-authority-001"},
            assessed_at=request.system_time,
        ),
        adapter_capability_source=lambda request: symbol_capability(
            request.route, request.provider_id, request.symbol
        )[0],
        auth_context_source=auth_context,
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
        broker_adapter=cast("object", adapter),
        live_session=session,
        account_state_source=lambda _request: _demo_account(),
        action_policy_source=_emergency_policy,
        kill_switch_state_source=inactive_kill_switch_hierarchy,
        child_risk_decision_source=_child_risk,
    )
    return deps, session


@pytest.mark.anyio
async def test_kill_switch_blocks_and_reports_partial_emergency_results() -> None:
    """New admission blocks while emergency uncertainty remains explicit."""
    blocked = trading_dependencies(action_policy=action_policy("resume_strategy"))
    blocked_request = trading_request(action="resume_strategy")
    active_states = list(inactive_kill_switch_hierarchy(blocked_request))
    active_states[0] = active_states[0].model_copy(update={"state": "active"})
    blocked = replace(
        blocked,
        kill_switch_state_source=lambda item: tuple(active_states),
    )
    blocked_result = await resume_strategy(blocked_request, blocked)
    assert blocked_result.status == "error"
    assert blocked_result.error is not None
    assert blocked_result.error.code == "KILL_SWITCH_ACTIVE"
    emergency = replace(
        emergency_dependencies("cancel_all_orders"),
        broker_adapter=_ErrorAdapter(
            get_broker_error_code("BROKER_RATE_LIMITED"),
            broker="sim",
            environment="simulation",
        ),
    )
    assert (
        await cancel_all_orders(trading_request(action="cancel_all_orders"), emergency)
    ).metadata.extensions["legacy_status"] == "partial"


@pytest.mark.anyio
async def test_demo_bulk_cancel_binds_each_child_risk_authority() -> None:
    """Demo bulk cancel reports success, skips, and state errors within its bound."""
    adapter = CountingAdapter()
    deps, session = _demo_emergency_dependencies(adapter)
    config = {
        **live_config(),
        "RUNTIME_PROFILE": "demo",
        "EXECUTION_ROUTE": "demo",
        "ALLOW_LIVE_MUTATIONS": True,
    }
    await start_live_session(session, config, live_evidence())
    item = trading_request(
        route="demo",
        provider_id="mt5",
        action="cancel_all_orders",
    )

    outcome = await cancel_all_orders(item, deps)

    assert outcome.status == "success"
    assert outcome.metadata.extensions["legacy_status"] == "partial"
    assert adapter.calls == 1
    assert len(outcome.data["results"]) == 2
    assert outcome.data["results"][0]["status"] == "cancelled"
    assert outcome.data["results"][1] == {
        "order_id": "order-missing",
        "status": "error",
        "code": "RECONCILIATION_REQUIRED",
    }
    assert outcome.data["skipped"] == [{"order_id": "order-filled", "state": "FILLED"}]
