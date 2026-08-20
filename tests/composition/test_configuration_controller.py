"""Unit tests for controlled Tier-1 configuration replacement controller.

Traces to: P17-T01, Phase 17, Gate G17
"""

from __future__ import annotations

import datetime as dt
from types import MappingProxyType

import pytest
from app.composition import (
    CompositionRuntime,
    ConfigurationReplacementEvidence,
    ProviderConfiguration,
    replace_provider_configuration,
)
from app.kernel.errors import ManifestValidationError
from app.kernel.identifiers import CapabilityId, ProviderId, SemanticVersion
from app.kernel.manifests import (
    Cardinality,
    EffectClass,
    LifecyclePolicy,
    ProvidedCapability,
    ProviderManifest,
    ReloadPolicy,
)
from app.kernel.profiles import RuntimeProfile
from app.kernel.registry import ProviderInventory


def _make_dummy_manifest(pid: str, cap: str) -> ProviderManifest:
    return ProviderManifest(
        provider_id=ProviderId.parse(pid),
        provider_version=SemanticVersion(1, 0, 0),
        entry_point="dummy.plugin:create_provider",
        provides=(
            ProvidedCapability(
                CapabilityId.parse(cap),
                SemanticVersion(1, 0, 0),
                Cardinality.EXACTLY_ONE,
            ),
        ),
        requires=(),
        optional_requires=(),
        profiles=(RuntimeProfile.LIVE,),
        scopes=("process",),
        effect_classes=(EffectClass.REVERSIBLE_EPHEMERAL,),
        lifecycle=LifecyclePolicy.SCOPED,
        reload=ReloadPolicy.PROCESS_RESTART,
        config_schema=None,
        state_schema_id=None,
        state_schema_version=None,
        migration_manifest=None,
        compatible_state_majors=(),
        uninstall_retention=None,
        purge_requires_authorization=False,
    )


def _empty_inventory() -> ProviderInventory:
    return ProviderInventory(
        providers=(),
        by_provider=MappingProxyType({}),
        by_capability=MappingProxyType({}),
    )


def test_blank_request_id_rejected() -> None:
    """Verify empty or blank request_id raises ValueError."""
    runtime = CompositionRuntime()
    inventory = _empty_inventory()
    config = ProviderConfiguration()
    with pytest.raises(ValueError, match="request_id"):
        replace_provider_configuration(
            runtime,
            inventory,
            config,
            config,
            factories={},
            request_id="   ",
        )


def test_uninstalled_provider_rejected_before_mutation() -> None:
    """Verify candidate with uninstalled provider raises ManifestValidationError."""
    runtime = CompositionRuntime()
    inventory = _empty_inventory()
    current = ProviderConfiguration()
    candidate = ProviderConfiguration(
        enabled_provider_ids=frozenset({ProviderId.parse("uninstalled.cap.prov")})
    )

    with pytest.raises(ManifestValidationError):
        replace_provider_configuration(
            runtime,
            inventory,
            current,
            candidate,
            factories={},
            request_id="req-001",
        )


def test_noop_replacement_returns_unchanged_evidence() -> None:
    """Verify identical configuration returns empty changed_provider_ids."""
    m = _make_dummy_manifest("test.cap.p1", "test.cap.v1")
    inventory = ProviderInventory(
        providers=(m,),
        by_provider=MappingProxyType({m.provider_id: m}),
        by_capability=MappingProxyType({CapabilityId.parse("test.cap.v1"): (m,)}),
    )
    runtime = CompositionRuntime()
    pid = m.provider_id
    config = ProviderConfiguration(
        enabled_provider_ids=frozenset({pid}),
    )

    evidence = replace_provider_configuration(
        runtime,
        inventory,
        config,
        config,
        factories={pid: lambda _cfg: "instance_p1"},
        request_id="req-noop",
        clock=lambda: dt.datetime(2026, 8, 20, 12, 0, 0, tzinfo=dt.UTC),
    )

    assert isinstance(evidence, ConfigurationReplacementEvidence)
    assert evidence.request_id == "req-noop"
    assert evidence.changed_provider_ids == ()
    assert not evidence.rolled_back
    assert evidence.completed_at == "2026-08-20T12:00:00+00:00"
