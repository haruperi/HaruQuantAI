"""Lifecycle and non-functional requirement tests for FEAT-PLUG-REGISTER_CONTRIBUTIONS.

Tests:
    ATN-PLUG-REGISTER_CONTRIBUTIONS-001:
        Disable and physically remove register_contributions; its operation is
        unavailable, unrelated capabilities remain usable, and retained source
        objects are unchanged. No dependent operation may silently select a
        substitute provider.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.contracts.plugins.ports import RegisterContributionsCapability
from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.register_contributions.feature import (
    RegisterContributionsFeature,
)


@pytest.mark.asyncio
async def test_trc_register_contributions_nfr_001_lifecycle_and_withdrawal(
    tmp_path: Path,
) -> None:
    """ATN-PLUG-REGISTER_CONTRIBUTIONS-001:

    Verify:
    1. Capability mount and unmount in shared kernel registry.
    2. Capability withdrawal renders REGISTER_CONTRIBUTIONS_CAPABILITY unavailable.
    3. Unrelated capabilities remain registered and usable.
    4. Retained source files on disk remain bit-for-bit unchanged.
    5. No silent substitute provider is selected when the capability is unavailable.
    """
    # 1. Setup shared registry with an unrelated capability
    registry = ServiceRegistry()
    event_bus = EventBus()

    unrelated_key: CapabilityKey[str] = CapabilityKey(
        name="unrelated.analytics", major=1
    )
    unrelated_scope = FeatureScope(owner_id="FEAT-ANA-SAMPLE")
    registry.register(
        unrelated_key,
        "sample_active_analytics_service",
        owner_id="FEAT-ANA-SAMPLE",
        scope=unrelated_scope,
    )

    # 2. Mount RegisterContributionsFeature
    feat = RegisterContributionsFeature()
    feat_scope = FeatureScope(owner_id=feat.spec.feature_id)

    def registrar(
        cap: CapabilityKey[Any],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(cap, impl, owner_id=feat.spec.feature_id, scope=sc)

    context = DefaultFeatureContext(
        spec=feat.spec,
        scope=feat_scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )

    await feat.mount(context, {})
    assert registry.is_available(REGISTER_CONTRIBUTIONS_CAPABILITY)
    assert registry.is_available(unrelated_key)

    service = registry.require(REGISTER_CONTRIBUTIONS_CAPABILITY)
    assert isinstance(service, RegisterContributionsCapability)

    # 3. Create a retained source fixture on disk
    fixture_file = tmp_path / "sample_contribution_source.py"
    fixture_content = (
        b"# Retained plugin contribution source code\ndef test_calc():\n    return 42\n"
    )
    fixture_file.write_bytes(fixture_content)
    initial_hash = hashlib.sha256(fixture_content).hexdigest()

    # 4. Disable and physically unmount RegisterContributionsFeature by closing its scope
    await feat_scope.close()
    await feat.unmount(context)

    # 5. Verify REGISTER_CONTRIBUTIONS_CAPABILITY is now unavailable
    assert not registry.is_available(REGISTER_CONTRIBUTIONS_CAPABILITY)
    assert registry.resolve(REGISTER_CONTRIBUTIONS_CAPABILITY) is None

    # Verifying no dependent operation may silently select a substitute provider
    with pytest.raises(CapabilityUnavailableError):
        registry.require(REGISTER_CONTRIBUTIONS_CAPABILITY)

    # 6. Verify unrelated capability remains usable
    assert registry.is_available(unrelated_key)
    assert registry.resolve(unrelated_key) == "sample_active_analytics_service"
    assert registry.require(unrelated_key) == "sample_active_analytics_service"

    # 7. Verify retained source objects on disk remain completely unchanged
    assert fixture_file.exists()
    retained_bytes = fixture_file.read_bytes()
    assert retained_bytes == fixture_content
    assert hashlib.sha256(retained_bytes).hexdigest() == initial_hash

    # Clean up unrelated scope
    await unrelated_scope.close()
    assert not registry.is_available(unrelated_key)
