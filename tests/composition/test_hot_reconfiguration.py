"""Tests verifying Phase 15: hot reconfiguration and transactional feature replacement."""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest

from app.composition.config import load_config_from_toml_string
from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.composition.watcher import ConfigFileWatcher
from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.contracts.events.system import (
    ConfigurationReloadedEvent,
    FeatureReconfiguredEvent,
)
from app.kernel.feature import Feature, FeatureSpec

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.kernel.context import FeatureContext


class ConfigurableBrokerService(BrokerMarketData):
    """Broker test double capturing configuration state."""

    def __init__(self, base_price: float = 1.0) -> None:
        self.base_price = base_price

    @override
    async def retrieve_bars(self, request: BrokerBarsRequest) -> Sequence[BrokerRawBar]:
        return (
            BrokerRawBar(
                timestamp=request.start,
                open_price=self.base_price,
                high_price=self.base_price + 1.0,
                low_price=self.base_price - 1.0,
                close_price=self.base_price,
                volume=100.0,
            ),
        )


class ConfigurableBrokerFeature(Feature):
    """Feature supporting dynamic reconfiguration and health check."""

    def __init__(self, should_fail_mount: bool = False) -> None:
        self.should_fail_mount = should_fail_mount
        self.mount_count = 0
        self.active_base_price = 1.0

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            feature_id="FEAT-BROKER-CONFIGURABLE",
            domain="broker",
            description="Configurable broker feature",
            provides=frozenset({BROKER_MARKET_DATA}),
            requires=frozenset(),
        )

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        if self.should_fail_mount:
            msg = "Simulated shadow mount crash"
            raise RuntimeError(msg)
        self.mount_count += 1
        cfg_dict = config if isinstance(config, dict) else {}
        self.active_base_price = float(cfg_dict.get("base_price", 1.0))
        service = ConfigurableBrokerService(base_price=self.active_base_price)
        context.provide(BROKER_MARKET_DATA, service)


@pytest.mark.asyncio
async def test_live_configuration_hot_reload() -> None:
    """Test hot reloading config updates and remounting only modified features."""
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)

    engine = CompositionEngine(discoverer=discoverer)
    events_received: list[ConfigurationReloadedEvent] = []

    async def on_reload(event: ConfigurationReloadedEvent) -> None:
        events_received.append(event)

    engine.event_bus.subscribe(ConfigurationReloadedEvent, on_reload)

    # Initial Mount
    initial_toml = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-CONFIGURABLE]
    enabled = true
    base_price = 1.10
    """
    await engine.load_and_reconcile_toml(initial_toml)
    assert feat.mount_count == 1
    assert feat.active_base_price == 1.10

    # Hot reload with updated config
    updated_toml = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-CONFIGURABLE]
    enabled = true
    base_price = 1.25
    """
    updated_cfg = load_config_from_toml_string(updated_toml)
    report = await engine.hot_reload_config(updated_cfg)

    assert "FEAT-BROKER-CONFIGURABLE" in report.started
    assert feat.mount_count == 2
    assert feat.active_base_price == 1.25
    assert len(events_received) == 1
    assert "FEAT-BROKER-CONFIGURABLE" in events_received[0].modified_features

    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_feature_replacement_success() -> None:
    """Test zero-downtime transactional feature replacement via shadow scopes."""
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)

    engine = CompositionEngine(discoverer=discoverer)
    reconfigured_events: list[FeatureReconfiguredEvent] = []

    async def on_reconfigured(event: FeatureReconfiguredEvent) -> None:
        reconfigured_events.append(event)

    engine.event_bus.subscribe(FeatureReconfiguredEvent, on_reconfigured)

    initial_toml = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-CONFIGURABLE]
    enabled = true
    base_price = 2.0
    """
    await engine.load_and_reconcile_toml(initial_toml)
    initial_binding = engine.registry.get_binding(BROKER_MARKET_DATA.identifier)
    assert initial_binding is not None
    assert initial_binding.token.generation == 1

    # Perform transactional swap
    success, err = await engine.replace_feature_transactional(
        "FEAT-BROKER-CONFIGURABLE",
        new_config={"base_price": 3.5},
    )
    assert success is True
    assert err is None
    assert feat.active_base_price == 3.5

    # Generation counter must increment
    swapped_binding = engine.registry.get_binding(BROKER_MARKET_DATA.identifier)
    assert swapped_binding is not None
    assert swapped_binding.token.generation == 2
    assert len(reconfigured_events) == 1
    assert reconfigured_events[0].generation == 2

    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_feature_replacement_failure_rollback() -> None:
    """Test that failure during shadow mount rolls back without affecting active provider."""
    good_feat = ConfigurableBrokerFeature(should_fail_mount=False)
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(good_feat)

    engine = CompositionEngine(discoverer=discoverer)
    initial_toml = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-CONFIGURABLE]
    enabled = true
    base_price = 10.0
    """
    await engine.load_and_reconcile_toml(initial_toml)
    active_service = engine.registry.require(BROKER_MARKET_DATA)
    assert isinstance(active_service, ConfigurableBrokerService)
    assert active_service.base_price == 10.0

    # Configure feature to fail on next mount
    good_feat.should_fail_mount = True

    success, err = await engine.replace_feature_transactional(
        "FEAT-BROKER-CONFIGURABLE",
        new_config={"base_price": 99.0},
    )
    assert success is False
    assert err is not None
    assert "Simulated shadow mount crash" in err

    # Active provider MUST still be active, untouched, and functional!
    current_service = engine.registry.require(BROKER_MARKET_DATA)
    assert current_service is active_service
    assert current_service.base_price == 10.0

    await engine.shutdown()


@pytest.mark.asyncio
async def test_config_file_watcher_polling(tmp_path: Path) -> None:
    """Test ConfigFileWatcher detects file changes and triggers reconciliation."""
    config_file = tmp_path / "app.toml"
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)

    engine = CompositionEngine(discoverer=discoverer)

    # Initial write
    config_file.write_text(
        """
        [profile]
        name = "research"
        [features.FEAT-BROKER-CONFIGURABLE]
        enabled = true
        base_price = 5.0
        """,
        encoding="utf-8",
    )

    await engine.load_and_reconcile_file(config_file)
    assert feat.active_base_price == 5.0

    watcher = ConfigFileWatcher(
        config_path=config_file,
        engine=engine,
        poll_interval=0.05,
        debounce=0.01,
    )
    watcher.start()
    assert watcher.is_running is True

    try:
        # Update config file on disk
        await asyncio.sleep(0.05)
        config_file.write_text(
            """
            [profile]
            name = "research"
            [features.FEAT-BROKER-CONFIGURABLE]
            enabled = true
            base_price = 8.5
            """,
            encoding="utf-8",
        )

        # Trigger manual check or wait for loop
        reloaded = await watcher.check_and_reload()
        assert reloaded is True
        assert feat.active_base_price == 8.5
    finally:
        await watcher.stop()
        assert watcher.is_running is False
        await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_replacement_preserves_staged_effects_after_commit() -> (
    None
):
    """Characterization test: replacement effects (tasks, listeners, callbacks) must survive after commit."""
    task_running = False
    task_cancelled = False
    listener_invoked = False
    callback_cleaned = False

    class RichLifecycleBrokerFeature(Feature):
        def __init__(self) -> None:
            self.mount_count = 0

        @property
        def spec(self) -> FeatureSpec:
            return FeatureSpec(
                feature_id="FEAT-BROKER-RICH_LIFECYCLE",
                domain="broker",
                provides=frozenset({BROKER_MARKET_DATA}),
            )

        @override
        async def mount(self, context: FeatureContext, config: object) -> None:
            nonlocal task_running, task_cancelled, listener_invoked, callback_cleaned
            self.mount_count += 1
            service = ConfigurableBrokerService(base_price=99.0)
            context.provide(BROKER_MARKET_DATA, service)

            if self.mount_count > 1:
                stop_evt = asyncio.Event()

                # Spawn background task on replacement
                async def worker() -> None:
                    nonlocal task_running, task_cancelled
                    task_running = True
                    try:
                        await stop_evt.wait()
                    except asyncio.CancelledError:
                        task_cancelled = True
                        raise

                context.spawn(worker(), name="replacement_worker")

                # Register listener on replacement
                def on_reconfigured(_e: FeatureReconfiguredEvent) -> None:
                    nonlocal listener_invoked
                    listener_invoked = True

                context.subscribe(FeatureReconfiguredEvent, on_reconfigured)

                # Register cleanup callback
                def cleanup_cb() -> None:
                    nonlocal callback_cleaned
                    callback_cleaned = True

                context.register_callback(cleanup_cb)

    feat = RichLifecycleBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)

    initial_toml = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-RICH_LIFECYCLE]
    enabled = true
    """
    await engine.load_and_reconcile_toml(initial_toml)
    assert feat.mount_count == 1

    # Perform transactional swap to generation 2
    success, err = await engine.replace_feature_transactional(
        "FEAT-BROKER-RICH_LIFECYCLE",
        new_config={"base_price": 100.0},
    )
    assert success is True
    assert err is None
    assert feat.mount_count == 2

    # Give task a moment to run
    await asyncio.sleep(0.02)

    # CRITICAL: Replacement task must STILL be running, not killed by shadow scope close!
    assert task_running is True, "Replacement background task was killed during commit!"
    assert not task_cancelled, (
        "Replacement task was cancelled during shadow scope cleanup!"
    )

    await engine.shutdown()
    assert task_cancelled is True, "Task was not cancelled on engine shutdown"
    assert callback_cleaned is True, (
        "Cleanup callback was not invoked on engine shutdown"
    )
