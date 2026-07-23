"""Executable Trading contracts usage example.

Demonstrates public Trading contracts, route selection, and validation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.trading.contracts import (
    TRADING_CONTRACT_VERSION,
    ExecutionReceipt,
    OrderIntent,
    PortfolioRebalanceExecutionRequest,
    StandardTradingEnvelope,
    TradeRecord,
    TradingError,
    TradingRequest,
    TradingRoute,
    create_trading_action_draft,
    get_public_contracts,
    map_trading_error,
    redact_trading_payload,
)
from app.utils import canonical_json

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _request_data() -> dict[str, object]:
    """Build complete canonical request material for usage examples."""
    return {
        "request_id": "usage-request-001",
        "workflow_id": "usage-workflow-001",
        "correlation_id": "usage-correlation-001",
        "route": "sim",
        "action": "submit_order",
        "provider_id": None,
        "account_id": "usage-account-001",
        "strategy_id": "usage-strategy-001",
        "strategy_version": "v1",
        "intent_id": "usage-source-intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "units",
        "quantity": "1.00",
        "risk_decision_id": "usage-risk-001",
        "action_policy_verdict_id": "usage-verdict-001",
        "approval_token_ref": "usage-approval-001",
        "idempotency_key": "usage-idempotency-001",
        "canonical_material_version": "v1",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }


def _receipt() -> ExecutionReceipt:
    """Build a confirmed simulator receipt for usage examples."""
    return ExecutionReceipt(
        receipt_id="usage-receipt-001",
        intent_id="usage-intent-001",
        client_order_id="usage-order-001",
        route=TradingRoute.SIM,
        authority="simulator",
        provider_order_id="sim-order-001",
        status="filled",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal("1.00"),
        average_price=Decimal("1.10000"),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="confirmed",
        retry_safe=False,
        reconciliation_required=False,
        request_id="usage-request-001",
        correlation_id="usage-correlation-001",
    )


def _rebalance_data() -> dict[str, object]:
    """Build a canonically bound portfolio rebalance request."""
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "usage-rebalance-001",
        "workflow_id": "usage-workflow-001",
        "correlation_id": "usage-correlation-001",
        "plan_id": "usage-plan-001",
        "plan_version": "v1",
        "portfolio_id": "usage-portfolio-001",
        "allocation_version": "allocation-v1",
        "allocation_decision_id": "usage-allocation-decision-001",
        "eligibility_decision_ids": ("usage-eligibility-001",),
        "actions": (
            {
                "action_id": "usage-action-001",
                "component_id": "usage-strategy-001",
                "eligibility_decision_id": "usage-eligibility-001",
                "action": "reduce_exposure",
                "reduce_only": True,
                "current_exposure": "0.50",
                "target_exposure": "0.25",
                "reduction_amount": "0.25",
            },
        ),
        "route": TradingRoute.SIM,
        "approval_token_ref": "usage-approval-001",
        "canonical_material_version": "v1",
        "valid_from": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    return data


def example_contracts() -> None:
    """Demonstrate Trading contracts and helper models."""
    print("=" * 80)
    print("Trading Example 1: Boundary Contracts and Validation")
    print("=" * 80)

    print(f"Trading contract version: {TRADING_CONTRACT_VERSION}")
    print(f"Selected route: {TradingRoute('paper').value}")

    request = TradingRequest.model_validate(_request_data())
    print(f"Validated TradingRequest risk_decision_id: {request.risk_decision_id}")

    envelope = StandardTradingEnvelope(
        status="success",
        message="Trading contract validated",
        data={"route": "sim"},
        errors=(),
        warnings=(),
        audit_metadata={"operation": "usage_example"},
    )
    print(f"StandardTradingEnvelope status: {envelope.status}")

    intent = OrderIntent(
        client_order_id="usage-order-001",
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
        route=TradingRoute.SIM,
        provider_id=None,
        account_id="usage-account-001",
        strategy_id="usage-strategy-001",
        strategy_version="v1",
        source_intent_id="usage-source-intent-001",
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
    print(f"OrderIntent client_order_id: {intent.client_order_id}")

    receipt = _receipt()
    print(f"ExecutionReceipt status: {receipt.status}")

    record = TradeRecord(
        record_id="usage-record-001",
        receipt=receipt,
        fill_ids=("usage-fill-001",),
        authority_state="confirmed",
        reconciliation_state="reconciled",
        created_at=NOW,
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
    )
    print(f"TradeRecord reconciliation_state: {record.reconciliation_state}")

    rebalance = PortfolioRebalanceExecutionRequest.model_validate(_rebalance_data())
    print(f"Rebalance request plan_id: {rebalance.plan_id}")

    error = TradingError("INVALID_REQUEST", "Request evidence is invalid")
    print(f"TradingError code: {error.trading_code}")

    mapped = map_trading_error(
        TimeoutError("provider detail"),
        {"operation": "submit_order", "request_id": "usage-request-001"},
    )
    print(f"Mapped trading error envelope status: {mapped.status}")

    redacted = redact_trading_payload({"credentials": {"api_key": "secret"}})
    print(f"Redacted payload: {redacted}")

    contracts = get_public_contracts()
    print(f"Discovered public contracts count: {len(contracts)}")

    draft = create_trading_action_draft(_request_data())
    print(f"Created action draft status: {draft.status}")


def main() -> None:
    """Run Trading contracts usage example."""
    example_contracts()


if __name__ == "__main__":
    main()
