"""Brokers-owned schema definitions executed by Data.

**Brokers persists almost nothing, and that is deliberate.** ``docs/PROJECT.md``
§5 records the domain as a stateless passthrough: connection and circuit-breaker
state is in-memory, balances are fetched live, and credentials are never
persisted. Decision D10 upheld that.

One table is the exception. Provider-to-canonical symbol translation is
reference data: it must be stable, versioned, and identical across restarts,
because a mis-mapped symbol routes an order to the wrong instrument. Private
support; see ``migrations/README.md`` and the Brokers README database specification.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.composition.logging import get_logger
from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)

logger = get_logger(__name__)

BROKER_SCHEMA_VERSION = "v4"

_BROKER_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS broker_symbol_map (
        map_id TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL,
        symbol_id TEXT NOT NULL,
        provider_symbol TEXT NOT NULL,
        contract_size_decimal TEXT NOT NULL DEFAULT '1',
        digits_override INTEGER,
        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (provider_code, provider_symbol, effective_from),
        UNIQUE (provider_code, symbol_id, effective_from)
    ) STRICT
    """.strip(),
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_symbol_active "
        "ON broker_symbol_map(provider_code, symbol_id) "
        "WHERE enabled = 1 AND effective_to IS NULL"
    ),
    (
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_symbol_reverse "
        "ON broker_symbol_map(provider_code, provider_symbol) "
        "WHERE enabled = 1 AND effective_to IS NULL"
    ),
)

_BROKER_CHANNEL_STATE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS broker_health_history (
        checkpoint_id TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL,
        account_ref_digest TEXT NOT NULL,
        environment TEXT NOT NULL,
        health_status TEXT NOT NULL,
        latency_ms_decimal TEXT,
        error_rate_decimal TEXT,
        maintenance INTEGER NOT NULL CHECK (maintenance IN (0, 1)),
        route_ready INTEGER NOT NULL CHECK (route_ready IN (0, 1)),
        observed_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS broker_route_recovery (
        route_ref TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL,
        account_ref_digest TEXT NOT NULL,
        environment TEXT NOT NULL,
        recovery_cursor TEXT NOT NULL,
        uncertainty TEXT NOT NULL,
        request_id TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS broker_environment_permissions (
        permission_id TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL,
        account_ref_digest TEXT NOT NULL,
        environment TEXT NOT NULL,
        allow_read INTEGER NOT NULL CHECK (allow_read IN (0, 1)),
        allow_mutation INTEGER NOT NULL CHECK (allow_mutation IN (0, 1)),
        enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        request_id TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (provider_code, account_ref_digest, environment, effective_from)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS broker_event_checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL,
        account_ref_digest TEXT NOT NULL,
        source_stream TEXT NOT NULL,
        source_cursor TEXT NOT NULL,
        source_sequence INTEGER,
        event_digest TEXT NOT NULL,
        request_id TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (provider_code, account_ref_digest, source_stream)
    ) STRICT
    """.strip(),
)

_BROKER_SYMBOL_MAP_RETIREMENT_STATEMENTS = (
    """
    CREATE TEMP TABLE broker_symbol_map_retirement_guard (
        row_count INTEGER NOT NULL CHECK (row_count = 0)
    ) STRICT
    """.strip(),
    """
    INSERT INTO broker_symbol_map_retirement_guard (row_count)
    SELECT COUNT(*) FROM broker_symbol_map
    """.strip(),
    "DROP TABLE broker_symbol_map",
    "DROP TABLE broker_symbol_map_retirement_guard",
)

_BROKER_ENVIRONMENT_PERMISSIONS_RETIREMENT_STATEMENTS = (
    """
    CREATE TEMP TABLE broker_environment_permissions_retirement_guard (
        row_count INTEGER NOT NULL CHECK (row_count = 0)
    ) STRICT
    """.strip(),
    """
    INSERT INTO broker_environment_permissions_retirement_guard (row_count)
    SELECT COUNT(*) FROM broker_environment_permissions
    """.strip(),
    "DROP TABLE broker_environment_permissions",
    "DROP TABLE broker_environment_permissions_retirement_guard",
)


def _migration_checksum(statements: tuple[str, ...]) -> str:
    """Return a stable checksum for ordered Brokers schema statements.

    Args:
        statements: Ordered additive SQL definitions.

    Returns:
        Lowercase SHA-256 checksum.
    """
    logger.debug("Calculating Brokers migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


BROKER_MIGRATIONS: tuple[Any, ...] = (
    build_migration_step(
        domain="brokers",
        migration_id="001_broker_symbol_map_v1",
        checksum=_migration_checksum(_BROKER_SCHEMA_STATEMENTS),
        statements=_BROKER_SCHEMA_STATEMENTS,
    ),
    build_migration_step(
        domain="brokers",
        migration_id="002_broker_channel_state_v1",
        checksum=_migration_checksum(_BROKER_CHANNEL_STATE_STATEMENTS),
        statements=_BROKER_CHANNEL_STATE_STATEMENTS,
    ),
    build_migration_step(
        domain="brokers",
        migration_id="003_retire_broker_symbol_map",
        checksum=_migration_checksum(_BROKER_SYMBOL_MAP_RETIREMENT_STATEMENTS),
        statements=_BROKER_SYMBOL_MAP_RETIREMENT_STATEMENTS,
    ),
    build_migration_step(
        domain="brokers",
        migration_id="004_retire_broker_environment_permissions",
        checksum=_migration_checksum(
            _BROKER_ENVIRONMENT_PERMISSIONS_RETIREMENT_STATEMENTS
        ),
        statements=_BROKER_ENVIRONMENT_PERMISSIONS_RETIREMENT_STATEMENTS,
    ),
)


def get_broker_migrations() -> tuple[object, ...]:
    """Return immutable Brokers-owned migration steps.

    Returns:
        Broker migration steps in application order.
    """
    return BROKER_MIGRATIONS


def run_broker_migrations(request_id: str) -> object:
    """Apply the immutable Brokers migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    logger.info("Running Brokers-owned schema migrations")
    request = build_migration_request(
        domain="brokers",
        steps=get_broker_migrations(),
        request_id=request_id,
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = [
    "BROKER_MIGRATIONS",
    "BROKER_SCHEMA_VERSION",
    "get_broker_migrations",
    "run_broker_migrations",
]
