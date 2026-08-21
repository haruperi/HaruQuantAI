"""Category C composability tests: lifecycle leaks and churn."""

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

MockFeedFeature = pytest.importorskip(
    "app.services.broker.mock_feed.feature"
).MockFeedFeature
HistoricalBarsFeature = pytest.importorskip(
    "app.services.data.historical_bars.feature"
).HistoricalBarsFeature
StorageFeature = pytest.importorskip(
    "app.services.system.storage.feature"
).StorageFeature


@pytest.mark.asyncio
async def test_100x_rapid_mount_unmount_churn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    [application]
    profile = "research"
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
    [application]
    profile = "research"
    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = false
    [features.FEAT-BROKER-FEED_MOCK]
    enabled = false
    [features.FEAT-DATA-RETRIEVE_BARS]
    enabled = false
    """
    for _ in range(100):
        await engine.load_and_reconcile_toml(enable_config)
        assert len(engine.reconciler.active_features) == 3
        assert len(engine.registry.active_capabilities()) == 3
        await engine.load_and_reconcile_toml(disable_config)
        assert len(engine.reconciler.active_features) == 0
        assert len(engine.registry.active_capabilities()) == 0
    await engine.shutdown()


class BuggyMountFeature(Feature):
    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            feature_id="FEAT-TEST-BUGGY_MOUNT",
            domain="test",
            provides=frozenset({CapabilityKey[object](name="test.buggy", major=1)}),
        )

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        _ = config
        context.provide(CapabilityKey[object](name="test.buggy", major=1), object())
        raise RuntimeError("Simulated crash during mount")


@pytest.mark.asyncio
async def test_partial_mount_failure_rollback() -> None:
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
    assert registry.active_capabilities() == {}


@pytest.mark.asyncio
async def test_background_task_and_listener_cleanup_on_unmount() -> None:
    registry = ServiceRegistry()
    event_bus = EventBus()
    spec = FeatureSpec(
        feature_id="FEAT-TEST-BG_WORKER",
        domain="test",
        provides=frozenset(),
    )
    scope = FeatureScope(owner_id=spec.feature_id)
    context = DefaultFeatureContext(
        spec=spec,
        scope=scope,
        resolver=registry.resolve,
        event_bus=event_bus,
    )
    task_cancelled = False

    async def worker() -> None:
        nonlocal task_cancelled
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            task_cancelled = True
            raise

    task = context.spawn(worker(), name="test_worker")
    await asyncio.sleep(0.02)
    events_received: list[FeatureMountedEvent] = []

    async def on_mounted(event: FeatureMountedEvent) -> None:
        events_received.append(event)

    context.subscribe(FeatureMountedEvent, on_mounted, mode=EventMode.PARALLEL)
    assert event_bus.listener_count(FeatureMountedEvent) == 1
    await scope.close()
    assert task_cancelled
    assert task.done()
    assert event_bus.listener_count(FeatureMountedEvent) == 0
