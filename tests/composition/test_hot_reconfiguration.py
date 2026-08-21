"""Tests for hot reconfiguration and transactional feature replacement."""

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
from app.contracts.events.system import ConfigurationReloadedEvent, FeatureReconfiguredEvent
from app.kernel.feature import Feature, FeatureSpec
from app.kernel.scope import FeatureScope

if TYPE_CHECKING:
    from collections.abc import Sequence
    from app.kernel.context import FeatureContext


class ConfigurableBrokerService(BrokerMarketData):
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
    def __init__(self, should_fail_mount: bool = False) -> None:
        self.should_fail_mount = should_fail_mount
        self.mount_count = 0
        self.active_base_price = 1.0

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            feature_id="FEAT-BROKER-CONFIGURABLE",
            domain="broker",
            provides=frozenset({BROKER_MARKET_DATA}),
        )

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        if self.should_fail_mount:
            raise RuntimeError("Simulated shadow mount crash")
        self.mount_count += 1
        cfg_dict = config if isinstance(config, dict) else {}
        self.active_base_price = float(cfg_dict.get("base_price", 1.0))
        context.provide(
            BROKER_MARKET_DATA,
            ConfigurableBrokerService(base_price=self.active_base_price),
        )


@pytest.mark.asyncio
async def test_live_configuration_hot_reload() -> None:
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)
    events: list[ConfigurationReloadedEvent] = []

    async def on_reload(event: ConfigurationReloadedEvent) -> None:
        events.append(event)

    engine.event_bus.subscribe(ConfigurationReloadedEvent, on_reload)
    initial = """
    [application]
    profile = "research"
    [features.FEAT-BROKER-CONFIGURABLE]
    enabled = true
    base_price = 1.10
    """
    await engine.load_and_reconcile_toml(initial)
    updated = load_config_from_toml_string(initial.replace("1.10", "1.25"))
    report = await engine.hot_reload_config(updated)
    assert "FEAT-BROKER-CONFIGURABLE" in report.started
    assert feat.mount_count == 2
    assert feat.active_base_price == 1.25
    assert len(events) == 1
    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_feature_replacement_success() -> None:
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)
    events: list[FeatureReconfiguredEvent] = []

    async def on_reconfigured(event: FeatureReconfiguredEvent) -> None:
        events.append(event)

    engine.event_bus.subscribe(FeatureReconfiguredEvent, on_reconfigured)
    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "research"
        [features.FEAT-BROKER-CONFIGURABLE]
        enabled = true
        base_price = 2.0
        """
    )
    success, warning = await engine.replace_feature_transactional(
        "FEAT-BROKER-CONFIGURABLE",
        new_config={"base_price": 3.5},
    )
    assert success
    assert warning is None
    binding = engine.registry.get_binding(BROKER_MARKET_DATA.identifier)
    assert binding is not None
    assert binding.token.generation == 2
    assert len(events) == 1
    await engine.shutdown()


@pytest.mark.asyncio
async def test_transactional_feature_replacement_failure_rollback() -> None:
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)
    await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "research"
        [features.FEAT-BROKER-CONFIGURABLE]
        enabled = true
        base_price = 10.0
        """
    )
    active_service = engine.registry.require(BROKER_MARKET_DATA)
    feat.should_fail_mount = True
    success, error = await engine.replace_feature_transactional(
        "FEAT-BROKER-CONFIGURABLE",
        new_config={"base_price": 99.0},
    )
    assert not success
    assert error is not None
    assert engine.registry.require(BROKER_MARKET_DATA) is active_service
    await engine.shutdown()


@pytest.mark.asyncio
async def test_config_file_watcher_polling(tmp_path: Path) -> None:
    config_file = tmp_path / "app.toml"
    feat = ConfigurableBrokerFeature()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(feat)
    engine = CompositionEngine(discoverer=discoverer)
    config_file.write_text(
        """
        [application]
        profile = "research"
        [features.FEAT-BROKER-CONFIGURABLE]
        enabled = true
        base_price = 5.0
        """,
        encoding="utf-8",
    )
    await engine.load_and_reconcile_file(config_file)
    watcher_scope = FeatureScope("SYS-CONFIG-WATCHER")
    watcher = ConfigFileWatcher(
        config_path=config_file,
        engine=engine,
        scope=watcher_scope,
        poll_interval=0.05,
        debounce=0.01,
    )
    watcher.start()
    try:
        await asyncio.sleep(0.05)
        config_file.write_text(
            config_file.read_text(encoding="utf-8").replace("5.0", "8.5"),
            encoding="utf-8",
        )
        assert await watcher.check_and_reload()
        assert feat.active_base_price == 8.5
    finally:
        await watcher.stop()
        await watcher_scope.close()
        await engine.shutdown()
