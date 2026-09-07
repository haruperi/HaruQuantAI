"""Feature-local persistence for workspace identity and recovery metadata.

This module is the documented bootstrap exception for the root Workspace
feature: it owns the metadata database that later bounded persistence providers
use. No connection escapes this module and every operation is namespace-bound.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.contracts.workspace.errors import (
    WorkspaceCorruptionError,
    WorkspaceMigrationError,
    WorkspaceNotFoundError,
    WorkspaceStorageError,
)
from app.contracts.workspace.models import (
    WorkspaceRef,
    WorkspaceStatus,
    WorkspaceVersion,
)

CURRENT_SCHEMA_VERSION = 2
CURRENT_APP_VERSION = "0.1.0"

MIGRATION_V1_SQL = """
CREATE TABLE IF NOT EXISTS workspace (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    row_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL,
    checksum TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_setting_versions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    settings_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    row_version INTEGER NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, version)
);

CREATE TABLE IF NOT EXISTS secret_refs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    row_version INTEGER NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, name)
);

CREATE TABLE IF NOT EXISTS audit_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    principal TEXT NOT NULL,
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    details_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS writer_leases (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    holder_pid INTEGER NOT NULL,
    lock_token TEXT NOT NULL UNIQUE,
    is_write_locked INTEGER NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    is_committed INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tombstones (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    deleted_at TEXT NOT NULL,
    UNIQUE(entity_type, entity_id)
);
"""

MIGRATION_V2_SQL = """
ALTER TABLE workspace ADD COLUMN account_id TEXT NOT NULL DEFAULT 'local';
ALTER TABLE artifacts ADD COLUMN relative_path TEXT NOT NULL DEFAULT '';
CREATE TABLE publication_journal (
    publication_id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL,
    staged_relative_path TEXT NOT NULL,
    final_relative_path TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('STAGED', 'PROMOTED', 'ORPHANED')),
    created_at TEXT NOT NULL
);
CREATE TABLE operation_receipts (
    request_id TEXT PRIMARY KEY,
    operation TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    workspace_revision INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
ALTER TABLE audit_events ADD COLUMN request_id TEXT;
CREATE UNIQUE INDEX audit_events_request_id
ON audit_events(request_id) WHERE request_id IS NOT NULL;
"""


@dataclass(frozen=True, slots=True)
class PublicationRecord:
    """One interrupted publication requiring reconciliation."""

    publication_id: str
    content_hash: str
    staged_relative_path: str
    final_relative_path: str
    state: str
    created_at: str


class WorkspacePersistence:
    """Bounded SQLite owner for the workspace metadata namespace."""

    def __init__(self, busy_timeout_seconds: float) -> None:
        self._timeout = busy_timeout_seconds

    def _connect(self, db_path: Path) -> sqlite3.Connection:
        connection = sqlite3.connect(str(db_path), timeout=self._timeout)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(f"PRAGMA busy_timeout={int(self._timeout * 1000)}")
        return connection

    def initialize(
        self,
        db_path: Path,
        *,
        workspace_id: str,
        name: str,
        account_id: str,
        timestamp: str,
    ) -> WorkspaceRef:
        """Create the workspace schema and immutable identity row.

        Returns:
            The newly persisted workspace reference.

        Raises:
            WorkspaceStorageError: If SQLite cannot initialize the workspace.
        """
        try:
            connection = self._connect(db_path)
            try:
                connection.execute("PRAGMA journal_mode=WAL")
                with connection:
                    connection.executescript(MIGRATION_V1_SQL)
                    connection.execute(
                        "INSERT INTO workspace "
                        "(id, name, created_at, updated_at, row_version) "
                        "VALUES (?, ?, ?, ?, 1)",
                        (workspace_id, name, timestamp, timestamp),
                    )
                    connection.execute(
                        "INSERT INTO schema_migrations "
                        "(version, name, applied_at, checksum) VALUES (?, ?, ?, ?)",
                        (
                            1,
                            "base_workspace_schema_v1",
                            timestamp,
                            hashlib.sha256(MIGRATION_V1_SQL.encode()).hexdigest(),
                        ),
                    )
                self._apply_v2(connection, timestamp)
                connection.execute(
                    "UPDATE workspace SET account_id = ? WHERE id = ?",
                    (account_id, workspace_id),
                )
                connection.commit()
            finally:
                connection.close()
        except sqlite3.Error as error:
            message = f"Workspace initialization failed: {error}"
            raise WorkspaceStorageError(message) from error
        return WorkspaceRef(
            workspace_id=workspace_id,
            name=name,
            root_path=db_path.parents[1],
            status=WorkspaceStatus.READY,
            created_at=timestamp,
        )

    def migrate(self, db_path: Path, timestamp: str) -> WorkspaceVersion:
        """Verify immutable migration checksums and apply pending migrations.

        Returns:
            The resulting workspace schema version.

        Raises:
            WorkspaceNotFoundError: If the metadata database does not exist.
            WorkspaceMigrationError: If a checksum or migration fails.
        """
        if not db_path.is_file():
            raise WorkspaceNotFoundError(str(db_path.parents[1]))
        try:
            connection = self._connect(db_path)
            try:
                row = connection.execute(
                    "SELECT checksum FROM schema_migrations WHERE version = 1"
                ).fetchone()
                expected = hashlib.sha256(MIGRATION_V1_SQL.encode()).hexdigest()
                if row is None or row["checksum"] != expected:
                    raise WorkspaceMigrationError(
                        "version 1 checksum mismatch", version=1
                    )
                self._apply_v2(connection, timestamp)
                latest = connection.execute(
                    "SELECT version, applied_at FROM schema_migrations "
                    "ORDER BY version DESC LIMIT 1"
                ).fetchone()
            finally:
                connection.close()
        except WorkspaceMigrationError:
            raise
        except sqlite3.Error as error:
            raise WorkspaceMigrationError(str(error)) from error
        return WorkspaceVersion(
            schema_version=int(latest["version"]),
            app_version=CURRENT_APP_VERSION,
            applied_at=str(latest["applied_at"]),
        )

    def _apply_v2(self, connection: sqlite3.Connection, timestamp: str) -> None:
        existing = connection.execute(
            "SELECT checksum FROM schema_migrations WHERE version = 2"
        ).fetchone()
        checksum = hashlib.sha256(MIGRATION_V2_SQL.encode()).hexdigest()
        if existing is not None:
            if existing["checksum"] != checksum:
                raise WorkspaceMigrationError("version 2 checksum mismatch", version=2)
            return
        try:
            with connection:
                connection.executescript(MIGRATION_V2_SQL)
                connection.execute(
                    "UPDATE artifacts SET relative_path = "
                    "'artifacts/objects/' || content_hash WHERE relative_path = ''"
                )
                connection.execute(
                    "INSERT INTO schema_migrations "
                    "(version, name, applied_at, checksum) VALUES (2, ?, ?, ?)",
                    ("workspace_recovery_v2", timestamp, checksum),
                )
        except sqlite3.Error as error:
            raise WorkspaceMigrationError(str(error), version=2) from error

    def workspace(self, db_path: Path) -> tuple[WorkspaceRef, str, int]:
        """Load the workspace reference, owning account, and revision.

        Returns:
            The workspace reference, account ID, and row revision.

        Raises:
            WorkspaceNotFoundError: If the metadata database does not exist.
            WorkspaceCorruptionError: If its identity row is missing.
        """
        if not db_path.is_file():
            raise WorkspaceNotFoundError(str(db_path.parents[1]))
        connection = self._connect(db_path)
        try:
            row = connection.execute(
                "SELECT id, name, created_at, account_id, row_version "
                "FROM workspace LIMIT 1"
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            raise WorkspaceCorruptionError("Workspace identity row is missing")
        return (
            WorkspaceRef(
                workspace_id=str(row["id"]),
                name=str(row["name"]),
                root_path=db_path.parents[1],
                status=WorkspaceStatus.READY,
                created_at=str(row["created_at"]),
            ),
            str(row["account_id"]),
            int(row["row_version"]),
        )

    def audit(
        self,
        db_path: Path,
        *,
        request_id: str,
        actor_id: str,
        action: str,
        workspace_id: str,
        outcome: str,
        revision: int,
        timestamp: str,
    ) -> None:
        """Append one deduplicated consequential-write audit event."""
        connection = self._connect(db_path)
        try:
            with connection:
                connection.execute(
                    "INSERT OR IGNORE INTO audit_events "
                    "(event_id, created_at, principal, action, object_type, "
                    "object_id, outcome, details_json, request_id) "
                    "VALUES (?, ?, ?, ?, 'workspace', ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        timestamp,
                        actor_id,
                        action,
                        workspace_id,
                        outcome,
                        json.dumps({"revision": revision}, sort_keys=True),
                        request_id,
                    ),
                )
        finally:
            connection.close()

    def committed_artifacts(self, db_path: Path) -> tuple[tuple[str, str, int], ...]:
        """Return committed artifact hash, relative path, and size records."""
        connection = self._connect(db_path)
        try:
            rows = connection.execute(
                "SELECT content_hash, relative_path, size_bytes FROM artifacts "
                "WHERE is_committed = 1 ORDER BY relative_path"
            ).fetchall()
            return tuple(
                (
                    str(row["content_hash"]),
                    str(row["relative_path"]),
                    int(row["size_bytes"]),
                )
                for row in rows
            )
        finally:
            connection.close()

    def catalogue_artifact(
        self,
        db_path: Path,
        *,
        content_hash: str,
        relative_path: str,
        size_bytes: int,
        timestamp: str,
    ) -> None:
        """Record one already-promoted immutable artifact for backup custody."""
        connection = self._connect(db_path)
        try:
            with connection:
                connection.execute(
                    "INSERT INTO artifacts "
                    "(id, content_hash, size_bytes, created_at, is_committed, "
                    "relative_path) "
                    "VALUES (?, ?, ?, ?, 1, ?) "
                    "ON CONFLICT(content_hash) DO UPDATE SET "
                    "size_bytes=excluded.size_bytes, "
                    "relative_path=excluded.relative_path",
                    (
                        str(uuid.uuid4()),
                        content_hash,
                        size_bytes,
                        timestamp,
                        relative_path,
                    ),
                )
        finally:
            connection.close()

    def publications(self, db_path: Path) -> tuple[PublicationRecord, ...]:
        """Return every nonterminal publication journal row."""
        connection = self._connect(db_path)
        try:
            rows = connection.execute(
                "SELECT publication_id, content_hash, staged_relative_path, "
                "final_relative_path, state, created_at FROM publication_journal "
                "ORDER BY created_at"
            ).fetchall()
            return tuple(PublicationRecord(**dict(row)) for row in rows)
        finally:
            connection.close()

    def set_publication_state(
        self, db_path: Path, publication_id: str, state: str
    ) -> None:
        """Set a journal row to a validated recovery state."""
        connection = self._connect(db_path)
        try:
            with connection:
                connection.execute(
                    "UPDATE publication_journal SET state = ? WHERE publication_id = ?",
                    (state, publication_id),
                )
        finally:
            connection.close()

    def delete_publication(self, db_path: Path, publication_id: str) -> None:
        """Delete a fully reconciled pre-promotion journal row."""
        connection = self._connect(db_path)
        try:
            with connection:
                connection.execute(
                    "DELETE FROM publication_journal WHERE publication_id = ?",
                    (publication_id,),
                )
        finally:
            connection.close()

    def artifact_is_committed(self, db_path: Path, content_hash: str) -> bool:
        """Return whether a content hash has a committed catalogue row."""
        connection = self._connect(db_path)
        try:
            return (
                connection.execute(
                    "SELECT 1 FROM artifacts WHERE content_hash = ? "
                    "AND is_committed = 1",
                    (content_hash,),
                ).fetchone()
                is not None
            )
        finally:
            connection.close()
