"""Immutable feature specification for FEAT-WS-MANAGE_ARTIFACTS."""

from __future__ import annotations

from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import (
    MANAGE_ARTIFACTS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-MANAGE_ARTIFACTS",
    domain="workspace",
    provides=frozenset({MANAGE_ARTIFACTS_CAPABILITY}),
    requires=frozenset({PERSISTENCE_CAPABILITY}),
    optional=frozenset({RESERVE_RESOURCES_CAPABILITY}),
    conflicts=frozenset(),
    description=(
        "Publish and retain immutable artifact bytes through staged "
        "validation, atomic content-addressed custody, bounded download "
        "grants, and admitted reference-aware maintenance."
    ),
    state=StateDeclaration(
        namespace="workspace.manage_artifacts",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Artifact catalog, custody/access/retention metadata and "
            "staging leases; immutable files remain content-addressed."
        ),
    ),
    config_keys=frozenset(
        {
            "database_path",
            "custody_root",
            "max_artifact_bytes",
            "staging_max_age_seconds",
            "cleanup_batch_limit",
            "grant_max_ttl_seconds",
        }
    ),
)
