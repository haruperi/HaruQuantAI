"""Transactional SQLite persistence feature for the Gateway domain.

Feature:
    FEAT-PERSISTENCE-GATEWAY

Purpose:
    Provides durable storage, parameterized SQL execution, and transactional
    invariants for gateway settings (e.g. remote access status), hashed API tokens,
    and request idempotency responses under namespace `gateway.v1`.

Key capabilities:
    * Durable key-value settings management.
    * Secret-safe hashed API token verification (SHA-256).
    * Idempotency response caching with time-to-live expiration.

Python API usage:
    persistence = ctx.require(GATEWAY_PERSISTENCE)
    is_valid = persistence.verify_token(token)

CLI usage:
    uv run python -m tests.examples.05_gateway
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, override

from app.contracts.gateway import (
    GATEWAY_PERSISTENCE,
)
from app.contracts.gateway import (
    GatewayPersistenceService as IGatewayPersistenceService,
)
from app.contracts.persistence import (
    DATABASE_SERVICE,
    DatabaseService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Schema Definitions
# ---------------------------------------------------------------------------

_SCHEMA_SCRIPT = """
CREATE TABLE IF NOT EXISTS gateway_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gateway_tokens (
    token_hash TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS gateway_idempotency (
    idempotency_key TEXT PRIMARY KEY,
    status_code INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_gateway_idempotency_expires
ON gateway_idempotency (expires_at);
"""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GatewayPersistenceConfig:
    """Runtime configuration for gateway persistence."""

    schema_version: int = 1
    default_idempotency_ttl_s: int = 86400

    def __post_init__(self) -> None:
        """Validate configuration limits."""
        if self.schema_version < 1:
            msg = f"schema_version must be >= 1; got {self.schema_version}"
            raise ValueError(msg)
        if self.default_idempotency_ttl_s <= 0:
            msg = (
                f"default_idempotency_ttl_s must be > 0; "
                f"got {self.default_idempotency_ttl_s}"
            )
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# Service Implementation
# ---------------------------------------------------------------------------


class GatewayPersistenceService(IGatewayPersistenceService):
    """Implement durable SQLite storage for the Gateway domain."""

    def __init__(
        self,
        db: DatabaseService,
        config: GatewayPersistenceConfig | None = None,
    ) -> None:
        """Initialize the gateway persistence service.

        Args:
            db: Low-level database capability.
            config: Optional runtime persistence configuration.
        """
        self._db = db
        self._config = config or GatewayPersistenceConfig()

    def initialize_schema(self) -> None:
        """Create database tables and indexes under namespace gateway.v1."""
        self._db.execute_script(_SCHEMA_SCRIPT)
        logger.info("gateway_schema_initialized")

    @override
    def get_setting(self, key: str) -> str | None:
        """Retrieve a stored setting value.

        Args:
            key: Setting key name.

        Returns:
            Stored value string, or None if not found.
        """
        query = "SELECT value FROM gateway_settings WHERE key = ?"
        rows = self._db.execute_query(query, (key,))
        if rows:
            return str(rows[0]["value"])
        return None

    @override
    def set_setting(self, key: str, value: str) -> None:
        """Persist a setting key-value pair.

        Args:
            key: Setting key name.
            value: Setting value.
        """
        now = datetime.now(UTC).isoformat()
        sql = """
            INSERT INTO gateway_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
        """
        self._db.execute_mutation(sql, (key, value, now))
        logger.info("gateway_setting_updated", key=key)

    @override
    def store_token(self, token: str, name: str) -> None:
        """Store a hashed API token.

        Args:
            token: Plaintext token to hash and store.
            name: Human-readable token name or description.
        """
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = datetime.now(UTC).isoformat()
        sql = """
            INSERT INTO gateway_tokens (token_hash, name, created_at, is_active)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(token_hash) DO UPDATE SET
                name = excluded.name,
                is_active = 1
        """
        self._db.execute_mutation(sql, (token_hash, name, now))
        logger.info("gateway_token_stored", name=name)

    @override
    def verify_token(self, token: str) -> bool:
        """Verify if a token hash exists and is active.

        Args:
            token: Plaintext token to verify.

        Returns:
            True if token is valid and active, False otherwise.
        """
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        query = """
            SELECT 1 FROM gateway_tokens
            WHERE token_hash = ? AND is_active = 1
        """
        rows = self._db.execute_query(query, (token_hash,))
        return len(rows) > 0

    @override
    def record_idempotency_key(
        self,
        key: str,
        status_code: int,
        response_body: str,
        expire_seconds: int = 86400,
    ) -> bool:
        """Record an idempotency key and its response.

        Args:
            key: Idempotency key.
            status_code: HTTP status code.
            response_body: Serialized response body.
            expire_seconds: Time-to-live in seconds.

        Returns:
            True if newly inserted, False if key already exists.
        """
        now_dt = datetime.now(UTC)
        expires_dt = now_dt + timedelta(seconds=expire_seconds)
        now = now_dt.isoformat()
        expires = expires_dt.isoformat()

        sql = """
            INSERT OR IGNORE INTO gateway_idempotency
            (idempotency_key, status_code, response_body, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """
        affected = self._db.execute_mutation(
            sql, (key, status_code, response_body, now, expires)
        )
        return affected > 0

    @override
    def get_idempotency_response(self, key: str) -> tuple[int, str] | None:
        """Retrieve a cached idempotency response if still valid.

        Args:
            key: Idempotency key.

        Returns:
            Tuple of (status_code, response_body) or None if absent/expired.
        """
        now = datetime.now(UTC).isoformat()
        query = """
            SELECT status_code, response_body
            FROM gateway_idempotency
            WHERE idempotency_key = ? AND expires_at > ?
        """
        rows = self._db.execute_query(query, (key, now))
        if rows:
            return int(rows[0]["status_code"]), str(rows[0]["response_body"])
        return None

    @override
    def purge_expired_idempotency(self, retention_seconds: int = 0) -> int:
        """Purge expired idempotency keys older than retention threshold.

        Args:
            retention_seconds: Extra grace period beyond expiration in seconds
                (default 0).

        Returns:
            Count of deleted rows.
        """
        cutoff_dt = datetime.now(UTC) - timedelta(seconds=retention_seconds)
        cutoff = cutoff_dt.isoformat()
        sql = "DELETE FROM gateway_idempotency WHERE expires_at < ?"
        deleted = self._db.execute_mutation(sql, (cutoff,))
        if deleted > 0:
            logger.info("gateway_idempotency_purged", count=deleted)
        return deleted


# ---------------------------------------------------------------------------
# Feature Specification and Wiring
# ---------------------------------------------------------------------------

SPEC = FeatureSpec(
    name="persistence.gateway",
    provides=frozenset({GATEWAY_PERSISTENCE}),
    requires=frozenset({DATABASE_SERVICE}),
    optional=frozenset(),
    description="Transactional SQLite persistence for the Gateway domain.",
)


class GatewayPersistenceFeature:
    """Composition feature wiring for gateway persistence."""

    def __init__(self, config: GatewayPersistenceConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional persistence configuration.
        """
        self._config = config or GatewayPersistenceConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return the immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Start the persistence service and initialize schema.

        Args:
            context: Feature composition context.
        """
        db = context.require(DATABASE_SERVICE)
        service = GatewayPersistenceService(db, self._config)
        service.initialize_schema()
        context.provide(GATEWAY_PERSISTENCE, service)

    async def stop(self) -> None:
        """Stop feature and clean up resources."""


def feature() -> GatewayPersistenceFeature:
    """Factory creating the default GatewayPersistenceFeature.

    Returns:
        Configured feature instance.
    """
    return GatewayPersistenceFeature()
