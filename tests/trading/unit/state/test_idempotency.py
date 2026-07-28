"""Unit tests for Trading caller-key idempotency."""

# ruff: noqa: INP001
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.trading.contracts import TradingRequest
from app.services.trading.state import IdempotencyReservation, reserve_idempotency

NOW = datetime(2026, 7, 19, 8, 0, tzinfo=UTC)


class _ReservationStore:
    """Atomic reservation fake for idempotency behavior."""

    def __init__(self) -> None:
        """Initialize without a reservation."""
        self.reservation: IdempotencyReservation | None = None

    def reserve_idempotency(
        self,
        key: str,
        material_hash: str,
        material_version: str,
        reserved_at: datetime,
        expires_at: datetime,
    ) -> IdempotencyReservation:
        """Return new, duplicate-active, or conflict atomically."""
        if self.reservation is None:
            self.reservation = IdempotencyReservation(
                key=key,
                material_hash=material_hash,
                material_version=material_version,
                status="new",
                reserved_at=reserved_at,
                expires_at=expires_at,
            )
            return self.reservation
        status = (
            "duplicate_active"
            if self.reservation.material_hash == material_hash
            else "conflict"
        )
        return self.reservation.model_copy(update={"status": status})

    def complete_idempotency(self, *args: object, **kwargs: object) -> None:
        """Accept completion calls outside this reservation-focused test."""
        del args, kwargs


def _request(*, symbol: str = "EURUSD") -> TradingRequest:
    """Build a canonical request with one fixed caller key."""
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
        symbol=symbol,
        side="BUY",
        order_type="MARKET",
        quantity_unit="units",
        quantity="1.00",
        risk_decision_id="risk-001",
        action_policy_verdict_id="verdict-001",
        approval_token_ref="approval-001",
        idempotency_key="caller-key-001",
        canonical_material_version="v1",
        system_time=NOW,
        valid_until=NOW + timedelta(minutes=5),
    )


def test_same_key_different_material_rejected() -> None:
    """A caller key cannot authorize different canonical request material."""
    store = _ReservationStore()
    first = reserve_idempotency(
        _request(),
        store,  # type: ignore[arg-type]
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    assert first.status == "success"
    assert first.data is not None
    assert first.data.status == "new"
    captured = reserve_idempotency(
        _request(symbol="GBPUSD"),
        store,  # type: ignore[arg-type]
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    assert captured.status == "error"
    assert captured.error is not None
    assert captured.error.code == "IDEMPOTENCY_CONFLICT"


def test_reservation_states_are_finite() -> None:
    """Reservation status rejects states outside the declared finite set."""
    with pytest.raises(ValueError, match="validation error"):
        IdempotencyReservation(
            key="key-001",
            material_hash="a" * 64,
            material_version="v1",
            status="invented",  # type: ignore[arg-type]
            reserved_at=NOW,
            expires_at=NOW + timedelta(seconds=1),
        )


def test_active_lock_exact_bound_passes_and_past_bound_fails() -> None:
    """Exact lock age remains active while older work fails closed."""
    store = _ReservationStore()
    reserve_idempotency(
        _request(),
        store,  # type: ignore[arg-type]
        reservation_time=NOW,
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    exact_response = reserve_idempotency(
        _request(),
        store,  # type: ignore[arg-type]
        reservation_time=NOW + timedelta(seconds=30),
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    assert exact_response.status == "success"
    assert exact_response.data is not None
    assert exact_response.data.status == "duplicate_active"
    stale = reserve_idempotency(
        _request(),
        store,  # type: ignore[arg-type]
        reservation_time=NOW + timedelta(seconds=31),
        retention_seconds=300,
        concurrency_lock_timeout_seconds=Decimal(30),
    )
    assert stale.status == "error"
    assert stale.error is not None
    assert stale.error.code == "TRADING_CONCURRENCY_CONFLICT"
