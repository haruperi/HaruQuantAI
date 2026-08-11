"""Deterministic order lifecycle with monotonic source sequencing."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.services.trading.contracts import TradingError

type OrderState = Literal[
    "CREATED",
    "STAGED",
    "SENT",
    "ACKNOWLEDGED",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCEL_PENDING",
    "CANCELLED",
    "REPLACE_PENDING",
    "REPLACED",
    "REJECTED",
    "EXPIRED",
    "UNKNOWN",
    "RECONCILED",
]

_EDGES = {
    "CREATED": {"STAGED", "REJECTED"},
    "STAGED": {"SENT", "CANCELLED", "REJECTED"},
    "SENT": {"ACKNOWLEDGED", "REJECTED", "UNKNOWN"},
    "ACKNOWLEDGED": {
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCEL_PENDING",
        "REPLACE_PENDING",
        "EXPIRED",
        "UNKNOWN",
    },
    "PARTIALLY_FILLED": {
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCEL_PENDING",
        "REPLACE_PENDING",
        "UNKNOWN",
    },
    "CANCEL_PENDING": {"CANCELLED", "PARTIALLY_FILLED", "FILLED", "UNKNOWN"},
    "REPLACE_PENDING": {"REPLACED", "PARTIALLY_FILLED", "FILLED", "UNKNOWN"},
    "UNKNOWN": {"RECONCILED"},
    "RECONCILED": {
        "ACKNOWLEDGED",
        "PARTIALLY_FILLED",
        "FILLED",
        "CANCELLED",
        "REJECTED",
        "EXPIRED",
    },
}


class _OrderLifecycle(BaseModel):
    """Private immutable current order lifecycle value."""

    model_config = ConfigDict(frozen=True, extra="forbid")
    order_id: str
    state: OrderState
    source_sequence: int
    version: int = 0
    unknown_reason: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if not self.order_id.strip() or self.source_sequence < 0 or self.version < 0:
            raise ValueError("order lifecycle identity and versions are invalid")
        if (self.state == "UNKNOWN") != (self.unknown_reason is not None):
            raise ValueError("UNKNOWN state requires an exclusive reason")
        return self


def create_order_lifecycle(**values: object) -> object:
    """Create one validated order lifecycle value.

    Args:
        **values: Field values matching _OrderLifecycle schema.

    Returns:
        Validated _OrderLifecycle model instance.
    """
    return _OrderLifecycle.model_validate(values)


def transition_order_lifecycle(
    current: object,
    *,
    state: str,
    source_sequence: int,
    unknown_reason: str | None = None,
) -> object:
    """Apply one allowed newer order transition or fail closed.

    Args:
        current: Current _OrderLifecycle instance.
        state: Target order state string.
        source_sequence: Monotonic source sequence integer.
        unknown_reason: Optional diagnostic string when state is UNKNOWN.

    Returns:
        New _OrderLifecycle instance with updated state and version.

    Raises:
        TradingError: If current order lifecycle is invalid, sequence is
            stale, or transition is forbidden.
    """
    if not isinstance(current, _OrderLifecycle):
        raise TradingError("INVALID_REQUEST", "Order lifecycle is invalid")
    if source_sequence <= current.source_sequence:
        raise TradingError("VERSION_CONFLICT", "Order transition sequence is stale")
    if state not in _EDGES.get(current.state, set()):
        raise TradingError("VALIDATION_FAILED", "Order transition is not allowed")
    return _OrderLifecycle.model_validate(
        {
            **current.model_dump(),
            "state": state,
            "source_sequence": source_sequence,
            "version": current.version + 1,
            "unknown_reason": unknown_reason,
        }
    )


__all__ = ["create_order_lifecycle", "transition_order_lifecycle"]
