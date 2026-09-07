"""Integration test for workspace persistence execution capability."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

import pytest
from app.contracts.workspace.capabilities import (
    MANAGE_WORKSPACES_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.contracts.workspace.manage_workspaces import (
    ManageWorkspaceOperation,
    ManageWorkspacesRequest,
)
from app.contracts.workspace.models import WorkspaceStatus
from app.contracts.workspace.persistence import (
    EvidenceRecord,
    ExportEvidenceRequest,
    FeatureMigration,
    FeatureMigrationManifest,
    NamespaceRegistration,
    PersistenceCapability,
    PersistenceStatement,
    PersistenceTransactionRequest,
)
from app.kernel.capability import CapabilityKey
from app.kernel.context import DefaultFeatureContext
from app.kernel.events import EventBus
from app.kernel.registry import ServiceRegistry
from app.kernel.scope import FeatureScope
from app.services.workspace.execute_persistence.feature import (
    feature as persistence_feature,
)
from app.services.workspace.manage_workspaces.feature import (
    feature as workspace_feature,
)


@pytest.mark.asyncio
async def test_execute_persistence_integration(tmp_path: Path) -> None:
    """Verify integration of manage_workspaces and execute_persistence in shared context."""
    registry = ServiceRegistry()
    event_bus = EventBus()

    ws_feat = workspace_feature()
    ws_scope = FeatureScope(owner_id=ws_feat.spec.feature_id)

    pers_feat = persistence_feature()
    pers_scope = FeatureScope(owner_id=pers_feat.spec.feature_id)

    def ws_registrar(cap: CapabilityKey[Any], impl: object, sc: FeatureScope) -> None:
        registry.register(cap, impl, owner_id=ws_feat.spec.feature_id, scope=sc)

    def pers_registrar(cap: CapabilityKey[Any], impl: object, sc: FeatureScope) -> None:
        registry.register(cap, impl, owner_id=pers_feat.spec.feature_id, scope=sc)

    ws_context = DefaultFeatureContext(
        spec=ws_feat.spec,
        scope=ws_scope,
        resolver=registry.resolve,
        provider_registrar=ws_registrar,
        event_bus=event_bus,
    )
    pers_context = DefaultFeatureContext(
        spec=pers_feat.spec,
        scope=pers_scope,
        resolver=registry.resolve,
        provider_registrar=pers_registrar,
        event_bus=event_bus,
    )

    # 1. Mount both features
    await ws_feat.mount(ws_context, {})
    await pers_feat.mount(pers_context, {})

    ws_service = registry.resolve(MANAGE_WORKSPACES_CAPABILITY)
    pers_service = registry.resolve(PERSISTENCE_CAPABILITY)

    assert ws_service is not None
    assert pers_service is not None
    assert isinstance(pers_service, PersistenceCapability)

    # 2. Initialize a workspace using manage_workspaces
    ws_root = tmp_path / "integration_workspace"
    open_res = ws_service.manage_workspaces(
        ManageWorkspacesRequest(
            request_id=str(uuid.uuid4()),
            actor_id="integration-actor",
            account_id="integration-account",
            operation=ManageWorkspaceOperation.OPEN,
            workspace_path=ws_root,
            name="Integration Workspace",
        )
    )
    assert open_res.workspace is not None
    assert open_res.workspace.status == WorkspaceStatus.READY

    # 3. Register feature namespace and apply migrations via execute_persistence
    pers_service.register_namespace(
        NamespaceRegistration(
            namespace="strategy",
            allowed_tables=("strategies", "strategy_params"),
            evidence_tables=("strategy_audit",),
        )
    )

    migration_sql = """
    CREATE TABLE strategies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1
    );
    CREATE TABLE strategy_params (
        strategy_id TEXT NOT NULL,
        param_name TEXT NOT NULL,
        param_value TEXT NOT NULL,
        PRIMARY KEY (strategy_id, param_name)
    );
    """
    manifest = FeatureMigrationManifest(
        namespace="strategy",
        migrations=(
            FeatureMigration(
                version=1,
                name="init_strategy_tables",
                sql=migration_sql,
                checksum=hashlib.sha256(migration_sql.encode()).hexdigest(),
            ),
        ),
    )
    mig_res = pers_service.apply_migrations(ws_root, manifest)
    assert mig_res.current_version == 1
    assert mig_res.applied_versions == (1,)

    # 4. Execute transaction with optimistic locking
    tx_res = pers_service.execute_transaction(
        PersistenceTransactionRequest(
            request_id=str(uuid.uuid4()),
            actor_id="integration-actor",
            account_id="integration-account",
            workspace_path=ws_root,
            namespace="strategy",
            statements=(
                PersistenceStatement(
                    sql="INSERT INTO strategies (id, name) VALUES ('strat-1', 'TrendFollower')"
                ),
                PersistenceStatement(
                    sql="INSERT INTO strategy_params (strategy_id, param_name, param_value) VALUES ('strat-1', 'period', '20')"
                ),
            ),
            expected_revision=1,
        )
    )
    assert tx_res.rows_affected == 2
    assert tx_res.new_revision == 2

    # 5. Append and export evidence
    evidence = EvidenceRecord(
        evidence_id="ev-strat-1",
        workspace_id=open_res.workspace.workspace_id,
        namespace="strategy",
        content_hash=hashlib.sha256(b"strat-1-evidence").hexdigest(),
        payload_json='{"status": "compiled", "metrics": {}}',
        created_at="2026-09-07T14:00:00.000000Z",
    )
    appended = pers_service.append_evidence(ws_root, "strategy", evidence)
    assert appended.sequence >= 1

    exported = pers_service.export_evidence(
        ExportEvidenceRequest(
            workspace_path=ws_root,
            namespace="strategy",
            limit=10,
            offset=0,
        )
    )
    assert exported.total_count == 1
    assert exported.records[0].evidence_id == "ev-strat-1"

    # 6. Teardown
    await pers_scope.close()
    await ws_scope.close()
    assert registry.resolve(PERSISTENCE_CAPABILITY) is None
    assert registry.resolve(MANAGE_WORKSPACES_CAPABILITY) is None
