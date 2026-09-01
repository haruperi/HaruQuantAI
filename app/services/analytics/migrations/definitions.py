"""Analytics-owned schema definitions executed by Data.

Analytics owns **derived, recomputable state only**. Every table records the
`source_hash` of the inputs it was computed from, so a stale value is detectable
rather than merely wrong, and nothing here is authoritative business state — the
authority is always Trading, Simulator, or Portfolio.

Equity-curve *points* are not stored: `analytics_equity_curves` holds the curve's
identity and summary statistics and references the artifact holding the series.
See ``FR-ANLT-055`` through ``FR-ANLT-060``.
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

ANALYTICS_SCHEMA_VERSION = "v3"

_ANALYTICS_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS analytics_metric_definitions (
        metric_id TEXT PRIMARY KEY,
        metric_code TEXT NOT NULL,
        version TEXT NOT NULL,
        category TEXT NOT NULL,
        formula_hash TEXT NOT NULL,
        min_sample_size INTEGER NOT NULL DEFAULT 1,
        requires_benchmark INTEGER NOT NULL DEFAULT 0
            CHECK (requires_benchmark IN (0, 1)),
        higher_is_better INTEGER NOT NULL DEFAULT 1
            CHECK (higher_is_better IN (0, 1)),
        unit TEXT NOT NULL,
        definition_json TEXT NOT NULL,
        state TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (metric_code, version)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS analytics_metric_values (
        value_id TEXT PRIMARY KEY,
        metric_id TEXT NOT NULL,
        scope_level TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        period_kind TEXT NOT NULL,
        period_start_utc INTEGER NOT NULL,
        period_end_utc INTEGER NOT NULL,
        value_decimal TEXT,
        sample_size INTEGER NOT NULL,
        confidence_low_decimal TEXT,
        confidence_high_decimal TEXT,
        is_significant INTEGER CHECK (is_significant IN (0, 1)),
        insufficient_sample INTEGER NOT NULL DEFAULT 0
            CHECK (insufficient_sample IN (0, 1)),
        source_hash TEXT NOT NULL,
        computed_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (
            metric_id, scope_level, scope_key, period_kind,
            period_start_utc, period_end_utc
        ),
        CHECK (insufficient_sample = 1 OR value_decimal IS NOT NULL)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_values_scope "
        "ON analytics_metric_values(scope_level, scope_key, computed_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_values_metric "
        "ON analytics_metric_values(metric_id, period_end_utc DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS analytics_trade_analysis (
        trade_id TEXT PRIMARY KEY,
        source_kind TEXT NOT NULL,
        run_id TEXT,
        position_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        symbol_id TEXT NOT NULL,
        strategy_version_id TEXT,
        direction TEXT NOT NULL,
        entry_price_decimal TEXT NOT NULL,
        exit_price_decimal TEXT NOT NULL,
        quantity_decimal TEXT NOT NULL,
        gross_pnl_decimal TEXT NOT NULL,
        net_pnl_decimal TEXT NOT NULL,
        commission_decimal TEXT NOT NULL DEFAULT '0',
        swap_decimal TEXT NOT NULL DEFAULT '0',
        slippage_decimal TEXT NOT NULL DEFAULT '0',
        r_multiple_decimal TEXT,
        mae_decimal TEXT,
        mfe_decimal TEXT,
        holding_seconds INTEGER NOT NULL,
        bars_held INTEGER,
        exit_reason TEXT NOT NULL,
        regime_id TEXT,
        entry_at TEXT NOT NULL,
        exit_at TEXT NOT NULL,
        source_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_trades_strategy "
        "ON analytics_trade_analysis(strategy_version_id, exit_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_trades_symbol "
        "ON analytics_trade_analysis(symbol_id, exit_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_trades_run "
        "ON analytics_trade_analysis(run_id) WHERE run_id IS NOT NULL"
    ),
    """
    CREATE TABLE IF NOT EXISTS analytics_pnl_attribution (
        attribution_id TEXT PRIMARY KEY,
        scope_level TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        period_start_utc INTEGER NOT NULL,
        period_end_utc INTEGER NOT NULL,
        factor TEXT NOT NULL,
        contribution_decimal TEXT NOT NULL,
        contribution_percent_decimal TEXT NOT NULL,
        trade_count INTEGER NOT NULL DEFAULT 0,
        source_hash TEXT NOT NULL,
        computed_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE (
            scope_level, scope_key, period_start_utc, period_end_utc, factor
        )
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_attrib_scope "
        "ON analytics_pnl_attribution(scope_level, scope_key, period_end_utc DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS analytics_equity_curves (
        curve_id TEXT PRIMARY KEY,
        scope_level TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        dataset_id TEXT,
        period_start_utc INTEGER NOT NULL,
        period_end_utc INTEGER NOT NULL,
        point_count INTEGER NOT NULL DEFAULT 0,
        start_equity_decimal TEXT NOT NULL,
        end_equity_decimal TEXT NOT NULL,
        peak_equity_decimal TEXT NOT NULL,
        trough_equity_decimal TEXT NOT NULL,
        max_drawdown_decimal TEXT NOT NULL DEFAULT '0',
        max_drawdown_percent_decimal TEXT NOT NULL DEFAULT '0',
        max_drawdown_start_utc INTEGER,
        max_drawdown_end_utc INTEGER,
        recovery_ts_utc INTEGER,
        source_hash TEXT NOT NULL,
        state TEXT NOT NULL,
        computed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (scope_level, scope_key, period_start_utc, period_end_utc),
        CHECK (period_end_utc >= period_start_utc)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_equity_scope "
        "ON analytics_equity_curves(scope_level, scope_key, period_end_utc DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_equity_dd "
        "ON analytics_equity_curves(scope_level, max_drawdown_percent_decimal)"
    ),
    """
    CREATE TABLE IF NOT EXISTS analytics_reports (
        report_id TEXT PRIMARY KEY,
        report_kind TEXT NOT NULL,
        scope_level TEXT NOT NULL,
        scope_key TEXT NOT NULL,
        period_start_utc INTEGER NOT NULL,
        period_end_utc INTEGER NOT NULL,
        content_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        artifact_path TEXT,
        state TEXT NOT NULL,
        generated_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_analytics_reports_scope "
        "ON analytics_reports(scope_level, scope_key, generated_at DESC)"
    ),
)

_ANALYTICS_SCHEMA_V2_RETIREMENT_STATEMENTS = (
    """
    CREATE TEMP TABLE analytics_decommission_guard (
        row_count INTEGER NOT NULL CHECK (row_count = 0)
    ) STRICT
    """.strip(),
    """
    INSERT INTO analytics_decommission_guard (row_count)
    SELECT
        (SELECT COUNT(*) FROM analytics_metric_definitions)
        + (SELECT COUNT(*) FROM analytics_metric_values)
        + (SELECT COUNT(*) FROM analytics_trade_analysis)
        + (SELECT COUNT(*) FROM analytics_pnl_attribution)
        + (SELECT COUNT(*) FROM analytics_equity_curves)
        + (SELECT COUNT(*) FROM analytics_reports)
    """.strip(),
    "DROP TABLE analytics_metric_values",
    "DROP TABLE analytics_trade_analysis",
    "DROP TABLE analytics_pnl_attribution",
    "DROP TABLE analytics_equity_curves",
    "DROP TABLE analytics_reports",
    "DROP TABLE analytics_metric_definitions",
    "DROP TABLE analytics_decommission_guard",
)

_ANALYTICS_PLAYER_EVIDENCE_STATEMENTS = tuple(
    f"""CREATE TABLE IF NOT EXISTS {table} (
        record_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        version TEXT NOT NULL,
        evidence_json TEXT NOT NULL,
        canonical_hash TEXT NOT NULL,
        occurred_at TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT""".strip()
    for table in (
        "analytics_journal_entries",
        "analytics_adherence_findings",
        "analytics_behavior_findings",
        "analytics_emergency_response_findings",
        "analytics_qualification_records",
    )
)


def _migration_checksum(statements: tuple[str, ...]) -> str:
    """Return a stable checksum for ordered Analytics schema statements.

    Args:
        statements: Ordered additive SQL definitions.

    Returns:
        Lowercase SHA-256 checksum.
    """
    logger.debug("Calculating Analytics migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


ANALYTICS_MIGRATIONS: tuple[Any, ...] = (
    build_migration_step(
        domain="analytics",
        migration_id="001_analytics_schema_v1",
        checksum=_migration_checksum(_ANALYTICS_SCHEMA_STATEMENTS),
        statements=_ANALYTICS_SCHEMA_STATEMENTS,
    ),
    build_migration_step(
        domain="analytics",
        migration_id="002_retire_unused_analytics_derived_store",
        checksum=_migration_checksum(_ANALYTICS_SCHEMA_V2_RETIREMENT_STATEMENTS),
        statements=_ANALYTICS_SCHEMA_V2_RETIREMENT_STATEMENTS,
    ),
    build_migration_step(
        domain="analytics",
        migration_id="003_player_evidence_schema",
        checksum=_migration_checksum(_ANALYTICS_PLAYER_EVIDENCE_STATEMENTS),
        statements=_ANALYTICS_PLAYER_EVIDENCE_STATEMENTS,
    ),
)


def get_analytics_migrations() -> tuple[object, ...]:
    """Return immutable Analytics-owned migration steps.

    Returns:
        Analytics migration steps in application order.
    """
    return ANALYTICS_MIGRATIONS


def run_analytics_migrations(request_id: str) -> object:
    """Apply the complete immutable Analytics migration manifest through Data.

    Args:
        request_id: Canonical startup request identifier.

    Returns:
        Data-owned standard migration response.
    """
    logger.info("Running Analytics-owned schema migrations")
    request = build_migration_request(
        domain="analytics",
        steps=get_analytics_migrations(),
        request_id=request_id,
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = [
    "ANALYTICS_MIGRATIONS",
    "ANALYTICS_SCHEMA_VERSION",
    "get_analytics_migrations",
    "run_analytics_migrations",
]
