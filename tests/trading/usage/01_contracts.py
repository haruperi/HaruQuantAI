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

from app.services.trading import (
    TRADING_CONTRACT_VERSION,
    ExecutionReceipt,
    OrderIntent,
    PortfolioRebalanceExecutionRequest,
    TradeRecord,
    TradingError,
    TradingRequest,
    TradingRoute,
    create_trading_action_draft,
    get_public_contracts,
    map_trading_error,
    redact_trading_payload,
)
from app.utils import (
    RiskLevel,
    StandardResponse,
    build_response_metadata,
    canonical_json,
)

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _request_data() -> dict[str, object]:
    """Build complete canonical request material for usage examples."""
    return {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def _rebalance_data() -> dict[str, object]:
    """Build a canonically bound portfolio rebalance request."""
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "req-77777777-7777-4777-8777-777777777777",
        "workflow_id": "wf-22222222-2222-4222-8222-222222222222",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
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
    _header("Demonstrate Trading contracts and helper models.")
    print("Trading Example 1: Boundary Contracts and Validation")

    print(f"Trading contract version: {TRADING_CONTRACT_VERSION}")
    print(f"Selected route: {TradingRoute('paper').value}")

    request = TradingRequest.model_validate(_request_data())
    print(f"Validated TradingRequest risk_decision_id: {request.risk_decision_id}")

    envelope = StandardResponse(
        status="success",
        message="Trading contract validated",
        data={"route": "sim"},
        error=None,
        metadata=build_response_metadata(
            name="trading.usage_contract",
            domain="trading",
            risk_level=RiskLevel.LOW,
            request_id="req-11111111-1111-4111-8111-111111111111",
            start_time=1,
            read_only=True,
            writes_file=False,
            modifies_database=False,
            places_trade=False,
            requires_network=False,
        ),
    )
    print(f"StandardResponse status: {envelope.status}")

    intent = OrderIntent(
        client_order_id="usage-order-001",
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )
    print(f"TradeRecord reconciliation_state: {record.reconciliation_state}")

    rebalance = PortfolioRebalanceExecutionRequest.model_validate(_rebalance_data())
    print(f"Rebalance request plan_id: {rebalance.plan_id}")

    error = TradingError("INVALID_REQUEST", "Request evidence is invalid")
    print(f"TradingError code: {error.trading_code}")

    mapped = map_trading_error(
        TimeoutError("provider detail"),
        {
            "operation": "submit_order",
            "request_id": "req-11111111-1111-4111-8111-111111111111",
        },
    )
    print(f"Mapped trading error envelope status: {mapped.status}")

    redacted = redact_trading_payload({"credentials": {"api_key": "secret"}})
    print(f"Redacted payload: {redacted.data}")

    contracts = get_public_contracts()
    print(f"Discovered public contracts count: {len(contracts.data or ())}")

    draft = create_trading_action_draft(_request_data())
    print(f"Created action draft status: {draft.status}")


def fr_trd_001() -> None:
    """FR-TRD-001: The system shall expose only `sim`, `paper`, and `live` action routes; package-only is a side-effect mode, not a route."""
    _header(
        "FR-TRD-001: The system shall expose only `sim`, `paper`, and `live` action routes; package-only is a side-effect mode, not a route."
    )
    example_contracts()


def fr_trd_002() -> None:
    """FR-TRD-002: The system shall validate one immutable canonical request with route, action, trace, authority, approval, Risk, idempotency, UTC evidence, approved `order_type`, validated instrument `quantity_unit`, optional stop/TIF/expiration material, and nullable Trading-state broker target identities."""
    _header(
        "FR-TRD-002: The system shall validate one immutable canonical request with route, action, trace, authority, approval, Risk, idempotency, UTC evidence, approved `order_type`, validated instrument `quantity_unit`, optional stop/TIF/expiration material, and nullable Trading-state broker target identities."
    )
    example_contracts()


def fr_trd_003() -> None:
    """FR-TRD-003: The system shall return one finite JSON-safe envelope distinguishing packaging, rejection, block, send, fill, cancellation, unknown outcome, and error."""
    _header(
        "FR-TRD-003: The system shall return one finite JSON-safe envelope distinguishing packaging, rejection, block, send, fill, cancellation, unknown outcome, and error."
    )
    example_contracts()


def fr_trd_004() -> None:
    """FR-TRD-004: The system shall expose complete deterministic `OrderIntent v1` exactly as defined in Section 1, preserving Risk-approved size, approved order type, validated quantity unit, optional order instructions, and Trading-state broker target identities without connection material."""
    _header(
        "FR-TRD-004: The system shall expose complete deterministic `OrderIntent v1` exactly as defined in Section 1, preserving Risk-approved size, approved order type, validated quantity unit, optional order instructions, and Trading-state broker target identities without connection material."
    )
    example_contracts()


def fr_trd_005() -> None:
    """FR-TRD-005: The system shall expose immutable `ExecutionReceipt v1` with authority, status, fill, retry, and reconciliation evidence."""
    _header(
        "FR-TRD-005: The system shall expose immutable `ExecutionReceipt v1` with authority, status, fill, retry, and reconciliation evidence."
    )
    example_contracts()


def fr_trd_006() -> None:
    """FR-TRD-006: The system shall expose `TradeRecord v1` without deriving Analytics metrics or hiding unreconciled state."""
    _header(
        "FR-TRD-006: The system shall expose `TradeRecord v1` without deriving Analytics metrics or hiding unreconciled state."
    )
    example_contracts()


def fr_trd_007() -> None:
    """FR-TRD-007: The system shall expose one finite Trading exception carrying a registered code and redacted trace context."""
    _header(
        "FR-TRD-007: The system shall expose one finite Trading exception carrying a registered code and redacted trace context."
    )
    example_contracts()


def fr_trd_008() -> None:
    """FR-TRD-008: The system shall map validation, permission, persistence, timeout, provider, and unknown failures into the canonical envelope without raw exceptions."""
    _header(
        "FR-TRD-008: The system shall map validation, permission, persistence, timeout, provider, and unknown failures into the canonical envelope without raw exceptions."
    )
    example_contracts()


def fr_trd_009() -> None:
    """FR-TRD-009: The system shall recursively redact secrets before any log, error, event, metric, or returned payload."""
    _header(
        "FR-TRD-009: The system shall recursively redact secrets before any log, error, event, metric, or returned payload."
    )
    example_contracts()


def fr_trd_010() -> None:
    """FR-TRD-010: The system shall return the exact stable Python API with routes, schemas, side effects, approvals, idempotency, statuses, errors, and stability metadata."""
    _header(
        "FR-TRD-010: The system shall return the exact stable Python API with routes, schemas, side effects, approvals, idempotency, statuses, errors, and stability metadata."
    )
    example_contracts()


def fr_trd_012() -> None:
    """FR-TRD-012: The system shall create a non-executable action draft that cannot call a route authority."""
    _header(
        "FR-TRD-012: The system shall create a non-executable action draft that cannot call a route authority."
    )
    example_contracts()


def fr_trd_063() -> None:
    """FR-TRD-063: The system shall expose `PortfolioRebalanceExecutionRequest v1` exactly as defined in §1 (plan/allocation/decision references, ordered actions, reduce-only flags, route, approval token, validity, canonical hash) carrying `contract_version="v1"` and `schema_id="trading.portfolio_rebalance_execution_request.v1"`."""
    _header(
        "FR-TRD-063: The system shall expose `PortfolioRebalanceExecutionRequest v1` exactly as defined in §1 (plan/allocation/decision references, ordered actions, reduce-only flags, route, approval token, validity, canonical hash) carrying `contract_version='v1'` and `schema_id='trading.portfolio_rebalance_execution_request.v1'`."
    )
    example_contracts()


def fr_trd_066() -> None:
    """FR-TRD-066: The system shall expose one canonical `TRADING_CONTRACT_VERSION="v1"` constant used by every Trading-owned versioned contract and report schema. `FR-TRD-011` remains retired with `CAP-TRD-022` and is not reused."""
    _header(
        "FR-TRD-066: The system shall expose one canonical `TRADING_CONTRACT_VERSION='v1'` constant used by every Trading-owned versioned contract and report schema. `FR-TRD-011` remains retired with `CAP-TRD-022` and is not reused."
    )
    example_contracts()


def main() -> None:
    """Run Trading contracts usage example."""
    example_contracts()


if __name__ == "__main__":
    main()
