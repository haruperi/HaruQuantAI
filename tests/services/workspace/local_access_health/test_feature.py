"""Unit tests for LocalAccessHealthFeature lifecycle and mounting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.workspace.capabilities import (
    MANAGE_WORKSPACES_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.contracts.workspace.ports import SecureLocalAccessCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.local_access_health.feature import (
    LocalAccessHealthFeature,
    feature,
)
from app.services.workspace.local_access_health.manifest import SPEC
from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
    WorkspaceLifecycleService,
)

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_feature_mount_and_discovery() -> None:
    """Test feature factory, mounting, and capability registration."""
    feat = feature()
    assert isinstance(feat, LocalAccessHealthFeature)
    assert feat.spec == SPEC
    assert feat.service is None

    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    # Register required dependency
    lifecycle_service = WorkspaceLifecycleService()
    lifecycle_scope = FeatureScope(owner_id="FEAT-WS-MANAGE_WORKSPACES")
    registry.register(
        MANAGE_WORKSPACES_CAPABILITY,
        lifecycle_service,
        owner_id="FEAT-WS-MANAGE_WORKSPACES",
        scope=lifecycle_scope,
    )

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

    await feat.mount(context, config={})
    resolved = registry.resolve(SECURE_LOCAL_ACCESS_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, SecureLocalAccessCapability)
    await scope.close()
