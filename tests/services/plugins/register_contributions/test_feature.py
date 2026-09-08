"""Tests for Plugin Contributions feature lifecycle adapter."""

from __future__ import annotations

from typing import Any

import pytest
from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.contracts.plugins.ports import RegisterContributionsCapability
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.declare_manifests.declare_manifests import (
    DeclareManifestsService,
)
from app.services.plugins.register_contributions.feature import (
    RegisterContributionsFeature,
    feature,
)
from app.services.plugins.register_contributions.manifest import SPEC


def test_feature_factory() -> None:
    """Verify feature factory returns initialized instance."""
    feat = feature()
    assert isinstance(feat, RegisterContributionsFeature)
    assert feat.spec == SPEC
    assert REGISTER_CONTRIBUTIONS_CAPABILITY in SPEC.provides
    assert DECLARE_MANIFESTS_CAPABILITY in SPEC.requires


@pytest.mark.asyncio
async def test_feature_mount_and_unmount() -> None:
    """Verify feature mount provides the capability and unmount clears it."""
    feat = feature()
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

    # Test explicit unmount
    await feat.unmount(context)
    assert feat.service is None

    await scope.close()


def test_entry_point_discovery() -> None:
    """Verify that plugins-register-contributions is registered in haruquantai.features."""
    import importlib.metadata

    eps = importlib.metadata.entry_points(group="haruquantai.features")
    matching = [ep for ep in eps if ep.name == "plugins-register-contributions"]
    assert len(matching) == 1
    loaded = matching[0].load()
    instance = loaded()
    assert isinstance(instance, RegisterContributionsFeature)
