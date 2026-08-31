import asyncio
from typing import TYPE_CHECKING

import pytest
from app.composition.engine import CompositionEngine
from app.composition.logging import (
    LoggingConfig,
    compute_secret_fingerprint,
    configure_logging,
)
from app.kernel.feature import FeatureSpec, FeatureState

from tests._support.composability import (
    CONSUMER_CAPABILITY,
    PROVIDER_CAPABILITY,
    ROOT_CAPABILITY,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class RootFeature:
    spec = FeatureSpec(
        feature_id="FEAT-TEST-PROVIDE_ROOT",
        domain="test",
        provides=frozenset({ROOT_CAPABILITY}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        context.provide(ROOT_CAPABILITY, "root_impl")


class ProviderFeature:
    spec = FeatureSpec(
        feature_id="FEAT-TEST-PROVIDE_SERVICE",
        domain="test",
        provides=frozenset({PROVIDER_CAPABILITY}),
        requires=frozenset({ROOT_CAPABILITY}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        root = context.require(ROOT_CAPABILITY)
        context.provide(PROVIDER_CAPABILITY, f"provider_impl_{root}")


class ConsumerFeature:
    spec = FeatureSpec(
        feature_id="FEAT-TEST-CONSUME_SERVICE",
        domain="test",
        provides=frozenset({CONSUMER_CAPABILITY}),
        requires=frozenset({PROVIDER_CAPABILITY}),
    )

    async def mount(self, context: FeatureContext, _config: object) -> None:
        provider = context.require(PROVIDER_CAPABILITY)
        context.provide(CONSUMER_CAPABILITY, f"consumer_impl_{provider}")


SAMPLE_TOML_ALL = """
[application]
profile = "offline"

[features."FEAT-TEST-PROVIDE_ROOT"]
enabled = true

[features."FEAT-TEST-PROVIDE_SERVICE"]
enabled = true

[features."FEAT-TEST-CONSUME_SERVICE"]
enabled = true
"""


@pytest.mark.asyncio
async def test_engine_load_and_reconcile_toml() -> None:
    """Test full bootstrap and readiness calculation via CompositionEngine."""
    engine = CompositionEngine()
    engine.discoverer.register_feature(RootFeature())
    engine.discoverer.register_feature(ProviderFeature())
    engine.discoverer.register_feature(ConsumerFeature())

    report = await engine.load_and_reconcile_toml(SAMPLE_TOML_ALL)
    assert report.started == (
        "FEAT-TEST-PROVIDE_ROOT",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
    )

    status = engine.get_status()
    assert status.profile == "offline"
    assert status.is_ready is True
    assert status.missing_profile_capabilities == ()
    assert "test.consumer@1" in status.active_capabilities
    assert status.feature_states["FEAT-TEST-CONSUME_SERVICE"] == FeatureState.ACTIVE

    await engine.shutdown()
    assert len(engine.reconciler.active_features) == 0
    assert len(engine.registry.active_capabilities()) == 0


@pytest.mark.asyncio
async def test_engine_reports_blocked_feature_with_missing_dependency() -> None:
    """Test a configured consumer remains blocked without its provider."""
    engine = CompositionEngine()
    engine.discoverer.register_feature(RootFeature())
    # The provider is intentionally not registered or enabled.
    engine.discoverer.register_feature(ConsumerFeature())

    incomplete_toml = """
    [application]
    profile = "offline"

    [features."FEAT-TEST-PROVIDE_ROOT"]
    enabled = true

    [features."FEAT-TEST-CONSUME_SERVICE"]
    enabled = true
    """

    report = await engine.load_and_reconcile_toml(incomplete_toml)
    assert "FEAT-TEST-CONSUME_SERVICE" in report.blocked_features

    status = engine.get_status()
    assert status.is_ready is True
    assert status.missing_profile_capabilities == ()
    assert status.feature_states["FEAT-TEST-CONSUME_SERVICE"] == FeatureState.BLOCKED

    await engine.shutdown()


@pytest.mark.asyncio
async def test_engine_load_and_reconcile_file(tmp_path: object) -> None:
    """Test engine loading and reconciling from file."""
    from pathlib import Path

    assert isinstance(tmp_path, Path)
    config_file = tmp_path / "app.toml"
    config_file.write_text(SAMPLE_TOML_ALL, encoding="utf-8")

    engine = CompositionEngine()
    engine.discoverer.register_feature(RootFeature())
    engine.discoverer.register_feature(ProviderFeature())
    engine.discoverer.register_feature(ConsumerFeature())

    report = await engine.load_and_reconcile_file(config_file)
    assert report.started == (
        "FEAT-TEST-PROVIDE_ROOT",
        "FEAT-TEST-PROVIDE_SERVICE",
        "FEAT-TEST-CONSUME_SERVICE",
    )
    assert engine.get_status().is_ready is True

    await engine.shutdown()


@pytest.mark.asyncio
async def test_engine_logging_boundary_events_and_secret_safety() -> None:
    """Engine reconciliation, runtime failure, and shutdown emit structured, secret-safe log events."""
    canary = "secret_engine_runtime_canary_key_12345"
    fp = compute_secret_fingerprint(canary)

    class FailingRuntimeFeature:
        spec = FeatureSpec(
            feature_id="FEAT-TEST-FAILING_RUNTIME",
            domain="test",
            provides=frozenset({ROOT_CAPABILITY}),
        )

        async def mount(self, context: FeatureContext, _config: object) -> None:
            context.provide(ROOT_CAPABILITY, "impl")

            async def faulty_task() -> None:
                msg = f"Crash with credential: {canary}"
                raise RuntimeError(msg)

            context.spawn(faulty_task(), name="faulty_bg_task")

    cfg = LoggingConfig(level="DEBUG", console=False, capture_capacity=50)
    with configure_logging(cfg) as handle:
        engine = CompositionEngine()
        engine.discoverer.register_feature(FailingRuntimeFeature())

        toml_content = """
        [application]
        profile = "offline"

        [features."FEAT-TEST-FAILING_RUNTIME"]
        enabled = true
        """
        await engine.load_and_reconcile_toml(toml_content)
        await asyncio.sleep(0.01)

        await engine.shutdown()

        capture = handle.capture_handler
        assert capture is not None
        records = capture.get_records()
        event_names = [r.event for r in records]

        assert "RECONCILIATION_START" in event_names
        assert "RECONCILIATION_COMPLETE" in event_names
        assert "FEATURE_RUNTIME_FAILED" in event_names
        assert "ENGINE_SHUTDOWN_START" in event_names
        assert "ENGINE_SHUTDOWN_COMPLETE" in event_names

        all_text = " ".join(str(r) for r in records)
        assert canary not in all_text
        assert fp in all_text
