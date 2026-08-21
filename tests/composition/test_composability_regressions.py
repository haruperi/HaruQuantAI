"""Regression tests for remediated spatiotemporal composability guarantees."""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.kernel.capability import CapabilityKey
from app.kernel.events import EventMode
from app.kernel.feature import FeatureSpec, FeatureState

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


@dataclass(frozen=True, slots=True)
class PingEvent:
    value: int


PROVIDER_CAP = CapabilityKey[object]("test.provider", 1)
CONSUMER_CAP = CapabilityKey[object]("test.consumer", 1)


class ProviderService:
    def __init__(self, generation: int) -> None:
        self.generation = generation


class ProviderFeature:
    spec = FeatureSpec(
        feature_id="FEAT-TEST-PROVIDER",
        domain="test",
        provides=frozenset({PROVIDER_CAP}),
    )

    def __init__(self) -> None:
        self.mounts = 0
        self.worker_cancelled = False
        self.events: list[int] = []

    async def mount(self, context: FeatureContext, config: object) -> None:
        self.mounts += 1
        generation = int(config.get("generation", self.mounts)) if isinstance(config, dict) else self.mounts
        context.provide(PROVIDER_CAP, ProviderService(generation))

        async def worker() -> None:
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                self.worker_cancelled = True
                raise

        async def on_ping(event: PingEvent) -> None:
            self.events.append(event.value)

        context.spawn(worker(), name="provider-worker")
        context.subscribe(PingEvent, on_ping, mode=EventMode.PUBLISH)


class ConsumerService:
    def __init__(self, provider: ProviderService) -> None:
        self.provider = provider


class ConsumerFeature:
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUMER",
        domain="test",
        provides=frozenset({CONSUMER_CAP}),
        requires=frozenset({PROVIDER_CAP}),
    )

    def __init__(self) -> None:
        self.mounts = 0

    async def mount(self, context: FeatureContext, config: object) -> None:
        _ = config
        self.mounts += 1
        provider = context.require(PROVIDER_CAP)
        assert isinstance(provider, ProviderService)
        context.provide(CONSUMER_CAP, ConsumerService(provider))


@pytest.mark.asyncio
async def test_provider_config_change_remounts_transitive_consumer() -> None:
    provider = ProviderFeature()
    consumer = ConsumerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider)
    discoverer.register_feature(consumer)
    engine = CompositionEngine(discoverer=discoverer)

    first = """
    [application]
    profile = "research"
    [features.FEAT-TEST-PROVIDER]
    enabled = true
    generation = 1
    [features.FEAT-TEST-CONSUMER]
    enabled = true
    """
    await engine.load_and_reconcile_toml(first)
    old_consumer = engine.registry.require(CONSUMER_CAP)
    assert isinstance(old_consumer, ConsumerService)
    assert old_consumer.provider.generation == 1

    second = first.replace("generation = 1", "generation = 2")
    report = await engine.load_and_reconcile_toml(second)
    assert "FEAT-TEST-PROVIDER" in report.stopped
    assert "FEAT-TEST-CONSUMER" in report.stopped
    assert "FEAT-TEST-PROVIDER" in report.started
    assert "FEAT-TEST-CONSUMER" in report.started

    new_consumer = engine.registry.require(CONSUMER_CAP)
    assert isinstance(new_consumer, ConsumerService)
    assert new_consumer is not old_consumer
    assert new_consumer.provider.generation == 2
    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_replacement_preserves_staged_tasks_and_listeners() -> None:
    provider = ProviderFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider)
    engine = CompositionEngine(discoverer=discoverer)
    config = """
    [application]
    profile = "research"
    [features.FEAT-TEST-PROVIDER]
    enabled = true
    generation = 1
    """
    await engine.load_and_reconcile_toml(config)

    success, warning = await engine.replace_feature_transactional(
        "FEAT-TEST-PROVIDER",
        {"generation": 2},
    )
    assert success
    assert warning is None
    service = engine.registry.require(PROVIDER_CAP)
    assert isinstance(service, ProviderService)
    assert service.generation == 2

    await engine.event_bus.publish(PingEvent(7))
    await asyncio.sleep(0)
    assert provider.events[-1] == 7
    assert "FEAT-TEST-PROVIDER" in engine.reconciler.active_features
    await engine.shutdown()


class CrashingFeature:
    spec = FeatureSpec(
        feature_id="FEAT-TEST-RUNTIME-CRASH",
        domain="test",
        provides=frozenset({PROVIDER_CAP}),
    )

    async def mount(self, context: FeatureContext, config: object) -> None:
        _ = config
        context.provide(PROVIDER_CAP, object())

        async def crash() -> None:
            await asyncio.sleep(0.01)
            raise RuntimeError("runtime crash")

        context.spawn(crash(), name="crasher")


@pytest.mark.asyncio
async def test_background_task_failure_transitions_owner_to_failed_runtime() -> None:
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(CrashingFeature())
    engine = CompositionEngine(discoverer=discoverer)
    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "research"
        [features.FEAT-TEST-RUNTIME-CRASH]
        enabled = true
        """
    )
    await asyncio.sleep(0.05)
    assert (
        engine.reconciler.feature_states["FEAT-TEST-RUNTIME-CRASH"]
        == FeatureState.FAILED_RUNTIME
    )
    assert not engine.registry.is_available(PROVIDER_CAP)
    await engine.shutdown()
