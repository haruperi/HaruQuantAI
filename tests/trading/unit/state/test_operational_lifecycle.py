"""Unit evidence for operational order and fill lifecycles."""

# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.trading import (
    apply_order_fill,
    create_fill_aggregate,
    create_order_lifecycle,
    get_fill_residual,
    transition_order_lifecycle,
)
from app.services.trading.contracts import TradingError


def test_unknown_order_requires_reconciliation_before_terminal_resolution() -> None:
    """Unknown outcomes cannot jump directly to a plausible terminal state."""
    current = create_order_lifecycle(
        order_id="order-001", state="SENT", source_sequence=1
    )
    unknown = transition_order_lifecycle(
        current, state="UNKNOWN", source_sequence=2, unknown_reason="timeout"
    )
    with pytest.raises(TradingError):
        transition_order_lifecycle(unknown, state="FILLED", source_sequence=3)
    reconciled = transition_order_lifecycle(
        unknown, state="RECONCILED", source_sequence=3
    )
    assert reconciled.state == "RECONCILED"


def test_partial_fills_update_average_and_residual_without_duplicates() -> None:
    """Fill aggregation is exact, bounded, and idempotency guarded."""
    aggregate = create_fill_aggregate(order_id="order-001", ordered_quantity=Decimal(2))
    aggregate = apply_order_fill(
        aggregate, fill_id="fill-001", quantity=Decimal(1), price=Decimal(10)
    )
    assert get_fill_residual(aggregate) == Decimal(1)
    with pytest.raises(TradingError):
        apply_order_fill(
            aggregate,
            fill_id="fill-001",
            quantity=Decimal(1),
            price=Decimal(11),
        )


def test_fill_and_order_lifecycles_reject_invalid_edges() -> None:
    """Invalid quantities, values, and transition sequences fail closed."""
    with pytest.raises(ValueError, match="outside the order boundary"):
        create_fill_aggregate(order_id="order-001", ordered_quantity=Decimal(0))
    aggregate = create_fill_aggregate(order_id="order-001", ordered_quantity=Decimal(1))
    with pytest.raises(TradingError):
        apply_order_fill(
            aggregate, fill_id="fill-001", quantity=Decimal(0), price=Decimal(1)
        )
    with pytest.raises(TradingError):
        apply_order_fill(
            aggregate, fill_id="fill-001", quantity=Decimal(2), price=Decimal(1)
        )
    with pytest.raises(TradingError):
        get_fill_residual(object())
    with pytest.raises(ValueError, match="identity and versions"):
        create_order_lifecycle(order_id="", state="CREATED", source_sequence=0)
    lifecycle = create_order_lifecycle(
        order_id="order-001", state="CREATED", source_sequence=1
    )
    with pytest.raises(TradingError):
        transition_order_lifecycle(object(), state="STAGED", source_sequence=2)
    with pytest.raises(TradingError):
        transition_order_lifecycle(lifecycle, state="STAGED", source_sequence=1)
    with pytest.raises(TradingError):
        transition_order_lifecycle(lifecycle, state="FILLED", source_sequence=2)
