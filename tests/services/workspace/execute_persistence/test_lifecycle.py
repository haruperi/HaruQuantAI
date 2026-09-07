"""Lifecycle and removability evidence for FEAT-WS-EXECUTE_PERSISTENCE."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest
from app.contracts.workspace.capabilities import PERSISTENCE_CAPABILITY
from app.contracts.workspace.persistence import (
    EvidenceRecord,
    ExportEvidenceRequest,
    NamespaceRegistration,
)
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.execute_persistence.feature import feature


@pytest.mark.asyncio
async def test_trc_execute_persistence_nfr_001(tmp_path: Path) -> None:
    """ATN-WS-EXECUTE_PERSISTENCE-001:

    Removing execute_persistence withdraws only its declared contribution;
    unrelated capabilities remain usable and retained database objects are unchanged.
    """
    registry = ServiceRegistry()
    scope = FeatureScope(owner_id="FEAT-WS-EXECUTE_PERSISTENCE")
    instance = feature()

    def registrar(
        capability: CapabilityKey[Any], implementation: object, owner: FeatureScope
    ) -> None:
        registry.register(
            capability,
            implementation,
            owner_id=instance.spec.feature_id,
            scope=owner,
        )

    context = DefaultFeatureContext(
        spec=instance.spec,
        scope=scope,
        resolver=registry.resolve,
        provider_registrar=registrar,
        event_bus=EventBus(),
    )
    await instance.mount(context, {})

    service = registry.resolve(PERSISTENCE_CAPABILITY)
    assert isinstance(service, ExecutePersistenceService)

    workspace = tmp_path / "lifecycle_ws"
    (workspace / "metadata").mkdir(parents=True)
    service.register_namespace(
        NamespaceRegistration(
            namespace="audit",
            evidence_tables=("audit_evidence",),
        )
    )
    ev = EvidenceRecord(
        evidence_id="ev-lifecycle-1",
        workspace_id=workspace.name,
        namespace="audit",
        content_hash=hashlib.sha256(b"lifecycle").hexdigest(),
        payload_json='{"retained": true}',
        created_at="2026-09-07T12:00:00.000000Z",
    )
    service.append_evidence(workspace, "audit", ev)

    # Close scope (simulate feature unmount / removal)
    await scope.close()

    # Capability is withdrawn
    assert registry.resolve(PERSISTENCE_CAPABILITY) is None

    # Underlying SQLite database file and records remain intact
    db_file = workspace / "metadata" / "workspace.db"
    assert db_file.is_file()

    reader = ExecutePersistenceService()
    export = reader.export_evidence(
        ExportEvidenceRequest(workspace_path=workspace, namespace="audit")
    )
    assert export.total_count == 1
    assert export.records[0].evidence_id == "ev-lifecycle-1"
    reader.close()

    await scope.close()
    assert scope.active_effect_count == 0


@pytest.mark.asyncio
async def test_invalid_mount_has_no_effects() -> None:
    scope = FeatureScope(owner_id="FEAT-WS-EXECUTE_PERSISTENCE")
    instance = feature()
    context = DefaultFeatureContext(spec=instance.spec, scope=scope)
    with pytest.raises(ValueError, match="Unknown"):
        await instance.mount(context, {"unexpected_key": True})
    assert scope.active_effect_count == 0
