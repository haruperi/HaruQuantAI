"""WF-TRD-PRI: fully illustrated approved-request-to-outcome Trading pipeline."""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import (
    build_execution_plan,
    classify_authority_response,
    create_readiness_assessment,
    evaluate_live_gate,
    start_live_session,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-PRI"
STAGES = (
    "Receive the canonical approved Trading request.",
    "Load timestamped route, account, instrument, order, and position evidence.",
    "Validate contract, identity, route, action, quantity, and validity material.",
    "Verify the current Risk decision and approved quantity.",
    "Check the complete applicable kill-switch hierarchy.",
    "Verify the Risk-owned action-policy verdict.",
    "Verify approval-token reference and exact authority scope.",
    "Assess combined execution readiness and freshness.",
    "Enforce route, environment, session, and live-enable safety.",
    "Build the deterministic side-effect-free execution plan.",
    "Reserve canonical idempotency material.",
    "Record the pre-dispatch audit boundary and run every mandatory gate.",
    "Illustrate one dispatch through a virtual non-production authority.",
    "Classify the virtual authority response into a canonical receipt.",
    "Prove an uncertain authority response remains retry-locked.",
    "Record bounded execution evidence in a virtual durable store.",
    "Apply ordered evidence to the virtual Trading projection.",
    "Reconcile the projection against virtual authority truth.",
    "Illustrate the later closed-position persistence record.",
    "Finalize the terminal virtual idempotency outcome.",
    "Emit bounded monitoring and reporting evidence.",
    "Return the canonical outcome without a real broker mutation.",
)


def _stage(number: int, *, actual: bool) -> None:
    """Print one explicitly classified workflow stage.

    Args:
        number: One-based stage number.
        actual: Whether the stage invokes or inspects genuine Trading behavior.
    """
    classification = "ACTUAL TRADING BEHAVIOR" if actual else "VIRTUAL BOUNDARY"
    print(
        f"\n{'=' * 88}\nStage {number:02d}/{len(STAGES)} — "
        f"{STAGES[number - 1]}\nClassification: {classification}\n{'=' * 88}"
    )


def _show(label: str, value: object) -> None:
    """Print bounded, secret-safe workflow evidence.

    Args:
        label: Human-readable evidence name.
        value: Bounded evidence value.
    """
    print(f"{label}: {value}")


async def run() -> None:  # noqa: PLR0915 - teaching workflow is intentionally linear.
    """Run the complete documented Trading workflow without external effects."""
    # Stage 01 — INPUT BOUNDARY: receive a canonical request, never a raw signal.
    _stage(1, actual=True)
    request = examples.live_gate_request()
    _show(
        "Request",
        {
            "request_id": request.request_id,
            "intent_id": request.intent_id,
            "route": request.route.value,
            "action": request.action,
            "symbol": request.symbol,
            "quantity": str(request.quantity),
        },
    )

    # Stage 02 — Load bounded virtual evidence; none is represented as broker truth.
    _stage(2, actual=False)
    virtual_positions = [
        {
            "ticket": 100001,
            "symbol": "GBPUSD",
            "type": "sell",
            "volume": "0.50",
            "strategy": "mean-reversion-v2",
            "account": 10001,
            "environment": "demo",
        }
    ]
    virtual_orders: list[dict[str, object]] = []
    virtual_route_evidence = {
        "source": "virtual-demo-authority",
        "available": True,
        "fresh": True,
        "positions": virtual_positions,
        "orders": virtual_orders,
    }
    _show("Virtual route evidence", virtual_route_evidence)

    # Stage 03 — Inspect the already validated typed request contract.
    _stage(3, actual=True)
    assert request.contract_version == "v1"
    assert request.valid_until > request.system_time
    assert request.quantity is not None
    assert request.quantity > 0
    _show("Validated schema", request.schema_id)

    # Stage 04 — Read current producer-owned Risk authority bound to this intent.
    _stage(4, actual=True)
    risk_decision = examples.live_risk_decision()
    assert risk_decision.intent_id == request.intent_id
    assert risk_decision.approved_size == request.quantity
    _show(
        "Risk authority",
        {
            "decision_id": risk_decision.decision_id,
            "state": risk_decision.state,
            "approved_size": str(risk_decision.approved_size),
        },
    )

    # Stage 05 — Supply every exact applicable inactive Risk switch scope.
    _stage(5, actual=True)
    kill_switches = examples.inactive_kill_switch_hierarchy(request)
    assert all(state.state == "inactive" for state in kill_switches)
    _show("Kill-switch scopes", [state.scope_level for state in kill_switches])

    # Stage 06 — Inspect the exact action-policy verdict consumed by the gate.
    _stage(6, actual=True)
    policy = examples.live_action_policy()
    assert policy.allowed
    assert policy.action == request.action
    _show("Action-policy verdict", policy.verdict_id)

    # Stage 07 — Approval references must match producer authority; no local minting.
    _stage(7, actual=True)
    assert risk_decision.token is not None
    assert risk_decision.token.token_id == request.approval_token_ref
    _show("Approval token reference", request.approval_token_ref)

    # Stage 08 — Build explicit current readiness evidence used by planning and gates.
    _stage(8, actual=True)
    readiness = create_readiness_assessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"route": "virtual-current", "risk": risk_decision.decision_id},
        assessed_at=request.system_time,
    )
    _show(
        "Readiness",
        {"passed": readiness.passed, "failures": readiness.failed_check_codes},
    )

    # Stage 09 — Start only an injected in-memory session; no adapter socket is opened.
    _stage(9, actual=True)
    audits: list[object] = []
    session = examples.live_gate_session(
        risk_decision=risk_decision,
        kill_switches=kill_switches,
        readiness=readiness,
        pre_audit_sink=audits.append,
    )
    startup = await start_live_session(
        session,
        {**examples.live_config(), "ALLOW_LIVE_MUTATIONS": True},
        examples.live_evidence(),
    )
    assert startup.status == "success"
    _show("Virtual session", "ready; external transport absent")

    # Stage 10 — Construct the deterministic plan without dispatch side effects.
    _stage(10, actual=True)
    plan_response = build_execution_plan(request, readiness)
    assert plan_response.status == "success"
    assert plan_response.data is not None
    execution_plan = plan_response.data
    _show("Execution plan", type(execution_plan).__name__)

    # Stage 11 — The following gate reserves this exact caller-supplied material.
    _stage(11, actual=False)
    virtual_idempotency = {
        "key": request.idempotency_key,
        "material_version": request.canonical_material_version,
        "status": "pending_gate",
    }
    _show("Idempotency material", virtual_idempotency)

    # Stage 12 — Execute the real ordered gate, including reservation and pre-audit.
    _stage(12, actual=True)
    gate = await evaluate_live_gate(request, {"route": "fresh"}, session)
    assert gate.status == "success"
    assert gate.data is not None
    assert gate.data["dispatch_allowed"] is True
    assert len(audits) == 1
    virtual_idempotency["status"] = "reserved"
    _show("Gate result", {"dispatch_allowed": True, "pre_audit_records": len(audits)})

    # Stage 13 — AUTHORITY BOUNDARY: construct a virtual response, but transmit nothing.
    _stage(13, actual=False)
    virtual_authority_response: dict[str, object] = {
        "receipt_id": "virtual-receipt-001",
        "intent_id": request.intent_id,
        "client_order_id": "virtual-client-order-001",
        "provider_order_id": "virtual-provider-order-001",
        "route": "live",
        "authority": "virtual-non-production-adapter",
        "status": "accepted",
        "requested_quantity": str(request.quantity),
        "filled_quantity": "0",
        "request_id": request.request_id,
        "correlation_id": request.correlation_id,
        "authority_timestamp": request.system_time.isoformat(),
        "received_at": request.system_time.isoformat(),
    }
    _show("Virtual authority response", virtual_authority_response)
    print(
        "No broker mutation was transmitted; the authority response is teaching data."
    )

    # Stage 14 — Run genuine conservative classification over the virtual response.
    _stage(14, actual=True)
    response_policy = {
        "malformed_response_policy": "unknown_outcome",
        "mutation_retry_policy": "reconcile_before_retry",
    }
    receipt_response = classify_authority_response(
        virtual_authority_response,  # type: ignore[arg-type]
        response_policy,  # type: ignore[arg-type]
    )
    assert receipt_response.status == "success"
    assert receipt_response.data is not None
    receipt = receipt_response.data
    assert receipt.status == "accepted"
    assert receipt.filled_quantity == Decimal(0)
    _show("Canonical receipt", {"status": receipt.status, "filled_quantity": "0"})

    # Stage 15 — Classify ambiguity separately and prove it is never blind-retry safe.
    _stage(15, actual=True)
    uncertain_raw = {**virtual_authority_response, "timed_out": True}
    uncertain_response = classify_authority_response(
        uncertain_raw,  # type: ignore[arg-type]
        response_policy,  # type: ignore[arg-type]
    )
    assert uncertain_response.data is not None
    uncertain = uncertain_response.data
    assert uncertain.status == "unknown_outcome"
    assert uncertain.reconciliation_required
    assert not uncertain.retry_safe
    _show("Uncertain branch", {"status": uncertain.status, "retry_safe": False})

    # Stage 16 — Persist only to an in-memory teaching ledger, never SQLite.
    _stage(16, actual=False)
    virtual_event_store = [
        {"sequence": 1, "type": "send_attempted", "request_id": request.request_id},
        {"sequence": 2, "type": "receipt_recorded", "status": receipt.status},
    ]
    _show("Virtual event store", virtual_event_store)

    # Stage 17 — Apply ordered teaching events to a bounded virtual projection.
    _stage(17, actual=False)
    virtual_projection = {
        "version": 2,
        "request_id": request.request_id,
        "order_id": receipt.provider_order_id,
        "status": receipt.status,
        "filled_quantity": str(receipt.filled_quantity),
    }
    _show("Virtual projection", virtual_projection)

    # Stage 18 — Compare that projection with equally explicit virtual authority truth.
    _stage(18, actual=False)
    virtual_authority_truth = {
        "order_id": receipt.provider_order_id,
        "status": "accepted",
        "filled_quantity": "0",
    }
    reconciliation_match = all(
        virtual_projection[key] == value
        for key, value in virtual_authority_truth.items()
    )
    assert reconciliation_match
    _show("Reconciliation", {"matched": reconciliation_match, "authority": "virtual"})

    # Stage 19 — Illustrate a later closed trade; it is not derived from this receipt.
    _stage(19, actual=False)
    virtual_closed_position = {
        "ticket": 100000,
        "symbol": "EURUSD",
        "type": "buy",
        "volume": "1.00",
        "entry_time": "2026-08-06T08:00:00+00:00",
        "entry_price": "1.10000",
        "stop_loss": "1.09500",
        "take_profit": "1.11000",
        "exit_time": "2026-08-06T10:00:00+00:00",
        "exit_price": "1.10500",
        "exit_reason": "virtual-teaching-close",
        "commission": "-7.00",
        "swap": "0.00",
        "profit": "500.00",
        "mae_points": 20,
        "mfe_points": 60,
        "slippage_points": 1,
        "magic": 3001,
        "strategy": "trend-following-v3",
        "account": 10001,
        "environment": "demo",
    }
    _show("Virtual closed-position record", virtual_closed_position)

    # Stage 20 — Finalize only the in-memory demonstration outcome.
    _stage(20, actual=False)
    virtual_idempotency.update(
        {"status": "completed", "receipt_id": receipt.receipt_id}
    )
    _show("Virtual idempotency outcome", virtual_idempotency)

    # Stage 21 — Emit bounded teaching evidence without an external alert sink.
    _stage(21, actual=False)
    virtual_monitoring = {
        "event_type": "EXECUTION_ACCEPTED",
        "request_id": request.request_id,
        "receipt_id": receipt.receipt_id,
        "reconciliation_required": receipt.reconciliation_required,
        "secrets_exposed": False,
    }
    _show("Virtual monitoring evidence", virtual_monitoring)

    # Stage 22 — OUTPUT BOUNDARY: return canonical data and disclose every limitation.
    _stage(22, actual=True)
    _show(
        "Output",
        {
            "status": receipt_response.status,
            "receipt_status": receipt.status,
            "filled_quantity": str(receipt.filled_quantity),
            "real_broker_mutation": False,
            "database_write": False,
        },
    )
    print("No broker mutation was transmitted and no broker fill was invented.")


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
