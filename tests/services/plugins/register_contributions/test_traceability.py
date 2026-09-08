"""Traceability acceptance tests for FEAT-PLUG-REGISTER_CONTRIBUTIONS.

Tests:
    AT-PLUG-REGISTER_CONTRIBUTIONS-001:
        Duplicate/conflicting registration is rejected; disposal removes only
        its own generation, not all matching names.
    AT-PLUG-REGISTER_CONTRIBUTIONS-002:
        An unmounted widget/role/provider cannot reappear in a later lookup through
        stale global state; contributions are exposed deterministically.
"""

from __future__ import annotations

import pytest
from app.contracts.plugins.errors import PluginContributionError
from app.contracts.plugins.models import (
    PluginContributionDescriptor,
    PluginManifest,
    PluginType,
)
from app.services.plugins.register_contributions.register_contributions import (
    RegisterContributionsService,
    fr_trc_plug_register_contributions_001,
    fr_trc_plug_register_contributions_002,
)


@pytest.fixture
def service() -> RegisterContributionsService:
    """Fixture providing a fresh RegisterContributionsService instance."""
    return RegisterContributionsService()


@pytest.fixture
def base_manifest() -> PluginManifest:
    """Fixture providing a base manifest for traceability tests."""
    return PluginManifest(
        id="com.haruquantai.test.contributions",
        version="2.1.0",
        api_range=">=1.0.0,<3.0.0",
        types=(
            PluginType.INDICATOR,
            PluginType.METRIC,
            PluginType.FILTER,
            PluginType.BLOCK,
        ),
    )


def test_trc_register_contributions_001_exact_generation_disposer_and_conflict_rejection(
    service: RegisterContributionsService,
    base_manifest: PluginManifest,
) -> None:
    """AT-PLUG-REGISTER_CONTRIBUTIONS-001:

    Verify:
    1. Register immutable owner-scoped contributions with exact ID/version/generation
       and return a disposer handle.
    2. Duplicate/conflicting registration (within request or active registry) is rejected.
    3. Disposal removes only its own generation, not all matching names or later generations.
    """
    # 1. Register generation 1
    c1 = PluginContributionDescriptor(
        plugin_id=base_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=f"{base_manifest.id}.macd",
        name="Shared Trend Name",
        description="Generation 1 MACD indicator",
    )
    c2 = PluginContributionDescriptor(
        plugin_id=base_manifest.id,
        plugin_type=PluginType.METRIC,
        contribution_id=f"{base_manifest.id}.volatility",
        name="Volatility Metric",
        description="Generation 1 volatility metric",
    )

    result_gen1 = fr_trc_plug_register_contributions_001(
        base_manifest, (c1, c2), service=service
    )
    assert result_gen1.is_successful is True
    assert result_gen1.generation == 1
    assert result_gen1.disposer is not None
    assert result_gen1.contributions[0].version == "2.1.0"
    assert result_gen1.contributions[0].generation == 1
    assert result_gen1.contributions[1].generation == 1

    # 2. Duplicate registration inside request is rejected
    c_dup = PluginContributionDescriptor(
        plugin_id=base_manifest.id,
        plugin_type=PluginType.FILTER,
        contribution_id=f"{base_manifest.id}.dup",
        name="Duplicate Target",
    )
    with pytest.raises(PluginContributionError, match="Duplicate contribution ID"):
        service.register_contributions(base_manifest, (c_dup, c_dup))

    # 3. Conflicting registration with already active contribution is rejected
    with pytest.raises(
        PluginContributionError, match="Conflicting contribution registration"
    ):
        service.register_contributions(base_manifest, (c1,))

    # Conflicting registration from another plugin attempting to hijack the ID is rejected
    other_manifest = PluginManifest(
        id="com.other.malicious.plugin",
        version="1.0.0",
        api_range=">=1.0.0",
        types=(PluginType.INDICATOR,),
    )
    c_hijack = PluginContributionDescriptor(
        plugin_id=other_manifest.id,
        plugin_type=PluginType.INDICATOR,
        contribution_id=c1.contribution_id,
        name="Hijack Attempt",
    )
    with pytest.raises(
        PluginContributionError, match="Conflicting contribution registration"
    ):
        service.register_contributions(other_manifest, (c_hijack,))

    # 4. Register generation 2 for base_manifest with a contribution sharing the SAME display name
    c3 = PluginContributionDescriptor(
        plugin_id=base_manifest.id,
        plugin_type=PluginType.BLOCK,
        contribution_id=f"{base_manifest.id}.trend_block",
        name="Shared Trend Name",  # Matching name!
        description="Generation 2 trend block sharing the display name",
    )
    result_gen2 = service.register_contributions(base_manifest, (c3,))
    assert result_gen2.is_successful is True
    assert result_gen2.generation == 2
    assert result_gen2.disposer is not None
    assert result_gen2.contributions[0].generation == 2

    # Currently 3 contributions are active
    assert len(service.get_contributions()) == 3

    # 5. Execute disposer handle for Generation 1
    removed_count = result_gen1.disposer()
    assert removed_count == 2

    # 6. Verify: Generation 1 items are removed
    assert service.get_contribution(c1.contribution_id) is None
    assert service.get_contribution(c2.contribution_id) is None

    # Crucial Oracle: Generation 2 item with the matching display name "Shared Trend Name"
    # remains registered and intact! Disposal did NOT remove all matching names!
    retained_gen2 = service.get_contribution(c3.contribution_id)
    assert retained_gen2 is not None
    assert retained_gen2.name == "Shared Trend Name"
    assert retained_gen2.generation == 2
    assert len(service.get_contributions()) == 1

    # Disposing already disposed handle is idempotent and returns 0
    assert result_gen1.disposer() == 0


def test_trc_register_contributions_002_deterministic_exposure_and_no_stale_global_state(
    service: RegisterContributionsService,
    base_manifest: PluginManifest,
) -> None:
    """AT-PLUG-REGISTER_CONTRIBUTIONS-002:

    Verify:
    1. Contributions are exposed in deterministic sorted order.
    2. Withdrawal on unregister is complete.
    3. An unmounted widget/role/provider cannot reappear in a later lookup through stale global state.
    """
    # Register unordered IDs
    ids = ["zeta_contrib", "alpha_contrib", "gamma_contrib", "beta_contrib"]
    items = tuple(
        PluginContributionDescriptor(
            plugin_id=base_manifest.id,
            plugin_type=PluginType.INDICATOR,
            contribution_id=f"{base_manifest.id}.{name}",
            name=name.capitalize(),
        )
        for name in ids
    )

    result = service.register_contributions(base_manifest, items)
    assert result.is_successful is True

    # 1. Deterministic exposure
    queried = fr_trc_plug_register_contributions_002(
        service, plugin_type=PluginType.INDICATOR
    )
    queried_ids = [q.contribution_id for q in queried]
    expected_sorted = sorted(c.contribution_id for c in items)
    assert queried_ids == expected_sorted, (
        "Contributions must be exposed in deterministic sorted order"
    )

    # 2. Complete unregistration
    removed = service.unregister_contributions(base_manifest.id)
    assert removed == 4

    # 3. Verify no stale state in the registry
    assert len(service.get_contributions()) == 0
    assert service.get_contribution(f"{base_manifest.id}.alpha_contrib") is None

    # 4. Fresh instance has zero retained or leaked state (no static global leak)
    fresh_service = RegisterContributionsService()
    assert len(fresh_service.get_contributions()) == 0
    for item in items:
        assert fresh_service.get_contribution(item.contribution_id) is None
