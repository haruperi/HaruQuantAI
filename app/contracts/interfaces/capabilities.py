"""Interfaces domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.interfaces.ports import ServeApiEventsCapability

SERVE_API_EVENTS_CAPABILITY: CapabilityKey[ServeApiEventsCapability] = CapabilityKey(
    name="interfaces.serve-api-events",
    major=1,
)
