"""Tests verifying Phase 15: hot reconfiguration and transactional feature replacement."""

import asyncio
from collections.abc import Awaitable
from pathlib import Path
from typing import TYPE_CHECKING, override

import pytest
from app.composition.config import load_config_from_toml_string
from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.composition.events import (
    ConfigurationReloadedEvent,
    FeatureReconfiguredEvent,
)
from app.composition.watcher import ConfigFileWatcher
from app.kernel.feature import Feature, FeatureSpec

from tests._support.composability import PROVIDER_CAPABILITY

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ConfigurableService:
    """Test service capturing configuration state."""

    def __init__(self, value: float = 1.0) -> None:
        self.value = value


class ConfigurableFeature(Feature):
    """Feature supporting dynamic reconfiguration and health check."""

    def __init__(self, should_fail_mount: bool = False) -> None:
        self.should_fail_mount = should_fail_mount
        self.mount_count = 0
        self.active_base_price = 1.0

    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-TEST-CONFIGURABLE",
        domain="test",
        description="Configurable test feature",
        provides=frozenset({PROVIDER_CAPABILITY}),
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
        service = ConfigurableService(value=self.active_base_price)
        context.provide(PROVIDER_CAPABILITY, service)


@pytest.mark.asyncio
async def test_live_configuration_hot_reload() -> None:
    """Test hot reloading config updates and remounting only modified features."""
    feat = ConfigurableFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)

    engine = CompositionEngine(discoverer=discoverer)
    events_received: list[ConfigurationReloadedEvent] = []

    async def on_reload(event: ConfigurationReloadedEvent) -> None:
        events_received.append(event)

    engine.event_bus.subscribe(ConfigurationReloadedEvent, on_reload)

    # Initial Mount
    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-CONFIGURABLE]
    enabled = true
    base_price = 1.10
    """
    await engine.load_and_reconcile_toml(initial_toml)
    assert feat.mount_count == 1
    assert feat.active_base_price == 1.10

    # Hot reload with updated config
    updated_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-CONFIGURABLE]
    enabled = true
    base_price = 1.25
    """
    updated_cfg = load_config_from_toml_string(updated_toml)
    report = await engine.hot_reload_config(updated_cfg)

    assert "FEAT-TEST-CONFIGURABLE" in report.started
    assert feat.mount_count == 2
    assert feat.active_base_price == 1.25
    assert len(events_received) == 1
    assert "FEAT-TEST-CONFIGURABLE" in events_received[0].modified_features

    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_feature_replacement_success() -> None:
    """Test zero-downtime transactional feature replacement via shadow scopes."""
    feat = ConfigurableFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)

    engine = CompositionEngine(discoverer=discoverer)
    reconfigured_events: list[FeatureReconfiguredEvent] = []

    async def on_reconfigured(event: FeatureReconfiguredEvent) -> None:
        reconfigured_events.append(event)

    engine.event_bus.subscribe(FeatureReconfiguredEvent, on_reconfigured)

    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-CONFIGURABLE]
    enabled = true
    base_price = 2.0
    """
    await engine.load_and_reconcile_toml(initial_toml)
    initial_binding = engine.registry.get_binding(PROVIDER_CAPABILITY.identifier)
    assert initial_binding is not None
    assert initial_binding.token.generation == 1

    # Perform transactional swap
    success, err = await engine.replace_feature_transactional(
        "FEAT-TEST-CONFIGURABLE",
        new_config={"base_price": 3.5},
    )
    assert success is True
    assert err is None
    assert feat.active_base_price == 3.5

    # Generation counter must increment
    swapped_binding = engine.registry.get_binding(PROVIDER_CAPABILITY.identifier)
    assert swapped_binding is not None
    assert swapped_binding.token.generation == 2
    assert len(reconfigured_events) == 1
    assert reconfigured_events[0].generation == 2

    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_feature_replacement_failure_rollback() -> None:
    """Test that failure during shadow mount rolls back without affecting active provider."""
    good_feat = ConfigurableFeature(should_fail_mount=False)
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(good_feat)

    engine = CompositionEngine(discoverer=discoverer)
    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-CONFIGURABLE]
    enabled = true
    base_price = 10.0
    """
    await engine.load_and_reconcile_toml(initial_toml)
    active_service = engine.registry.require(PROVIDER_CAPABILITY)
    assert isinstance(active_service, ConfigurableService)
    assert active_service.value == 10.0

    # Configure feature to fail on next mount
    good_feat.should_fail_mount = True

    success, err = await engine.replace_feature_transactional(
        "FEAT-TEST-CONFIGURABLE",
        new_config={"base_price": 99.0},
    )
    assert success is False
    assert err is not None
    assert "Simulated shadow mount crash" in err

    # Active provider MUST still be active, untouched, and functional!
    current_service = engine.registry.require(PROVIDER_CAPABILITY)
    assert current_service is active_service
    assert current_service.value == 10.0

    await engine.shutdown()


@pytest.mark.asyncio
async def test_config_file_watcher_polling(tmp_path: Path) -> None:
    """Test ConfigFileWatcher detects file changes and triggers reconciliation."""
    config_file = tmp_path / "app.toml"
    feat = ConfigurableFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)

    engine = CompositionEngine(discoverer=discoverer)

    # Initial write
    config_file.write_text(
        """
        [application]
        profile = "research"
        [features.FEAT-TEST-CONFIGURABLE]
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

    try:
        # Update config file on disk
        await asyncio.sleep(0.05)
        config_file.write_text(
            """
            [application]
            profile = "research"
            [features.FEAT-TEST-CONFIGURABLE]
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
    lifecycle: dict[str, bool] = {
        "task_running": False,
        "task_cancelled": False,
        "listener_invoked": False,
        "callback_cleaned": False,
    }

    class RichLifecycleFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-RICH_LIFECYCLE",
            domain="test",
            provides=frozenset({PROVIDER_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0

        @override
        async def mount(self, context: FeatureContext, config: object) -> None:
            self.mount_count += 1
            service = ConfigurableService(value=99.0)
            context.provide(PROVIDER_CAPABILITY, service)

            if self.mount_count > 1:
                stop_evt = asyncio.Event()

                # Spawn background task on replacement
                async def worker() -> None:
                    lifecycle["task_running"] = True
                    try:
                        await stop_evt.wait()
                    except asyncio.CancelledError:
                        lifecycle["task_cancelled"] = True
                        raise

                context.spawn(worker(), name="replacement_worker")

                # Register listener on replacement
                def on_reconfigured(_e: FeatureReconfiguredEvent) -> None:
                    lifecycle["listener_invoked"] = True

                context.subscribe(FeatureReconfiguredEvent, on_reconfigured)

                # Register cleanup callback
                def cleanup_cb() -> None:
                    lifecycle["callback_cleaned"] = True

                context.register_callback(cleanup_cb)

    feat = RichLifecycleFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)

    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-RICH_LIFECYCLE]
    enabled = true
    """
    await engine.load_and_reconcile_toml(initial_toml)
    assert feat.mount_count == 1

    # Perform transactional swap to generation 2
    success, err = await engine.replace_feature_transactional(
        "FEAT-TEST-RICH_LIFECYCLE",
        new_config={"base_price": 100.0},
    )
    assert success is True
    assert err is None
    assert feat.mount_count == 2

    # Give task a moment to run
    await asyncio.sleep(0.02)

    # CRITICAL: Replacement task must STILL be running, not killed by shadow scope close!
    read_flag = lifecycle.__getitem__
    assert read_flag("task_running") is True, (
        "Replacement background task was killed during commit!"
    )
    assert not read_flag("task_cancelled"), (
        "Replacement task was cancelled during shadow scope cleanup!"
    )

    await engine.shutdown()
    assert read_flag("task_cancelled") is True, (
        "Task was not cancelled on engine shutdown"
    )
    assert read_flag("callback_cleaned") is True, (
        "Cleanup callback was not invoked on engine shutdown"
    )


@pytest.mark.asyncio
async def test_transactional_replacement_health_check_failure_rolls_back() -> None:
    """Test feature with health_check hook rolling back on failure."""

    class HealthCheckingFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-HEALTH_CHECK",
            domain="test",
            provides=frozenset({PROVIDER_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0
            self.should_fail_health = False

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            context.provide(
                PROVIDER_CAPABILITY,
                ConfigurableService(value=float(self.mount_count)),
            )

        def health_check(self) -> None:
            if self.should_fail_health:
                msg = "Upstream broker health check timeout"
                raise RuntimeError(msg)

    feat = HealthCheckingFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)

    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-HEALTH_CHECK]
    enabled = true
    """
    await engine.load_and_reconcile_toml(initial_toml)
    assert feat.mount_count == 1

    # Configure health check failure
    feat.should_fail_health = True

    report = await engine.replace_feature_transactional_detailed(
        "FEAT-TEST-HEALTH_CHECK"
    )
    assert report.committed is False
    assert report.rolled_back is True
    assert report.status == "rolled_back"
    assert "health check timeout" in (report.error or "")

    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_replacement_quiesce_and_drain() -> None:
    """Test that quiesce and drain hooks on old feature are executed during replacement."""
    quiesced = False
    drained = False

    class QuiescingFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-QUIESCE",
            domain="test",
            provides=frozenset({PROVIDER_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            context.provide(PROVIDER_CAPABILITY, ConfigurableService())

        def quiesce(self) -> Awaitable[None] | None:
            nonlocal quiesced
            quiesced = True
            return None

        def drain(self) -> Awaitable[None] | None:
            nonlocal drained
            drained = True
            return None

    feat = QuiescingFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)

    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-QUIESCE]
    enabled = true
    """
    await engine.load_and_reconcile_toml(initial_toml)
    assert feat.mount_count == 1

    report = await engine.replace_feature_transactional_detailed(
        "FEAT-TEST-QUIESCE", new_config={"reloaded": True}
    )
    assert report.committed is True
    assert report.rolled_back is False
    assert report.status == "committed"
    assert quiesced is True
    assert drained is True

    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_replacement_cleanup_error_degrades_status() -> None:
    """Test post-commit cleanup error in old scope marks status degraded without rolling back."""

    class FailingCleanupFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-CLEANUP_ERR",
            domain="test",
            provides=frozenset({PROVIDER_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            context.provide(PROVIDER_CAPABILITY, ConfigurableService())

            if self.mount_count == 1:

                def broken_cleanup() -> None:
                    msg = "Corrupted connection release"
                    raise RuntimeError(msg)

                context.register_callback(broken_cleanup)

    feat = FailingCleanupFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)

    initial_toml = """
    [application]
    profile = "research"
    [features.FEAT-TEST-CLEANUP_ERR]
    enabled = true
    """
    await engine.load_and_reconcile_toml(initial_toml)

    report = await engine.replace_feature_transactional_detailed(
        "FEAT-TEST-CLEANUP_ERR", new_config={"gen": 2}
    )
    assert report.committed is True
    assert report.rolled_back is False
    assert report.status == "degraded"
    assert len(report.cleanup_errors) == 1
    assert "Corrupted connection release" in report.cleanup_errors[0]

    await engine.shutdown()


@pytest.mark.asyncio
async def test_watcher_logging_lifecycle_and_error_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Watcher deterministically emits change, poll-error, start, and stop evidence."""
    from app.composition.logging import (
        LoggingConfig,
        compute_secret_fingerprint,
        configure_logging,
    )

    path_canary = "path_secret=watcher_path_canary_7319"
    error_canary = "poll_secret=watcher_error_canary_2984"
    config_file = tmp_path / f"{path_canary}.toml"
    config_file.write_text(
        """
        [application]
        profile = "offline"
        """,
        encoding="utf-8",
    )

    cfg = LoggingConfig(level="DEBUG", console=False, capture_capacity=50)
    with configure_logging(cfg) as handle:
        engine = CompositionEngine()
        watcher = ConfigFileWatcher(
            config_file,
            engine,
            poll_interval=0.01,
            debounce=0.0,
        )

        watcher._last_mtime = float("-inf")
        assert await watcher.check_and_reload() is True

        poll_called = asyncio.Event()

        async def fail_poll() -> bool:
            poll_called.set()
            raise RuntimeError(error_canary)

        monkeypatch.setattr(watcher, "check_and_reload", fail_poll)
        watcher.start()
        assert bool(watcher.is_running)
        await asyncio.wait_for(poll_called.wait(), timeout=0.1)
        await watcher.stop()
        assert not bool(watcher.is_running)
        await engine.shutdown()

        capture = handle.capture_handler
        assert capture is not None
        records = capture.get_records()
        event_names = [r.event for r in records]

        assert "WATCHER_START" in event_names
        assert "WATCHER_FILE_CHANGED" in event_names
        assert "WATCHER_POLL_ERROR" in event_names
        assert "WATCHER_STOP" in event_names
        rendered = str(records)
        assert path_canary not in rendered
        assert error_canary not in rendered
        assert compute_secret_fingerprint(str(config_file)) in rendered
        assert compute_secret_fingerprint("watcher_error_canary_2984") in rendered
