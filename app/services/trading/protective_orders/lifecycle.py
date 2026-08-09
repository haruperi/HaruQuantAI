# ruff: noqa: DOC201, DOC501
"""Fail-closed protective-order lifecycle operations."""

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.trading.contracts import TradingError
from app.services.trading.protective_orders.contracts import _ProtectiveOrderPlan
from app.utils import to_json_safe


def create_protective_order_plan(**values: object) -> object:
    """Create one validated protective-order plan."""
    return _ProtectiveOrderPlan.model_validate(values)


def verify_protective_order_coverage(
    plan: object,
    *,
    open_quantity: Decimal,
    stop_acknowledged: bool,
    target_acknowledged: bool,
) -> dict[str, Any]:
    """Return exact coverage evidence or fail closed."""
    if not isinstance(plan, _ProtectiveOrderPlan) or open_quantity < 0:
        raise TradingError("INVALID_REQUEST", "Protection evidence is invalid")
    covered = (
        plan.quantity == open_quantity and stop_acknowledged and target_acknowledged
    )
    return {
        "status": "PROTECTED" if covered else "UNKNOWN",
        "covered_quantity": str(plan.quantity if covered else Decimal(0)),
        "required_quantity": str(open_quantity),
    }


def resize_protective_orders(
    plan: object, *, residual_quantity: Decimal, source_sequence: int
) -> object:
    """Resize protection to an exact residual without reverse exposure."""
    if not isinstance(plan, _ProtectiveOrderPlan) or residual_quantity <= 0:
        raise TradingError("VALIDATION_FAILED", "Residual protection must be positive")
    if residual_quantity > plan.quantity or source_sequence <= plan.source_sequence:
        raise TradingError(
            "VALIDATION_FAILED", "Protection resize could increase exposure"
        )
    return _ProtectiveOrderPlan.model_validate(
        {
            **plan.model_dump(),
            "quantity": residual_quantity,
            "source_sequence": source_sequence,
        }
    )


def build_protective_order_plan(plan: object) -> dict[str, Any]:
    """Build a validated JSON-safe protective-order mapping."""
    if not isinstance(plan, _ProtectiveOrderPlan):
        raise TradingError("INVALID_REQUEST", "Protective-order plan is invalid")
    safe = to_json_safe(plan.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("protective-order transport must be a mapping")
    return safe


def parse_protective_order_plan(value: Mapping[str, object]) -> object:
    """Parse a protective-order mapping."""
    return _ProtectiveOrderPlan.model_validate(value)


def persist_protective_order_plan(
    plan: object, *, correlation_id: str, occurred_at: datetime
) -> None:
    """Append both protection legs through the Trading persistence boundary."""
    from app.services.trading.persistence.create import create_protective_order_records

    create_protective_order_records(
        plan, correlation_id=correlation_id, occurred_at=occurred_at
    )


__all__ = [
    "build_protective_order_plan",
    "create_protective_order_plan",
    "parse_protective_order_plan",
    "persist_protective_order_plan",
    "resize_protective_orders",
    "verify_protective_order_coverage",
]
