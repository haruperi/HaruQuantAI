"""Brokers-owned schema definitions executed by Data.

**Brokers persists almost nothing, and that is deliberate.** ``docs/PROJECT.md``
§5 records the domain as a stateless passthrough: connection and circuit-breaker
state is in-memory, balances are fetched live, and credentials are never
persisted. Decision D10 upheld that.

One table is the exception. Provider-to-canonical symbol translation is
reference data: it must be stable, versioned, and identical across restarts,
because a mis-mapped symbol routes an order to the wrong instrument. Private
support; see ``migrations/README.md`` and ``docs/schema`` decision D10.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.data import build_migration_step
from app.utils import get_logger

logger = get_logger(__name__)

BROKER_SCHEMA_VERSION = "v1"

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
)


def get_broker_migrations() -> tuple[object, ...]:
    """Return immutable Brokers-owned migration steps.

    Returns:
        Broker migration steps in application order.
    """
    return BROKER_MIGRATIONS


__all__ = [
    "BROKER_MIGRATIONS",
    "BROKER_SCHEMA_VERSION",
    "get_broker_migrations",
]
