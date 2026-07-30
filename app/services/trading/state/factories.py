"""Function-only construction and inspection for Trading state values."""

from __future__ import annotations

from app.services.trading.state.events import TradingEvent
from app.services.trading.state.idempotency import IdempotencyReservation
from app.services.trading.state.migrations import TRADING_SCHEMA_VERSION
from app.services.trading.state.projections import TradingProjection


def get_trading_schema_version() -> str:
    """Return the canonical Trading schema version.

    Returns:
        Current Trading schema version.
    """
    return TRADING_SCHEMA_VERSION


def create_trading_event(**values: object) -> TradingEvent:
    """Construct one validated Trading event.

    Args:
        **values: Event field values.

    Returns:
        Validated internal Trading event.
    """
    return TradingEvent.model_validate(values)


def create_idempotency_reservation(**values: object) -> IdempotencyReservation:
    """Construct one validated idempotency reservation.

    Args:
        **values: Reservation field values.

    Returns:
        Validated internal reservation.
    """
    return IdempotencyReservation.model_validate(values)


def create_trading_projection(**values: object) -> TradingProjection:
    """Construct one validated Trading projection.

    Args:
        **values: Projection field values.

    Returns:
        Validated internal projection.
    """
    return TradingProjection.model_validate(values)


__all__ = [
    "create_idempotency_reservation",
    "create_trading_event",
    "create_trading_projection",
    "get_trading_schema_version",
]
