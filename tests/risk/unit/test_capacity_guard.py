"""Unit evidence for the durable Risk concurrent-capacity reservation guard."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.risk.capacity import runtime as capacity_runtime
from app.services.risk.capacity.runtime import _DurableCapacityGuard

_NOW = datetime(2026, 8, 14, tzinfo=UTC)


def _row(reservation_key: str) -> dict[str, object]:
    """Build one minimal active-reservation row."""
    return {
        "reservation_key": reservation_key,
        "requested_notional": "1000",
        "expires_at": (_NOW + timedelta(minutes=5)).isoformat(),
    }


def test_reserve_capacity_reserves_when_scope_is_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty scope is reserved and persisted exactly once."""
    created: list[dict[str, object]] = []
    monkeypatch.setattr(
        capacity_runtime, "read_active_capacity_reservations", lambda *_a, **_k: ()
    )
    monkeypatch.setattr(
        capacity_runtime,
        "create_capacity_reservation",
        lambda **kwargs: created.append(kwargs),
    )

    outcome = _DurableCapacityGuard().reserve_capacity(
        reservation_key="key-one",
        account_id="account-one",
        strategy_id="strategy-one",
        symbol="EURUSD",
        requested_notional=Decimal(1000),
        expires_at=_NOW + timedelta(minutes=5),
        timeout_seconds=None,
    )

    assert outcome == "reserved"
    assert created[0]["reservation_key"] == "key-one"


def test_reserve_capacity_replays_the_same_key_idempotently(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A retried call with the identical key is the same reservation."""
    monkeypatch.setattr(
        capacity_runtime,
        "read_active_capacity_reservations",
        lambda *_a, **_k: (_row("key-one"),),
    )

    def _fail_create(**_kwargs: object) -> None:
        raise AssertionError("must not attempt to create a duplicate reservation")

    monkeypatch.setattr(capacity_runtime, "create_capacity_reservation", _fail_create)

    outcome = _DurableCapacityGuard().reserve_capacity(
        reservation_key="key-one",
        account_id="account-one",
        strategy_id="strategy-one",
        symbol="EURUSD",
        requested_notional=Decimal(1000),
        expires_at=_NOW + timedelta(minutes=5),
        timeout_seconds=None,
    )

    assert outcome == "already_reserved"


def test_reserve_capacity_conflicts_with_a_different_active_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two different proposals cannot both hold the same exact scope."""
    monkeypatch.setattr(
        capacity_runtime,
        "read_active_capacity_reservations",
        lambda *_a, **_k: (_row("key-other"),),
    )

    outcome = _DurableCapacityGuard().reserve_capacity(
        reservation_key="key-one",
        account_id="account-one",
        strategy_id="strategy-one",
        symbol="EURUSD",
        requested_notional=Decimal(1000),
        expires_at=_NOW + timedelta(minutes=5),
        timeout_seconds=None,
    )

    assert outcome == "conflict"


def test_reserve_capacity_conflicts_when_insert_races(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A losing insert race is a conflict, not an unhandled error."""
    monkeypatch.setattr(
        capacity_runtime, "read_active_capacity_reservations", lambda *_a, **_k: ()
    )

    def _raise_conflict(**_kwargs: object) -> None:
        raise ValueError("Risk capacity reservation identity conflict")

    monkeypatch.setattr(
        capacity_runtime, "create_capacity_reservation", _raise_conflict
    )

    outcome = _DurableCapacityGuard().reserve_capacity(
        reservation_key="key-one",
        account_id="account-one",
        strategy_id="strategy-one",
        symbol="EURUSD",
        requested_notional=Decimal(1000),
        expires_at=_NOW + timedelta(minutes=5),
        timeout_seconds=None,
    )

    assert outcome == "conflict"
