"""Unit tests for immutable Trading contract models."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

import pytest
from app.services.trading.contracts import (
    TRADING_CONTRACT_VERSION,
    ExecutionReceipt,
    OrderIntent,
    PortfolioRebalanceExecutionRequest,
    StandardTradingEnvelope,
    TradeRecord,
    TradingRequest,
    TradingRoute,
)
from app.utils import canonical_json
from pydantic import ValidationError

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _request_data() -> dict[str, object]:
    """Return complete governed Trading request material."""
    return {
        "request_id": "req-001",
        "workflow_id": "wf-001",
        "correlation_id": "corr-001",
        "route": TradingRoute.SIM,
        "action": "submit_order",
        "provider_id": None,
        "account_id": "account-001",
        "strategy_id": "strategy-001",
        "strategy_version": "v1",
        "intent_id": "source-intent-001",
        "symbol": "EURUSD",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity_unit": "units",
        "quantity": Decimal("1.00"),
        "risk_decision_id": "risk-001",
        "action_policy_verdict_id": "verdict-001",
        "approval_token_ref": "approval-001",
        "idempotency_key": "caller-key-001",
        "canonical_material_version": "v1",
        "system_time": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }


def _receipt(*, reconciliation_required: bool = False) -> ExecutionReceipt:
    """Return a valid execution receipt."""
    return ExecutionReceipt(
        receipt_id="receipt-001",
        intent_id="intent-001",
        client_order_id="client-order-001",
        route=TradingRoute.SIM,
        authority="simulator",
        provider_order_id="authority-order-001",
        status="filled",
        requested_quantity=Decimal("1.00"),
        filled_quantity=Decimal("1.00"),
        average_price=Decimal("1.10000"),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="confirmed",
        retry_safe=False,
        reconciliation_required=reconciliation_required,
        request_id="req-001",
        correlation_id="corr-001",
    )


def _rebalance_data() -> dict[str, object]:
    """Return canonically hashed rebalance material."""
    actions = (
        {
            "action_id": "action-001",
            "component_id": "strategy-001",
            "eligibility_decision_id": "eligibility-001",
            "action": "reduce_exposure",
            "reduce_only": True,
            "current_exposure": "0.60",
            "target_exposure": "0.50",
            "reduction_amount": "0.10",
        },
    )
    data: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "trading.portfolio_rebalance_execution_request.v1",
        "request_id": "rebalance-req-001",
        "workflow_id": "wf-rebalance-001",
        "correlation_id": "corr-rebalance-001",
        "plan_id": "plan-001",
        "plan_version": "v3",
        "portfolio_id": "portfolio-001",
        "allocation_version": "allocation-v7",
        "allocation_decision_id": "allocation-decision-001",
        "eligibility_decision_ids": ("eligibility-001",),
        "actions": actions,
        "route": TradingRoute.SIM,
        "approval_token_ref": "approval-rebalance-001",
        "canonical_material_version": "v1",
        "valid_from": NOW,
        "valid_until": NOW + timedelta(minutes=5),
    }
    data["canonical_hash"] = sha256(canonical_json(data).encode()).hexdigest()
    return data


def test_trading_route_rejects_unknown() -> None:
    """Only sim, paper, and live are valid routes."""
    with pytest.raises(ValueError, match="not a valid TradingRoute"):
        TradingRoute("package")


def test_trading_request_requires_governed_evidence() -> None:
    """Canonical requests require approval and Risk evidence."""
    data = _request_data()
    data.pop("risk_decision_id")
    with pytest.raises(ValidationError):
        TradingRequest.model_validate(data)
    unsafe = _request_data()
    unsafe["quantity"] = 1.0
    with pytest.raises(TypeError, match="cannot be a float"):
        TradingRequest.model_validate(unsafe)


def test_standard_envelope_status_contract() -> None:
    """Failure statuses require structured failure evidence."""
    with pytest.raises(ValidationError):
        StandardTradingEnvelope(
            status="error",
            message="Trading failed",
            data=None,
            errors=(),
            warnings=(),
            audit_metadata={"operation": "unit_test"},
        )


def test_envelope_rejects_unredacted_sensitive_keys() -> None:
    """A true redaction marker cannot accompany protected payload keys."""
    with pytest.raises(ValidationError, match="unredacted sensitive keys"):
        StandardTradingEnvelope(
            status="success",
            message="Unsafe evidence",
            data={"nested": {"access_token": "secret"}},
            errors=(),
            warnings=(),
            audit_metadata={"operation": "unit", "redaction_applied": True},
        )


def test_contract_version_is_canonical() -> None:
    """Every Trading-owned model uses the one exported contract version."""
    assert TRADING_CONTRACT_VERSION == "v1"
    assert TradingRequest.model_validate(_request_data()).contract_version == (
        TRADING_CONTRACT_VERSION
    )


def test_order_intent_cannot_exceed_risk_size() -> None:
    """Executable size must equal the exact Risk-approved size."""
    with pytest.raises(ValidationError):
        OrderIntent(
            client_order_id="client-order-001",
            request_id="req-001",
            workflow_id="wf-001",
            correlation_id="corr-001",
            route=TradingRoute.SIM,
            provider_id=None,
            account_id="account-001",
            strategy_id="strategy-001",
            strategy_version="v1",
            source_intent_id="source-intent-001",
            symbol="EURUSD",
            action="submit_order",
            side="BUY",
            order_type="MARKET",
            quantity_unit="units",
            approved_volume=Decimal("1.01"),
            risk_approved_volume=Decimal("1.00"),
            idempotency_hash="a" * 64,
            canonical_material_version="v1",
            risk_decision_id="risk-001",
            action_policy_verdict_id="verdict-001",
            approval_token_ref="approval-001",
            created_at=NOW,
            valid_until=NOW + timedelta(minutes=5),
        )


def test_order_intent_preserves_stop_limit_execution_material() -> None:
    """Executable stop-limit fields remain explicit and unmodified."""
    intent = OrderIntent(
        client_order_id="client-order-002",
        request_id="req-002",
        workflow_id="wf-002",
        correlation_id="corr-002",
        route=TradingRoute.SIM,
        provider_id=None,
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        source_intent_id="source-intent-002",
        symbol="EURUSD",
        action="submit_order",
        side="BUY",
        order_type="STOP_LIMIT",
        quantity_unit="units",
        approved_volume=Decimal("1.00"),
        risk_approved_volume=Decimal("1.00"),
        price=Decimal("1.10200"),
        stop_price=Decimal("1.10100"),
        time_in_force="GTD",
        expiration=NOW + timedelta(minutes=4),
        idempotency_hash="c" * 64,
        canonical_material_version="v1",
        risk_decision_id="risk-002",
        action_policy_verdict_id="verdict-002",
        approval_token_ref="approval-002",
        created_at=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )

    assert intent.order_type == "STOP_LIMIT"
    assert intent.stop_price == Decimal("1.10100")


def test_gtd_order_intent_requires_expiration() -> None:
    """GTD execution material cannot omit its expiration timestamp."""
    data = _request_data()
    data["time_in_force"] = "GTD"
    with pytest.raises(ValidationError, match="GTD requests require expiration"):
        TradingRequest.model_validate(data)


def test_receipt_requires_authority_evidence() -> None:
    """Acknowledged authority outcomes require an authority order identity."""
    data = _receipt().model_dump()
    data["provider_order_id"] = None
    with pytest.raises(ValidationError):
        ExecutionReceipt.model_validate(data)


def test_trade_record_flags_unreconciled_state() -> None:
    """A receipt requiring reconciliation cannot be recorded as reconciled."""
    with pytest.raises(ValidationError):
        TradeRecord(
            record_id="record-001",
            receipt=_receipt(reconciliation_required=True),
            fill_ids=("fill-001",),
            authority_state="confirmed",
            reconciliation_state="reconciled",
            created_at=NOW,
            request_id="req-001",
            workflow_id="wf-001",
            correlation_id="corr-001",
        )


def test_rebalance_request_requires_canonical_hash() -> None:
    """Rebalance requests bind all ordered material to the canonical hash."""
    data = _rebalance_data()
    request = PortfolioRebalanceExecutionRequest.model_validate(data)
    assert request.canonical_hash == data["canonical_hash"]
    data["plan_version"] = "v4"
    with pytest.raises(ValidationError):
        PortfolioRebalanceExecutionRequest.model_validate(data)
