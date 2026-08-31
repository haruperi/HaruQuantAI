"""Regression tests for the final spatiotemporal-composability guarantees."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

import pytest
from app.composition.config import load_config_from_toml_string
from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.kernel.capability import CapabilityKey
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from app.kernel.graph import DependencyGraph, ProviderSelectionError

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


@dataclass(frozen=True, slots=True)
class ProviderService:
    """Provider test object carrying an implementation identity."""

    name: str
    generation: int


@dataclass(frozen=True, slots=True)
class ConsumerService:
    """Consumer test object retaining its provider reference."""

    provider: ProviderService


PROVIDER_CAP = CapabilityKey[ProviderService]("test.provider", 1)
CONSUMER_CAP = CapabilityKey[ConsumerService]("test.consumer", 1)
DOWNSTREAM_CAP = CapabilityKey[object]("test.downstream", 1)
OPTIONAL_CAP = CapabilityKey[object]("test.optional", 1)
OPTIONAL_CONSUMER_CAP = CapabilityKey[object]("test.optional-consumer", 1)


class NamedProviderFeature(Feature):
    """Test provider that records whether it was mounted."""

    def __init__(self, feature_id: str, name: str) -> None:
        self.spec = FeatureSpec(
            feature_id=feature_id,
            domain="test",
            provides=frozenset({PROVIDER_CAP}),
        )
        self.name = name
        self.mount_count = 0

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        self.mount_count += 1
        context.provide(
            PROVIDER_CAP,
            ProviderService(self.name, self.mount_count),
        )


class CapturingConsumerFeature(Feature):
    """Required consumer that exposes the provider instance it captured."""

    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUMER",
        domain="test",
        provides=frozenset({CONSUMER_CAP}),
        requires=frozenset({PROVIDER_CAP}),
    )

    def __init__(self) -> None:
        self.mount_count = 0
        self.captured: ProviderService | None = None

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        self.mount_count += 1
        self.captured = context.require(PROVIDER_CAP)
        context.provide(CONSUMER_CAP, ConsumerService(self.captured))


class DownstreamFeature(Feature):
    """Second-level required consumer."""

    spec = FeatureSpec(
        feature_id="FEAT-TEST-DOWNSTREAM",
        domain="test",
        provides=frozenset({DOWNSTREAM_CAP}),
        requires=frozenset({CONSUMER_CAP}),
    )

    def __init__(self) -> None:
        self.mount_count = 0
        self.captured: ConsumerService | None = None

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        self.mount_count += 1
        self.captured = context.require(CONSUMER_CAP)
        context.provide(DOWNSTREAM_CAP, object())


@pytest.mark.asyncio
async def test_selected_provider_is_the_only_provider_mounted() -> None:
    """Explicit provider selection controls graph and registry together."""
    provider_a = NamedProviderFeature("FEAT-TEST-PROVIDER_A", "A")
    provider_b = NamedProviderFeature("FEAT-TEST-PROVIDER_B", "B")
    consumer = CapturingConsumerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider_a)
    discoverer.register_feature(provider_b)
    discoverer.register_feature(consumer)
    engine = CompositionEngine(discoverer=discoverer)

    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [providers]
        "test.provider@1" = "FEAT-TEST-PROVIDER_B"
        [features.FEAT-TEST-PROVIDER_A]
        enabled = true
        [features.FEAT-TEST-PROVIDER_B]
        enabled = true
        [features.FEAT-TEST-CONSUMER]
        enabled = true
        """
    )

    assert provider_a.mount_count == 0
    assert provider_b.mount_count == 1
    assert consumer.captured is not None
    assert consumer.captured.name == "B"
    assert engine.registry.require(PROVIDER_CAP).name == "B"
    assert engine.reconciler.feature_states["FEAT-TEST-PROVIDER_A"] == (
        FeatureState.BLOCKED
    )
    await engine.shutdown()


def test_invalid_selection_fails_with_one_or_zero_candidates() -> None:
    """Configured providers are validated even when the choice is unambiguous."""
    only_provider = NamedProviderFeature("FEAT-TEST-PROVIDER_A", "A")
    graph = DependencyGraph({only_provider.spec.feature_id: only_provider.spec})
    with pytest.raises(
        ProviderSelectionError,
        match="disabled or was not discovered",
    ):
        graph.resolve(
            [only_provider.spec.feature_id],
            provider_selections={"test.provider@1": "FEAT-TEST-MISSING"},
        )
    with pytest.raises(ProviderSelectionError, match="does not provide"):
        graph.resolve(
            [only_provider.spec.feature_id],
            provider_selections={
                "test.other@1": only_provider.spec.feature_id,
            },
        )


def test_optional_only_cycle_does_not_block_activation() -> None:
    """Optional ordering cycles fall back to required-only ordering."""
    cap_a = CapabilityKey[object]("test.optional-a", 1)
    cap_b = CapabilityKey[object]("test.optional-b", 1)
    spec_a = FeatureSpec(
        "FEAT-TEST-OPTIONAL_A",
        "test",
        provides=frozenset({cap_a}),
        optional=frozenset({cap_b}),
    )
    spec_b = FeatureSpec(
        "FEAT-TEST-OPTIONAL_B",
        "test",
        provides=frozenset({cap_b}),
        optional=frozenset({cap_a}),
    )
    resolution = DependencyGraph(
        {spec_a.feature_id: spec_a, spec_b.feature_id: spec_b}
    ).resolve([spec_a.feature_id, spec_b.feature_id])
    assert set(resolution.eligible_features) == {
        spec_a.feature_id,
        spec_b.feature_id,
    }


class OptionalProviderFeature(Feature):
    """Optional root provider used to test capability disappearance."""

    spec = FeatureSpec(
        "FEAT-TEST-OPTIONAL_PROVIDER",
        "test",
        provides=frozenset({OPTIONAL_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(OPTIONAL_CAP, object())


class OptionalConsumerFeature(Feature):
    """Consumer that must refresh a captured optional provider reference."""

    spec = FeatureSpec(
        "FEAT-TEST-OPTIONAL_CONSUMER",
        "test",
        provides=frozenset({OPTIONAL_CONSUMER_CAP}),
        optional=frozenset({OPTIONAL_CAP}),
    )

    def __init__(self) -> None:
        self.mount_count = 0
        self.captured: object | None = None

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        self.mount_count += 1
        self.captured = context.optional(OPTIONAL_CAP)
        context.provide(OPTIONAL_CONSUMER_CAP, object())


@pytest.mark.asyncio
async def test_optional_provider_removal_remounts_consumer_without_provider() -> None:
    """Optional capability disappearance refreshes captured references."""
    provider = OptionalProviderFeature()
    consumer = OptionalConsumerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider)
    discoverer.register_feature(consumer)
    engine = CompositionEngine(discoverer=discoverer)

    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-OPTIONAL_PROVIDER]
        enabled = true
        [features.FEAT-TEST-OPTIONAL_CONSUMER]
        enabled = true
        """
    )
    first_optional = consumer.captured
    assert first_optional is not None
    assert consumer.mount_count == 1

    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-OPTIONAL_PROVIDER]
        enabled = false
        [features.FEAT-TEST-OPTIONAL_CONSUMER]
        enabled = true
        """
    )
    assert consumer.mount_count == 2
    assert consumer.captured is None
    assert engine.registry.is_available(OPTIONAL_CONSUMER_CAP)
    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_replacement_remounts_two_level_consumer_chain() -> None:
    """Provider replacement eliminates stale references in all consumers."""
    provider = NamedProviderFeature("FEAT-TEST-PROVIDER_A", "provider")
    consumer = CapturingConsumerFeature()
    downstream = DownstreamFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider)
    discoverer.register_feature(consumer)
    discoverer.register_feature(downstream)
    engine = CompositionEngine(discoverer=discoverer)

    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-PROVIDER_A]
        enabled = true
        [features.FEAT-TEST-CONSUMER]
        enabled = true
        [features.FEAT-TEST-DOWNSTREAM]
        enabled = true
        """
    )
    first_provider = consumer.captured
    assert first_provider is not None
    assert first_provider.generation == 1

    report = await engine.replace_feature_transactional_detailed("FEAT-TEST-PROVIDER_A")
    assert report.committed
    assert report.status == "committed"
    assert not report.consumer_errors
    assert provider.mount_count == 2
    assert consumer.mount_count == 2
    assert downstream.mount_count == 2
    assert consumer.captured is not first_provider
    assert consumer.captured is not None
    assert consumer.captured.generation == 2
    assert downstream.captured is not None
    assert downstream.captured.provider is consumer.captured
    await engine.shutdown()


class SlowProviderFeature(Feature):
    """Provider used to prove reconciliation mutations do not overlap."""

    spec = FeatureSpec(
        "FEAT-TEST-SLOW_PROVIDER",
        "test",
        provides=frozenset({PROVIDER_CAP}),
    )

    def __init__(self) -> None:
        self.mount_count = 0
        self.concurrent_mounts = 0
        self.max_concurrent_mounts = 0

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        self.concurrent_mounts += 1
        self.max_concurrent_mounts = max(
            self.max_concurrent_mounts,
            self.concurrent_mounts,
        )
        try:
            await asyncio.sleep(0.01)
            self.mount_count += 1
            generation = (
                int(config.get("generation", self.mount_count))
                if isinstance(config, dict)
                else self.mount_count
            )
            context.provide(
                PROVIDER_CAP,
                ProviderService("slow", generation),
            )
        finally:
            self.concurrent_mounts -= 1


@pytest.mark.asyncio
async def test_reload_and_replacement_are_serialized() -> None:
    """Concurrent mutation requests never overlap feature mounts."""
    feature = SlowProviderFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feature)
    engine = CompositionEngine(discoverer=discoverer)
    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-SLOW_PROVIDER]
        enabled = true
        generation = 1
        """
    )

    reloaded = load_config_from_toml_string(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-SLOW_PROVIDER]
        enabled = true
        generation = 2
        """
    )
    reload_result, replacement_result = await asyncio.gather(
        engine.hot_reload_config(reloaded),
        engine.replace_feature_transactional_detailed(
            "FEAT-TEST-SLOW_PROVIDER",
            new_config={"generation": 3},
        ),
    )
    assert reload_result.active_features == ("FEAT-TEST-SLOW_PROVIDER",)
    assert replacement_result.committed
    assert feature.max_concurrent_mounts == 1
    assert engine.registry.is_available(PROVIDER_CAP)
    await engine.shutdown()
