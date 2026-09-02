"""Lifecycle tests for plugin development compatibility."""

from typing import Any

import pytest
from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    MAINTAIN_COMPATIBILITY_CAPABILITY,
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.contributions.plugin_contributions import (
    RegisterContributionsService,
)
from app.services.plugins.development_compatibility.feature import (
    DevelopmentCompatibilityFeature,
    feature,
)
from app.services.plugins.development_compatibility.manifest import SPEC
from app.services.plugins.manifests.plugin_manifests import DeclareManifestsService


def test_feature_factory_and_spec() -> None:
    instance = feature()
    assert isinstance(instance, DevelopmentCompatibilityFeature)
    assert instance.spec == SPEC
    assert MAINTAIN_COMPATIBILITY_CAPABILITY in SPEC.provides
    assert DECLARE_MANIFESTS_CAPABILITY in SPEC.requires
    assert REGISTER_CONTRIBUTIONS_CAPABILITY in SPEC.requires


@pytest.mark.asyncio
async def test_feature_mounts_provider_and_clears_on_unmount() -> None:
    instance = feature()
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id=SPEC.feature_id)

    def register(capability: Any, provider: Any, owner_scope: FeatureScope) -> None:
        registry.register(
            capability, provider, owner_id=SPEC.feature_id, scope=owner_scope
        )

    registry.register(
        DECLARE_MANIFESTS_CAPABILITY,
        DeclareManifestsService(),
        owner_id="test.manifests",
        scope=scope,
    )
    registry.register(
        REGISTER_CONTRIBUTIONS_CAPABILITY,
        RegisterContributionsService(),
        owner_id="test.contributions",
        scope=scope,
    )
    context = DefaultFeatureContext(
        spec=SPEC,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )
    await instance.mount(context, {})
    assert registry.resolve(MAINTAIN_COMPATIBILITY_CAPABILITY) is instance.service
    await instance.unmount(context)
    assert instance.service is None
    await scope.close()
