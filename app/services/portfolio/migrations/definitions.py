"""Portfolio-owned additive schema definitions executed by Data.

Conformed to the authoritative schema model in ``app/services/portfolio/README.md``. The
step has never been applied to a database, so the definition is edited in place
rather than extended by a follow-on migration; see ``FR-PORT-041`` through
``FR-PORT-043``.

The model adopts this domain's shape rather than the reverse. ``portfolio_definitions``
already keys on ``(portfolio_id, portfolio_version)``, so definition history is
immutable without a separate versions table, and ``portfolio_active_scopes`` carries
the current-version pointer. No Portfolio table declares a foreign key: version rows
are immutable and must survive independently, so references are soft and validated in
the owning feature modules.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from app.composition.logging import get_logger
from app.services.data import build_migration_step

logger = get_logger(__name__)

PORTFOLIO_SCHEMA_VERSION = "v3"

_PORTFOLIO_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS portfolio_definitions (
        portfolio_id TEXT NOT NULL,
        portfolio_version TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        definition_json TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (portfolio_id, portfolio_version)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_defs_scope "
        "ON portfolio_definitions(portfolio_id, scope_key)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_construction_results (
        result_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        portfolio_version TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        result_json TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_results_portfolio "
        "ON portfolio_construction_results(portfolio_id, created_at DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_allocation_versions (
        allocation_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        allocation_version TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        allocation_json TEXT NOT NULL,
        activated_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (portfolio_id, allocation_version)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS portfolio_active_scopes (
        portfolio_id TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        allocation_version TEXT NOT NULL,
        revision INTEGER NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
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
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        PRIMARY KEY (plan_id, plan_version)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_plans_portfolio "
        "ON portfolio_rebalance_plans(portfolio_id, created_at DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_idempotency (
        idempotency_key TEXT PRIMARY KEY,
        material_hash TEXT NOT NULL,
        result_type TEXT NOT NULL,
        result_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL
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
        occurred_at TEXT NOT NULL,
        publication_state TEXT NOT NULL DEFAULT 'pending',
        attempts INTEGER NOT NULL DEFAULT 0,
        published_at TEXT,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_outbox_pending "
        "ON portfolio_audit_outbox(occurred_at) "
        "WHERE publication_state = 'pending'"
    ),
)


_PORTFOLIO_LEDGER_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS portfolio_ledger_accounts (
        account_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        currency TEXT NOT NULL,
        normal_balance TEXT NOT NULL,
        category TEXT NOT NULL,
        account_json TEXT NOT NULL,
        registered_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (portfolio_id, account_id)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_ledger_accounts_portfolio "
        "ON portfolio_ledger_accounts(portfolio_id)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_ledger_posting_batches (
        batch_id TEXT PRIMARY KEY,
        source_event_id TEXT NOT NULL,
        source_sequence INTEGER NOT NULL,
        entry_sequence INTEGER NOT NULL,
        reversal_of TEXT,
        posted_at TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        batch_json TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (source_event_id, source_sequence)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_ledger_batches_event "
        "ON portfolio_ledger_posting_batches(source_event_id, source_sequence)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_ledger_entries (
        entry_id TEXT NOT NULL,
        batch_id TEXT NOT NULL,
        entry_sequence INTEGER NOT NULL,
        account_id TEXT NOT NULL,
        side TEXT NOT NULL CHECK (side IN ('debit', 'credit')),
        amount_decimal TEXT NOT NULL,
        currency TEXT NOT NULL,
        posting_type TEXT NOT NULL,
        posted_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (entry_id, batch_id)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_ledger_entries_account "
        "ON portfolio_ledger_entries(account_id, currency)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_ledger_balances (
        balance_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        currency TEXT NOT NULL,
        settled_decimal TEXT NOT NULL,
        unsettled_decimal TEXT NOT NULL,
        accrued_income_decimal TEXT NOT NULL,
        accrued_cost_decimal TEXT NOT NULL,
        as_of TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (account_id, currency, as_of)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_portfolio_ledger_balances_account "
        "ON portfolio_ledger_balances(account_id, as_of DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS portfolio_ledger_snapshots (
        snapshot_id TEXT PRIMARY KEY,
        entry_range_start INTEGER NOT NULL,
        entry_range_end INTEGER NOT NULL,
        balances_json TEXT NOT NULL,
        material_hash TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
)

_PORTFOLIO_OPERATIONS_SCHEMA_STATEMENTS = tuple(
    f"""CREATE TABLE IF NOT EXISTS {table} (
        record_id TEXT PRIMARY KEY,
        portfolio_id TEXT NOT NULL,
        version TEXT NOT NULL,
        record_json TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""".strip()
    for table in (
        "portfolio_valuation_policies",
        "position_lots",
        "valuation_snapshots",
        "margin_risk_snapshots",
        "reconciliation_incidents",
        "lifecycle_events",
    )
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


PORTFOLIO_MIGRATIONS: tuple[Any, ...] = (
    build_migration_step(
        domain="portfolio",
        migration_id="001_initial_portfolio_schema",
        checksum=_migration_checksum(_PORTFOLIO_SCHEMA_STATEMENTS),
        statements=_PORTFOLIO_SCHEMA_STATEMENTS,
    ),
    build_migration_step(
        domain="portfolio",
        migration_id="002_portfolio_ledger_schema",
        checksum=_migration_checksum(_PORTFOLIO_LEDGER_SCHEMA_STATEMENTS),
        statements=_PORTFOLIO_LEDGER_SCHEMA_STATEMENTS,
    ),
    build_migration_step(
        domain="portfolio",
        migration_id="003_portfolio_operations_schema",
        checksum=_migration_checksum(_PORTFOLIO_OPERATIONS_SCHEMA_STATEMENTS),
        statements=_PORTFOLIO_OPERATIONS_SCHEMA_STATEMENTS,
    ),
)


def get_portfolio_migrations() -> tuple[object, ...]:
    """Return immutable Portfolio-owned migration steps.

    Returns:
        Portfolio migration steps in application order.
    """
    return PORTFOLIO_MIGRATIONS


__all__: tuple[str, ...] = (
    "PORTFOLIO_MIGRATIONS",
    "PORTFOLIO_SCHEMA_VERSION",
    "get_portfolio_migrations",
)
