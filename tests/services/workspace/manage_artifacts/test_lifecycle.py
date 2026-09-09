"""Lifecycle and removability evidence for FEAT-WS-MANAGE_ARTIFACTS.

Binds ``ATN-WS-MANAGE_ARTIFACTS-001``: scope close withdraws only the
declared ``workspace.artifacts@1`` contribution, unrelated capabilities
remain usable, and committed artifact custody state is retained.
"""

from __future__ import annotations

import hashlib
import sqlite3
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any
from uuid import uuid7

import pytest
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.orchestration.resources import ResourceAdmissionPort
from app.contracts.workspace.artifacts import (
    ArtifactPublication,
    InspectArtifactRequest,
    PublishArtifactRequest,
)
from app.contracts.workspace.capabilities import (
    MANAGE_ARTIFACTS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext, FeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.orchestration.reserve_resources._persistence import (
    ResourceReservationStore,
)
from app.services.orchestration.reserve_resources.reserve_resources import (
    ReserveResourcesService,
)
from app.services.workspace.manage_artifacts.feature import feature
from app.services.workspace.manage_artifacts.manage_artifacts import (
    ManageArtifactsService,
)

_WORKSPACE = "lifecycle-workspace"
_ACCOUNT = "lifecycle-account"
_PRINCIPAL = "lifecycle-principal"
_PAYLOAD = b"lifecycle artifact payload\n" * 4
_PAYLOAD_HASH = f"sha256:{hashlib.sha256(_PAYLOAD).hexdigest()}"

_UNRELATED_PROTOCOL = CapabilityKey[Any](name="test.unrelated", major=1)


class _UnrelatedProvider:
    """Sibling provider proving capability isolation across scope close."""

    def ping(self) -> str:
        """Return one stable sibling observation."""
        return "unrelated"


class _MountableFeature:
    """Minimal typed shape of an entry-point feature factory result."""

    spec: Any

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount into the supplied scoped context."""


def _context(
    instance: Any,
    scope: FeatureScope,
    registry: ServiceRegistry,
) -> FeatureContext:
    """Build one scoped feature context bound to the local registry."""

    def register(
        capability: CapabilityKey[Any],
        implementation: object,
        owner_scope: FeatureScope,
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner_scope,
        )

    return DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=register,
        event_bus=EventBus(),
    )


@pytest.mark.asyncio
async def test_trc_ws_manage_artifacts_nfr_001_removal_and_retention(
    tmp_path: Path,
) -> None:
    """ATN-001: withdrawal is scoped; committed custody is retained."""
    root = tmp_path / "workspace"
    root.mkdir()
    registry = ServiceRegistry()

    candidates = entry_points(group="haruquantai.features")
    persistence_entry = next(
        entry for entry in candidates if entry.name == "workspace-execute-persistence"
    )
    persistence_feature: Any = persistence_entry.load()()
    persistence_scope = FeatureScope(owner_id=persistence_feature.spec.feature_id)
    await persistence_feature.mount(
        _context(persistence_feature, persistence_scope, registry),
        {},
    )
    assert registry.resolve(PERSISTENCE_CAPABILITY) is not None

    admission: ResourceAdmissionPort = ReserveResourcesService(
        store=ResourceReservationStore(),
        total_disk_bytes=100 * 1024**3,
        free_disk_bytes=50 * 1024**3,
    )
    admission_scope = FeatureScope(owner_id="FEAT-ORCH-RESERVE_RESOURCES")
    registry.register(
        RESERVE_RESOURCES_CAPABILITY,
        admission,
        owner_id="FEAT-ORCH-RESERVE_RESOURCES",
        scope=admission_scope,
    )

    sibling_scope = FeatureScope(owner_id="TEST-UNRELATED")
    registry.register(
        _UNRELATED_PROTOCOL,
        _UnrelatedProvider(),
        owner_id="TEST-UNRELATED",
        scope=sibling_scope,
    )

    artifacts_feature = feature()
    artifacts_scope = FeatureScope(owner_id=artifacts_feature.spec.feature_id)
    await artifacts_feature.mount(
        _context(artifacts_feature, artifacts_scope, registry),
        {"database_path": root},
    )
    provider = registry.require(MANAGE_ARTIFACTS_CAPABILITY)
    assert isinstance(provider, ManageArtifactsService)

    receipt = await provider.publish_artifact(
        PublishArtifactRequest(
            request_id=str(uuid7()),
            actor_id=_PRINCIPAL,
            publication=ArtifactPublication(
                artifact_id="lifecycle-artifact",
                workspace_id=_WORKSPACE,
                account_id=_ACCOUNT,
                schema_declaration="application/octet-stream",
                byte_count=len(_PAYLOAD),
                content_hash=_PAYLOAD_HASH,
                idempotency_key="lifecycle-key",
                source_reference="run-0001",
            ),
            payload=_PAYLOAD,
        )
    )
    digest = receipt.content_hash.removeprefix("sha256:")
    object_file = provider.custody_root / "objects" / digest[:2] / f"{digest}.bin"
    assert object_file.is_file()

    await artifacts_scope.close()
    assert registry.resolve(MANAGE_ARTIFACTS_CAPABILITY) is None
    assert registry.resolve(PERSISTENCE_CAPABILITY) is not None
    assert registry.resolve(RESERVE_RESOURCES_CAPABILITY) is not None
    assert registry.require(_UNRELATED_PROTOCOL).ping() == "unrelated"

    assert object_file.is_file()
    connection = sqlite3.connect(root / "database" / "haruquantai.db")
    try:
        retained_rows = connection.execute(
            "SELECT COUNT(*) FROM artifact_publications WHERE artifact_id = ?",
            ("lifecycle-artifact",),
        ).fetchone()[0]
    finally:
        connection.close()
    assert retained_rows == 1

    replacement = feature()
    replacement_scope = FeatureScope(owner_id=replacement.spec.feature_id)
    await replacement.mount(
        _context(replacement, replacement_scope, registry),
        {"database_path": root},
    )
    retained_provider = registry.require(MANAGE_ARTIFACTS_CAPABILITY)
    assert isinstance(retained_provider, ManageArtifactsService)
    committed = await retained_provider.inspect_artifact(
        InspectArtifactRequest(
            request_id=str(uuid7()),
            actor_id=_PRINCIPAL,
            artifact_id="lifecycle-artifact",
            workspace_id=_WORKSPACE,
            account_id=_ACCOUNT,
        )
    )
    assert committed.content_hash == receipt.content_hash

    retained_provider.close()
    retained_provider.close()
    await replacement_scope.close()
    await sibling_scope.close()
    await admission_scope.close()
    await persistence_scope.close()
