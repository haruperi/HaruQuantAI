"""Acceptance tests for the three owned persistence requirements."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest
from app.contracts.workspace.errors import (
    EvidenceImmutableError,
    MigrationChecksumError,
    NamespaceAccessDeniedError,
    RevisionConflictError,
    WorkspaceMigrationError,
)
from app.contracts.workspace.persistence import (
    EvidenceRecord,
    ExportEvidenceRequest,
    FeatureMigration,
    FeatureMigrationManifest,
    NamespaceRegistration,
    PersistenceStatement,
    PersistenceTransactionRequest,
)
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)


def test_trc_execute_persistence_001(tmp_path: Path) -> None:
    """AT-WS-EXECUTE_PERSISTENCE-001:

    A workflow writer cannot update claim tables; two competing
    expected-revision writes accept exactly one.
    """
    workspace = tmp_path / "ws_001"
    (workspace / "metadata").mkdir(parents=True)
    service = ExecutePersistenceService()

    # 1. Register namespaces
    service.register_namespace(
        NamespaceRegistration(
            namespace="workflow",
            allowed_tables=("wf_runs", "wf_steps"),
        )
    )
    service.register_namespace(
        NamespaceRegistration(
            namespace="claim",
            allowed_tables=("claims", "claim_history"),
        )
    )

    # Set up tables via migrations
    service.apply_migrations(
        workspace,
        FeatureMigrationManifest(
            namespace="workflow",
            migrations=(
                FeatureMigration(
                    version=1,
                    name="init_wf",
                    sql="CREATE TABLE wf_runs (id TEXT PRIMARY KEY, name TEXT);",
                    checksum=hashlib.sha256(
                        b"CREATE TABLE wf_runs (id TEXT PRIMARY KEY, name TEXT);"
                    ).hexdigest(),
                ),
            ),
        ),
    )
    service.apply_migrations(
        workspace,
        FeatureMigrationManifest(
            namespace="claim",
            migrations=(
                FeatureMigration(
                    version=1,
                    name="init_claims",
                    sql="CREATE TABLE claims (id TEXT PRIMARY KEY, amount REAL);",
                    checksum=hashlib.sha256(
                        b"CREATE TABLE claims (id TEXT PRIMARY KEY, amount REAL);"
                    ).hexdigest(),
                ),
            ),
        ),
    )

    # 2. A workflow writer attempts to update claim tables -> denied
    cross_write_request = PersistenceTransactionRequest(
        request_id=str(uuid.uuid4()),
        actor_id="actor-workflow",
        account_id="acc-1",
        workspace_path=workspace,
        namespace="workflow",
        statements=(
            PersistenceStatement(
                sql="UPDATE claims SET amount = 100.0 WHERE id = 'c-1'"
            ),
        ),
    )
    with pytest.raises(NamespaceAccessDeniedError) as exc_info:
        service.execute_transaction(cross_write_request)
    assert exc_info.value.namespace == "workflow"
    assert exc_info.value.table == "claims"

    # Also check direct INSERT into claims by workflow
    cross_insert_request = PersistenceTransactionRequest(
        request_id=str(uuid.uuid4()),
        actor_id="actor-workflow",
        account_id="acc-1",
        workspace_path=workspace,
        namespace="workflow",
        statements=(
            PersistenceStatement(
                sql="INSERT INTO claims (id, amount) VALUES ('c-2', 50.0)"
            ),
        ),
    )
    with pytest.raises(NamespaceAccessDeniedError):
        service.execute_transaction(cross_insert_request)

    # 3. Two competing expected-revision writes: accept exactly one
    tx_a = PersistenceTransactionRequest(
        request_id=str(uuid.uuid4()),
        actor_id="actor-a",
        account_id="acc-1",
        workspace_path=workspace,
        namespace="workflow",
        statements=(
            PersistenceStatement(
                sql="INSERT INTO wf_runs (id, name) VALUES ('run-1', 'job-a')"
            ),
        ),
        expected_revision=1,
    )
    tx_b = PersistenceTransactionRequest(
        request_id=str(uuid.uuid4()),
        actor_id="actor-b",
        account_id="acc-1",
        workspace_path=workspace,
        namespace="workflow",
        statements=(
            PersistenceStatement(
                sql="INSERT INTO wf_runs (id, name) VALUES ('run-2', 'job-b')"
            ),
        ),
        expected_revision=1,
    )

    result_a = service.execute_transaction(tx_a)
    assert result_a.rows_affected == 1
    assert result_a.new_revision == 2

    # Second competing request with expected_revision=1 must fail
    with pytest.raises(RevisionConflictError) as conflict_info:
        service.execute_transaction(tx_b)
    assert conflict_info.value.expected == 1
    assert conflict_info.value.actual == 2

    # Idempotency: replaying tx_a returns the cached result without error
    replay_a = service.execute_transaction(tx_a)
    assert replay_a.request_id == tx_a.request_id
    assert replay_a.new_revision == 2

    service.close()


def test_trc_execute_persistence_002(tmp_path: Path) -> None:
    """AT-WS-EXECUTE_PERSISTENCE-002:

    Reapplying the same manifest changes nothing; changed checksum fails;
    a failed migration does not partially advance the schema version.
    """
    workspace = tmp_path / "ws_002"
    (workspace / "metadata").mkdir(parents=True)
    service = ExecutePersistenceService()

    sql_v1 = "CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);"
    checksum_v1 = hashlib.sha256(sql_v1.encode()).hexdigest()
    manifest_v1 = FeatureMigrationManifest(
        namespace="admin",
        migrations=(
            FeatureMigration(
                version=1,
                name="create_settings",
                sql=sql_v1,
                checksum=checksum_v1,
            ),
        ),
    )

    # Initial apply
    result1 = service.apply_migrations(workspace, manifest_v1)
    assert result1.current_version == 1
    assert result1.applied_versions == (1,)

    # 1. Reapplying identical manifest changes nothing
    result_reapply = service.apply_migrations(workspace, manifest_v1)
    assert result_reapply.current_version == 1
    assert result_reapply.applied_versions == ()

    # 2. Changed checksum fails
    tampered_manifest = FeatureMigrationManifest(
        namespace="admin",
        migrations=(
            FeatureMigration(
                version=1,
                name="create_settings",
                sql=sql_v1,
                checksum="tampered_checksum_hex",
            ),
        ),
    )
    with pytest.raises(MigrationChecksumError) as checksum_exc:
        service.apply_migrations(workspace, tampered_manifest)
    assert checksum_exc.value.namespace == "admin"
    assert checksum_exc.value.version == 1

    # 3. Failed migration does not partially advance schema version
    sql_v2_broken = "CREATE TABLE broken_table (syntax error ???);"
    broken_manifest = FeatureMigrationManifest(
        namespace="admin",
        migrations=(
            FeatureMigration(
                version=1,
                name="create_settings",
                sql=sql_v1,
                checksum=checksum_v1,
            ),
            FeatureMigration(
                version=2,
                name="broken_migration",
                sql=sql_v2_broken,
                checksum=hashlib.sha256(sql_v2_broken.encode()).hexdigest(),
            ),
        ),
    )
    with pytest.raises(WorkspaceMigrationError) as mig_exc:
        service.apply_migrations(workspace, broken_manifest)
    assert mig_exc.value.version == 2

    # Schema version should still be 1, not 2
    verify_result = service.apply_migrations(workspace, manifest_v1)
    assert verify_result.current_version == 1

    service.close()


def test_trc_execute_persistence_003(tmp_path: Path) -> None:
    """AT-WS-EXECUTE_PERSISTENCE-003:

    An attempted overwrite/delete of retained evidence is denied;
    paged export has stable order and cannot cross workspace scope.
    """
    workspace_a = tmp_path / "ws_003_a"
    workspace_b = tmp_path / "ws_003_b"
    (workspace_a / "metadata").mkdir(parents=True)
    (workspace_b / "metadata").mkdir(parents=True)
    service = ExecutePersistenceService()

    service.register_namespace(
        NamespaceRegistration(
            namespace="audit",
            allowed_tables=("audit_runs",),
            evidence_tables=("audit_evidence",),
        )
    )

    ev_1 = EvidenceRecord(
        evidence_id="ev-100",
        workspace_id=workspace_a.name,
        namespace="audit",
        content_hash=hashlib.sha256(b"payload-1").hexdigest(),
        payload_json='{"event": "start"}',
        created_at="2026-09-07T10:00:00.000000Z",
    )
    ev_2 = EvidenceRecord(
        evidence_id="ev-101",
        workspace_id=workspace_a.name,
        namespace="audit",
        content_hash=hashlib.sha256(b"payload-2").hexdigest(),
        payload_json='{"event": "complete"}',
        created_at="2026-09-07T10:05:00.000000Z",
    )
    ev_b = EvidenceRecord(
        evidence_id="ev-200",
        workspace_id=workspace_b.name,
        namespace="audit",
        content_hash=hashlib.sha256(b"payload-b").hexdigest(),
        payload_json='{"event": "workspace_b_event"}',
        created_at="2026-09-07T10:10:00.000000Z",
    )

    stored_1 = service.append_evidence(workspace_a, "audit", ev_1)
    stored_2 = service.append_evidence(workspace_a, "audit", ev_2)
    service.append_evidence(workspace_b, "audit", ev_b)

    assert stored_1.sequence < stored_2.sequence

    # 1. Attempted overwrite of retained evidence is denied
    with pytest.raises(EvidenceImmutableError):
        service.append_evidence(workspace_a, "audit", ev_1)

    # 2. Direct attempt to update or delete evidence via transaction is denied
    direct_update = PersistenceTransactionRequest(
        request_id=str(uuid.uuid4()),
        actor_id="actor-auditor",
        account_id="acc-1",
        workspace_path=workspace_a,
        namespace="audit",
        statements=(
            PersistenceStatement(
                sql="UPDATE audit_evidence SET payload_json = '{}' WHERE evidence_id = 'ev-100'"
            ),
        ),
    )
    with pytest.raises(EvidenceImmutableError):
        service.execute_transaction(direct_update)

    direct_delete = PersistenceTransactionRequest(
        request_id=str(uuid.uuid4()),
        actor_id="actor-auditor",
        account_id="acc-1",
        workspace_path=workspace_a,
        namespace="audit",
        statements=(
            PersistenceStatement(
                sql="DELETE FROM audit_evidence WHERE evidence_id = 'ev-100'"
            ),
        ),
    )
    with pytest.raises(EvidenceImmutableError):
        service.execute_transaction(direct_delete)

    # 3. Paged export has stable order and cannot cross workspace scope
    export_page_1 = service.export_evidence(
        ExportEvidenceRequest(
            workspace_path=workspace_a,
            namespace="audit",
            limit=1,
            offset=0,
        )
    )
    assert export_page_1.total_count == 2
    assert len(export_page_1.records) == 1
    assert export_page_1.records[0].evidence_id == "ev-100"
    assert export_page_1.has_more is True

    export_page_2 = service.export_evidence(
        ExportEvidenceRequest(
            workspace_path=workspace_a,
            namespace="audit",
            limit=1,
            offset=1,
        )
    )
    assert len(export_page_2.records) == 1
    assert export_page_2.records[0].evidence_id == "ev-101"
    assert export_page_2.has_more is False

    # Check that export from workspace_a does not contain evidence from workspace_b
    all_exported_ids = {r.evidence_id for r in export_page_1.records} | {
        r.evidence_id for r in export_page_2.records
    }
    assert "ev-200" not in all_exported_ids

    # Export from workspace_b only contains ev-200
    export_b = service.export_evidence(
        ExportEvidenceRequest(
            workspace_path=workspace_b,
            namespace="audit",
            limit=10,
            offset=0,
        )
    )
    assert export_b.total_count == 1
    assert export_b.records[0].evidence_id == "ev-200"

    service.close()
