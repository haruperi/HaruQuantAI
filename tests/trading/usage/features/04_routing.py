"""Executable Trading routing usage example.

Demonstrates FEAT-TRD-04 adapter capabilities and order dispatch.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.trading import (
    classify_authority_response,
    create_execution_receipt,
    create_order_intent,
    dispatch_order_intent,
    validate_adapter_capability,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)
OrderIntent = Any


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _intent() -> OrderIntent:
    """Build one complete simulation executable intent."""
    return create_order_intent(
        client_order_id="usage-client-order-001",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        provider_id=None,
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        source_intent_id="usage-intent-001",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        approved_volume=Decimal("1.00"),
        risk_approved_volume=Decimal("1.00"),
        idempotency_hash="b" * 64,
        canonical_material_version="v1",
        risk_decision_id="usage-risk-001",
        action_policy_verdict_id="usage-verdict-001",
        approval_token_ref="usage-approval-001",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _paper_intent() -> OrderIntent:
    """Build one paper intent for adapter-capability validation."""
    return _intent().model_copy(update={"route": "paper", "provider_id": "mt5"})


def _capability() -> dict[str, object]:
    """Build complete approved adapter capability evidence."""
    return {
        "provider_id": "mt5",
        "contract_version": "v1",
        "schema_id": "brokers.adapter.v1",
        "provider_api_version": "5",
        "supported_actions": ["submit_order"],
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "security_profile": "approved",
        "operation_timeout_seconds": "10",
        "malformed_response_policy": "unknown_outcome",
        "rate_limit_policy": "provider_retry_after",
        "mutation_retry_policy": "reconcile_before_retry",
        "redaction_applied": True,
    }


def fr_trd_029() -> None:
    """FR-TRD-029: Stage 2 — Reject adapters lacking required capability declarations."""
    _header("Stage 2: Capability Validation - Validate Adapter Capability (FR-TRD-029)")
    capability_result = validate_adapter_capability(  # type: ignore[arg-type]
        _paper_intent(),
        _capability(),
        operation_timeout_seconds=Decimal(10),
    )
    print(_format_result(capability_result))
    print(f"Data -> status='{capability_result.status}'")


def fr_trd_030() -> None:
    """FR-TRD-030: Stage 2 — Classify authority response conservatively."""
    _header(
        "Stage 2: Response Classification - Classify Authority Response (FR-TRD-030)"
    )
    raw = {
        "receipt_id": "usage-receipt-001",
        "intent_id": "usage-intent-001",
        "client_order_id": "usage-client-order-001",
        "route": "paper",
        "authority": "mt5",
        "provider_order_id": "broker-order-001",
        "status": "accepted",
        "requested_quantity": "1.00",
        "filled_quantity": "0",
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
        "authority_timestamp": NOW.isoformat(),
        "received_at": NOW.isoformat(),
    }
    receipt_result = classify_authority_response(  # type: ignore[arg-type]
        raw,
        _capability(),  # type: ignore[arg-type]
    )
    print(_format_result(receipt_result))
    print(f"Data -> status='{receipt_result.status}'")


def fr_trd_031() -> None:
    """FR-TRD-031: Stage 3 — Dispatch approved intent to Simulation or Broker target."""
    _header("Stage 3: Dispatch Execution - Dispatch Order Intent (FR-TRD-031)")

    async def simulation_dispatch(intent: OrderIntent):
        return create_execution_receipt(
            receipt_id="usage-sim-receipt-001",
            intent_id=intent.source_intent_id,
            client_order_id=intent.client_order_id,
            route="sim",
            authority="simulator",
            provider_order_id="usage-sim-order-001",
            status="filled",
            requested_quantity=intent.approved_volume,
            filled_quantity=intent.approved_volume,
            authority_timestamp=NOW,
            received_at=NOW,
            response_classification="confirmed",
            retry_safe=False,
            reconciliation_required=False,
            request_id=intent.request_id,
            correlation_id=intent.correlation_id,
        )

    dispatched_receipt = asyncio.run(
        dispatch_order_intent(
            _intent(),
            None,
            None,
            simulation_dispatch,
            operation_timeout_seconds=Decimal(10),
            clock=lambda: NOW,
        )
    )
    print(_format_result(dispatched_receipt))
    print(f"Data -> status='{dispatched_receipt.status}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-TRD-04 — routing/ — Authority Selection and Dispatch\n\n"
        "Purpose: Validate adapter capability declarations, classify authority responses, and dispatch order intents to targets.\n\n"
        "Module flow:\n"
        "-> Stage 1: Order intent preparation and adapter declaration inspection\n"
        "-> Stage 2: Fail-closed adapter validation and authority response classification\n"
        "-> Stage 3: Order intent dispatch to target authority and execution receipt generation"
    )

    # Stage 2: Capability validation & Response classification
    fr_trd_029()
    fr_trd_030()

    # Stage 3: Dispatch execution
    fr_trd_031()


if __name__ == "__main__":
    main()
