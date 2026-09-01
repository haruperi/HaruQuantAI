"""Unit tests for HostedWorkspaceFeature lifecycle and mounting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.workspace.capabilities import HOST_WORKSPACES_CAPABILITY
from app.contracts.workspace.ports import HostWorkspacesCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.hosted_workspace.feature import (
    HostedWorkspaceFeature,
    feature,
)
from app.services.workspace.hosted_workspace.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_feature_mount_and_discovery() -> None:
    """Test feature factory, mounting, and capability registration."""
    feat = feature()
    assert isinstance(feat, HostedWorkspaceFeature)
    assert feat.spec == SPEC

    registry = ServiceRegistry()
    event_bus = EventBus()
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

    await feat.mount(context, config={})
    resolved = registry.resolve(HOST_WORKSPACES_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, HostWorkspacesCapability)
    assert feat.service is not None
    await scope.close()
