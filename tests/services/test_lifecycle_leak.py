"""Removal-safe lifecycle leak, churn, and runtime-failure tests."""

from __future__ import annotations

import asyncio
from typing import Any, override

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.events.system import FeatureMountedEvent
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext, FeatureContext
from app.kernel.events import EventBus, EventMode
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope

ROOT_CAP = CapabilityKey[object]("test.churn-root", 1)
CONSUMER_CAP = CapabilityKey[object]("test.churn-consumer", 1)
UNRELATED_CAP = CapabilityKey[object]("test.unrelated", 1)
CRASHING_CAP = CapabilityKey[object]("test.crashing", 1)


def _active_feature_count(engine: CompositionEngine) -> int:
    """Return a fresh active-feature count after lifecycle mutations."""
    return len(engine.reconciler.active_features)


def _active_capability_count(engine: CompositionEngine) -> int:
    """Return a fresh active-capability count after lifecycle mutations."""
    return len(engine.registry.active_capabilities())


class ChurnRootFeature(Feature):
    """Root feature used by rapid mount/unmount tests."""

    spec = FeatureSpec(
        "FEAT-TEST-CHURN_ROOT",
        "test",
        provides=frozenset({ROOT_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(ROOT_CAP, object())


class ChurnConsumerFeature(Feature):
    """Required consumer used by rapid mount/unmount tests."""

    spec = FeatureSpec(
        "FEAT-TEST-CHURN_CONSUMER",
        "test",
        provides=frozenset({CONSUMER_CAP}),
        requires=frozenset({ROOT_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.require(ROOT_CAP)
        context.provide(CONSUMER_CAP, object())


class UnrelatedFeature(Feature):
    """Feature whose capability must survive unrelated failures."""

    spec = FeatureSpec(
        "FEAT-TEST-UNRELATED",
        "test",
        provides=frozenset({UNRELATED_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(UNRELATED_CAP, object())


@pytest.mark.asyncio
async def test_100x_rapid_mount_unmount_churn() -> None:
    """Repeated composition leaves no provider or listener accumulation."""
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(ChurnRootFeature())
    discoverer.register_feature(ChurnConsumerFeature())
    discoverer.register_feature(UnrelatedFeature())
    engine = CompositionEngine(discoverer=discoverer)

    enabled = """
    [application]
    profile = "offline"
    [features.FEAT-TEST-CHURN_ROOT]
    enabled = true
    [features.FEAT-TEST-CHURN_CONSUMER]
    enabled = true
    [features.FEAT-TEST-UNRELATED]
    enabled = true
    """
    disabled = """
    [application]
    profile = "offline"
    [features.FEAT-TEST-CHURN_ROOT]
    enabled = false
    [features.FEAT-TEST-CHURN_CONSUMER]
    enabled = false
    [features.FEAT-TEST-UNRELATED]
    enabled = false
    """

    for _ in range(100):
        await engine.load_and_reconcile_toml(enabled)
        assert _active_feature_count(engine) == 3
        assert _active_capability_count(engine) == 3
        await engine.load_and_reconcile_toml(disabled)
        assert _active_feature_count(engine) == 0
        assert _active_capability_count(engine) == 0
        assert engine.event_bus.listener_count() == 0
    await engine.shutdown()


class BuggyMountFeature(Feature):
    """Feature that fails after registering a staged provider."""

    BUGGY_CAP = CapabilityKey[object]("test.buggy", 1)
    spec = FeatureSpec(
        "FEAT-TEST-BUGGY_MOUNT",
        "test",
        provides=frozenset({BUGGY_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(self.BUGGY_CAP, object())
        raise RuntimeError("Simulated crash during mount")


@pytest.mark.asyncio
async def test_partial_mount_failure_rolls_back_every_effect() -> None:
    """A failed mount never publishes its staged capability."""
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(BuggyMountFeature())
    engine = CompositionEngine(discoverer=discoverer)
    report = await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-BUGGY_MOUNT]
        enabled = true
        """
    )
    assert "FEAT-TEST-BUGGY_MOUNT" in report.errors
    assert not engine.registry.is_available(BuggyMountFeature.BUGGY_CAP)
    await engine.shutdown()


@pytest.mark.asyncio
async def test_background_task_and_listener_cleanup_on_scope_close() -> None:
    """Closing a scope cancels tasks and removes exact subscriptions."""
    event_bus = EventBus()
    scope = FeatureScope("FEAT-TEST-WORKER")
    spec = FeatureSpec("FEAT-TEST-WORKER", "test", provides=frozenset())
    context = DefaultFeatureContext(spec=spec, scope=scope, event_bus=event_bus)
    task_started = False
    task_cancelled = False
    wait_forever = asyncio.Event()

    async def worker() -> None:
        nonlocal task_started, task_cancelled
        task_started = True
        try:
            await wait_forever.wait()
        except asyncio.CancelledError:
            task_cancelled = True
            raise

    task = context.spawn(worker(), name="worker")
    await asyncio.sleep(0)
    assert task_started

    async def handler(_event: FeatureMountedEvent) -> None:
        return None

    context.subscribe(FeatureMountedEvent, handler, mode=EventMode.PARALLEL)
    assert event_bus.listener_count(FeatureMountedEvent) == 1
    await scope.close()
    assert task.done()
    assert task_cancelled
    assert event_bus.listener_count(FeatureMountedEvent) == 0


class CrashingProviderFeature(Feature):
    """Provider whose worker raises after activation."""

    spec = FeatureSpec(
        "FEAT-TEST-CRASHING_PROVIDER",
        "test",
        provides=frozenset({CRASHING_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(CRASHING_CAP, object())

        async def crash() -> None:
            await asyncio.sleep(0.01)
            raise RuntimeError("Simulated provider worker failure")

        context.spawn(crash(), name="crashing-worker")


class RequiredCrashConsumer(Feature):
    """Required consumer that must block when its provider crashes."""

    spec = FeatureSpec(
        "FEAT-TEST-CRASH_CONSUMER",
        "test",
        provides=frozenset({CONSUMER_CAP}),
        requires=frozenset({CRASHING_CAP}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.require(CRASHING_CAP)
        context.provide(CONSUMER_CAP, object())


@pytest.mark.asyncio
async def test_runtime_failure_blocks_required_consumers_only() -> None:
    """A crashed provider removes dependents but preserves unrelated features."""
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(CrashingProviderFeature())
    discoverer.register_feature(RequiredCrashConsumer())
    discoverer.register_feature(UnrelatedFeature())
    engine = CompositionEngine(discoverer=discoverer)
    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-CRASHING_PROVIDER]
        enabled = true
        [features.FEAT-TEST-CRASH_CONSUMER]
        enabled = true
        [features.FEAT-TEST-UNRELATED]
        enabled = true
        """
    )
    await asyncio.sleep(0.08)

    status = engine.get_status()
    assert status.feature_states["FEAT-TEST-CRASHING_PROVIDER"] == (
        FeatureState.FAILED_RUNTIME
    )
    assert status.feature_states["FEAT-TEST-CRASH_CONSUMER"] == (
        FeatureState.BLOCKED
    )
    assert status.feature_states["FEAT-TEST-UNRELATED"] == FeatureState.ACTIVE
    assert not engine.registry.is_available(CRASHING_CAP)
    assert not engine.registry.is_available(CONSUMER_CAP)
    assert engine.registry.is_available(UNRELATED_CAP)
    assert "FEAT-TEST-CRASHING_PROVIDER" in status.runtime_failures
    await engine.shutdown()


@pytest.mark.asyncio
async def test_partial_scope_rollback_without_engine() -> None:
    """A raw FeatureContext can roll back an interrupted mount."""
    feature = BuggyMountFeature()
    registry = ServiceRegistry()
    scope = FeatureScope(feature.spec.feature_id)

    def registrar(
        capability: CapabilityKey[Any],
        provider: Any,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            provider,
            feature.spec.feature_id,
            scope=owner_scope,
        )

    context = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
    )
    with pytest.raises(RuntimeError, match="Simulated crash"):
        await feature.mount(context, {})
    await scope.close()
    assert not registry.active_capabilities()
