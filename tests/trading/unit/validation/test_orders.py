"""Unit tests for aggregate Trading order validation."""

# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.evidence.account_contracts import (
    AccountOrder,
    AccountPosition,
    AccountStateSnapshot,
)
from app.services.trading.contracts import TradingError, TradingRequest
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
        request_id="request-001",
        workflow_id="workflow-001",
        correlation_id="correlation-001",
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


def _account() -> AccountStateSnapshot:
    """Build current connected Data-owned account evidence."""
    return AccountStateSnapshot(
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
        request_id=(
            "req-dd37fc1c2cd6d665f9a7a7f9a2482efe3347c7bb51ac073ef12ef9b7eb511055"
        ),
    )


def test_invalid_order_never_reaches_authority() -> None:
    """Missing precision evidence rejects before any authority interaction."""
    authority_calls = 0
    with pytest.raises(TradingError) as captured:
        validate_order_request(_request(), _account(), _symbol_capability())
    assert captured.value.trading_code == "VALIDATION_FAILED"
    assert authority_calls == 0
    valid = _request().model_copy(
        update={
            "instrument_min_quantity": Decimal("0.01"),
            "instrument_max_quantity": Decimal("10.00"),
            "instrument_quantity_step": Decimal("0.01"),
        }
    )
    assert validate_order_request(valid, _account(), _symbol_capability()) is valid
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
        with pytest.raises(TradingError):
            validate_order_request(invalid, _account(), _symbol_capability())
    unsupported = {"supported_order_types": ["LIMIT"], "quantity_unit": "units"}
    with pytest.raises(TradingError) as unsupported_error:
        validate_order_request(valid, _account(), unsupported)
    assert unsupported_error.value.trading_code == "VALIDATION_FAILED"
    mismatched_unit = {
        "supported_order_types": ["MARKET"],
        "quantity_unit": "lots",
    }
    with pytest.raises(TradingError) as unit_error:
        validate_order_request(valid, _account(), mismatched_unit)
    assert unit_error.value.trading_code == "VALIDATION_FAILED"
    order = AccountOrder(
        order_id="order-001",
        symbol="EURUSD",
        side="BUY",
        state="pending",
        quantity=Decimal("1.00"),
    )
    position = AccountPosition(
        position_id="position-001",
        symbol="EURUSD",
        side="LONG",
        quantity=Decimal("1.00"),
    )
    addressed_account = _account().model_copy(
        update={"orders": (order,), "positions": (position,)}
    )
    modify_order = valid.model_copy(
        update={
            "action": "modify_order",
            "order_id": "order-001",
            "target_broker_order_id": "broker-order-001",
        }
    )
    with pytest.raises(TradingError) as missing_version:
        validate_order_request(
            modify_order,
            addressed_account,
            _symbol_capability(),
        )
    assert missing_version.value.trading_code == "VERSION_CONFLICT"
    close_position = valid.model_copy(
        update={
            "action": "close_position",
            "position_id": "position-missing",
            "target_broker_position_id": "broker-position-missing",
        }
    )
    with pytest.raises(TradingError, match="VALIDATION_FAILED"):
        validate_order_request(
            close_position,
            addressed_account,
            _symbol_capability(),
        )
