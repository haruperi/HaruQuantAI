"""Process-local execution-position state and deterministic transitions."""

# ruff: noqa: SLF001 - function facades operate on the private internal store.

from __future__ import annotations

from decimal import Decimal
from threading import RLock
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.trading.contracts import TradingError
from app.utils import get_logger

logger = get_logger(__name__)

type PositionState = Literal[
    "FLAT",
    "OPENING",
    "OPEN",
    "REDUCING",
    "CLOSING",
    "OVERNIGHT_APPROVED",
    "EMERGENCY_CONTROLLED",
    "LIQUIDATION_PENDING",
    "UNKNOWN",
]

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "FLAT": frozenset({"OPENING", "UNKNOWN"}),
    "OPENING": frozenset({"OPEN", "CLOSING", "EMERGENCY_CONTROLLED", "UNKNOWN"}),
    "OPEN": frozenset(
        {
            "REDUCING",
            "CLOSING",
            "OVERNIGHT_APPROVED",
            "EMERGENCY_CONTROLLED",
            "LIQUIDATION_PENDING",
            "UNKNOWN",
        }
    ),
    "REDUCING": frozenset(
        {"OPEN", "CLOSING", "FLAT", "EMERGENCY_CONTROLLED", "UNKNOWN"}
    ),
    "CLOSING": frozenset(
        {"FLAT", "EMERGENCY_CONTROLLED", "LIQUIDATION_PENDING", "UNKNOWN"}
    ),
    "OVERNIGHT_APPROVED": frozenset(
        {"OPEN", "REDUCING", "CLOSING", "EMERGENCY_CONTROLLED", "UNKNOWN"}
    ),
    "EMERGENCY_CONTROLLED": frozenset(
        {"REDUCING", "CLOSING", "LIQUIDATION_PENDING", "FLAT", "UNKNOWN"}
    ),
    "LIQUIDATION_PENDING": frozenset({"FLAT", "EMERGENCY_CONTROLLED", "UNKNOWN"}),
    "UNKNOWN": frozenset(
        {"FLAT", "OPEN", "REDUCING", "CLOSING", "EMERGENCY_CONTROLLED"}
    ),
}


class _ExecutionPosition(BaseModel):
    """Validated current position retained only inside one process."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    position_id: str
    account_id: str
    symbol: str
    broker_position_id: str
    state: PositionState
    quantity: Decimal
    average_entry_price: Decimal | None = None
    source_sequence: int
    version: int = 0
    unknown_reason: str | None = None

    @field_validator("position_id", "account_id", "symbol", "broker_position_id")
    @classmethod
    def _validate_text(cls, value: str) -> str:
        """Require non-empty trimmed identifiers.

        Returns:
            Validated text.

        Raises:
            ValueError: If the text is empty or untrimmed.
        """
        if not value or value != value.strip():
            raise ValueError("position identifiers must be non-empty and trimmed")
        return value

    @model_validator(mode="after")
    def _validate_state(self) -> Self:
        """Enforce quantities, sequence, version, and unknown evidence.

        Returns:
            Validated position.

        Raises:
            ValueError: If state invariants are violated.
        """
        if not self.quantity.is_finite() or self.quantity < 0:
            raise ValueError("position quantity must be finite and non-negative")
        if self.state == "FLAT" and self.quantity != 0:
            raise ValueError("flat position quantity must be zero")
        if self.state not in {"FLAT", "UNKNOWN"} and self.quantity <= 0:
            raise ValueError("active position quantity must be positive")
        if self.source_sequence < 0 or self.version < 0:
            raise ValueError("position sequence and version must be non-negative")
        if self.state == "UNKNOWN" and not self.unknown_reason:
            raise ValueError("unknown position state requires an explicit reason")
        if self.state != "UNKNOWN" and self.unknown_reason is not None:
            raise ValueError("unknown reason is valid only for unknown state")
        return self


class _ExecutionPositionStore:
    """Thread-safe process-local position registry with no persistence hooks."""

    def __init__(self) -> None:
        """Initialize empty process-local position dictionary and lock."""
        self._positions: dict[str, _ExecutionPosition] = {}
        self._lock = RLock()


def create_execution_position_store() -> object:
    """Create an empty process-local execution-position store.

    Returns:
        Opaque in-memory store for dependency injection.
    """
    return _ExecutionPositionStore()


def create_execution_position(**values: object) -> object:
    """Create one validated memory-only execution position.

    Args:
        **values: Execution-position fields.

    Returns:
        Validated internal position value.
    """
    return _ExecutionPosition.model_validate(values)


def set_execution_position(store: object, position: object) -> object:
    """Insert one newer position state into the process-local store.

    Args:
        store: Execution-position store instance.
        position: Execution position object to insert.

    Returns:
        Stored position.

    Raises:
        TradingError: If the store/value is invalid or stale.
    """
    if not isinstance(store, _ExecutionPositionStore) or not isinstance(
        position, _ExecutionPosition
    ):
        raise TradingError("INVALID_REQUEST", "Execution-position state is invalid")
    with store._lock:
        current = store._positions.get(position.position_id)
        if current is not None and (
            position.source_sequence <= current.source_sequence
            or position.version <= current.version
        ):
            raise TradingError("VERSION_CONFLICT", "Execution-position update is stale")
        store._positions[position.position_id] = position
    return position


def transition_execution_position(
    store: object,
    position_id: str,
    *,
    state: str,
    quantity: Decimal,
    source_sequence: int,
    unknown_reason: str | None = None,
) -> object:
    """Apply one allowed deterministic position transition in memory.

    Args:
        store: Execution-position store instance.
        position_id: Target position identifier.
        state: New target position state.
        quantity: New position quantity.
        source_sequence: Update sequence number.
        unknown_reason: Optional diagnostic string for UNKNOWN state.

    Returns:
        Updated position.

    Raises:
        TradingError: If state is absent, stale, invalid, or exposure-increasing
            from ``UNKNOWN``.
    """
    if not isinstance(store, _ExecutionPositionStore):
        raise TradingError("INVALID_REQUEST", "Execution-position store is invalid")
    with store._lock:
        current = store._positions.get(position_id)
        if current is None:
            raise TradingError("RECONCILIATION_REQUIRED", "Position state is absent")
        if state not in _ALLOWED_TRANSITIONS[current.state]:
            raise TradingError(
                "VALIDATION_FAILED", "Position transition is not allowed"
            )
        if source_sequence <= current.source_sequence:
            raise TradingError("VERSION_CONFLICT", "Position transition is stale")
        if current.state == "UNKNOWN" and quantity > current.quantity:
            raise TradingError(
                "RECONCILIATION_REQUIRED",
                "Unknown position cannot increase exposure",
            )
        try:
            updated = current.model_copy(
                update={
                    "state": state,
                    "quantity": quantity,
                    "source_sequence": source_sequence,
                    "version": current.version + 1,
                    "unknown_reason": unknown_reason,
                }
            )
            updated = _ExecutionPosition.model_validate(updated.model_dump())
        except ValueError as error:
            raise TradingError("VALIDATION_FAILED", str(error)) from error
        store._positions[position_id] = updated
        logger.info("Applied in-memory Trading position transition to %s", state)
        return updated


def get_execution_position(store: object, position_id: str) -> object | None:
    """Return one current process-local position without persistence.

    Args:
        store: Execution-position store instance.
        position_id: Target position identifier.

    Returns:
        Current position or ``None``.

    Raises:
        TradingError: If the store is invalid.
    """
    if not isinstance(store, _ExecutionPositionStore):
        raise TradingError("INVALID_REQUEST", "Execution-position store is invalid")
    with store._lock:
        return store._positions.get(position_id)


def get_execution_position_snapshot(store: object) -> dict[str, Any]:
    """Return a detached JSON-safe snapshot for reconciliation only.

    Args:
        store: Execution-position store instance.

    Returns:
        Position facts keyed by position identity.

    Raises:
        TradingError: If the store is invalid.
    """
    if not isinstance(store, _ExecutionPositionStore):
        raise TradingError("INVALID_REQUEST", "Execution-position store is invalid")
    with store._lock:
        return {
            identity: position.model_dump(mode="json")
            for identity, position in store._positions.items()
        }


__all__ = [
    "create_execution_position",
    "create_execution_position_store",
    "get_execution_position",
    "get_execution_position_snapshot",
    "set_execution_position",
    "transition_execution_position",
]
