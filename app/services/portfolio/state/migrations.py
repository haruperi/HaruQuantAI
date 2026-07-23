"""Portfolio-owned additive schema definitions executed by Data."""

from __future__ import annotations

from hashlib import sha256

from app.services.data.persistence.contracts import (
    MigrationStep,
)
from app.utils import logger

_PORTFOLIO_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS portfolio_definitions (
        portfolio_id TEXT NOT NULL,
        portfolio_version TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        definition_json TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        PRIMARY KEY (portfolio_id, portfolio_version)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_construction_results (
        result_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        portfolio_version TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_allocation_versions (
        allocation_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        allocation_version TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        allocation_json TEXT NOT NULL,
        activated_at TEXT NOT NULL,
        UNIQUE (portfolio_id, allocation_version)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_active_scopes (
        portfolio_id TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        allocation_version TEXT NOT NULL,
        revision INTEGER NOT NULL,
        PRIMARY KEY (portfolio_id, scope_key)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_rebalance_plans (
        plan_id TEXT NOT NULL,
        plan_version TEXT NOT NULL,
        portfolio_id TEXT NOT NULL,
        allocation_version TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        plan_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (plan_id, plan_version)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_idempotency (
        idempotency_key TEXT PRIMARY KEY,
        material_hash TEXT NOT NULL,
        result_type TEXT NOT NULL,
        result_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_audit_outbox (
        event_id TEXT PRIMARY KEY,
        event_type TEXT NOT NULL,
        aggregate_id TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        occurred_at TEXT NOT NULL
    ) STRICT
    """.strip(),
)


def _migration_checksum(statements: tuple[str, ...]) -> str:
    """Return a stable checksum for ordered Portfolio schema statements.

    Args:
        statements: Ordered additive SQL definitions.

    Returns:
        Lowercase SHA-256 checksum.
    """
    logger.debug("Calculating Portfolio migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return sha256(material).hexdigest()


PORTFOLIO_MIGRATIONS: tuple[MigrationStep, ...] = (
    MigrationStep(
        domain="portfolio",
        migration_id="001_initial_portfolio_schema",
        checksum=_migration_checksum(_PORTFOLIO_SCHEMA_STATEMENTS),
        statements=_PORTFOLIO_SCHEMA_STATEMENTS,
    ),
)

__all__: tuple[str, ...] = ("PORTFOLIO_MIGRATIONS",)
