"""Offline usage demonstrations for FEAT-WS-EXECUTE_PERSISTENCE."""

from __future__ import annotations

import hashlib
import tempfile
import uuid
from pathlib import Path

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


def _run_usage_example() -> None:  # noqa: C901, PLR0915 - executable FR walkthrough.
    """Run all four bounded offline persistence scenarios.

    Raises:
        RuntimeError: If an expected outcome fails.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        workspace_root = Path(tmp_dir) / "demo_workspace"
        (workspace_root / "metadata").mkdir(parents=True, exist_ok=True)
        service = ExecutePersistenceService()

        print("[1/4] Registering namespaces and executing migrations...")
        service.register_namespace(
            NamespaceRegistration(
                namespace="workflow",
                allowed_tables=("wf_runs", "wf_steps"),
                evidence_tables=("wf_evidence",),
            )
        )
        service.register_namespace(
            NamespaceRegistration(
                namespace="claims",
                allowed_tables=("claim_records",),
            )
        )

        v1_sql = """
        CREATE TABLE wf_runs (
            run_id TEXT PRIMARY KEY,
            status TEXT NOT NULL
        );
        CREATE TABLE wf_steps (
            step_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            name TEXT NOT NULL
        );
        """
        v1_checksum = hashlib.sha256(v1_sql.encode()).hexdigest()
        manifest = FeatureMigrationManifest(
            namespace="workflow",
            migrations=(
                FeatureMigration(
                    version=1,
                    name="create_workflow_tables",
                    sql=v1_sql,
                    checksum=v1_checksum,
                ),
            ),
        )
        mig_result = service.apply_migrations(workspace_root, manifest)
        if mig_result.current_version != 1 or mig_result.applied_versions != (1,):
            raise RuntimeError("Initial migration did not produce version 1")

        # Reapplying same manifest changes nothing
        reapply = service.apply_migrations(workspace_root, manifest)
        if reapply.current_version != 1 or reapply.applied_versions != ():
            raise RuntimeError("Idempotent migration re-application altered state")
        print("  - Migration v1 applied and verified idempotent.")

        # Tampered checksum fails
        tampered_manifest = FeatureMigrationManifest(
            namespace="workflow",
            migrations=(
                FeatureMigration(
                    version=1,
                    name="create_workflow_tables",
                    sql=v1_sql,
                    checksum="tampered_hash_value",
                ),
            ),
        )
        try:
            service.apply_migrations(workspace_root, tampered_manifest)
        except MigrationChecksumError:
            print("  - Tampered migration checksum rejected successfully.")

        # Failed migration rolls back transactionally
        bad_manifest = FeatureMigrationManifest(
            namespace="workflow",
            migrations=(
                FeatureMigration(
                    version=1,
                    name="create_workflow_tables",
                    sql=v1_sql,
                    checksum=v1_checksum,
                ),
                FeatureMigration(
                    version=2,
                    name="broken_table",
                    sql="CREATE TABLE broken_table (syntax error here);",
                    checksum="some_hash",
                ),
            ),
        )
        try:
            service.apply_migrations(workspace_root, bad_manifest)
        except WorkspaceMigrationError:
            print(
                "  - Faulty migration step rolled back without advancing "
                "schema version."
            )

        print("[2/4] Verifying namespace table boundary enforcement...")
        # Workflow writer attempts to update claim_records (undeclared table)
        denied_req = PersistenceTransactionRequest(
            request_id=str(uuid.uuid4()),
            actor_id="actor-1",
            account_id="acc-1",
            workspace_path=workspace_root,
            namespace="workflow",
            statements=(
                PersistenceStatement(
                    sql="INSERT INTO claim_records (id) VALUES ('fake-claim')"
                ),
            ),
        )
        try:
            service.execute_transaction(denied_req)
        except NamespaceAccessDeniedError:
            print("  - Cross-namespace write to 'claim_records' by 'workflow' denied.")

        print("[3/4] Testing optimistic revision control and idempotency...")
        tx_req1 = PersistenceTransactionRequest(
            request_id=str(uuid.uuid4()),
            actor_id="actor-1",
            account_id="acc-1",
            workspace_path=workspace_root,
            namespace="workflow",
            statements=(
                PersistenceStatement(
                    sql=(
                        "INSERT INTO wf_runs (run_id, status) "
                        "VALUES ('run-1', 'RUNNING')"
                    )
                ),
            ),
            expected_revision=1,
        )
        tx_res1 = service.execute_transaction(tx_req1)
        expected_next_rev = 2
        if tx_res1.new_revision != expected_next_rev:
            raise RuntimeError("First transaction did not advance revision to 2")
        print("  - First transaction committed; revision advanced 1 -> 2.")

        # Re-submitting identical request_id is idempotent
        idem_res = service.execute_transaction(tx_req1)
        if idem_res.new_revision != expected_next_rev:
            raise RuntimeError("Idempotent replay did not match previous result")
        print("  - Duplicate request_id returned cached idempotent result.")

        # Competing write with stale expected_revision=1 fails
        tx_competing = PersistenceTransactionRequest(
            request_id=str(uuid.uuid4()),
            actor_id="actor-2",
            account_id="acc-1",
            workspace_path=workspace_root,
            namespace="workflow",
            statements=(
                PersistenceStatement(
                    sql=(
                        "INSERT INTO wf_runs (run_id, status) "
                        "VALUES ('run-2', 'QUEUED')"
                    )
                ),
            ),
            expected_revision=1,
        )
        try:
            service.execute_transaction(tx_competing)
        except RevisionConflictError:
            print("  - Competing write with stale expected_revision=1 rejected.")

        print("[4/4] Testing append-only evidence custody and paged export...")
        evidence1 = EvidenceRecord(
            evidence_id="ev-001",
            workspace_id="demo_workspace",
            namespace="workflow",
            content_hash=hashlib.sha256(b"ev-content-1").hexdigest(),
            payload_json='{"status": "PASSED"}',
            created_at="2026-09-07T12:00:00.000000Z",
        )
        stored_ev1 = service.append_evidence(workspace_root, "workflow", evidence1)
        if stored_ev1.sequence < 1:
            raise RuntimeError("Evidence sequence was not positive integer")
        print("  - Evidence ev-001 appended.")

        # Duplicate/overwrite denied
        try:
            service.append_evidence(workspace_root, "workflow", evidence1)
        except EvidenceImmutableError:
            print("  - Overwrite of evidence ev-001 denied.")

        # Paged export
        export_res = service.export_evidence(
            ExportEvidenceRequest(
                workspace_path=workspace_root,
                namespace="workflow",
                limit=10,
                offset=0,
            )
        )
        if (
            export_res.total_count != 1
            or len(export_res.records) != 1
            or export_res.records[0].evidence_id != "ev-001"
        ):
            raise RuntimeError("Paged export did not return expected evidence record")
        print("  - Paged export returned 1 record with stable ordering.")

        service.close()
        print("\nAll usage demonstrations completed successfully.")


if __name__ == "__main__":
    _run_usage_example()
