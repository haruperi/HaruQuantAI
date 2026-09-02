"""Tests for Plugin Manifests feature lifecycle and mount."""

from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.contracts.plugins.ports import DeclareManifestsCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.manifests.feature import PluginManifestsFeature, feature
from app.services.plugins.manifests.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_feature_mount_and_provide() -> None:
    """Verify feature mount stages and provides the capability in the context."""
    feat = feature()
    assert isinstance(feat, PluginManifestsFeature)
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

    await feat.mount(context, {"max_file_count": 200})
    assert feat.service is not None

    resolved = registry.resolve(DECLARE_MANIFESTS_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, DeclareManifestsCapability)
    await scope.close()
