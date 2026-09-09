"""Bounded persistence adapter for artifact-custody-owned records.

All SQL lives in this module and executes strictly through the public
``workspace.persistence@1`` capability inside the feature-owned
``workspace.manage_artifacts`` namespace; no raw connections are opened.
"""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any

from app.contracts.workspace.persistence import (
    FeatureMigration,
    FeatureMigrationManifest,
    NamespaceRegistration,
    PersistenceCapability,
    PersistenceStatement,
    PersistenceTransactionRequest,
    PersistenceTransactionResult,
)

NAMESPACE = "workspace.manage_artifacts"
_TABLES = (
    "artifact_publications",
    "artifact_staging",
    "artifact_references",
    "artifact_retention_state",
    "artifact_grants",
)
_SCHEMA_VERSION = 1

# Rows in artifact_publications and artifact_staging carry a custody state
# constrained to exactly the ratified restart classification; durable
# unknown states therefore fail closed at write time.
_MIGRATION_1_SQL = """
CREATE TABLE IF NOT EXISTS artifact_publications (
    artifact_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    schema_declaration TEXT NOT NULL,
    byte_count INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    idempotency_fingerprint TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    custody_revision INTEGER NOT NULL,
    published_at TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('PUBLISHED_VALID')),
    PRIMARY KEY (workspace_id, artifact_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_publication_idempotency
ON artifact_publications(workspace_id, idempotency_key);
CREATE INDEX IF NOT EXISTS idx_publication_content
ON artifact_publications(content_hash);
CREATE TABLE IF NOT EXISTS artifact_staging (
    staging_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    schema_declaration TEXT NOT NULL,
    byte_count INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    idempotency_fingerprint TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN
        ('STAGING_INCOMPLETE', 'BYTES_READY_METADATA_PENDING')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_staging_idempotency
ON artifact_staging(workspace_id, idempotency_key);
CREATE TABLE IF NOT EXISTS artifact_references (
    reference_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    owner_namespace TEXT NOT NULL,
    owner_record_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (workspace_id, artifact_id, owner_namespace, owner_record_id)
);
CREATE INDEX IF NOT EXISTS idx_reference_artifact
ON artifact_references(workspace_id, artifact_id);
CREATE TABLE IF NOT EXISTS artifact_retention_state (
    workspace_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    legal_hold INTEGER NOT NULL CHECK (legal_hold IN (0, 1)),
    updated_at TEXT NOT NULL,
    PRIMARY KEY (workspace_id, artifact_id)
);
CREATE TABLE IF NOT EXISTS artifact_grants (
    grant_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    action TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    generation INTEGER NOT NULL CHECK (generation >= 1),
    revoked INTEGER NOT NULL CHECK (revoked IN (0, 1)),
    created_at TEXT NOT NULL
);
"""


def _migration(version: int, name: str, sql: str) -> FeatureMigration:
    """Build one checksum-pinned additive migration.

    Returns:
        Immutable migration record with a digest of the exact SQL bytes.
    """
    return FeatureMigration(
        version=version,
        name=name,
        sql=sql,
        checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
    )


MIGRATIONS = FeatureMigrationManifest(
    namespace=NAMESPACE,
    migrations=(_migration(1, "create_artifact_custody_tables", _MIGRATION_1_SQL),),
)


class ArtifactCustodyStore:
    """Own all artifact SQL while using only the public persistence capability."""

    def __init__(
        self,
        persistence: PersistenceCapability,
        workspace_path: Path,
    ) -> None:
        """Register artifact table boundaries and apply additive migrations.

        Args:
            persistence: Active bounded Workspace persistence provider.
            workspace_path: Canonical workspace root.

        Raises:
            RuntimeError: If migrations do not reach the declared schema.
        """
        self._persistence = persistence
        self._workspace_path = workspace_path
        persistence.register_namespace(
            NamespaceRegistration(namespace=NAMESPACE, allowed_tables=_TABLES)
        )
        result = persistence.apply_migrations(workspace_path, MIGRATIONS)
        if result.current_version != _SCHEMA_VERSION:
            raise RuntimeError(
                "manage-artifacts schema migration did not reach version 1"
            )

    def execute(
        self,
        *,
        request_id: str,
        actor_id: str,
        account_id: str,
        statements: tuple[PersistenceStatement, ...],
    ) -> PersistenceTransactionResult:
        """Execute one namespace-bound custody transaction.

        Args:
            request_id: Fresh unique transaction identity.
            actor_id: Acting principal identity.
            account_id: Requesting account scope.
            statements: Ordered bounded statements.

        Returns:
            Transaction execution outcome with results and new revision.
        """
        return self._persistence.execute_transaction(
            PersistenceTransactionRequest(
                request_id=request_id,
                actor_id=actor_id,
                account_id=account_id,
                workspace_path=self._workspace_path,
                namespace=NAMESPACE,
                statements=statements,
            )
        )

    @staticmethod
    def read_request_id(request_id: str, operation: str) -> str:
        """Create a fresh persistence identity for a current-state read.

        Returns:
            Unique bounded read identity that cannot replay a stale result.
        """
        return f"{request_id}:{operation}:{uuid.uuid4()}"

    def find_publication(
        self,
        *,
        request_id: str,
        workspace_id: str,
        artifact_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | None:
        """Return one published artifact row by identity or idempotency key.

        Returns:
            Current publication row, or None when absent.
        """
        if artifact_id is not None:
            sql = (
                "SELECT * FROM artifact_publications "
                "WHERE workspace_id = ? AND artifact_id = ?"
            )
            parameters: tuple[Any, ...] = (workspace_id, artifact_id)
        else:
            sql = (
                "SELECT * FROM artifact_publications "
                "WHERE workspace_id = ? AND idempotency_key = ?"
            )
            parameters = (workspace_id, idempotency_key)
        result = self.execute(
            request_id=self.read_request_id(request_id, "find-publication"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(PersistenceStatement(sql=sql, parameters=parameters),),
        )
        rows = result.results[0]
        return rows[0] if rows else None

    def find_staging(
        self,
        *,
        request_id: str,
        workspace_id: str,
        idempotency_key: str,
    ) -> dict[str, Any] | None:
        """Return one staging row by workspace and idempotency key.

        Returns:
            Current staging row, or None when absent.
        """
        result = self.execute(
            request_id=self.read_request_id(request_id, "find-staging"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql=(
                        "SELECT * FROM artifact_staging "
                        "WHERE workspace_id = ? AND idempotency_key = ?"
                    ),
                    parameters=(workspace_id, idempotency_key),
                ),
            ),
        )
        rows = result.results[0]
        return rows[0] if rows else None

    def insert_staging(self, *, request_id: str, row: dict[str, Any]) -> None:
        """Create one durable staging record in ``STAGING_INCOMPLETE`` state."""
        self.execute(
            request_id=f"{request_id}:stage",
            actor_id="artifact-custody",
            account_id=row["account_id"],
            statements=(
                PersistenceStatement(
                    sql="""
                    INSERT INTO artifact_staging (
                        staging_id, artifact_id, workspace_id, account_id,
                        schema_declaration, byte_count, content_hash,
                        idempotency_key, idempotency_fingerprint,
                        source_reference, state, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'STAGING_INCOMPLETE', ?, ?)
                    """,
                    parameters=(
                        row["staging_id"],
                        row["artifact_id"],
                        row["workspace_id"],
                        row["account_id"],
                        row["schema_declaration"],
                        row["byte_count"],
                        row["content_hash"],
                        row["idempotency_key"],
                        row["idempotency_fingerprint"],
                        row["source_reference"],
                        row["created_at"],
                        row["created_at"],
                    ),
                ),
            ),
        )

    def mark_staging_bytes_ready(
        self, *, request_id: str, staging_id: str, updated_at: str
    ) -> bool:
        """Advance one staging record to ``BYTES_READY_METADATA_PENDING``.

        Returns:
            True when the guarded state transition applied.
        """
        result = self.execute(
            request_id=f"{request_id}:bytes-ready",
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    UPDATE artifact_staging
                    SET state = 'BYTES_READY_METADATA_PENDING', updated_at = ?
                    WHERE staging_id = ? AND state = 'STAGING_INCOMPLETE'
                    """,
                    parameters=(updated_at, staging_id),
                ),
            ),
        )
        return result.rows_affected == 1

    def finalize_publication(
        self,
        *,
        request_id: str,
        staging_id: str,
    ) -> PersistenceTransactionResult:
        """Atomically publish staged metadata and close the staging record.

        The insert is guarded by the staging state so a concurrent
        finalization or cleanup cannot publish twice; the per-workspace
        custody sequence is computed inside the transaction; and the
        retention state row is created with revision 1 in the same
        transaction.

        Args:
            request_id: Fresh unique transaction identity.
            staging_id: Staging record to publish.

        Returns:
            Transaction outcome; ``rows_affected`` is 3 exactly when this
            call performed the publication, retention seeding, and
            staging close.
        """
        return self.execute(
            request_id=f"{request_id}:finalize",
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    INSERT INTO artifact_publications (
                        artifact_id, workspace_id, account_id,
                        schema_declaration, byte_count, content_hash,
                        idempotency_key, idempotency_fingerprint,
                        source_reference, custody_revision, published_at,
                        state
                    )
                    SELECT artifact_id, workspace_id, account_id,
                           schema_declaration, byte_count, content_hash,
                           idempotency_key, idempotency_fingerprint,
                           source_reference,
                           (SELECT COUNT(*) FROM artifact_publications p2
                            WHERE p2.workspace_id = artifact_staging.workspace_id
                           ) + 1,
                           updated_at,
                           'PUBLISHED_VALID'
                    FROM artifact_staging
                    WHERE staging_id = ?
                      AND state = 'BYTES_READY_METADATA_PENDING'
                      AND NOT EXISTS (
                          SELECT 1 FROM artifact_publications p
                          WHERE p.workspace_id = artifact_staging.workspace_id
                            AND p.artifact_id = artifact_staging.artifact_id
                      )
                    """,
                    parameters=(staging_id,),
                ),
                PersistenceStatement(
                    sql="""
                    INSERT INTO artifact_retention_state (
                        workspace_id, artifact_id, revision, legal_hold,
                        updated_at
                    )
                    SELECT workspace_id, artifact_id, 1, 0, updated_at
                    FROM artifact_staging
                    WHERE staging_id = ?
                      AND state = 'BYTES_READY_METADATA_PENDING'
                      AND NOT EXISTS (
                          SELECT 1 FROM artifact_retention_state r
                          WHERE r.workspace_id = artifact_staging.workspace_id
                            AND r.artifact_id = artifact_staging.artifact_id
                      )
                    """,
                    parameters=(staging_id,),
                ),
                PersistenceStatement(
                    sql="""
                    DELETE FROM artifact_staging
                    WHERE staging_id = ?
                      AND state = 'BYTES_READY_METADATA_PENDING'
                      AND EXISTS (
                          SELECT 1 FROM artifact_publications p
                          WHERE p.workspace_id = artifact_staging.workspace_id
                            AND p.artifact_id = artifact_staging.artifact_id
                      )
                    """,
                    parameters=(staging_id,),
                ),
            ),
        )

    def retention_state(
        self, *, request_id: str, workspace_id: str, artifact_id: str
    ) -> dict[str, Any] | None:
        """Return the mutable retention row for one artifact.

        Returns:
            Current retention row, or None when absent.
        """
        result = self.execute(
            request_id=self.read_request_id(request_id, "retention"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT * FROM artifact_retention_state
                    WHERE workspace_id = ? AND artifact_id = ?
                    """,
                    parameters=(workspace_id, artifact_id),
                ),
            ),
        )
        rows = result.results[0]
        return rows[0] if rows else None

    def reference_count(
        self, *, request_id: str, workspace_id: str, artifact_id: str
    ) -> int:
        """Return the number of live semantic references to one artifact."""
        result = self.execute(
            request_id=self.read_request_id(request_id, "refcount"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT COUNT(*) AS count FROM artifact_references
                    WHERE workspace_id = ? AND artifact_id = ?
                    """,
                    parameters=(workspace_id, artifact_id),
                ),
            ),
        )
        return int(result.results[0][0]["count"])

    def find_reference(
        self,
        *,
        request_id: str,
        reference_id: str,
    ) -> dict[str, Any] | None:
        """Return one semantic reference row.

        Returns:
            Current reference row, or None when absent.
        """
        result = self.execute(
            request_id=self.read_request_id(request_id, "find-reference"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="SELECT * FROM artifact_references WHERE reference_id = ?",
                    parameters=(reference_id,),
                ),
            ),
        )
        rows = result.results[0]
        return rows[0] if rows else None

    def insert_reference(
        self,
        *,
        request_id: str,
        reference_id: str,
        workspace_id: str,
        artifact_id: str,
        owner_namespace: str,
        owner_record_id: str,
        created_at: str,
    ) -> PersistenceTransactionResult:
        """Add one semantic reference and bump the retention revision.

        Returns:
            Persistence transaction result with bumped revision.
        """
        return self.execute(
            request_id=f"{request_id}:add-reference",
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    INSERT INTO artifact_references (
                        reference_id, workspace_id, artifact_id,
                        owner_namespace, owner_record_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    parameters=(
                        reference_id,
                        workspace_id,
                        artifact_id,
                        owner_namespace,
                        owner_record_id,
                        created_at,
                    ),
                ),
                PersistenceStatement(
                    sql="""
                    UPDATE artifact_retention_state
                    SET revision = revision + 1, updated_at = ?
                    WHERE workspace_id = ? AND artifact_id = ?
                    """,
                    parameters=(created_at, workspace_id, artifact_id),
                ),
            ),
        )

    def remove_reference(
        self,
        *,
        request_id: str,
        reference_id: str,
        workspace_id: str,
        artifact_id: str,
        expected_revision: int,
        updated_at: str,
    ) -> PersistenceTransactionResult:
        """Remove one reference under an artifact revision fence.

        Both statements are fenced on the artifact's current retention
        revision equaling ``expected_revision``, so a stale request
        removes and mutates nothing: ``rows_affected`` is 2 exactly when
        the reference was removed (delete + revision bump), 0 otherwise.

        Args:
            request_id: Fresh unique transaction identity.
            reference_id: Reference to remove.
            workspace_id: Owning workspace scope.
            artifact_id: Referenced artifact identity.
            expected_revision: Retention revision the caller observed.
            updated_at: Fresh bump timestamp.

        Returns:
            Transaction outcome with the fenced aggregate row count.
        """
        return self.execute(
            request_id=f"{request_id}:remove-reference",
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    DELETE FROM artifact_references
                    WHERE reference_id = ? AND workspace_id = ?
                      AND EXISTS (
                          SELECT 1 FROM artifact_retention_state r
                          WHERE r.workspace_id = ?
                            AND r.artifact_id = ?
                            AND r.revision = ?
                      )
                    """,
                    parameters=(
                        reference_id,
                        workspace_id,
                        workspace_id,
                        artifact_id,
                        expected_revision,
                    ),
                ),
                PersistenceStatement(
                    sql="""
                    UPDATE artifact_retention_state
                    SET revision = revision + 1, updated_at = ?
                    WHERE workspace_id = ? AND artifact_id = ? AND revision = ?
                    """,
                    parameters=(
                        updated_at,
                        workspace_id,
                        artifact_id,
                        expected_revision,
                    ),
                ),
            ),
        )

    def set_legal_hold(
        self,
        *,
        request_id: str,
        workspace_id: str,
        artifact_id: str,
        hold: bool,
        expected_revision: int,
        updated_at: str,
    ) -> PersistenceTransactionResult:
        """Set or clear one legal hold under an artifact revision fence.

        Returns:
            Persistence transaction result with updated revision fence.
        """
        return self.execute(
            request_id=f"{request_id}:legal-hold",
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    UPDATE artifact_retention_state
                    SET legal_hold = ?, revision = revision + 1, updated_at = ?
                    WHERE workspace_id = ? AND artifact_id = ? AND revision = ?
                    """,
                    parameters=(
                        1 if hold else 0,
                        updated_at,
                        workspace_id,
                        artifact_id,
                        expected_revision,
                    ),
                ),
            ),
        )

    def insert_grant(self, *, request_id: str, row: dict[str, Any]) -> None:
        """Create one durable bounded download grant."""
        self.execute(
            request_id=f"{request_id}:grant",
            actor_id="artifact-custody",
            account_id=row["account_id"],
            statements=(
                PersistenceStatement(
                    sql="""
                    INSERT INTO artifact_grants (
                        grant_id, workspace_id, artifact_id, account_id,
                        principal_id, action, expires_at, generation,
                        revoked, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    """,
                    parameters=(
                        row["grant_id"],
                        row["workspace_id"],
                        row["artifact_id"],
                        row["account_id"],
                        row["principal_id"],
                        row["action"],
                        row["expires_at"],
                        row["generation"],
                        row["created_at"],
                    ),
                ),
            ),
        )

    def find_grant(self, *, request_id: str, grant_id: str) -> dict[str, Any] | None:
        """Return one durable grant row.

        Returns:
            Current grant row, or None when absent.
        """
        result = self.execute(
            request_id=self.read_request_id(request_id, "find-grant"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="SELECT * FROM artifact_grants WHERE grant_id = ?",
                    parameters=(grant_id,),
                ),
            ),
        )
        rows = result.results[0]
        return rows[0] if rows else None

    def staging_scan(
        self,
        *,
        request_id: str,
        state: str,
        created_before: str | None = None,
        limit: int,
    ) -> tuple[dict[str, Any], ...]:
        """Return bounded staging rows for one classification state.

        Args:
            request_id: Fresh read identity.
            state: Custody classification state to select.
            created_before: Optional inclusive created_at cutoff.
            limit: Maximum rows returned.

        Returns:
            Staging rows ordered deterministically by creation.
        """
        sql = "SELECT * FROM artifact_staging WHERE state = ?"
        parameters: list[Any] = [state]
        if created_before is not None:
            sql += " AND created_at <= ?"
            parameters.append(created_before)
        sql += " ORDER BY created_at, staging_id LIMIT ?"
        parameters.append(limit)
        result = self.execute(
            request_id=self.read_request_id(request_id, "staging-scan"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(PersistenceStatement(sql=sql, parameters=tuple(parameters)),),
        )
        return result.results[0]

    def delete_staging_guarded(
        self,
        *,
        request_id: str,
        staging_id: str,
        expected_state: str,
        created_before: str,
    ) -> PersistenceTransactionResult:
        """Delete one staging row only while its classification is unchanged.

        The state and age guards fence the deletion against a concurrent
        finalization or state transition; a changed row is never deleted.

        Returns:
            Transaction outcome; ``rows_affected`` is 1 exactly when the
            guarded deletion applied.
        """
        return self.execute(
            request_id=f"{request_id}:drop-staging",
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    DELETE FROM artifact_staging
                    WHERE staging_id = ? AND state = ? AND created_at <= ?
                    """,
                    parameters=(staging_id, expected_state, created_before),
                ),
            ),
        )

    def published_content_hashes(
        self,
        *,
        request_id: str,
        content_hashes: tuple[str, ...],
    ) -> set[str]:
        """Return which requested content hashes have published artifacts."""
        if not content_hashes:
            return set()
        placeholders = ", ".join("?" for _ in content_hashes)
        sql = (
            "SELECT DISTINCT content_hash FROM artifact_publications "  # noqa: S608
            f"WHERE content_hash IN ({placeholders})"
        )
        result = self.execute(
            request_id=self.read_request_id(request_id, "content-hashes"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql=sql,
                    parameters=content_hashes,
                ),
            ),
        )
        return {str(row["content_hash"]) for row in result.results[0]}

    def staging_content_hashes(
        self,
        *,
        request_id: str,
        content_hashes: tuple[str, ...],
    ) -> set[str]:
        """Return which requested content hashes have live staging rows."""
        if not content_hashes:
            return set()
        placeholders = ", ".join("?" for _ in content_hashes)
        sql = (
            "SELECT DISTINCT content_hash FROM artifact_staging "  # noqa: S608
            f"WHERE content_hash IN ({placeholders})"
        )
        result = self.execute(
            request_id=self.read_request_id(request_id, "staging-hashes"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql=sql,
                    parameters=content_hashes,
                ),
            ),
        )
        return {str(row["content_hash"]) for row in result.results[0]}

    def referenced_artifacts(self, *, request_id: str, limit: int) -> tuple[str, ...]:
        """Return bounded artifact ids that still carry live references."""
        result = self.execute(
            request_id=self.read_request_id(request_id, "referenced"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT DISTINCT artifact_id FROM artifact_references
                    ORDER BY artifact_id LIMIT ?
                    """,
                    parameters=(limit,),
                ),
            ),
        )
        return tuple(str(row["artifact_id"]) for row in result.results[0])

    def held_artifacts(self, *, request_id: str, limit: int) -> tuple[str, ...]:
        """Return bounded artifact ids currently under legal hold."""
        result = self.execute(
            request_id=self.read_request_id(request_id, "held"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT artifact_id FROM artifact_retention_state
                    WHERE legal_hold = 1
                    ORDER BY artifact_id LIMIT ?
                    """,
                    parameters=(limit,),
                ),
            ),
        )
        return tuple(str(row["artifact_id"]) for row in result.results[0])

    def publications_missing_objects(
        self, *, request_id: str, limit: int
    ) -> tuple[dict[str, Any], ...]:
        """Return bounded publication rows for integrity existence checks."""
        result = self.execute(
            request_id=self.read_request_id(request_id, "publications"),
            actor_id="artifact-custody",
            account_id="system",
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT artifact_id, workspace_id, content_hash
                    FROM artifact_publications
                    ORDER BY workspace_id, artifact_id LIMIT ?
                    """,
                    parameters=(limit,),
                ),
            ),
        )
        return result.results[0]
