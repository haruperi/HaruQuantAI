"""Tests for memory-only Trading execution-position state."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.trading import (
    create_execution_position,
    create_execution_position_store,
    get_execution_position,
    get_execution_position_snapshot,
    set_execution_position,
    transition_execution_position,
)
from app.services.trading.contracts import TradingError


def _open_position() -> object:
    """Return one valid initial position."""
    return create_execution_position(
        position_id="position-001",
        account_id="account-001",
        symbol="EURUSD",
        broker_position_id="broker-position-001",
        state="OPEN",
        quantity=Decimal("1.00"),
        average_entry_price=Decimal("1.10"),
        source_sequence=1,
        version=1,
    )


def test_position_state_is_process_local_and_transitions_deterministically() -> None:
    """The in-memory port applies an allowed newer transition."""
    store = create_execution_position_store()
    set_execution_position(store, _open_position())

    reduced = transition_execution_position(
        store,
        "position-001",
        state="REDUCING",
        quantity=Decimal("0.50"),
        source_sequence=2,
    )

    assert reduced.state == "REDUCING"
    assert reduced.version == 2
    assert get_execution_position(store, "position-001") == reduced
    assert get_execution_position_snapshot(store)["position-001"]["quantity"] == "0.50"


def test_unknown_state_requires_reason_and_cannot_increase_exposure() -> None:
    """Unknown state is visible and blocks exposure-increasing recovery."""
    store = create_execution_position_store()
    set_execution_position(store, _open_position())
    unknown = transition_execution_position(
        store,
        "position-001",
        state="UNKNOWN",
        quantity=Decimal("1.00"),
        source_sequence=2,
        unknown_reason="restart_requires_authority_reconciliation",
    )

    assert unknown.state == "UNKNOWN"
    with pytest.raises(TradingError) as captured:
        transition_execution_position(
            store,
            "position-001",
            state="OPEN",
            quantity=Decimal("1.01"),
            source_sequence=3,
        )
    assert captured.value.code == "RECONCILIATION_REQUIRED"


def test_stale_or_invalid_transition_fails_closed() -> None:
    """Stale sequences and unsupported state edges are rejected."""
    store = create_execution_position_store()
    set_execution_position(store, _open_position())

    with pytest.raises(TradingError) as invalid:
        transition_execution_position(
            store,
            "position-001",
            state="FLAT",
            quantity=Decimal(0),
            source_sequence=2,
        )
    assert invalid.value.code == "VALIDATION_FAILED"
    with pytest.raises(TradingError) as stale:
        transition_execution_position(
            store,
            "position-001",
            state="REDUCING",
            quantity=Decimal("0.50"),
            source_sequence=1,
        )
    assert stale.value.code == "VERSION_CONFLICT"


@pytest.mark.parametrize(
    "changes",
    [
        {"position_id": " "},
        {"quantity": Decimal("NaN")},
        {"state": "FLAT", "quantity": Decimal(1)},
        {"state": "OPEN", "quantity": Decimal(0)},
        {"source_sequence": -1},
        {"state": "UNKNOWN", "unknown_reason": None},
        {"state": "OPEN", "unknown_reason": "unexpected"},
    ],
)
def test_position_contract_rejects_invalid_state(changes: dict[str, object]) -> None:
    """Every memory-only position invariant fails closed."""
    values: dict[str, object] = {
        "position_id": "position-001",
        "account_id": "account-001",
        "symbol": "EURUSD",
        "broker_position_id": "broker-position-001",
        "state": "OPEN",
        "quantity": Decimal(1),
        "average_entry_price": Decimal("1.10"),
        "source_sequence": 1,
        "version": 1,
    }
    with pytest.raises(ValueError, match=r"position|finite number"):
        create_execution_position(**{**values, **changes})


def test_position_store_rejects_invalid_handles_and_stale_values() -> None:
    """Opaque stores cannot be bypassed or overwritten with stale evidence."""
    with pytest.raises(TradingError):
        set_execution_position(object(), object())
    with pytest.raises(TradingError):
        transition_execution_position(
            object(),
            "position-001",
            state="OPEN",
            quantity=Decimal(1),
            source_sequence=1,
        )
    store = create_execution_position_store()
    with pytest.raises(TradingError):
        transition_execution_position(
            store,
            "position-001",
            state="OPEN",
            quantity=Decimal(1),
            source_sequence=1,
        )
    set_execution_position(store, _open_position())
    with pytest.raises(TradingError):
        set_execution_position(store, _open_position())
    with pytest.raises(TradingError):
        get_execution_position(object(), "position-001")
    with pytest.raises(TradingError):
        get_execution_position_snapshot(object())
