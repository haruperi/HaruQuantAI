"""Agentic domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.agentic.mandate import MandateCapability
    from app.contracts.agentic.operations import AgenticOperationsCapability
    from app.contracts.agentic.roles import RolesCapability
    from app.contracts.agentic.tool_governance import ToolGovernanceCapability

MANDATE_CAPABILITY: CapabilityKey[MandateCapability] = CapabilityKey(name="agentic.mandate", major=1)
OPERATIONS_CAPABILITY: CapabilityKey[AgenticOperationsCapability] = CapabilityKey(name="agentic.operations", major=1)
ROLES_CAPABILITY: CapabilityKey[RolesCapability] = CapabilityKey(name="agentic.roles", major=1)
TOOL_GOVERNANCE_CAPABILITY: CapabilityKey[ToolGovernanceCapability] = CapabilityKey(name="agentic.tool-governance", major=1)

__all__ = ["MANDATE_CAPABILITY", "OPERATIONS_CAPABILITY", "ROLES_CAPABILITY", "TOOL_GOVERNANCE_CAPABILITY"]
