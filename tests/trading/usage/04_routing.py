"""Executable Trading routing usage example.

Demonstrates adapter capabilities and order dispatch.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading.contracts import ExecutionReceipt, OrderIntent
from app.services.trading.routing import (
    classify_authority_response,
    dispatch_order_intent,
    validate_adapter_capability,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _intent() -> OrderIntent:
    """Build one complete simulation executable intent."""
    return OrderIntent(
        client_order_id="usage-client-order-001",
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
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


def example_routing() -> None:
    """Demonstrate Trading routing API."""
    print("=" * 80)
    print("Trading Example 4: Adapter Capabilities and Order Dispatch")
    print("=" * 80)

    # 1. Validate adapter capability
    validate_adapter_capability(  # type: ignore[arg-type]
        _paper_intent(),
        _capability(),
        operation_timeout_seconds=Decimal(10),
    )
    print("Validated adapter capability successfully")

    # 2. Classify authority response
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
        "request_id": "usage-request-001",
        "correlation_id": "usage-correlation-001",
        "authority_timestamp": NOW.isoformat(),
        "received_at": NOW.isoformat(),
    }
    receipt = classify_authority_response(  # type: ignore[arg-type]
        raw,
        _capability(),  # type: ignore[arg-type]
    )
    print(f"Classified authority response status: {receipt.status}")

    # 3. Dispatch order intent
    async def simulation_dispatch(intent: OrderIntent) -> ExecutionReceipt:
        return ExecutionReceipt(
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
    print(f"Dispatched order intent receipt status: {dispatched_receipt.status}")


def main() -> None:
    """Run Trading routing usage example."""
    example_routing()


if __name__ == "__main__":
    main()
