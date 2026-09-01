"""Tests for ResultPanelsFeature lifecycle and mounting."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
    RENDER_RESULT_PANELS_CAPABILITY,
)

if TYPE_CHECKING:
    from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.result_panels.feature import (
    ResultPanelsFeature,
    feature,
)
from app.services.plugins.result_panels.manifest import SPEC


def test_feature_factory() -> None:
    feat = feature()
    assert isinstance(feat, ResultPanelsFeature)
    assert feat.spec == SPEC
    assert feat.spec.feature_id == "FEAT-PLUG-RENDER_RESULT_PANELS"
    assert feat.spec.domain == "plugins"
    assert RENDER_RESULT_PANELS_CAPABILITY in feat.spec.provides
    assert REGISTER_CONTRIBUTIONS_CAPABILITY in feat.spec.optional


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

    await feat.mount(context, {"max_panels_per_query": 50})
    active_service = feat.service
    assert active_service is not None

    resolved = registry.resolve(RENDER_RESULT_PANELS_CAPABILITY)
    assert resolved is active_service

    await feat.unmount(context)
    service_after = feat.service
    assert service_after is None
    await scope.close()
