"""Tests for external feature packaging and dependency diagnostics."""

import importlib.metadata
from typing import TYPE_CHECKING, Any, override

import pytest

from app.composition.discovery import FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.kernel.capability import CapabilityKey
from app.kernel.feature import Feature, FeatureSpec, FeatureState
from tests._support.composability import PROVIDER_CAPABILITY

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

EXTERNAL_CONSUMER_CAPABILITY = CapabilityKey[object](
    name="test.external-consumer",
    major=1,
)


class ExternalProviderPlugin(Feature):
    """Simulated external provider distributed in a separate wheel."""

    spec = FeatureSpec(
        feature_id="FEAT-TEST-EXTERNAL_PROVIDER",
        domain="test",
        description="External test provider",
        provides=frozenset({PROVIDER_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(PROVIDER_CAPABILITY, object())


class DependentConsumerPlugin(Feature):
    """Simulated external plugin with one required capability."""

    spec = FeatureSpec(
        feature_id="FEAT-TEST-EXTERNAL_CONSUMER",
        domain="test",
        description="External test consumer",
        provides=frozenset({EXTERNAL_CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )

    @override
    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.require(PROVIDER_CAPABILITY)
        context.provide(EXTERNAL_CONSUMER_CAPABILITY, object())


def test_external_plugin_entry_point_discovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Discover an external feature factory through package metadata."""
    plugin_instance = ExternalProviderPlugin()

    class FakeEntryPoint:
        name = "external-test-provider"
        value = "fake_external_pkg.feature:create_feature"
        group = "haruquantai.features"

        def load(self) -> Any:
            return lambda: plugin_instance

    monkeypatch.setattr(
        importlib.metadata,
        "entry_points",
        lambda group: (FakeEntryPoint(),) if group == "haruquantai.features" else (),
    )

    result = FeatureDiscoverer().discover()

    assert result.discovered == {"FEAT-TEST-EXTERNAL_PROVIDER": plugin_instance}


@pytest.mark.asyncio
async def test_package_dependency_error_diagnosed_separately() -> None:
    """Missing Python packages remain distinct from capability failures."""
    discoverer = FeatureDiscoverer()

    def buggy_factory() -> Feature:
        msg = "No module named 'example_dependency'"
        raise ModuleNotFoundError(msg, name="example_dependency")

    feature_id = "FEAT-TEST-MISSING_PACKAGE"
    discoverer.register_feature(buggy_factory, feature_id=feature_id)
    result = discoverer.discover()

    assert "example_dependency" in result.failed_imports[feature_id]

    engine = CompositionEngine(discoverer=discoverer)
    await engine.load_and_reconcile_toml(
        f"""
        [application]
        profile = "offline"
        [features.{feature_id}]
        enabled = true
        """
    )
    status = engine.get_status()

    assert "example_dependency" in status.package_dependency_errors[feature_id]
    assert feature_id not in status.capability_dependency_errors
    assert status.feature_states[feature_id] == FeatureState.MISSING
    await engine.shutdown()


@pytest.mark.asyncio
async def test_capability_dependency_error_diagnosed_separately() -> None:
    """Missing runtime capabilities produce capability diagnostics."""
    consumer = DependentConsumerPlugin()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(consumer)
    engine = CompositionEngine(discoverer=discoverer)

    report = await engine.load_and_reconcile_toml(
        """
        [application]
        profile = "offline"
        [features.FEAT-TEST-EXTERNAL_CONSUMER]
        enabled = true
        """
    )
    status = engine.get_status()

    assert consumer.spec.feature_id in report.blocked_features
    assert status.feature_states[consumer.spec.feature_id] == FeatureState.BLOCKED
    assert consumer.spec.feature_id in status.capability_dependency_errors
    assert consumer.spec.feature_id not in status.package_dependency_errors
    await engine.shutdown()


@pytest.mark.asyncio
async def test_external_plugin_mount_and_unmount_cycle() -> None:
    """Mount and remove an external provider-consumer pair cleanly."""
    provider = ExternalProviderPlugin()
    consumer = DependentConsumerPlugin()
    discoverer = FeatureDiscoverer()
    discoverer.register_feature(provider)
    discoverer.register_feature(consumer)
    engine = CompositionEngine(discoverer=discoverer)

    enabled = """
    [application]
    profile = "offline"
    [features.FEAT-TEST-EXTERNAL_PROVIDER]
    enabled = true
    [features.FEAT-TEST-EXTERNAL_CONSUMER]
    enabled = true
    """
    report = await engine.load_and_reconcile_toml(enabled)

    assert report.started == (
        provider.spec.feature_id,
        consumer.spec.feature_id,
    )
    assert len(engine.registry.active_capabilities()) == 2

    disabled = """
    [application]
    profile = "offline"
    [features.FEAT-TEST-EXTERNAL_PROVIDER]
    enabled = false
    [features.FEAT-TEST-EXTERNAL_CONSUMER]
    enabled = false
    """
    report = await engine.load_and_reconcile_toml(disabled)

    assert set(report.stopped) == {
        provider.spec.feature_id,
        consumer.spec.feature_id,
    }
    assert not engine.registry.active_capabilities()
    await engine.shutdown()
