"""Bounded persistence adapter for account-owned records."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.contracts.workspace.persistence import (
    FeatureMigration,
    FeatureMigrationManifest,
    NamespaceRegistration,
    PersistenceCapability,
    PersistenceStatement,
    PersistenceTransactionRequest,
)

NAMESPACE = "workspace.manage_accounts"
_TABLES = ("users", "user_sessions")
_SCHEMA_VERSION = 2

_MIGRATION_1_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    roles_json TEXT NOT NULL,
    permissions_json TEXT NOT NULL,
    environment TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
    created_at TEXT NOT NULL,
    last_login_at TEXT,
    runtime_profile TEXT NOT NULL DEFAULT 'research' CHECK (
        runtime_profile IN ('research', 'simulation', 'demo', 'live')
    )
);
CREATE TABLE IF NOT EXISTS user_sessions (
    session_digest TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    csrf_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    revoked_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
"""

_MIGRATION_2_SQL = """
ALTER TABLE users ADD COLUMN account_id TEXT NOT NULL DEFAULT 'local';
ALTER TABLE users ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'local';
ALTER TABLE user_sessions ADD COLUMN account_id TEXT NOT NULL DEFAULT 'local';
ALTER TABLE user_sessions ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'local';
ALTER TABLE user_sessions
ADD COLUMN authentication_audit_ref TEXT NOT NULL DEFAULT 'auth_legacy';
CREATE INDEX IF NOT EXISTS idx_user_scope
ON users(account_id, workspace_id, username);
CREATE INDEX IF NOT EXISTS idx_session_scope
ON user_sessions(account_id, workspace_id, user_id);
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
    migrations=(
        _migration(1, "create_legacy_account_tables", _MIGRATION_1_SQL),
        _migration(2, "add_verified_scope_and_audit_reference", _MIGRATION_2_SQL),
    ),
)


@dataclass(frozen=True, slots=True)
class SafeSessionAuditRecord:
    """Credential-free retained authentication/session reference."""

    authentication_audit_ref: str
    user_id: str
    account_id: str
    workspace_id: str
    created_at: str
    expires_at: str
    revoked_at: str | None


class AccountPersistence:
    """Own all account SQL while using only the public persistence capability."""

    def __init__(
        self,
        persistence: PersistenceCapability,
        workspace_path: Path,
    ) -> None:
        """Register account table boundaries and apply additive migrations.

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
                "manage-accounts schema migration did not reach version 2"
            )

    def _execute(
        self,
        *,
        request_id: str,
        actor_id: str,
        account_id: str,
        statements: tuple[PersistenceStatement, ...],
    ) -> tuple[tuple[dict[str, Any], ...], ...]:
        result = self._persistence.execute_transaction(
            PersistenceTransactionRequest(
                request_id=request_id,
                actor_id=actor_id,
                account_id=account_id,
                workspace_path=self._workspace_path,
                namespace=NAMESPACE,
                statements=statements,
            )
        )
        return result.results

    @staticmethod
    def _read_request_id(request_id: str, operation: str) -> str:
        """Create a fresh persistence identity for a current-state read.

        Returns:
            Unique bounded read identity that cannot replay a stale result.
        """
        return f"{request_id}:{operation}:{uuid.uuid4()}"

    def username_exists(
        self,
        *,
        request_id: str,
        username: str,
        account_id: str,
    ) -> bool:
        """Return whether a case-insensitive username already exists.

        Returns:
            True when the retained registry already owns the username.
        """
        results = self._execute(
            request_id=self._read_request_id(request_id, "username"),
            actor_id="system-registration",
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql=(
                        "SELECT 1 AS present FROM users "
                        "WHERE LOWER(username) = LOWER(?)"
                    ),
                    parameters=(username,),
                ),
            ),
        )
        return bool(results[0])

    def register_account(
        self,
        *,
        request_id: str,
        user_id: str,
        username: str,
        password_hash: str,
        account_id: str,
        workspace_id: str,
        runtime_profile: str,
        session_digest: str,
        csrf_digest: str,
        audit_ref: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        """Atomically create an account and its first scoped session."""
        self._execute(
            request_id=f"{request_id}:register",
            actor_id="system-registration",
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql="""
                    INSERT INTO users (
                        user_id, username, password_hash, roles_json,
                        permissions_json, environment, active, verified,
                        created_at, runtime_profile, account_id, workspace_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    parameters=(
                        user_id,
                        username,
                        password_hash,
                        '["user"]',
                        "[]",
                        "development",
                        1,
                        1,
                        created_at,
                        runtime_profile,
                        account_id,
                        workspace_id,
                    ),
                ),
                PersistenceStatement(
                    sql="""
                    INSERT INTO user_sessions (
                        session_digest, user_id, csrf_digest, created_at,
                        expires_at, account_id, workspace_id,
                        authentication_audit_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    parameters=(
                        session_digest,
                        user_id,
                        csrf_digest,
                        created_at,
                        expires_at,
                        account_id,
                        workspace_id,
                        audit_ref,
                    ),
                ),
            ),
        )

    def find_credentials(
        self,
        *,
        request_id: str,
        username: str,
        account_id: str,
        workspace_id: str,
    ) -> dict[str, Any] | None:
        """Return one internal credential row for exact authorized scope."""
        results = self._execute(
            request_id=self._read_request_id(request_id, "credentials"),
            actor_id="system-authentication",
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT user_id, username, password_hash, active, verified,
                           runtime_profile, account_id, workspace_id
                    FROM users
                    WHERE LOWER(username) = LOWER(?)
                      AND account_id = ? AND workspace_id = ?
                    """,
                    parameters=(username, account_id, workspace_id),
                ),
            ),
        )
        rows = results[0]
        return rows[0] if rows else None

    def issue_session(
        self,
        *,
        request_id: str,
        user_id: str,
        account_id: str,
        workspace_id: str,
        session_digest: str,
        csrf_digest: str,
        audit_ref: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        """Create one scoped digest-only session and update login time."""
        self._execute(
            request_id=f"{request_id}:session:{session_digest[:16]}",
            actor_id=user_id,
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql="""
                    INSERT INTO user_sessions (
                        session_digest, user_id, csrf_digest, created_at,
                        expires_at, account_id, workspace_id,
                        authentication_audit_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    parameters=(
                        session_digest,
                        user_id,
                        csrf_digest,
                        created_at,
                        expires_at,
                        account_id,
                        workspace_id,
                        audit_ref,
                    ),
                ),
                PersistenceStatement(
                    sql="UPDATE users SET last_login_at = ? WHERE user_id = ?",
                    parameters=(created_at, user_id),
                ),
            ),
        )

    def resolve_session(
        self,
        *,
        request_id: str,
        session_digest: str,
        account_id: str,
        workspace_id: str,
    ) -> dict[str, Any] | None:
        """Read current principal/session state for the exact requested scope.

        Returns:
            Current joined identity/session row, or None when not found.
        """
        results = self._execute(
            request_id=self._read_request_id(request_id, "revalidate"),
            actor_id="session-verifier",
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT u.user_id, u.username, u.runtime_profile,
                           u.active, u.verified, s.expires_at, s.revoked_at,
                           s.account_id, s.workspace_id,
                           s.authentication_audit_ref
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.user_id
                    WHERE s.session_digest = ?
                      AND s.account_id = ? AND s.workspace_id = ?
                      AND u.account_id = s.account_id
                      AND u.workspace_id = s.workspace_id
                    """,
                    parameters=(session_digest, account_id, workspace_id),
                ),
            ),
        )
        rows = results[0]
        return rows[0] if rows else None

    def revoke_session(
        self,
        *,
        request_id: str,
        session_digest: str,
        revoked_at: str,
        account_id: str,
    ) -> None:
        """Idempotently revoke one digest-identified session."""
        self._execute(
            request_id=f"{request_id}:revoke",
            actor_id="session-revoker",
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql="""
                    UPDATE user_sessions SET revoked_at = ?
                    WHERE session_digest = ? AND revoked_at IS NULL
                    """,
                    parameters=(revoked_at, session_digest),
                ),
            ),
        )

    def safe_session_audit_records(
        self,
        *,
        request_id: str,
        account_id: str,
    ) -> tuple[SafeSessionAuditRecord, ...]:
        """Return retained credential-free session/audit projections."""
        results = self._execute(
            request_id=self._read_request_id(request_id, "safe-audit"),
            actor_id="audit-reader",
            account_id=account_id,
            statements=(
                PersistenceStatement(
                    sql="""
                    SELECT authentication_audit_ref, user_id, account_id,
                           workspace_id, created_at, expires_at, revoked_at
                    FROM user_sessions WHERE account_id = ?
                    ORDER BY created_at, authentication_audit_ref
                    """,
                    parameters=(account_id,),
                ),
            ),
        )
        return tuple(SafeSessionAuditRecord(**row) for row in results[0])
