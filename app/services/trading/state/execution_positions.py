"""Process-local execution-position state and deterministic transitions."""

# ruff: noqa: SLF001 - function facades operate on the private internal store.

from __future__ import annotations

from decimal import Decimal
from threading import RLock
from typing import Any, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.services.brokers import get_broker_deal, get_broker_position
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
    side: Literal["LONG", "SHORT", "UNKNOWN"] = "UNKNOWN"
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
        self._receipt_positions: dict[str, str] = {}
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


def serialize_execution_position_store(store: object) -> dict[str, object]:
    """Serialize authoritative positions and receipt watermarks for restart.

    Args:
        store: Execution-position store instance.

    Returns:
        JSON-safe deterministic store state.

    Raises:
        TradingError: If the store is invalid.
    """
    if not isinstance(store, _ExecutionPositionStore):
        raise TradingError("INVALID_REQUEST", "Execution-position store is invalid")
    with store._lock:
        return {
            "positions": {
                identity: position.model_dump(mode="json")
                for identity, position in sorted(store._positions.items())
            },
            "receipt_positions": dict(sorted(store._receipt_positions.items())),
        }


def restore_execution_position_store(state: dict[str, object]) -> object:
    """Restore restart-safe position state through current validators.

    Args:
        state: Serialized state returned by ``serialize_execution_position_store``.

    Returns:
        Restored opaque execution-position store.

    Raises:
        TradingError: If serialized state is malformed.
    """
    positions = state.get("positions")
    watermarks = state.get("receipt_positions")
    if not isinstance(positions, dict) or not isinstance(watermarks, dict):
        raise TradingError("INVALID_REQUEST", "Execution-position state is invalid")
    store = _ExecutionPositionStore()
    try:
        store._positions = {
            str(identity): _ExecutionPosition.model_validate(value)
            for identity, value in positions.items()
        }
        store._receipt_positions = {
            str(receipt_id): str(position_id)
            for receipt_id, position_id in watermarks.items()
        }
    except (TypeError, ValueError) as error:
        raise TradingError(
            "INVALID_REQUEST", "Execution-position state is invalid"
        ) from error
    return store


def _unknown_position(
    store: _ExecutionPositionStore,
    *,
    receipt_id: str,
    account_id: str,
    symbol: str,
    reason: str,
    position_id: str | None = None,
) -> _ExecutionPosition:
    """Atomically retain an unverifiable receipt as blocking UNKNOWN state.

    Returns:
        Stored blocking position state.
    """
    identity = position_id or store._receipt_positions.get(
        receipt_id, f"receipt-{receipt_id}"
    )
    current = store._positions.get(identity)
    position = _ExecutionPosition(
        position_id=identity,
        account_id=account_id,
        symbol=symbol,
        broker_position_id=identity,
        side="UNKNOWN" if current is None else current.side,
        state="UNKNOWN",
        quantity=Decimal(0) if current is None else current.quantity,
        average_entry_price=None if current is None else current.average_entry_price,
        source_sequence=0 if current is None else current.source_sequence + 1,
        version=0 if current is None else current.version + 1,
        unknown_reason=reason,
    )
    store._positions[identity] = position
    store._receipt_positions[receipt_id] = identity
    return position


async def reconcile_execution_position_receipt(  # noqa: C901, PLR0911
    receipt: object,
    store: object,
    broker_adapter: object,
    *,
    account_id: str,
    symbol: str,
) -> object:
    """Correlate one durable receipt through Broker deals and position authority.

    Args:
        receipt: Trading ``ExecutionReceipt`` carrying provider deal identifiers.
        store: Process-local execution-position store.
        broker_adapter: Injected Brokers adapter instance.
        account_id: Exact authority account identifier.
        symbol: Expected canonical symbol.

    Returns:
        Verified OPEN/FLAT position, or a blocking UNKNOWN position.

    Raises:
        TradingError: If inputs are not valid Trading/Brokers contract values.
    """
    if not isinstance(store, _ExecutionPositionStore):
        raise TradingError("INVALID_REQUEST", "Execution-position store is invalid")
    receipt_id = getattr(receipt, "receipt_id", None)
    deal_ids = getattr(receipt, "provider_deal_ids", None)
    if not isinstance(receipt_id, str) or not receipt_id:
        raise TradingError("INVALID_REQUEST", "Durable receipt identity is required")
    with store._lock:
        prior_identity = store._receipt_positions.get(receipt_id)
        if prior_identity is not None:
            return store._positions[prior_identity]
    if not isinstance(deal_ids, tuple) or not deal_ids:
        with store._lock:
            return _unknown_position(
                store,
                receipt_id=receipt_id,
                account_id=account_id,
                symbol=symbol,
                reason="receipt has no provider deal identity",
            )

    position_ids: set[str] = set()
    for deal_id in deal_ids:
        response = await get_broker_deal(cast("Any", broker_adapter), deal_id)
        deal = getattr(response, "data", None)
        position_id = getattr(deal, "position_id", None)
        if getattr(response, "status", None) != "success" or not position_id:
            with store._lock:
                return _unknown_position(
                    store,
                    receipt_id=receipt_id,
                    account_id=account_id,
                    symbol=symbol,
                    reason="provider deal cannot be verified",
                )
        position_ids.add(position_id)
    if len(position_ids) != 1:
        with store._lock:
            return _unknown_position(
                store,
                receipt_id=receipt_id,
                account_id=account_id,
                symbol=symbol,
                reason="receipt deals disagree on position authority",
            )

    broker_position_id = next(iter(position_ids))
    response = await get_broker_position(
        cast("Any", broker_adapter), broker_position_id
    )
    authority = getattr(response, "data", None)
    source_sequence = getattr(authority, "source_sequence", None)
    if (
        getattr(response, "status", None) != "success"
        or authority is None
        or getattr(authority, "position_id", None) != broker_position_id
        or getattr(authority, "symbol", None) != symbol
        or not isinstance(source_sequence, int)
    ):
        with store._lock:
            return _unknown_position(
                store,
                receipt_id=receipt_id,
                account_id=account_id,
                symbol=symbol,
                reason="position authority snapshot is incomplete or disagrees",
                position_id=broker_position_id,
            )
    state: PositionState = (
        "OPEN" if getattr(authority, "state", None) == "OPEN" else "FLAT"
    )
    side = getattr(authority, "side", None)
    quantity = getattr(authority, "quantity", None)
    if (
        not isinstance(quantity, Decimal)
        or side not in {"LONG", "SHORT", "UNKNOWN"}
        or (state == "FLAT" and quantity != 0)
    ):
        with store._lock:
            return _unknown_position(
                store,
                receipt_id=receipt_id,
                account_id=account_id,
                symbol=symbol,
                reason="position authority quantity is invalid",
                position_id=broker_position_id,
            )
    verified = _ExecutionPosition(
        position_id=broker_position_id,
        account_id=account_id,
        symbol=symbol,
        broker_position_id=broker_position_id,
        side=side,
        state=state,
        quantity=quantity,
        average_entry_price=getattr(authority, "open_price", None),
        source_sequence=source_sequence,
        version=source_sequence,
    )
    with store._lock:
        current = store._positions.get(broker_position_id)
        if current is not None and source_sequence < current.source_sequence:
            return _unknown_position(
                store,
                receipt_id=receipt_id,
                account_id=account_id,
                symbol=symbol,
                reason="position authority sequence regressed",
                position_id=broker_position_id,
            )
        store._positions[broker_position_id] = verified
        store._receipt_positions[receipt_id] = broker_position_id
        return verified


__all__ = [
    "create_execution_position",
    "create_execution_position_store",
    "get_execution_position",
    "get_execution_position_snapshot",
    "reconcile_execution_position_receipt",
    "restore_execution_position_store",
    "serialize_execution_position_store",
    "set_execution_position",
    "transition_execution_position",
]
