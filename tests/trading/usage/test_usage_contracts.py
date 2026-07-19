"""Runnable usage evidence for public Trading contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

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
                "account_id": "usage-account-001",
                "strategy_id": "usage-strategy-001",
                "strategy_version": "v1",
                "source_intent_id": "usage-intent-001",
                "risk_decision_id": "usage-risk-decision-001",
                "action_policy_verdict_id": "usage-verdict-001",
                "eligibility_decision_id": "usage-eligibility-001",
                "symbol": "EURUSD",
                "action": "reduce_exposure",
                "side": "SELL",
                "order_type": "MARKET",
                "approved_volume": "0.25",
                "price": None,
                "stop_price": None,
                "stop_loss": None,
                "take_profit": None,
                "time_in_force": None,
                "expiration": None,
                "reduce_only": True,
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


def test_usage_models_trading_route() -> None:
    """Select one of the three finite execution routes."""
    assert TradingRoute("paper") is TradingRoute.PAPER


def test_usage_contract_version() -> None:
    """Read the sole canonical Trading contract version."""
    assert TRADING_CONTRACT_VERSION == "v1"


def test_usage_models_trading_request() -> None:
    """Validate an immutable governed request at the Trading boundary."""
    request = TradingRequest.model_validate(_request_data())
    assert request.risk_decision_id == "usage-risk-001"


def test_usage_models_standard_envelope() -> None:
    """Return a structured JSON-safe Trading result."""
    envelope = StandardTradingEnvelope(
        status="success",
        message="Trading contract validated",
        data={"route": "sim"},
        errors=(),
        warnings=(),
        audit_metadata={"operation": "usage_example"},
    )
    assert envelope.status == "success"


def test_usage_models_order_intent() -> None:
    """Represent exact Risk-approved executable order material."""
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
    assert intent.approved_volume == intent.risk_approved_volume
    assert intent.quantity_unit == "units"


def test_usage_models_execution_receipt() -> None:
    """Consume immutable authority response evidence."""
    assert _receipt().status == "filled"


def test_usage_models_trade_record() -> None:
    """Package factual execution and reconciliation state."""
    record = TradeRecord(
        record_id="usage-record-001",
        receipt=_receipt(),
        fill_ids=("usage-fill-001",),
        authority_state="confirmed",
        reconciliation_state="reconciled",
        created_at=NOW,
        request_id="usage-request-001",
        workflow_id="usage-workflow-001",
        correlation_id="usage-correlation-001",
    )
    assert record.reconciliation_state == "reconciled"


def test_usage_models_portfolio_rebalance_request() -> None:
    """Validate a receiver-owned authorized rebalance request."""
    request = PortfolioRebalanceExecutionRequest.model_validate(_rebalance_data())
    assert request.actions[0]["reduce_only"] is True


def test_usage_errors_trading_error() -> None:
    """Raise one finite coded and redacted Trading failure."""
    error = TradingError("INVALID_REQUEST", "Request evidence is invalid")
    assert error.trading_code == "INVALID_REQUEST"


def test_usage_errors_map_trading_error() -> None:
    """Map boundary failures without returning raw exceptions."""
    envelope = map_trading_error(
        TimeoutError("provider detail"),
        {"operation": "submit_order", "request_id": "usage-request-001"},
    )
    assert envelope.status == "unknown_outcome"


def test_usage_errors_redact_trading_payload() -> None:
    """Redact nested secret material before boundary use."""
    result = redact_trading_payload({"credentials": {"api_key": "secret"}})
    assert "secret" not in str(result)


def test_usage_registry_get_public_contracts() -> None:
    """Discover the exact stable typed Trading API."""
    assert any(row["symbol"] == "TradingRequest" for row in get_public_contracts())


def test_usage_registry_create_draft() -> None:
    """Package a governed request without invoking route authority."""
    envelope = create_trading_action_draft(_request_data())
    assert envelope.status == "packaged"
