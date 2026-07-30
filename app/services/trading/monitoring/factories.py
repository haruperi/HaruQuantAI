"""Function-only construction for Trading operational evidence."""

from __future__ import annotations

from app.services.trading.monitoring.events import OperationalEvent


def create_operational_event(**values: object) -> OperationalEvent:
    """Construct one validated operational event.

    Args:
        **values: Event field values.

    Returns:
        Validated internal operational event.
    """
    return OperationalEvent.model_validate(values)


__all__ = ["create_operational_event"]
