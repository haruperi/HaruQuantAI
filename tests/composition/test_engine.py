from typing import TYPE_CHECKING

import pytest

from app.composition.engine import CompositionEngine
from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.contracts.system.clock import SYSTEM_CLOCK
from app.kernel.feature import FeatureSpec, FeatureState

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class MockClockFeature:
    spec = FeatureSpec(
        feature_id="FEAT-SYS-PROVIDE_CLOCK",
        domain="system",
        provides=frozenset({SYSTEM_CLOCK}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(SYSTEM_CLOCK, "clock_impl")


class MockBrokerFeature:
    spec = FeatureSpec(
        feature_id="FEAT-BROKER-FEED_MT5",
        domain="broker",
        provides=frozenset({BROKER_MARKET_DATA}),
        requires=frozenset({SYSTEM_CLOCK}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        clock = context.require(SYSTEM_CLOCK)
        context.provide(BROKER_MARKET_DATA, f"broker_impl_{clock}")


class MockDataFeature:
    spec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        broker = context.require(BROKER_MARKET_DATA)
        context.provide(HISTORICAL_BARS, f"data_impl_{broker}")


SAMPLE_TOML_ALL = """
[application]
profile = "research"

[features."FEAT-SYS-PROVIDE_CLOCK"]
enabled = true

[features."FEAT-BROKER-FEED_MT5"]
enabled = true

[features."FEAT-DATA-RETRIEVE_BARS"]
enabled = true
"""


@pytest.mark.asyncio
async def test_engine_load_and_reconcile_toml() -> None:
    """Test full bootstrap and readiness calculation via CompositionEngine."""
    engine = CompositionEngine()
    engine.discoverer.register_feature(MockClockFeature())
    engine.discoverer.register_feature(MockBrokerFeature())
    engine.discoverer.register_feature(MockDataFeature())

    report = await engine.load_and_reconcile_toml(SAMPLE_TOML_ALL)
    assert report.started == (
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-DATA-RETRIEVE_BARS",
    )

    status = engine.get_status()
    assert status.profile == "research"
    assert status.is_ready is True
    assert status.missing_profile_capabilities == ()
    assert "data.historical-bars@1" in status.active_capabilities
    assert status.feature_states["FEAT-DATA-RETRIEVE_BARS"] == FeatureState.ACTIVE

    await engine.shutdown()
    assert len(engine.reconciler.active_features) == 0
    assert len(engine.registry.active_capabilities()) == 0


@pytest.mark.asyncio
async def test_engine_graceful_missing_feature_readiness() -> None:
    """Test when required feature is missing from configuration."""
    engine = CompositionEngine()
    engine.discoverer.register_feature(MockClockFeature())
    # Note: Broker is not registered or enabled
    engine.discoverer.register_feature(MockDataFeature())

    incomplete_toml = """
    [application]
    profile = "research"

    [features."FEAT-SYS-PROVIDE_CLOCK"]
    enabled = true

    [features."FEAT-DATA-RETRIEVE_BARS"]
    enabled = true
    """

    report = await engine.load_and_reconcile_toml(incomplete_toml)
    assert "FEAT-DATA-RETRIEVE_BARS" in report.blocked_features

    status = engine.get_status()
    assert status.is_ready is False
    assert "data.historical-bars@1" in status.missing_profile_capabilities
    assert status.feature_states["FEAT-DATA-RETRIEVE_BARS"] == FeatureState.BLOCKED

    await engine.shutdown()


@pytest.mark.asyncio
async def test_engine_load_and_reconcile_file(tmp_path: object) -> None:
    """Test engine loading and reconciling from file."""
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    config_file = tmp_path / "app.toml"
    config_file.write_text(SAMPLE_TOML_ALL, encoding="utf-8")

    engine = CompositionEngine()
    engine.discoverer.register_feature(MockClockFeature())
    engine.discoverer.register_feature(MockBrokerFeature())
    engine.discoverer.register_feature(MockDataFeature())

    report = await engine.load_and_reconcile_file(config_file)
    assert report.started == (
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-DATA-RETRIEVE_BARS",
    )
    assert engine.get_status().is_ready is True

    await engine.shutdown()
