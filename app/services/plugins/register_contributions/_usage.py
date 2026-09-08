"""Bounded offline usage demonstration for FEAT-PLUG-REGISTER_CONTRIBUTIONS.

Demonstrates:
    Scenario 1: Register contributions with exact ID/version/generation.
    Scenario 2: Reject duplicate or conflicting registrations.
    Scenario 3: Disposal removes only its own generation.
    Scenario 4: Deterministic exposure and unmount/withdrawal.
    Scenario 5: Clean capability withdrawal leaving unrelated state intact.
"""

from __future__ import annotations

import asyncio

from app.composition.logging import get_logger
from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.contracts.plugins.errors import (
    PluginContributionError,
)
from app.contracts.plugins.models import (
    ContributionRegistrationResult,
    PluginContributionDescriptor,
    PluginManifest,
    PluginType,
)
from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.register_contributions.feature import (
    RegisterContributionsFeature,
)
from app.services.plugins.register_contributions.register_contributions import (
    RegisterContributionsService,
)

logger = get_logger(__name__)

_EXPECTED_GEN_1: int = 1
_EXPECTED_GEN_2: int = 2
_EXPECTED_REMOVED_GEN_1: int = 2


class MockRSI:
    """Mock implementation of an indicator calculation."""

    def calculate(self, series: list[float]) -> list[float]:
        """Calculate mock indicator values.

        Returns:
            Computed series.
        """
        return [50.0] * len(series)


class MockSharpe:
    """Mock implementation of a metric computation."""

    def compute(self, returns: list[float]) -> float:
        """Compute mock Sharpe ratio.

        Returns:
            Computed ratio value.
        """
        return 1.85 if returns else 0.0


class MockBeta:
    """Mock implementation of a beta metric computation."""

    def compute(self, returns: list[float]) -> float:
        """Compute mock Beta ratio.

        Returns:
            Computed ratio value.
        """
        return 1.05 if returns else 0.0


def _demo_scenario_1_and_2(
    service: RegisterContributionsService,
    manifest: PluginManifest,
    c1: PluginContributionDescriptor,
    c2: PluginContributionDescriptor,
) -> ContributionRegistrationResult:
    print(
        "\n[Scenario 1] Registering generation 1 contributions with disposer handle..."
    )
    implementations = {
        c1.contribution_id: MockRSI(),
        c2.contribution_id: MockSharpe(),
    }

    result1 = service.register_contributions(
        manifest, (c1, c2), implementations=implementations
    )
    if not result1.is_successful:
        msg = f"Registration failed: {result1.errors}"
        raise RuntimeError(msg)
    if result1.generation != _EXPECTED_GEN_1:
        msg = f"Expected generation 1, got {result1.generation}"
        raise RuntimeError(msg)
    if result1.disposer is None:
        msg = "Expected disposer handle in result"
        raise RuntimeError(msg)
    if result1.contributions[0].version != "1.2.0":
        msg = f"Expected version 1.2.0, got {result1.contributions[0].version}"
        raise RuntimeError(msg)
    if result1.contributions[0].generation != _EXPECTED_GEN_1:
        msg = f"Expected generation 1, got {result1.contributions[0].generation}"
        raise RuntimeError(msg)
    print(
        f"  -> Successfully registered {len(result1.contributions)} "
        f"contributions at generation {result1.generation}."
    )

    print("\n[Scenario 2] Verifying rejection of duplicate/conflicting...")
    conflict_detected = False
    try:
        service.register_contributions(manifest, (c1,))
    except PluginContributionError as exc:
        conflict_detected = True
        print(f"  -> Conflicting registration rejected as expected: {exc}")

    if not conflict_detected:
        msg = "Expected duplicate registration to be rejected!"
        raise RuntimeError(msg)

    return result1


def _demo_scenario_3(
    service: RegisterContributionsService,
    manifest: PluginManifest,
    c1: PluginContributionDescriptor,
    c2: PluginContributionDescriptor,
    result1: ContributionRegistrationResult,
) -> PluginContributionDescriptor:
    print("\n[Scenario 3] Registering generation 2 and verifying scoped disposal...")
    c3 = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.METRIC,
        contribution_id=f"{manifest.id}.beta",
        name="Beta Ratio",
        description="Market sensitivity metric.",
    )
    result2 = service.register_contributions(
        manifest, (c3,), implementations={c3.contribution_id: MockBeta()}
    )
    if result2.generation != _EXPECTED_GEN_2:
        msg = f"Expected generation 2, got {result2.generation}"
        raise RuntimeError(msg)
    print(f"  -> Generation 2 registered with contribution '{c3.contribution_id}'.")

    # Dispose ONLY generation 1 using its disposer handle
    removed = result1.disposer()
    if removed != _EXPECTED_REMOVED_GEN_1:
        msg = f"Expected 2 generation-1 contributions removed, got {removed}"
        raise RuntimeError(msg)
    print(f"  -> Disposer executed: removed {removed} items from generation 1.")

    if service.get_contribution(c1.contribution_id) is not None:
        msg = f"Generation 1 contribution '{c1.contribution_id}' was not removed"
        raise RuntimeError(msg)
    if service.get_contribution(c2.contribution_id) is not None:
        msg = f"Generation 1 contribution '{c2.contribution_id}' was not removed"
        raise RuntimeError(msg)
    active_gen2 = service.get_contribution(c3.contribution_id)
    if active_gen2 is None:
        msg = "Generation 2 contribution was unexpectedly removed!"
        raise RuntimeError(msg)
    if active_gen2.generation != _EXPECTED_GEN_2:
        msg = f"Expected generation 2, got {active_gen2.generation}"
        raise RuntimeError(msg)
    print(
        f"  -> Verified: generation 1 items removed while generation 2 item "
        f"'{c3.contribution_id}' remains active."
    )
    return c3


def _demo_scenario_4(
    service: RegisterContributionsService,
    manifest: PluginManifest,
    c3: PluginContributionDescriptor,
) -> None:
    print("\n[Scenario 4] Verifying deterministic exposure and withdrawal...")
    all_active = service.get_contributions()
    if len(all_active) != 1 or all_active[0].contribution_id != c3.contribution_id:
        msg = "Active contributions query returned unexpected items"
        raise RuntimeError(msg)

    withdrawn = service.unregister_contributions(manifest.id)
    if withdrawn != 1:
        msg = f"Expected 1 item withdrawn, got {withdrawn}"
        raise RuntimeError(msg)
    if len(service.get_contributions()) != 0:
        msg = "Expected empty registry after full unregister"
        raise RuntimeError(msg)
    if service.get_contribution(c3.contribution_id) is not None:
        msg = "Contribution still accessible after unregister"
        raise RuntimeError(msg)
    print("  -> Full withdrawal verified: zero active contributions, no stale state.")


async def _demo_scenario_5_lifecycle() -> None:
    print("\n[Scenario 5] Testing lifecycle mount and capability withdrawal...")
    registry = ServiceRegistry()
    unrelated_key: CapabilityKey[str] = CapabilityKey(
        name="unrelated.analytics", major=1
    )
    unrelated_scope = FeatureScope(owner_id="FEAT-ANA-SAMPLE")
    registry.register(
        unrelated_key,
        "sample_active_analytics",
        owner_id="FEAT-ANA-SAMPLE",
        scope=unrelated_scope,
    )

    feat = RegisterContributionsFeature()
    scope = FeatureScope(owner_id=feat.spec.feature_id)

    def registrar(
        cap: CapabilityKey[object],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=EventBus(),
    )

    await feat.mount(context, {})
    if registry.resolve(REGISTER_CONTRIBUTIONS_CAPABILITY) is None:
        msg = "Expected registered capability on mount"
        raise RuntimeError(msg)
    print("  -> Mounted RegisterContributionsFeature into registry.")

    await scope.close()
    await feat.unmount(context)

    # Confirm capability is unavailable
    if registry.is_available(REGISTER_CONTRIBUTIONS_CAPABILITY):
        msg = "Capability still available after unmount"
        raise RuntimeError(msg)
    if registry.resolve(REGISTER_CONTRIBUTIONS_CAPABILITY) is not None:
        msg = "Capability still resolved after unmount"
        raise RuntimeError(msg)

    unavailable = False
    try:
        registry.require(REGISTER_CONTRIBUTIONS_CAPABILITY)
    except CapabilityUnavailableError:
        unavailable = True
    if not unavailable:
        msg = "Expected CapabilityUnavailableError from registry.require"
        raise RuntimeError(msg)

    # Confirm unrelated capability is unaffected
    if not registry.is_available(unrelated_key):
        msg = "Unrelated capability became unavailable"
        raise RuntimeError(msg)
    if registry.resolve(unrelated_key) != "sample_active_analytics":
        msg = "Unrelated capability resolution value changed"
        raise RuntimeError(msg)
    if registry.require(unrelated_key) != "sample_active_analytics":
        msg = "Unrelated capability require value changed"
        raise RuntimeError(msg)
    print(
        "  -> Verified: RegisterContributionsCapability withdrawn while "
        "unrelated capabilities remain intact."
    )


def _run_usage_example() -> None:
    """Execute all bounded offline demonstration scenarios.

    Raises:
        RuntimeError: If any demonstration invariant fails.
    """
    print("=== [FEAT-PLUG-REGISTER_CONTRIBUTIONS] Demonstrating Scenarios ===")
    logger.info(
        "Starting usage demonstration",
        feature_id="FEAT-PLUG-REGISTER_CONTRIBUTIONS",
        event="plugins.register_contributions.usage_start",
    )

    service = RegisterContributionsService()

    manifest = PluginManifest(
        id="com.haruquantai.sample.analytics",
        version="1.2.0",
        api_range=">=1.0.0,<2.0.0",
        types=(PluginType.INDICATOR, PluginType.METRIC),
    )

    c1 = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=f"{manifest.id}.rsi",
        name="Relative Strength Index",
        description="Standard 14-period RSI indicator.",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=manifest.id,
        plugin_type=PluginType.METRIC,
        contribution_id=f"{manifest.id}.sharpe",
        name="Sharpe Ratio",
        description="Risk-adjusted return metric.",
    )

    res1 = _demo_scenario_1_and_2(service, manifest, c1, c2)
    c3 = _demo_scenario_3(service, manifest, c1, c2, res1)
    _demo_scenario_4(service, manifest, c3)
    asyncio.run(_demo_scenario_5_lifecycle())

    print(
        "\n[SUCCESS] FEAT-PLUG-REGISTER_CONTRIBUTIONS: All 5 usage scenarios "
        "passed cleanly."
    )
    logger.info(
        "Usage demonstration completed successfully",
        feature_id="FEAT-PLUG-REGISTER_CONTRIBUTIONS",
        event="plugins.register_contributions.usage_success",
    )


if __name__ == "__main__":
    _run_usage_example()
