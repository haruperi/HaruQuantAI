"""Tests for Plugin Contributions feature lifecycle and mount."""

from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.contracts.plugins.ports import RegisterContributionsCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.contributions.feature import (
    PluginContributionsFeature,
    feature,
)
from app.services.plugins.contributions.manifest import SPEC
from app.services.plugins.manifests.plugin_manifests import DeclareManifestsService

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


@pytest.mark.asyncio
async def test_feature_mount_and_provide() -> None:
    """Verify feature mount provides the capability in the context."""
    feat = feature()
    assert isinstance(feat, PluginContributionsFeature)
    assert feat.spec == SPEC

    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    # Register required upstream dependency
    manifest_service = DeclareManifestsService()
    manifest_scope = FeatureScope(owner_id="FEAT-PLUG-DECLARE_MANIFESTS")
    registry.register(
        DECLARE_MANIFESTS_CAPABILITY,
        manifest_service,
        owner_id="FEAT-PLUG-DECLARE_MANIFESTS",
        scope=manifest_scope,
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

    await feat.mount(context, {"max_contributions_per_plugin": 50})
    assert feat.service is not None

    resolved = registry.resolve(REGISTER_CONTRIBUTIONS_CAPABILITY)
    assert resolved is not None
    assert isinstance(resolved, RegisterContributionsCapability)

    await scope.close()
    await manifest_scope.close()
