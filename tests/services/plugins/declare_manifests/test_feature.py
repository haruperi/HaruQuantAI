"""Unit tests for DeclareManifestsFeature lifecycle and entry points."""

from __future__ import annotations

import pytest
from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.contracts.plugins.ports import DeclareManifestsCapability
from app.services.plugins.declare_manifests.feature import (
    DeclareManifestsFeature,
    feature,
)
from app.services.plugins.declare_manifests.manifest import SPEC

from tests.conformance.stateless_feature import (
    StatelessFeatureCase,
    assert_factory_spec,
    assert_scoped_withdrawal,
    mount_stateless_feature,
)

CASE = StatelessFeatureCase(
    factory=feature,
    feature_type=DeclareManifestsFeature,
    spec=SPEC,
    capability=DECLARE_MANIFESTS_CAPABILITY,
    entry_point_name="plugins-declare-manifests",
)


def test_feature_factory_and_spec() -> None:
    """Verify feature factory and SPEC declaration."""
    feat = assert_factory_spec(CASE)
    assert feat.spec.feature_id == "FEAT-PLUG-DECLARE_MANIFESTS"
    assert feat.spec.domain == "plugins"
    assert DECLARE_MANIFESTS_CAPABILITY in feat.spec.provides
    assert not feat.spec.requires
    assert feat.spec.config_keys == frozenset(
        {"max_package_size_bytes", "max_file_count", "strict_signatures"}
    )
    assert feat.service is None


@pytest.mark.asyncio
async def test_feature_mount() -> None:
    """Verify feature mounting provides DECLARE_MANIFESTS_CAPABILITY in context."""
    feat, _registry, scope, resolved = await mount_stateless_feature(
        CASE, {"max_package_size_bytes": 1024 * 1024}
    )

    assert feat.service is not None
    assert resolved is feat.service
    assert isinstance(resolved, DeclareManifestsCapability)

    await scope.close()


@pytest.mark.asyncio
async def test_shared_scope_withdrawal_conformance() -> None:
    """Verify the generic owner-scope withdrawal contract."""
    await assert_scoped_withdrawal(CASE)
