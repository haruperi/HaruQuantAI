"""Tests verifying Phase 14: external plugin packaging and dependency diagnostics."""

import importlib.metadata
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, override

import pytest

from app.api.system import SystemAPI
from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.broker.market_data import (
    BROKER_MARKET_DATA,
    BrokerBarsRequest,
    BrokerMarketData,
    BrokerRawBar,
)
from app.kernel.capability import CapabilityKey
from app.kernel.feature import Feature, FeatureSpec, FeatureState

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class DummyExternalBrokerService(BrokerMarketData):
    """External broker service implementation."""

    @override
    async def retrieve_bars(self, request: BrokerBarsRequest) -> Sequence[BrokerRawBar]:
        return (
            BrokerRawBar(
                timestamp=request.start,
                open_price=100.0,
                high_price=105.0,
                low_price=99.0,
                close_price=102.0,
                volume=500.0,
            ),
        )


class ExternalBrokerPlugin(Feature):
    """Simulated external plugin distributed in a separate wheel."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            feature_id="FEAT-BROKER-FEED_EXTERNAL",
            domain="broker",
            description="External broker plugin",
            provides=frozenset({BROKER_MARKET_DATA}),
            requires=frozenset(),
        )

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        context.provide(BROKER_MARKET_DATA, DummyExternalBrokerService())


class DependentConsumerPlugin(Feature):
    """Simulated external plugin depending on broker.market-data@1."""

    @property
    def spec(self) -> FeatureSpec:
        return FeatureSpec(
            feature_id="FEAT-DATA-EXTERNAL_CONSUMER",
            domain="data",
            description="External consumer plugin",
            provides=frozenset({CapabilityKey[object](name="data.external", major=1)}),
            requires=frozenset({BROKER_MARKET_DATA}),
        )

    @override
    async def mount(self, context: FeatureContext, config: object) -> None:
        market_data = context.require(BROKER_MARKET_DATA)
        assert market_data is not None
        context.provide(CapabilityKey[object](name="data.external", major=1), object())


@pytest.mark.asyncio
async def test_external_plugin_entry_point_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test discovering and mounting an external plugin registered via entry points."""
    plugin_instance = ExternalBrokerPlugin()

    class FakeEntryPoint:
        name = "FEAT-BROKER-FEED_EXTERNAL"
        value = "fake_external_pkg.feature:create_feature"
        group = "haruquantai.features"

        def load(self) -> Any:
            return lambda: plugin_instance

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group: (FakeEntryPoint(),) if group == "haruquantai.features" else (),
    )

    discoverer = FeatureDiscoverer()
    result = discoverer.discover()

    assert "FEAT-BROKER-FEED_EXTERNAL" in result.discovered
    assert result.discovered["FEAT-BROKER-FEED_EXTERNAL"] == plugin_instance


@pytest.mark.asyncio
async def test_package_dependency_error_diagnosed_separately() -> None:
    """Test that missing Python packages produce distinct PackageDependency errors."""
    discoverer = FeatureDiscoverer()

    def buggy_factory() -> Feature:
        msg = "No module named 'ccxt'"
        raise ModuleNotFoundError(msg, name="ccxt")

    discoverer.register_feature(buggy_factory, feature_id="FEAT-UNKNOWN-MISSING_PKG")
    result = discoverer.discover()

    assert len(result.failed_imports) > 0
    assert "FEAT-UNKNOWN-MISSING_PKG" in result.failed_imports
    err = result.failed_imports["FEAT-UNKNOWN-MISSING_PKG"]
    assert "ccxt" in err

    engine = CompositionEngine(discoverer=discoverer)
    config = """
    [profile]
    name = "research"
    [features.FEAT-UNKNOWN-MISSING_PKG]
    enabled = true
    """

    await engine.load_and_reconcile_toml(config)
    status = engine.get_status()

    # Verify Package Dependency Error is recorded in status
    assert "FEAT-UNKNOWN-MISSING_PKG" in status.package_dependency_errors
    assert "ccxt" in status.package_dependency_errors["FEAT-UNKNOWN-MISSING_PKG"]
    assert "FEAT-UNKNOWN-MISSING_PKG" not in status.capability_dependency_errors

    # Verify SystemAPI reports separate diagnostics
    api = SystemAPI(registry=engine.registry, engine=engine)
    pkg_errors = api.list_package_dependency_errors()
    assert "FEAT-UNKNOWN-MISSING_PKG" in pkg_errors

    diag = api.inspect_feature("FEAT-UNKNOWN-MISSING_PKG")
    assert diag.is_active is False
    assert diag.package_error is not None
    assert "ccxt" in diag.package_error
    assert diag.capability_error is None


@pytest.mark.asyncio
async def test_capability_dependency_error_diagnosed_separately() -> None:
    """Test that missing runtime capabilities produce distinct CapabilityDependency errors."""
    consumer = DependentConsumerPlugin()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(consumer)

    engine = CompositionEngine(discoverer=discoverer)
    config = """
    [profile]
    name = "research"
    [features.FEAT-DATA-EXTERNAL_CONSUMER]
    enabled = true
    """

    report = await engine.load_and_reconcile_toml(config)
    assert "FEAT-DATA-EXTERNAL_CONSUMER" in report.blocked_features

    status = engine.get_status()
    assert status.feature_states["FEAT-DATA-EXTERNAL_CONSUMER"] == FeatureState.BLOCKED
    assert "FEAT-DATA-EXTERNAL_CONSUMER" in status.capability_dependency_errors
    assert "FEAT-DATA-EXTERNAL_CONSUMER" not in status.package_dependency_errors

    api = SystemAPI(registry=engine.registry, engine=engine)
    cap_errors = api.list_capability_dependency_errors()
    assert "FEAT-DATA-EXTERNAL_CONSUMER" in cap_errors

    diag = api.inspect_feature("FEAT-DATA-EXTERNAL_CONSUMER")
    assert diag.is_active is False
    assert diag.package_error is None
    assert diag.capability_error is not None
    assert "capabilities" in diag.capability_error


@pytest.mark.asyncio
async def test_external_plugin_mount_and_unmount_cycle() -> None:
    """Test successful mounting and unmounting of an external plugin."""
    broker_plugin = ExternalBrokerPlugin()
    consumer_plugin = DependentConsumerPlugin()

    discoverer = FeatureDiscoverer()
    discoverer.register_feature(broker_plugin)
    discoverer.register_feature(consumer_plugin)

    engine = CompositionEngine(discoverer=discoverer)
    config = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-FEED_EXTERNAL]
    enabled = true
    [features.FEAT-DATA-EXTERNAL_CONSUMER]
    enabled = true
    """

    report = await engine.load_and_reconcile_toml(config)
    assert "FEAT-BROKER-FEED_EXTERNAL" in report.started
    assert "FEAT-DATA-EXTERNAL_CONSUMER" in report.started
    assert len(engine.registry.active_capabilities()) == 2

    # Unmount
    unmount_cfg = """
    [profile]
    name = "research"
    [features.FEAT-BROKER-FEED_EXTERNAL]
    enabled = false
    [features.FEAT-DATA-EXTERNAL_CONSUMER]
    enabled = false
    """
    report_unmount = await engine.load_and_reconcile_toml(unmount_cfg)
    assert "FEAT-BROKER-FEED_EXTERNAL" in report_unmount.stopped
    assert "FEAT-DATA-EXTERNAL_CONSUMER" in report_unmount.stopped
    assert len(engine.registry.active_capabilities()) == 0

    await engine.shutdown()
