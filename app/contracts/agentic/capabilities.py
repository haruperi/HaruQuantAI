"""Agentic domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.agentic.mandate import MandateCapability

MANDATE_CAPABILITY: CapabilityKey[MandateCapability] = CapabilityKey(name="agentic.mandate", major=1)

__all__ = ["MANDATE_CAPABILITY"]
