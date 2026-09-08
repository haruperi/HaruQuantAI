"""Agentic domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.agentic.mandate import MandateCapability
    from app.contracts.agentic.operations import AgenticOperationsCapability

MANDATE_CAPABILITY: CapabilityKey[MandateCapability] = CapabilityKey(name="agentic.mandate", major=1)
OPERATIONS_CAPABILITY: CapabilityKey[AgenticOperationsCapability] = CapabilityKey(name="agentic.operations", major=1)

__all__ = ["MANDATE_CAPABILITY", "OPERATIONS_CAPABILITY"]
