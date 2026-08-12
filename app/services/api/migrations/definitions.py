"""Authoritative UI/API-owned persistence migration manifest.

Relocated from ``app/services/api/identity/`` to the canonical per-domain
migration location recorded in ``docs/ARCHITECTURE.md``; see ``FR-API-073``.
The additive normalized authority schema is ``FR-API-074``.

``api-0001`` through ``api-0003`` are **applied steps**. Their statement tuples
and checksums are moved byte-for-byte: a checksum covers the ordered statements,
so any reformatting here would change the digest and the ledger would block
database access.
"""

from __future__ import annotations

import hashlib

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)

_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS api_accounts (
        user_id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        roles_json TEXT NOT NULL,
        permissions_json TEXT NOT NULL,
        scopes_json TEXT NOT NULL,
        environment TEXT NOT NULL,
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
        created_at TEXT NOT NULL,
        last_login_at TEXT
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_sessions (
        session_digest TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        csrf_digest TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        revoked_at TEXT,
        FOREIGN KEY (user_id) REFERENCES api_accounts(user_id)
    ) STRICT
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_sessions_user ON api_sessions(user_id)",
    """
    CREATE TABLE IF NOT EXISTS api_credentials (
        reference TEXT PRIMARY KEY,
        owner_id TEXT NOT NULL,
        key_id TEXT NOT NULL,
        nonce_b64 TEXT NOT NULL,
        ciphertext_b64 TEXT NOT NULL,
        created_at TEXT NOT NULL,
        version INTEGER NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_idempotency (
        scope_key TEXT PRIMARY KEY,
        request_hash TEXT NOT NULL,
        response_json TEXT,
        status_code INTEGER,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_approvals (
        approval_id TEXT PRIMARY KEY,
        issuer_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        scope TEXT NOT NULL,
        evidence_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        consumed_at TEXT
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_user_settings (
        user_id TEXT PRIMARY KEY,
        settings_json TEXT NOT NULL,
        version INTEGER NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
)

_CHECKSUM = hashlib.sha256(
    canonical_json(
        {"domain": "api", "migration": "api-0001", "sql": _STATEMENTS}
    ).encode("utf-8")
).hexdigest()

_AUTH_FAILURE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS api_auth_failures (
        username_hash TEXT PRIMARY KEY,
        failure_count INTEGER NOT NULL,
        window_started_at TEXT NOT NULL,
        locked_until TEXT
    ) STRICT
    """.strip(),
)
_AUTH_FAILURE_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0002",
            "sql": _AUTH_FAILURE_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()

_AUTHORITY_SPLIT_STATEMENTS = (
    "ALTER TABLE api_accounts ADD COLUMN runtime_profile TEXT NOT NULL "
    "DEFAULT 'research' CHECK (runtime_profile IN "
    "('research', 'simulation', 'paper', 'live'))",
    "UPDATE api_accounts SET environment = 'development' WHERE environment = 'dev'",
)
_AUTHORITY_SPLIT_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0003",
            "sql": _AUTHORITY_SPLIT_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()

_RBAC_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS api_roles (
        role_id TEXT PRIMARY KEY,
        role_name TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL DEFAULT '',
        is_system INTEGER NOT NULL CHECK (is_system IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_permissions (
        permission_id TEXT PRIMARY KEY,
        permission_key TEXT NOT NULL UNIQUE,
        domain TEXT NOT NULL,
        action TEXT NOT NULL CHECK (
            action IN ('read', 'write', 'execute', 'approve', 'admin')
        ),
        is_mutating INTEGER NOT NULL CHECK (is_mutating IN (0, 1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (permission_key NOT LIKE '%*%')
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_role_permissions (
        role_id TEXT NOT NULL,
        permission_id TEXT NOT NULL,
        granted_at TEXT NOT NULL,
        granted_by TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (role_id, permission_id),
        FOREIGN KEY (role_id) REFERENCES api_roles(role_id) ON DELETE RESTRICT,
        FOREIGN KEY (permission_id) REFERENCES api_permissions(permission_id)
            ON DELETE RESTRICT
    ) STRICT, WITHOUT ROWID
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS api_role_bindings (
        binding_id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        role_id TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        granted_by TEXT NOT NULL,
        expires_at TEXT,
        revoked_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (account_id, role_id, scope_key),
        FOREIGN KEY (account_id) REFERENCES api_accounts(user_id) ON DELETE RESTRICT,
        FOREIGN KEY (role_id) REFERENCES api_roles(role_id) ON DELETE RESTRICT
    ) STRICT
    """.strip(),
    """
    CREATE TEMP TABLE api_rbac_migration_guard (
        valid INTEGER NOT NULL CHECK (valid = 1)
    ) STRICT
    """.strip(),
    """
    INSERT INTO api_rbac_migration_guard (valid)
    SELECT CASE WHEN EXISTS (
        SELECT 1
        FROM (
            SELECT role.value AS role_name,
                   COUNT(DISTINCT account.permissions_json) AS authority_count
            FROM api_accounts AS account,
                 json_each(account.roles_json) AS role
            GROUP BY role.value
            HAVING authority_count > 1
        )
    ) THEN 0 ELSE 1 END
    """.strip(),
    """
    INSERT INTO api_roles (
        role_id, role_name, description, is_system, created_at, updated_at
    )
    SELECT DISTINCT 'role:' || role.value, role.value, '', 0,
                    account.created_at, account.created_at
    FROM api_accounts AS account, json_each(account.roles_json) AS role
    """.strip(),
    """
    INSERT INTO api_permissions (
        permission_id, permission_key, domain, action, is_mutating,
        created_at, updated_at
    )
    SELECT DISTINCT
        'permission:' || permission.value,
        permission.value,
        CASE
            WHEN instr(permission.value, ':') > 0
                THEN substr(permission.value, 1, instr(permission.value, ':') - 1)
            WHEN instr(permission.value, '.') > 0
                THEN substr(permission.value, 1, instr(permission.value, '.') - 1)
            ELSE permission.value
        END,
        CASE
            WHEN permission.value LIKE '%read' THEN 'read'
            WHEN permission.value LIKE '%write' THEN 'write'
            WHEN permission.value LIKE '%approve' THEN 'approve'
            WHEN permission.value LIKE '%admin' THEN 'admin'
            ELSE 'execute'
        END,
        CASE WHEN permission.value LIKE '%read' THEN 0 ELSE 1 END,
        account.created_at,
        account.created_at
    FROM api_accounts AS account,
         json_each(account.permissions_json) AS permission
    """.strip(),
    """
    INSERT INTO api_role_permissions (
        role_id, permission_id, granted_at, granted_by, created_at
    )
    SELECT DISTINCT 'role:' || role.value, 'permission:' || permission.value,
                    account.created_at, account.user_id, account.created_at
    FROM api_accounts AS account,
         json_each(account.roles_json) AS role,
         json_each(account.permissions_json) AS permission
    """.strip(),
    """
    INSERT INTO api_role_bindings (
        binding_id, account_id, role_id, scope_key, granted_by,
        expires_at, revoked_at, created_at, updated_at
    )
    SELECT DISTINCT
        'binding:' || account.user_id || ':' || role.value || ':' || scope.value,
        account.user_id,
        'role:' || role.value,
        scope.value,
        account.user_id,
        NULL,
        NULL,
        account.created_at,
        account.created_at
    FROM api_accounts AS account,
         json_each(account.roles_json) AS role,
         json_each(account.scopes_json) AS scope
    UNION ALL
    SELECT DISTINCT
        'binding:' || account.user_id || ':' || role.value || ':',
        account.user_id,
        'role:' || role.value,
        '',
        account.user_id,
        NULL,
        NULL,
        account.created_at,
        account.created_at
    FROM api_accounts AS account, json_each(account.roles_json) AS role
    WHERE json_array_length(account.scopes_json) = 0
    """.strip(),
    "DROP TABLE api_rbac_migration_guard",
    "CREATE INDEX IF NOT EXISTS idx_api_bindings_account "
    "ON api_role_bindings(account_id) WHERE revoked_at IS NULL",
    "CREATE INDEX IF NOT EXISTS idx_api_role_permissions_permission "
    "ON api_role_permissions(permission_id)",
)
_RBAC_CHECKSUM = hashlib.sha256(
    canonical_json(
        {"domain": "api", "migration": "api-0005", "sql": _RBAC_STATEMENTS}
    ).encode("utf-8")
).hexdigest()

_SETTINGS_UNIFICATION_STATEMENTS = (
    """
    CREATE TABLE api_settings (
        scope TEXT NOT NULL CHECK (scope IN ('system', 'user')),
        subject_id TEXT NOT NULL CHECK (subject_id <> ''),
        settings_json TEXT NOT NULL CHECK (
            json_valid(settings_json) AND json_type(settings_json) = 'object'
        ),
        version INTEGER NOT NULL CHECK (version >= 1),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        updated_by TEXT NOT NULL,
        request_id TEXT NOT NULL,
        PRIMARY KEY (scope, subject_id),
        CHECK (
            (scope = 'system' AND subject_id = 'global')
            OR (scope = 'user' AND subject_id <> 'global')
        )
    ) STRICT, WITHOUT ROWID
    """.strip(),
    """
    INSERT INTO api_settings (
        scope, subject_id, settings_json, version, created_at, updated_at,
        updated_by, request_id
    )
    SELECT 'user', user_id, settings_json, version, updated_at, updated_at,
           user_id, ''
    FROM api_user_settings
    """.strip(),
    """
    CREATE TEMP TABLE api_settings_migration_guard (
        valid INTEGER NOT NULL CHECK (valid = 1)
    ) STRICT
    """.strip(),
    """
    INSERT INTO api_settings_migration_guard (valid)
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM api_user_settings) =
             (SELECT COUNT(*) FROM api_settings WHERE scope = 'user')
        THEN 1 ELSE 0
    END
    """.strip(),
    "DROP TABLE api_settings_migration_guard",
    "DROP TABLE api_user_settings",
)
_SETTINGS_UNIFICATION_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0006",
            "sql": _SETTINGS_UNIFICATION_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()

_WATCHLISTS_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS api_watchlists (
        watchlist_id TEXT PRIMARY KEY,
        account_id TEXT NOT NULL,
        name TEXT NOT NULL CHECK (name <> ''),
        is_default INTEGER NOT NULL CHECK (is_default IN (0, 1)),
        sort_order INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (account_id, name),
        FOREIGN KEY (account_id) REFERENCES api_accounts(user_id)
            ON DELETE RESTRICT
    ) STRICT
    """.strip(),
    # At most one default watchlist per account; enforced at the DB layer so
    # the invariant holds even if application logic has a bug.
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_api_watchlists_one_default "
    "ON api_watchlists(account_id) WHERE is_default = 1",
    "CREATE INDEX IF NOT EXISTS idx_api_watchlists_account "
    "ON api_watchlists(account_id)",
    """
    CREATE TABLE IF NOT EXISTS api_watchlist_items (
        watchlist_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        symbol TEXT NOT NULL CHECK (symbol <> ''),
        sort_order INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (watchlist_id, source_id, symbol),
        FOREIGN KEY (watchlist_id) REFERENCES api_watchlists(watchlist_id)
            ON DELETE RESTRICT
    ) STRICT, WITHOUT ROWID
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_watchlist_items_watchlist "
    "ON api_watchlist_items(watchlist_id)",
)
_WATCHLISTS_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0007",
            "sql": _WATCHLISTS_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()


def get_api_migration_steps() -> tuple[object, ...]:
    """Return the immutable API migration manifest.

    Returns:
        Ordered API-owned migration definitions.
    """
    return (
        build_migration_step(
            domain="api",
            migration_id="api-0001",
            checksum=_CHECKSUM,
            statements=_STATEMENTS,
        ),
        build_migration_step(
            domain="api",
            migration_id="api-0002",
            checksum=_AUTH_FAILURE_CHECKSUM,
            statements=_AUTH_FAILURE_STATEMENTS,
        ),
        build_migration_step(
            domain="api",
            migration_id="api-0003",
            checksum=_AUTHORITY_SPLIT_CHECKSUM,
            statements=_AUTHORITY_SPLIT_STATEMENTS,
        ),
        build_migration_step(
            domain="api",
            migration_id="api-0005",
            checksum=_RBAC_CHECKSUM,
            statements=_RBAC_STATEMENTS,
        ),
        build_migration_step(
            domain="api",
            migration_id="api-0006",
            checksum=_SETTINGS_UNIFICATION_CHECKSUM,
            statements=_SETTINGS_UNIFICATION_STATEMENTS,
        ),
        build_migration_step(
            domain="api",
            migration_id="api-0007",
            checksum=_WATCHLISTS_CHECKSUM,
            statements=_WATCHLISTS_STATEMENTS,
        ),
    )


def run_api_migrations(request_id: str) -> object:
    """Apply the API migration manifest through Data's public executor.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    logger.info("Running UI/API-owned schema migrations")
    request = build_migration_request(
        domain="api",
        steps=get_api_migration_steps(),
        request_id=request_id,
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = ("get_api_migration_steps", "run_api_migrations")
