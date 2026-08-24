"""Workspace domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.workspace.ports import (
        ConfigureRuntimeCapability,
        ManageWorkspacesCapability,
        SecureLocalAccessCapability,
    )

MANAGE_WORKSPACES_CAPABILITY: CapabilityKey[ManageWorkspacesCapability] = CapabilityKey(
    name="workspace.manage-workspaces",
    major=1,
)

CONFIGURE_RUNTIME_CAPABILITY: CapabilityKey[ConfigureRuntimeCapability] = CapabilityKey(
    name="workspace.configure-runtime",
    major=1,
)

SECURE_LOCAL_ACCESS_CAPABILITY: CapabilityKey[SecureLocalAccessCapability] = (
    CapabilityKey(
        name="workspace.secure-local-access",
        major=1,
    )
)
