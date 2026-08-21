"""Category C Composability Tests: Lifecycle-Leak & Churn Suite."""

import asyncio
from pathlib import Path
from typing import Any, override

import pytest

from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.events.system import FeatureMountedEvent
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext, FeatureContext
from app.kernel.events import EventBus, EventMode
from app.kernel.feature import Feature, FeatureSpec
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.broker.mock_feed.feature import MockFeedFeature
from app.services.data.historical_bars.feature import HistoricalBarsFeature
from app.services.system.storage.feature import StorageFeature


@pytest.mark.asyncio
async def test_100x_rapid_mount_unmount_churn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test mounting and unmounting features 100 times without resource accumulation."""
    engine = CompositionEngine()
    storage_feat = StorageFeature()
    mock_feed = MockFeedFeature()
    hist_bars = HistoricalBarsFeature()

    monkeypatch.setattr(
        FeatureDiscoverer,
        "discover",
        lambda _self: DiscoveryResult(
            discovered={
                "FEAT-SYS-PERSIST_STORAGE": storage_feat,
                "FEAT-BROKER-FEED_MOCK": mock_feed,
                "FEAT-DATA-RETRIEVE_BARS": hist_bars,
            }
        ),
    )

    db_file = tmp_path / "churn.db"
    enable_config = f"""
    [profile]
    name = "research"
    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = true
    db_path = "{db_file.as_posix()}"
    driver = "sqlite"
    [features.FEAT-BROKER-FEED_MOCK]
    enabled = true
    [features.FEAT-DATA-RETRIEVE_BARS]
    enabled = true
    """

    disable_config = """
    [profile]
    name = "research"
    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = false
    [features.FEAT-BROKER-FEED_MOCK]
    enabled = false
    [features.FEAT-DATA-RETRIEVE_BARS]
    enabled = false
    """

    for _ in range(100):
        # 1. Mount
        await engine.load_and_reconcile_toml(enable_config)
        assert len(engine.reconciler.active_features) == 3
        assert len(engine.registry.active_capabilities()) == 3

        # 2. Unmount
        await engine.load_and_reconcile_toml(disable_config)
        assert len(engine.reconciler.active_features) == 0
        assert len(engine.registry.active_capabilities()) == 0

    await engine.reconciler.stop_all()


class BuggyMountFeature(Feature):
    """Feature that deliberately crashes halfway through mount."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            feature_id="FEAT-TEST-BUGGY_MOUNT",
            domain="test",
            description="Deliberately fails mount",
            provides=frozenset({CapabilityKey[object](name="test.buggy", major=1)}),
        )

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        context.provide(
            CapabilityKey[object](name="test.buggy", major=1),
            object(),
        )
        raise RuntimeError("Simulated crash during mount")


@pytest.mark.asyncio
async def test_partial_mount_failure_rollback() -> None:
    """Test that a failure during mount immediately cleans up all partial effects."""
    feat = BuggyMountFeature()
    registry = ServiceRegistry()
    event_bus = EventBus()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def register_provider(cap: CapabilityKey[Any], prov: Any, sc: FeatureScope) -> None:
        registry.register(cap, prov, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register_provider,
        event_bus=event_bus,
    )
    with pytest.raises(RuntimeError, match="Simulated crash during mount"):
        await feat.mount(context, {})
    await scope.close()

    # Verify no dangling capabilities exist in registry
    assert len(registry.active_capabilities()) == 0


@pytest.mark.asyncio
async def test_background_task_and_listener_cleanup_on_unmount() -> None:
    """Test that spawned tasks are cancelled and event listeners are removed on unmount."""
    registry = ServiceRegistry()
    event_bus = EventBus()
    spec = FeatureSpec(
        feature_id="FEAT-TEST-BG_WORKER",
        domain="test",
        description="Worker test",
        provides=frozenset(),
    )
    scope = FeatureScope(owner_id=spec.feature_id)
    context = DefaultFeatureContext(
        spec=spec,
        scope=scope,
        resolver=registry.resolve,
        event_bus=event_bus,
    )

    task_ran = False
    task_cancelled = False
    stop_event = asyncio.Event()

    async def worker() -> None:
        nonlocal task_ran, task_cancelled
        task_ran = True
        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            task_cancelled = True
            raise

    # 1. Spawn background worker
    task = context.spawn(worker(), name="test_worker")
    await asyncio.sleep(0.02)
    assert task_ran is True
    assert not task.done()

    # 2. Subscribe to event
    events_received: list[FeatureMountedEvent] = []

    async def on_mounted(event: FeatureMountedEvent) -> None:
        events_received.append(event)

    context.subscribe(FeatureMountedEvent, on_mounted, mode=EventMode.PARALLEL)
    assert event_bus.listener_count(FeatureMountedEvent) == 1

    # 3. Close scope (unmount)
    await scope.close()

    # 4. Verify task cancelled and listener removed
    assert task_cancelled is True
    assert task.done()
    assert event_bus.listener_count(FeatureMountedEvent) == 0


@pytest.mark.asyncio
async def test_unexpected_task_failure_transitions_to_failed_runtime() -> None:
    """Characterization test: background task crash must transition owner to FAILED_RUNTIME and revoke capability."""
    cap_worker = CapabilityKey[object](name="test.worker_service", major=1)

    class CrashingWorkerFeature(Feature):
        @property
        def spec(self) -> FeatureSpec:
            return FeatureSpec(
                feature_id="FEAT-TEST-CRASHING_WORKER",
                domain="test",
                provides=frozenset({cap_worker}),
            )

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            context.provide(cap_worker, "active_worker_instance")

            async def crashing_loop() -> None:
                await asyncio.sleep(0.01)
                msg = "Simulated unexpected worker failure in runtime task"
                raise RuntimeError(msg)

            context.spawn(crashing_loop(), name="failing_task")

    feat = CrashingWorkerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)

    config_toml = """
    [profile]
    name = "research"
    [features.FEAT-TEST-CRASHING_WORKER]
    enabled = true
    """
    await engine.load_and_reconcile_toml(config_toml)
    assert engine.registry.is_available(cap_worker)
    assert (
        engine.reconciler.feature_states["FEAT-TEST-CRASHING_WORKER"].name == "ACTIVE"
    )

    # Wait for the task to crash
    await asyncio.sleep(0.05)

    # After unexpected task failure:
    # 1. Feature state must NOT remain ACTIVE
    state = engine.reconciler.feature_states.get("FEAT-TEST-CRASHING_WORKER")
    assert state is not None
    assert state.name == "FAILED_RUNTIME"

    # 2. Capability must be revoked
    assert not engine.registry.is_available(cap_worker), (
        "Capability was not revoked after runtime task crash"
    )

    await engine.shutdown()
