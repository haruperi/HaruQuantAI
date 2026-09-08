"""Workspace domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.workspace.manage_accounts import ManageAccountsCapability
    from app.contracts.workspace.manage_workspaces import ManageWorkspacesCapability
    from app.contracts.workspace.persistence import PersistenceCapability
    from app.contracts.workspace.ports import (
        AdministerSettingsCapability,
        BuildDiagnosticsCapability,
        ConfigureRuntimeCapability,
        DistributeWorkersCapability,
        HostWorkspacesCapability,
        ManageWatchlistsCapability,
        SecureLocalAccessCapability,
    )

MANAGE_WORKSPACES_CAPABILITY: CapabilityKey[ManageWorkspacesCapability] = CapabilityKey(
    name="workspace.manage-workspaces",
    major=1,
)

PERSISTENCE_CAPABILITY: CapabilityKey[PersistenceCapability] = CapabilityKey(
    name="workspace.persistence",
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

BUILD_DIAGNOSTICS_CAPABILITY: CapabilityKey[BuildDiagnosticsCapability] = CapabilityKey(
    name="workspace.build-diagnostics",
    major=1,
)

DISTRIBUTE_WORKERS_CAPABILITY: CapabilityKey[DistributeWorkersCapability] = (
    CapabilityKey(
        name="workspace.distribute-workers",
        major=1,
    )
)

HOST_WORKSPACES_CAPABILITY: CapabilityKey[HostWorkspacesCapability] = CapabilityKey(
    name="workspace.host-workspaces",
    major=1,
)

MANAGE_WATCHLISTS_CAPABILITY: CapabilityKey[ManageWatchlistsCapability] = CapabilityKey(
    name="workspace.manage-watchlists",
    major=1,
)

ADMINISTER_SETTINGS_CAPABILITY: CapabilityKey[AdministerSettingsCapability] = (
    CapabilityKey(
        name="workspace.administer-settings",
        major=1,
    )
)

MANAGE_ACCOUNTS_CAPABILITY: CapabilityKey[ManageAccountsCapability] = CapabilityKey(
    name="workspace.manage-accounts",
    major=1,
)
