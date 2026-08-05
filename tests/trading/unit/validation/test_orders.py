"""Unit tests for aggregate Trading order validation."""

# ruff: noqa: INP001
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from app.services.data import (
    build_account_order,
    build_account_state_snapshot,
)
from app.services.trading.contracts import TradingRequest
from app.services.trading.validation import validate_order_request

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


def _symbol_capability() -> dict[str, object]:
    """Build explicit Broker feature and symbol metadata evidence."""
    return {
        "supported_order_types": ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
        "quantity_unit": "units",
    }


def _request() -> TradingRequest:
    """Build an invalid order lacking required instrument metadata."""
    return TradingRequest(
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
        route="sim",
        action="submit_order",
        account_id="account-001",
        strategy_id="strategy-001",
        strategy_version="v1",
        intent_id="intent-001",
        symbol="EURUSD",
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity=Decimal("1.00"),
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def _account() -> Any:
    """Build current connected Data-owned account evidence."""
    return build_account_state_snapshot(
        account_id="account-001",
        currency="USD",
        balances=(),
        equity=Decimal(10000),
        margin_available=Decimal(9000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="simulator",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id=("req-dd37fc1c-2cd6-4d66-9f9a-7a7f9a2482ef"),
    )


def test_invalid_order_never_reaches_authority() -> None:
    """Missing precision evidence rejects before any authority interaction."""
    authority_calls = 0
    captured = validate_order_request(_request(), _account(), _symbol_capability())
    assert captured.status == "error"
    assert captured.error is not None
    assert captured.error.code == "VALIDATION_FAILED"
    assert authority_calls == 0
    valid = _request().model_copy(
        update={
            "instrument_min_quantity": Decimal("0.01"),
            "instrument_max_quantity": Decimal("10.00"),
            "instrument_quantity_step": Decimal("0.01"),
        }
    )
    validated = validate_order_request(valid, _account(), _symbol_capability())
    assert validated.status == "success"
    assert validated.data == valid
    invalid_requests = (
        valid.model_copy(update={"quantity": Decimal("11.00")}),
        valid.model_copy(update={"quantity": Decimal("1.005")}),
        valid.model_copy(update={"price": Decimal("1.1000")}),
        valid.model_copy(
            update={
                "price": Decimal("1.1000"),
                "stop_loss": Decimal("1.2000"),
                "instrument_price_tick": Decimal("0.0001"),
            }
        ),
    )
    for invalid in invalid_requests:
        result = validate_order_request(invalid, _account(), _symbol_capability())
        assert result.status == "error"
    unsupported = {"supported_order_types": ["LIMIT"], "quantity_unit": "units"}
    unsupported_error = validate_order_request(valid, _account(), unsupported)
    assert unsupported_error.status == "error"
    assert unsupported_error.error is not None
    assert unsupported_error.error.code == "VALIDATION_FAILED"
    mismatched_unit = {
        "supported_order_types": ["MARKET"],
        "quantity_unit": "lots",
    }
    unit_error = validate_order_request(valid, _account(), mismatched_unit)
    assert unit_error.status == "error"
    assert unit_error.error is not None
    assert unit_error.error.code == "VALIDATION_FAILED"
    order = build_account_order(
        order_id="order-001",
        symbol="EURUSD",
        side="BUY",
        state="pending",
        quantity=Decimal("1.00"),
    )
    addressed_account = build_account_state_snapshot(
        account_id="account-001",
        currency="USD",
        balances=(),
        equity=Decimal(10000),
        margin_available=Decimal(9000),
        positions=(
            {
                "position_id": "position-001",
                "symbol": "EURUSD",
                "side": "LONG",
                "quantity": Decimal("1.00"),
            },
        ),
        orders=(order,),
        connected=True,
        trading_allowed=True,
        source_id="simulator",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-dd37fc1c-2cd6-4d66-9f9a-7a7f9a2482ef",
    )
    modify_order = valid.model_copy(
        update={
            "action": "modify_order",
            "order_id": "order-001",
            "target_broker_order_id": "broker-order-001",
        }
    )
    missing_version = validate_order_request(
        modify_order,
        addressed_account,
        _symbol_capability(),
    )
    assert missing_version.status == "error"
    assert missing_version.error is not None
    assert missing_version.error.code == "VERSION_CONFLICT"
    close_position = valid.model_copy(
        update={
            "action": "close_position",
            "position_id": "position-missing",
            "target_broker_position_id": "broker-position-missing",
        }
    )
    close_result = validate_order_request(
        close_position,
        addressed_account,
        _symbol_capability(),
    )
    assert close_result.status == "error"
    assert close_result.error is not None
    assert close_result.error.code == "VALIDATION_FAILED"
