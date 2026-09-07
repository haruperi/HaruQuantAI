"""Lifecycle and removability evidence for FEAT-WS-MANAGE_WORKSPACES."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from app.contracts.workspace.capabilities import MANAGE_WORKSPACES_CAPABILITY
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.manage_workspaces.feature import feature
from app.services.workspace.manage_workspaces.manage_workspaces import (
    ManageWorkspacesService,
)


@pytest.mark.asyncio
async def test_trc_manage_workspaces_nfr_001(tmp_path: Path) -> None:
    """Removing the scope withdraws only its provider and retains workspace data."""
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id="FEAT-WS-MANAGE_WORKSPACES")
    instance = feature()

    def registrar(
        capability: CapabilityKey[Any], implementation: object, owner: FeatureScope
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner,
        )

    context = DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=EventBus(),
    )
    await instance.mount(context, {})
    service = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    assert isinstance(service, ManageWorkspacesService)
    workspace = service.initialize_workspace(tmp_path / "retained")
    fence = service.fence_workspace_writers(workspace)
    assert fence.is_write_locked

    await scope.close()
    assert registry.resolve(MANAGE_WORKSPACES_CAPABILITY) is None
    assert (workspace.root_path / "metadata" / "workspace.db").is_file()
    assert not (workspace.root_path / ".workspace.lock").exists()
    await scope.close()
    assert scope.active_effect_count == 0


@pytest.mark.asyncio
async def test_invalid_mount_has_no_effects() -> None:
    scope = FeatureScope(owner_id="FEAT-WS-MANAGE_WORKSPACES")
    instance = feature()
    context = DefaultFeatureContext(spec=instance.spec, scope=scope)
    with pytest.raises(ValueError, match="Unknown"):
        await instance.mount(context, {"unexpected": True})
    assert scope.active_effect_count == 0
