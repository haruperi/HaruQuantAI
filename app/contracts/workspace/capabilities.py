"""Workspace domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.workspace.ports import (
        ConfigureRuntimeCapability,
        ManageWorkspacesCapability,
    )

MANAGE_WORKSPACES_CAPABILITY: CapabilityKey[ManageWorkspacesCapability] = CapabilityKey(
    name="workspace.manage-workspaces",
    major=1,
)

CONFIGURE_RUNTIME_CAPABILITY: CapabilityKey[ConfigureRuntimeCapability] = CapabilityKey(
    name="workspace.configure-runtime",
    major=1,
)
