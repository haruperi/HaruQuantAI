"""Integration test for WF-WS-002 (Runtime Configuration workflow)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from app.contracts.workspace.capabilities import (
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
)
from app.contracts.workspace.models import (
    JobKind,
    ServerRuntimeSettings,
    StorageGuardLimits,
    WorkspaceSettings,
    WorkspaceStatus,
)
from app.contracts.workspace.ports import (
    ConfigureRuntimeCapability,
    ManageWorkspacesCapability,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.runtime_configuration.feature import (
    feature as runtime_feature,
)
from app.services.workspace.workspace_lifecycle.feature import (
    feature as lifecycle_feature,
)

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey

INTEGRATION_PORT = 48813


async def _mount_feature(
    feat: Any, registry: ServiceRegistry, event_bus: EventBus
) -> None:
    """Mount one feature into the shared test registry.

    Args:
        feat: Feature instance exposing spec and mount.
        registry: Shared service registry.
        event_bus: Shared event bus.
    """
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def registrar(
        cap: CapabilityKey[Any],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )
    await feat.mount(context, {})


@pytest.mark.asyncio
async def test_runtime_configuration_workflow(tmp_path: Path) -> None:
    """Verify WF-WS-002 through mounted capability contexts."""
    registry = ServiceRegistry()
    event_bus = EventBus()

    # Mount the required lifecycle feature first, then this feature.
    await _mount_feature(lifecycle_feature(), registry, event_bus)
    await _mount_feature(runtime_feature(), registry, event_bus)

    workspace_service = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    assert isinstance(workspace_service, ManageWorkspacesCapability)
    config_service = registry.resolve(CONFIGURE_RUNTIME_CAPABILITY)
    assert isinstance(config_service, ConfigureRuntimeCapability)

    ws_root = tmp_path / "runtime_ws"
    ref = workspace_service.initialize_workspace(ws_root, name="Runtime Test WS")
    assert ref.status == WorkspaceStatus.READY

    settings = WorkspaceSettings(
        timezone="UTC",
        locale="en-US",
        worker_count=4,
        worker_memory_mb=2048,
        max_artifact_size_mb=2048,
        max_total_artifact_gb=50,
    )
    versioned = config_service.configure_workspace(ref, settings)
    assert versioned.version == 1
    latest = config_service.get_workspace_settings(ref)
    assert latest is not None
    assert latest.settings.timezone == "UTC"

    admitted = config_service.enforce_storage_guards(
        ref,
        job_kind=JobKind.BACKTEST,
        projected_artifact_mb=50.0,
        limits=StorageGuardLimits(min_free_space_mb=1, max_artifact_size_mb=4096),
    )
    assert admitted.admitted

    runtime = config_service.configure_server_runtime(
        ServerRuntimeSettings(port=INTEGRATION_PORT, headless=True)
    )
    assert runtime.valid

    profile = config_service.publish_runtime_support()
    assert profile.profile_version >= 1


@pytest.mark.asyncio
async def test_runtime_configuration_degradation(tmp_path: Path) -> None:
    """Verify the deletion contract: without the feature, admission fails."""
    registry = ServiceRegistry()
    event_bus = EventBus()
    await _mount_feature(lifecycle_feature(), registry, event_bus)

    workspace_service = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    assert workspace_service is not None
    ws_root = tmp_path / "degraded_ws"
    workspace_service.initialize_workspace(ws_root, name="Degraded WS")

    # With the runtime-configuration feature absent, its capability resolves
    # to None: defaults stay readable, changes and guarded admission degrade,
    # and the domain (lifecycle feature) continues loading.
    assert registry.resolve(CONFIGURE_RUNTIME_CAPABILITY) is None
    assert (ws_root / "metadata" / "workspace.db").exists()
