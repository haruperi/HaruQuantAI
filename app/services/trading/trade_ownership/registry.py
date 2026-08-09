# ruff: noqa: DOC201, DOC501
"""Process-local ownership registry and JSON transport."""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.services.trading.contracts import TradingError
from app.services.trading.trade_ownership.contracts import _TradeOwnership
from app.utils import to_json_safe


class _OwnershipRegistry:
    def __init__(self) -> None:
        self.items: dict[str, _TradeOwnership] = {}


def create_trade_ownership_registry() -> object:
    """Create an empty process-local ownership registry."""
    return _OwnershipRegistry()


def build_trade_ownership(**values: object) -> dict[str, Any]:
    """Build one validated JSON-safe ownership mapping."""
    value = _TradeOwnership.model_validate(values)
    safe = to_json_safe(value.model_dump(mode="json"))
    if not isinstance(safe, dict):
        raise TypeError("ownership transport must be a mapping")
    return safe


def parse_trade_ownership(value: Mapping[str, object]) -> object:
    """Parse one validated ownership mapping."""
    return _TradeOwnership.model_validate(value)


def assign_trade_ownership(registry: object, ownership: object) -> object:
    """Assign one exact active owner or reject ambiguity."""
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
    """Return exact active ownership or fail closed."""
    if not isinstance(registry, _OwnershipRegistry):
        raise TradingError("INVALID_REQUEST", "Ownership registry is invalid")
    ownership = registry.items.get(position_id)
    if ownership is None or ownership.released:
        raise TradingError("RECONCILIATION_REQUIRED", "Position ownership is unknown")
    return ownership


def detect_orphaned_trade(registry: object, position_id: str) -> bool:
    """Return true when exact active ownership cannot be proven."""
    try:
        get_trade_ownership(registry, position_id)
    except TradingError:
        return True
    return False


def persist_trade_ownership(
    ownership: object, *, correlation_id: str, occurred_at: datetime
) -> None:
    """Append one ownership fact through the Trading persistence boundary."""
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
