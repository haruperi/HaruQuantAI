"""Read-only durable Trading operational-event view."""

from collections.abc import Sequence

from app.services.trading.state.runtime import (
    build_trading_state_store,
    execute_trading_state_store_operation,
)

_MAX_OPERATIONAL_EVENTS = 200


def get_trading_operational_events(*, limit: int = 200) -> Sequence[object]:
    """Return unresolved durable Trading attempts as operational evidence.

    Args:
        limit: Maximum number of records returned.

    Returns:
        Bounded owner-authored unresolved-attempt sequence.

    Raises:
        ValueError: If the requested limit is outside the public bound.
        TypeError: If durable storage violates its sequence contract.
    """
    if isinstance(limit, bool) or not 1 <= limit <= _MAX_OPERATIONAL_EVENTS:
        raise ValueError("limit must be between 1 and 200")
    store = build_trading_state_store()
    records = execute_trading_state_store_operation(
        store, "load_all_unresolved_attempts", limit
    )
    if not isinstance(records, Sequence):
        raise TypeError("Trading event store returned an invalid sequence")
    return tuple(records[:limit])


__all__ = ("get_trading_operational_events",)
