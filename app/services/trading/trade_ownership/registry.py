"""Process-local ownership registry and JSON transport."""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.kernel.serialization import to_json_safe
from app.services.trading.contracts import TradingError
from app.services.trading.trade_ownership.contracts import _TradeOwnership


class _OwnershipRegistry:
    """Internal in-memory trade ownership registry."""

    def __init__(self) -> None:
        """Initialize an empty ownership dictionary."""
        self.items: dict[str, _TradeOwnership] = {}


def create_trade_ownership_registry() -> object:
    """Create an empty process-local ownership registry.

    Returns:
        New empty _OwnershipRegistry instance.
    """
    return _OwnershipRegistry()


def build_trade_ownership(**values: object) -> dict[str, Any]:
    """Build one validated JSON-safe ownership mapping.

    Args:
        **values: Field values matching _TradeOwnership schema.

    Returns:
        JSON-safe dictionary representation of trade ownership.

    Raises:
        TypeError: If serialized payload is not a mapping.
    """
    value = _TradeOwnership.model_validate(values)
    safe = to_json_safe(value.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("ownership transport must be a mapping")
    return safe


def parse_trade_ownership(value: Mapping[str, object]) -> object:
    """Parse one validated ownership mapping.

    Args:
        value: Mapping payload to parse.

    Returns:
        Validated _TradeOwnership model instance.
    """
    return _TradeOwnership.model_validate(value)


def assign_trade_ownership(registry: object, ownership: object) -> object:
    """Assign one exact active owner or reject ambiguity.

    Args:
        registry: Target _OwnershipRegistry instance.
        ownership: _TradeOwnership instance to assign.

    Returns:
        Assigned _TradeOwnership instance.

    Raises:
        TradingError: If parameters are invalid or position already has an
            active unreleased owner.
    """
    if not isinstance(registry, _OwnershipRegistry) or not isinstance(
        ownership, _TradeOwnership
    ):
        raise TradingError("INVALID_REQUEST", "Ownership assignment is invalid")
    current = registry.items.get(ownership.position_id)
    if current is not None and not current.released:
        raise TradingError("VERSION_CONFLICT", "Position already has an active owner")
    registry.items[ownership.position_id] = ownership
    return ownership


def get_trade_ownership(registry: object, position_id: str) -> object:
    """Return exact active ownership or fail closed.

    Args:
        registry: Target _OwnershipRegistry instance.
        position_id: Position identifier string.

    Returns:
        Active _TradeOwnership instance.

    Raises:
        TradingError: If registry is invalid or ownership is absent/released.
    """
    if not isinstance(registry, _OwnershipRegistry):
        raise TradingError("INVALID_REQUEST", "Ownership registry is invalid")
    ownership = registry.items.get(position_id)
    if ownership is None or ownership.released:
        raise TradingError("RECONCILIATION_REQUIRED", "Position ownership is unknown")
    return ownership


def detect_orphaned_trade(registry: object, position_id: str) -> bool:
    """Return true when exact active ownership cannot be proven.

    Args:
        registry: Target _OwnershipRegistry instance.
        position_id: Position identifier string.

    Returns:
        True if trade ownership cannot be proven, False otherwise.
    """
    try:
        get_trade_ownership(registry, position_id)
    except TradingError:
        return True
    return False


def persist_trade_ownership(
    ownership: object, *, correlation_id: str, occurred_at: datetime
) -> None:
    """Append one ownership fact through the Trading persistence boundary.

    Args:
        ownership: Validated ownership object.
        correlation_id: Audit correlation identifier.
        occurred_at: Aware UTC timestamp when ownership fact occurred.
    """
    from app.services.trading.persistence.create import create_trade_ownership_record

    create_trade_ownership_record(
        ownership, correlation_id=correlation_id, occurred_at=occurred_at
    )


__all__ = [
    "assign_trade_ownership",
    "build_trade_ownership",
    "create_trade_ownership_registry",
    "detect_orphaned_trade",
    "get_trade_ownership",
    "parse_trade_ownership",
    "persist_trade_ownership",
]
