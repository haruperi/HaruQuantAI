"""Agentic domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.agentic.mandate import EnforceMandateCapability

ENFORCE_MANDATE_CAPABILITY: CapabilityKey[EnforceMandateCapability] = CapabilityKey(
    name="agentic.mandate",
    major=1,
)

__all__ = ["ENFORCE_MANDATE_CAPABILITY"]
