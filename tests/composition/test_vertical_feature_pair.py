"""Removal-safe integration test for a neutral provider-consumer pair."""

from typing import TYPE_CHECKING, override

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from tests._support.composability import (
    CONSUMER_CAPABILITY,
    PROVIDER_CAPABILITY,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ProviderService:
    """Business-neutral provider test object."""


class ConsumerService:
    """Consumer retaining the exact resolved provider instance."""

    def __init__(self, provider: object) -> None:
        self.provider = provider


class ProviderFeature(Feature):
    """Local provider used by core composability tests."""

    spec = FeatureSpec(
        "FEAT-TEST-VERTICAL_PROVIDER",
        "test",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(PROVIDER_CAPABILITY, ProviderService())


class ConsumerFeature(Feature):
    """Local required consumer used by core composability tests."""

    spec = FeatureSpec(
        "FEAT-TEST-VERTICAL_CONSUMER",
        "test",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(
            CONSUMER_CAPABILITY,
            ConsumerService(context.require(PROVIDER_CAPABILITY)),
        )


@pytest.mark.asyncio
async def test_vertical_pair_provider_loss_and_recovery() -> None:
    """Required capability loss blocks and later remounts its consumer."""
    provider = ProviderFeature()
    consumer = ConsumerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider)
    discoverer.register_feature(consumer)
    engine = CompositionEngine(discoverer=discoverer)

    enabled = """
    [application]
    profile = "offline"
    [features.FEAT-TEST-VERTICAL_PROVIDER]
    enabled = true
    [features.FEAT-TEST-VERTICAL_CONSUMER]
    enabled = true
    """
    provider_disabled = """
    [application]
    profile = "offline"
    [features.FEAT-TEST-VERTICAL_PROVIDER]
    enabled = false
    [features.FEAT-TEST-VERTICAL_CONSUMER]
    enabled = true
    """

    await engine.load_and_reconcile_toml(enabled)
    service = engine.registry.require(CONSUMER_CAPABILITY)
    assert isinstance(service, ConsumerService)
    assert isinstance(service.provider, ProviderService)

    await engine.load_and_reconcile_toml(provider_disabled)
    assert not engine.registry.is_available(PROVIDER_CAPABILITY)
    assert not engine.registry.is_available(CONSUMER_CAPABILITY)
    assert engine.reconciler.feature_states[consumer.spec.feature_id] == (
        FeatureState.BLOCKED
    )
    assert engine.get_status().is_ready

    await engine.load_and_reconcile_toml(enabled)
    assert engine.registry.is_available(CONSUMER_CAPABILITY)
    assert engine.get_status().is_ready
    await engine.shutdown()
