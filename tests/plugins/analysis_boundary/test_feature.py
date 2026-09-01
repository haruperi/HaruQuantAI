"""Tests for IsolateAnalysisFeature lifecycle and mounting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.plugins.capabilities import (
    ISOLATE_ANALYSIS_CAPABILITY,
    SANDBOX_PERMISSIONS_CAPABILITY,
)

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.analysis_boundary.feature import (
    IsolateAnalysisFeature,
    feature,
)
from app.services.plugins.analysis_boundary.manifest import SPEC


def test_feature_factory() -> None:
    feat = feature()
    assert isinstance(feat, IsolateAnalysisFeature)
    assert feat.spec == SPEC
    assert feat.spec.feature_id == "FEAT-PLUG-ISOLATE_ANALYSIS"
    assert feat.spec.domain == "plugins"
    assert ISOLATE_ANALYSIS_CAPABILITY in feat.spec.provides
    assert SANDBOX_PERMISSIONS_CAPABILITY in feat.spec.optional


@pytest.mark.asyncio
async def test_feature_mount_and_unmount() -> None:
    feat = feature()
    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def register_provider(
        cap: CapabilityKey[Any],
        prov: Any,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, prov, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register_provider,
        event_bus=event_bus,
    )

    await feat.mount(context, {"max_input_handles": 10})
    active_service = feat.service
    assert active_service is not None

    resolved = registry.resolve(ISOLATE_ANALYSIS_CAPABILITY)
    assert resolved is active_service

    await feat.unmount(context)
    service_after = feat.service
    assert service_after is None
    await scope.close()
