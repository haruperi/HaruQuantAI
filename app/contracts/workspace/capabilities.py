"""Workspace domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.workspace.ports import ManageWorkspacesCapability

MANAGE_WORKSPACES_CAPABILITY: CapabilityKey[ManageWorkspacesCapability] = CapabilityKey(
    name="workspace.manage-workspaces",
    major=1,
)
