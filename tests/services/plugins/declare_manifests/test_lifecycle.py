"""Lifecycle and non-functional requirement tests for FEAT-PLUG-DECLARE_MANIFESTS.

Tests:
    ATN-PLUG-DECLARE_MANIFESTS-001:
        Disable and physically remove declare_manifests; its operation is unavailable,
        unrelated capabilities remain usable, and retained source objects are unchanged.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.contracts.plugins.ports import DeclareManifestsCapability
from app.kernel.capability import CapabilityKey, CapabilityUnavailableError
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.plugins.declare_manifests.feature import DeclareManifestsFeature


@pytest.mark.asyncio
async def test_trc_declare_manifests_nfr_001_lifecycle_and_withdrawal(
    tmp_path: Path,
) -> None:
    """ATN-PLUG-DECLARE_MANIFESTS-001: Capability withdrawal leaves unrelated capabilities & files intact."""
    # 1. Setup shared registry with DeclareManifestsFeature and an unrelated capability
    registry = ServiceRegistry()
    event_bus = EventBus()

    unrelated_key: CapabilityKey[str] = CapabilityKey(
        name="unrelated.analytics", major=1
    )
    unrelated_scope = FeatureScope(owner_id="FEAT-ANA-SAMPLE")
    registry.register(
        unrelated_key,
        "active_service_instance",
        owner_id="FEAT-ANA-SAMPLE",
        scope=unrelated_scope,
    )

    # 2. Mount DeclareManifestsFeature under its own feature scope
    manifest_feature = DeclareManifestsFeature()
    manifest_scope = FeatureScope(owner_id=manifest_feature.spec.feature_id)

    def registrar(
        cap: CapabilityKey[Any],
        impl: object,
        sc: FeatureScope,
    ) -> None:
        registry.register(
            cap, impl, owner_id=manifest_feature.spec.feature_id, scope=sc
        )

    manifest_context = DefaultFeatureContext(
        spec=manifest_feature.spec,
        scope=manifest_scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=event_bus,
    )
    await manifest_feature.mount(manifest_context, {})

    # Both capabilities are present in the registry
    assert registry.is_available(DECLARE_MANIFESTS_CAPABILITY)
    assert registry.is_available(unrelated_key)

    # 3. Create and validate a retained plugin package on disk
    zip_path = tmp_path / "retained_plugin.zip"
    manifest_data = {
        "id": "com.haruquantai.test.retained",
        "version": "1.0.0",
        "apiRange": ">=1.0.0,<2.0.0",
        "type": ["BLOCK"],
        "entryPoint": "block.py",
    }
    payload_bytes = b"print('retained block')\n"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("plugin.json", json.dumps(manifest_data))
        zf.writestr("block.py", payload_bytes)

    initial_bytes = zip_path.read_bytes()
    initial_hash = hashlib.sha256(initial_bytes).hexdigest()

    # Inspect using active capability
    cap = registry.require(DECLARE_MANIFESTS_CAPABILITY)
    assert isinstance(cap, DeclareManifestsCapability)
    validation = cap.validate_package(zip_path)
    assert validation.is_valid

    # 4. Disable and physically withdraw declare_manifests by closing its scope
    await manifest_scope.close()

    # 5. Verify DECLARE_MANIFESTS_CAPABILITY is now unavailable
    assert not registry.is_available(DECLARE_MANIFESTS_CAPABILITY)
    assert registry.resolve(DECLARE_MANIFESTS_CAPABILITY) is None
    with pytest.raises(CapabilityUnavailableError):
        registry.require(DECLARE_MANIFESTS_CAPABILITY)

    # 6. Verify unrelated capability remains completely registered and usable
    assert registry.is_available(unrelated_key)
    assert registry.resolve(unrelated_key) == "active_service_instance"

    # 7. Verify retained source objects on disk are completely unchanged
    assert zip_path.exists()
    retained_bytes = zip_path.read_bytes()
    assert hashlib.sha256(retained_bytes).hexdigest() == initial_hash
    assert retained_bytes == initial_bytes

    # 8. Unrelated scope cleanup
    await unrelated_scope.close()
    assert not registry.is_available(unrelated_key)
