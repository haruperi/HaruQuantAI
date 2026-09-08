"""Persistence adapter for artifact metadata, references, holds, and grants."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.contracts.workspace.persistence import (
    FeatureMigration,
    FeatureMigrationManifest,
    NamespaceRegistration,
    PersistenceCapability,
    PersistenceStatement,
    PersistenceTransactionRequest,
)

NAMESPACE = "workspace.artifacts"
TABLES = (
    "workspace_artifacts",
    "workspace_artifact_refs",
    "workspace_artifact_holds",
    "workspace_artifact_grants",
)
MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS workspace_artifacts (
    artifact_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    byte_count INTEGER NOT NULL,
    schema_id TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    published_at TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS workspace_artifact_refs (
    artifact_id TEXT NOT NULL,
    reference_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    PRIMARY KEY (artifact_id, reference_id)
);
CREATE TABLE IF NOT EXISTS workspace_artifact_holds (
    artifact_id TEXT NOT NULL,
    hold_id TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    PRIMARY KEY (artifact_id, hold_id)
);
CREATE TABLE IF NOT EXISTS workspace_artifact_grants (
    grant_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    content_hash TEXT NOT NULL
);
""".strip()
MIGRATION = FeatureMigration(
    1,
    "artifact-custody-v1",
    MIGRATION_SQL,
    "e7ae8957f795eef6d6f6a79362ba11c292668690dfad311bc273cd38822b206e",
)


class ArtifactStore:
    """Namespace-bound artifact persistence helper."""

    def __init__(self, persistence: PersistenceCapability, workspace_path: Path) -> None:
        self._persistence = persistence
        self.workspace_path = workspace_path
        persistence.register_namespace(NamespaceRegistration(NAMESPACE, TABLES))
        persistence.apply_migrations(
            workspace_path,
            FeatureMigrationManifest(NAMESPACE, (MIGRATION,)),
        )

    def execute(
        self,
        request_id: str,
        actor_id: str,
        account_id: str,
        statements: tuple[PersistenceStatement, ...],
    ) -> tuple[tuple[dict[str, object], ...], ...]:
        """Execute one namespace-scoped transaction."""
        result = self._persistence.execute_transaction(
            PersistenceTransactionRequest(
                request_id=request_id,
                actor_id=actor_id,
                account_id=account_id,
                workspace_path=self.workspace_path,
                namespace=NAMESPACE,
                statements=statements,
            )
        )
        return result.results

    def query(
        self,
        account_id: str,
        sql: str,
        parameters: tuple[object, ...],
    ) -> tuple[dict[str, object], ...]:
        """Execute a deterministic bounded read transaction."""
        canonical = json.dumps(
            [sql, [str(parameter) for parameter in parameters]],
            separators=(",", ":"),
            ensure_ascii=True,
        )
        digest = hashlib.sha256(canonical.encode()).hexdigest()[:24]
        rows = self.execute(
            f"artifact-query:{digest}",
            "artifact-system",
            account_id,
            (PersistenceStatement(sql, parameters),),
        )
        return rows[0] if rows else ()
