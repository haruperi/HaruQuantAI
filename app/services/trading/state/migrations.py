"""Additive Trading-owned schema definitions executed by Data."""

from hashlib import sha256

from app.services.data.persistence.contracts import (
    MigrationStep,
)
from app.utils import logger

TRADING_SCHEMA_VERSION = "v1"

_TRADING_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS trading_events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        event_version TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        aggregate_version INTEGER NOT NULL,
        occurred_at TEXT NOT NULL,
        payload_json TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS trading_idempotency (
        idempotency_key TEXT PRIMARY KEY,
        material_hash TEXT NOT NULL,
        material_version TEXT NOT NULL,
        status TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        receipt_id TEXT
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS trading_projections (
        scope_key TEXT PRIMARY KEY,
        projection_version INTEGER NOT NULL,
        projection_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
)


def _migration_checksum(statements: tuple[str, ...]) -> str:
    """Return a stable checksum for ordered Trading schema statements.

    Args:
        statements: Ordered additive SQL definitions.

    Returns:
        Lowercase SHA-256 checksum.
    """
    logger.debug("Calculating Trading migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return sha256(material).hexdigest()


def get_trading_migrations() -> tuple[MigrationStep, ...]:
    """Return additive Trading migration definitions without opening storage.

    Returns:
        Ordered immutable Data-owned migration contracts.
    """
    logger.debug("Returning Trading-owned migration definitions")
    return (
        MigrationStep(
            domain="trading",
            migration_id="001_initial_trading_schema",
            checksum=_migration_checksum(_TRADING_SCHEMA_STATEMENTS),
            statements=_TRADING_SCHEMA_STATEMENTS,
        ),
    )


__all__ = ["TRADING_SCHEMA_VERSION", "get_trading_migrations"]
