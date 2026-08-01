"""Authoritative UI/API-owned persistence migration manifest."""

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
    )
    return run_domain_migrations(request)


__all__ = ("get_api_migration_steps", "run_api_migrations")
