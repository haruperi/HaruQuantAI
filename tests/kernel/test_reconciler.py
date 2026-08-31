from typing import TYPE_CHECKING, override

import pytest
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from app.kernel.reconciler import Reconciler
from app.kernel.registry import ServiceRegistry

from tests._support.composability import (
    CONSUMER_CAPABILITY,
    PROVIDER_CAPABILITY,
    ROOT_CAPABILITY,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


def _active_feature_ids(reconciler: Reconciler) -> set[str]:
    """Return a fresh set so type narrowing cannot outlive mutations."""
    return set(reconciler.active_features)


class MockClockFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-TEST-PROVIDE_ROOT",
        domain="system",
        provides=frozenset({ROOT_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(ROOT_CAPABILITY, "clock_service_instance")


class MockBrokerFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-TEST-PROVIDE_SERVICE",
        domain="broker",
        provides=frozenset({PROVIDER_CAPABILITY}),
        requires=frozenset({ROOT_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        clock = context.require(ROOT_CAPABILITY)
        context.provide(PROVIDER_CAPABILITY, f"broker_service_using_{clock}")


class MockDataFeature(Feature):
    spec: FeatureSpec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="data",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(CONSUMER_CAPABILITY, "data_service_instance")


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
        "FEAT-TEST-PROVIDE_ROOT": MockClockFeature(),
        "FEAT-TEST-PROVIDE_SERVICE": MockBrokerFeature(),
        "FEAT-TEST-CONSUME_SERVICE": MockDataFeature(),
    }

    report = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
    )

    assert report.started == (
        "FEAT-TEST-PROVIDE_ROOT",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
    )
    assert report.stopped == ()
    assert report.active_features == (
        "FEAT-TEST-PROVIDE_ROOT",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
    )
    assert registry.is_available(ROOT_CAPABILITY)
    assert registry.is_available(PROVIDER_CAPABILITY)
    assert registry.is_available(CONSUMER_CAPABILITY)

    states = reconciler.feature_states
    assert states["FEAT-TEST-PROVIDE_ROOT"] == FeatureState.ACTIVE
    assert states["FEAT-TEST-PROVIDE_SERVICE"] == FeatureState.ACTIVE
    assert states["FEAT-TEST-CONSUME_SERVICE"] == FeatureState.ACTIVE


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
        "FEAT-TEST-PROVIDE_ROOT": MockClockFeature(),
        "FEAT-TEST-PROVIDE_SERVICE": MockBrokerFeature(),
        "FEAT-TEST-CONSUME_SERVICE": MockDataFeature(),
    }

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
    )
    assert _active_feature_ids(reconciler) == set(features)

    report2 = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=[
            "FEAT-TEST-PROVIDE_ROOT",
            "FEAT-TEST-CONSUME_SERVICE",
        ],
    )

    assert "FEAT-TEST-CONSUME_SERVICE" in report2.stopped
    assert "FEAT-TEST-PROVIDE_SERVICE" in report2.stopped
    assert _active_feature_ids(reconciler) == {"FEAT-TEST-PROVIDE_ROOT"}
    assert not registry.is_available(CONSUMER_CAPABILITY)
    assert not registry.is_available(PROVIDER_CAPABILITY)
    assert registry.is_available(ROOT_CAPABILITY)
    assert (
        reconciler.feature_states["FEAT-TEST-CONSUME_SERVICE"] == FeatureState.BLOCKED
    )
    assert (
        reconciler.feature_states["FEAT-TEST-PROVIDE_SERVICE"] == FeatureState.DISABLED
    )


@pytest.mark.asyncio
async def test_reconciler_config_change_triggers_remount() -> None:
    """Test updating a feature configuration triggers remount."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features: dict[str, Feature] = {"FEAT-TEST-PROVIDE_ROOT": MockClockFeature()}

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=["FEAT-TEST-PROVIDE_ROOT"],
        configs={"FEAT-TEST-PROVIDE_ROOT": {"mode": "utc"}},
    )
    assert _active_feature_ids(reconciler) == {"FEAT-TEST-PROVIDE_ROOT"}

    report = await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=["FEAT-TEST-PROVIDE_ROOT"],
        configs={"FEAT-TEST-PROVIDE_ROOT": {"mode": "simulated"}},
    )

    assert "FEAT-TEST-PROVIDE_ROOT" in report.stopped
    assert "FEAT-TEST-PROVIDE_ROOT" in report.started
    assert _active_feature_ids(reconciler) == {"FEAT-TEST-PROVIDE_ROOT"}


@pytest.mark.asyncio
async def test_reconciler_stop_all() -> None:
    """Test stop_all stops all active features and cleans registry."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    features: dict[str, Feature] = {
        "FEAT-TEST-PROVIDE_ROOT": MockClockFeature(),
        "FEAT-TEST-PROVIDE_SERVICE": MockBrokerFeature(),
    }

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
    )
    assert _active_feature_ids(reconciler) == set(features)

    await reconciler.stop_all()
    assert not _active_feature_ids(reconciler)
    assert not registry.is_available(ROOT_CAPABILITY)
    assert not registry.is_available(PROVIDER_CAPABILITY)


@pytest.mark.asyncio
async def test_provider_reconfiguration_remounts_transitive_consumers() -> None:
    """Characterization test: changing provider config must remount all transitive consumers in order."""
    registry = ServiceRegistry()
    reconciler = Reconciler(registry)

    class CountingClockFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-PROVIDE_ROOT",
            domain="system",
            provides=frozenset({ROOT_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0

        @override
        async def mount(self, context: FeatureContext, config: object) -> None:
            self.mount_count += 1
            mode = "default"
            if isinstance(config, dict):
                mode = config.get("mode", "default")
            context.provide(ROOT_CAPABILITY, {"mode": mode, "gen": self.mount_count})

    class CountingBrokerFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-PROVIDE_SERVICE",
            domain="broker",
            provides=frozenset({PROVIDER_CAPABILITY}),
            requires=frozenset({ROOT_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0
            self.captured_clock: object = None

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            self.captured_clock = context.require(ROOT_CAPABILITY)
            context.provide(PROVIDER_CAPABILITY, {"broker_gen": self.mount_count})

    class CountingDataFeature(Feature):
        spec: FeatureSpec = FeatureSpec(
            feature_id="FEAT-TEST-CONSUME_SERVICE",
            domain="data",
            provides=frozenset({CONSUMER_CAPABILITY}),
            requires=frozenset({PROVIDER_CAPABILITY}),
        )

        def __init__(self) -> None:
            self.mount_count = 0
            self.captured_broker: object = None

        @override
        async def mount(self, context: FeatureContext, _config: object) -> None:
            self.mount_count += 1
            self.captured_broker = context.require(PROVIDER_CAPABILITY)
            context.provide(CONSUMER_CAPABILITY, {"data_gen": self.mount_count})

    clock_feat = CountingClockFeature()
    broker_feat = CountingBrokerFeature()
    data_feat = CountingDataFeature()

    features: dict[str, Feature] = {
        "FEAT-TEST-PROVIDE_ROOT": clock_feat,
        "FEAT-TEST-PROVIDE_SERVICE": broker_feat,
        "FEAT-TEST-CONSUME_SERVICE": data_feat,
    }

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
        configs={"FEAT-TEST-PROVIDE_ROOT": {"mode": "v1"}},
    )

    assert clock_feat.mount_count == 1
    assert broker_feat.mount_count == 1
    assert data_feat.mount_count == 1
    assert broker_feat.captured_clock == {"mode": "v1", "gen": 1}
    assert data_feat.captured_broker == {"broker_gen": 1}

    await reconciler.reconcile(
        discovered_features=features,
        enabled_feature_ids=features.keys(),
        configs={"FEAT-TEST-PROVIDE_ROOT": {"mode": "v2"}},
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
