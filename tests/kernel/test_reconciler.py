from typing import TYPE_CHECKING, override

import pytest

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.contracts.system.clock import SYSTEM_CLOCK
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from app.kernel.reconciler import Reconciler
from app.kernel.registry import ServiceRegistry

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


def _active_feature_ids(reconciler: Reconciler) -> set[str]:
    """Return a fresh set so type narrowing cannot outlive mutations."""
    return set(reconciler.active_features)


class MockClockFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-SYS-PROVIDE_CLOCK",
        domain="system",
        provides=frozenset({SYSTEM_CLOCK}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(SYSTEM_CLOCK, "clock_service_instance")


class MockBrokerFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-BROKER-FEED_MT5",
        domain="broker",
        provides=frozenset({BROKER_MARKET_DATA}),
        requires=frozenset({SYSTEM_CLOCK}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        clock = context.require(SYSTEM_CLOCK)
        context.provide(BROKER_MARKET_DATA, f"broker_service_using_{clock}")


class MockDataFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-DATA-RETRIEVE_BARS",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(HISTORICAL_BARS, "data_service_instance")


class FailingFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-TEST-FAIL_MOUNT",
        domain="test",
        provides=frozenset(),
    )

    @override
    async def mount(self, _context: FeatureContext, _config: object) -> None:
        msg = "Fatal error inside mount"
        raise RuntimeError(msg)


@pytest.mark.asyncio
async def test_reconciler_topological_mounting_flow() -> None:
    """Test full sequential mount in dependency order."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features: dict[str, Feature] = {
        "FEAT-SYS-PROVIDE_CLOCK": MockClockFeature(),
        "FEAT-BROKER-FEED_MT5": MockBrokerFeature(),
        "FEAT-DATA-RETRIEVE_BARS": MockDataFeature(),
    }

    report = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
    )

    assert report.started == (
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-DATA-RETRIEVE_BARS",
    )
    assert report.stopped == ()
    assert report.active_features == (
        "FEAT-SYS-PROVIDE_CLOCK",
        "FEAT-BROKER-FEED_MT5",
        "FEAT-DATA-RETRIEVE_BARS",
    )
    assert registry.is_available(SYSTEM_CLOCK)
    assert registry.is_available(BROKER_MARKET_DATA)
    assert registry.is_available(HISTORICAL_BARS)

    states = reconciler.feature_states
    assert states["FEAT-SYS-PROVIDE_CLOCK"] == FeatureState.ACTIVE
    assert states["FEAT-BROKER-FEED_MT5"] == FeatureState.ACTIVE
    assert states["FEAT-DATA-RETRIEVE_BARS"] == FeatureState.ACTIVE


@pytest.mark.asyncio
async def test_reconciler_transactional_rollback_on_failure() -> None:
    """Test failure during mount triggers rollback and sets FAILED_START."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features = {"FEAT-TEST-FAIL_MOUNT": FailingFeature()}
    report = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=["FEAT-TEST-FAIL_MOUNT"],
    )

    assert report.started == ()
    assert "FEAT-TEST-FAIL_MOUNT" in report.errors
    assert "Fatal error inside mount" in report.errors["FEAT-TEST-FAIL_MOUNT"]
    assert (
        reconciler.feature_states["FEAT-TEST-FAIL_MOUNT"] == FeatureState.FAILED_START
    )
    assert not _active_feature_ids(reconciler)


@pytest.mark.asyncio
async def test_reconciler_graceful_provider_removal_and_dependent_unmount() -> None:
    """Test removing a provider unmounts dependents in reverse topological order."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features: dict[str, Feature] = {
        "FEAT-SYS-PROVIDE_CLOCK": MockClockFeature(),
        "FEAT-BROKER-FEED_MT5": MockBrokerFeature(),
        "FEAT-DATA-RETRIEVE_BARS": MockDataFeature(),
    }

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
    )
    assert _active_feature_ids(reconciler) == set(features)

    report2 = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=[
            "FEAT-SYS-PROVIDE_CLOCK",
            "FEAT-DATA-RETRIEVE_BARS",
        ],
    )

    assert "FEAT-DATA-RETRIEVE_BARS" in report2.stopped
    assert "FEAT-BROKER-FEED_MT5" in report2.stopped
    assert _active_feature_ids(reconciler) == {"FEAT-SYS-PROVIDE_CLOCK"}
    assert not registry.is_available(HISTORICAL_BARS)
    assert not registry.is_available(BROKER_MARKET_DATA)
    assert registry.is_available(SYSTEM_CLOCK)
    assert reconciler.feature_states["FEAT-DATA-RETRIEVE_BARS"] == FeatureState.BLOCKED
    assert reconciler.feature_states["FEAT-BROKER-FEED_MT5"] == FeatureState.DISABLED


@pytest.mark.asyncio
async def test_reconciler_config_change_triggers_remount() -> None:
    """Test updating a feature configuration triggers remount."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features: dict[str, Feature] = {"FEAT-SYS-PROVIDE_CLOCK": MockClockFeature()}

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=["FEAT-SYS-PROVIDE_CLOCK"],
        configs={"FEAT-SYS-PROVIDE_CLOCK": {"mode": "utc"}},
    )
    assert _active_feature_ids(reconciler) == {"FEAT-SYS-PROVIDE_CLOCK"}

    report = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=["FEAT-SYS-PROVIDE_CLOCK"],
        configs={"FEAT-SYS-PROVIDE_CLOCK": {"mode": "simulated"}},
    )

    assert "FEAT-SYS-PROVIDE_CLOCK" in report.stopped
    assert "FEAT-SYS-PROVIDE_CLOCK" in report.started
    assert _active_feature_ids(reconciler) == {"FEAT-SYS-PROVIDE_CLOCK"}


@pytest.mark.asyncio
async def test_reconciler_stop_all() -> None:
    """Test stop_all stops all active features and cleans registry."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features: dict[str, Feature] = {
        "FEAT-SYS-PROVIDE_CLOCK": MockClockFeature(),
        "FEAT-BROKER-FEED_MT5": MockBrokerFeature(),
    }

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
    )
    assert _active_feature_ids(reconciler) == set(features)

    await reconciler.stop_all()
    assert not _active_feature_ids(reconciler)
    assert not registry.is_available(SYSTEM_CLOCK)
    assert not registry.is_available(BROKER_MARKET_DATA)


@pytest.mark.asyncio
async def test_provider_reconfiguration_remounts_transitive_consumers() -> None:
    """Characterization test: changing provider config must remount all transitive consumers in order."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    class CountingClockFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-SYS-PROVIDE_CLOCK",
            domain="system",
            provides=frozenset({SYSTEM_CLOCK}),
        )

        def __init__(self) -> None:
            self.mount_count = 0

        @override
        async def mount(self, context: FeatureContext, config: object) -> None:
            self.mount_count += 1
            mode = "default"
            if isinstance(config, dict):
                mode = config.get("mode", "default")
            context.provide(SYSTEM_CLOCK, {"mode": mode, "gen": self.mount_count})

    class CountingBrokerFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-BROKER-FEED_MT5",
            domain="broker",
            provides=frozenset({BROKER_MARKET_DATA}),
            requires=frozenset({SYSTEM_CLOCK}),
        )

        def __init__(self) -> None:
            self.mount_count = 0
            self.captured_clock: object = None

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            self.captured_clock = context.require(SYSTEM_CLOCK)
            context.provide(BROKER_MARKET_DATA, {"broker_gen": self.mount_count})

    class CountingDataFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-DATA-RETRIEVE_BARS",
            domain="data",
            provides=frozenset({HISTORICAL_BARS}),
            requires=frozenset({BROKER_MARKET_DATA}),
        )

        def __init__(self) -> None:
            self.mount_count = 0
            self.captured_broker: object = None

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            self.captured_broker = context.require(BROKER_MARKET_DATA)
            context.provide(HISTORICAL_BARS, {"data_gen": self.mount_count})

    clock_feat = CountingClockFeature()
    broker_feat = CountingBrokerFeature()
    data_feat = CountingDataFeature()

    features: dict[str, Feature] = {
        "FEAT-SYS-PROVIDE_CLOCK": clock_feat,
        "FEAT-BROKER-FEED_MT5": broker_feat,
        "FEAT-DATA-RETRIEVE_BARS": data_feat,
    }

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
        configs={"FEAT-SYS-PROVIDE_CLOCK": {"mode": "v1"}},
    )

    assert clock_feat.mount_count == 1
    assert broker_feat.mount_count == 1
    assert data_feat.mount_count == 1
    assert broker_feat.captured_clock == {"mode": "v1", "gen": 1}
    assert data_feat.captured_broker == {"broker_gen": 1}

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
        configs={"FEAT-SYS-PROVIDE_CLOCK": {"mode": "v2"}},
    )

    assert clock_feat.mount_count == 2
    assert broker_feat.mount_count == 2, (
        "Broker consumer was not remounted on clock change!"
    )
    assert data_feat.mount_count == 2, (
        "Data downstream consumer was not remounted on clock change!"
    )
    assert broker_feat.captured_clock == {"mode": "v2", "gen": 2}
    assert data_feat.captured_broker == {"broker_gen": 2}
