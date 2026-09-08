"""Unit tests for DeclareManifestsFeature lifecycle and entry points."""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.contracts.plugins.ports import DeclareManifestsCapability
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.declare_manifests.feature import (
    DeclareManifestsFeature,
    feature,
)
from app.services.plugins.declare_manifests.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey


def test_feature_factory_and_spec() -> None:
    """Verify feature factory and SPEC declaration."""
    feat = feature()
    assert isinstance(feat, DeclareManifestsFeature)
    assert feat.spec == SPEC
    assert feat.spec.feature_id == "FEAT-PLUG-DECLARE_MANIFESTS"
    assert feat.spec.domain == "plugins"
    assert DECLARE_MANIFESTS_CAPABILITY in feat.spec.provides
    assert not feat.spec.requires
    assert feat.spec.config_keys == frozenset(
        {"max_package_size_bytes", "max_file_count", "strict_signatures"}
    )
    assert feat.service is None


@pytest.mark.asyncio
async def test_feature_mount() -> None:
    """Verify feature mounting provides DECLARE_MANIFESTS_CAPABILITY in context."""
    registry = ServiceRegistry()
    event_bus = EventBus()
    feat = DeclareManifestsFeature()
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

    await feat.mount(context, {"max_package_size_bytes": 1024 * 1024})

    assert feat.service is not None
    resolved = registry.resolve(DECLARE_MANIFESTS_CAPABILITY)
    assert resolved is not None
    assert resolved is feat.service
    assert isinstance(resolved, DeclareManifestsCapability)

    await scope.close()


def test_entry_point_discovery() -> None:
    """Verify that plugins-declare-manifests is registered in haruquantai.features."""
    eps = importlib.metadata.entry_points(group="haruquantai.features")
    matching = [ep for ep in eps if ep.name == "plugins-declare-manifests"]
    assert len(matching) == 1
    loaded = matching[0].load()
    instance = loaded()
    assert isinstance(instance, DeclareManifestsFeature)
