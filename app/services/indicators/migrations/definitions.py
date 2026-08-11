"""Indicators-owned schema definitions executed by Data.

Indicators declares its schema steps; Data owns migration execution, the
immutable ledger, checksums, and write locks. This module declares values only —
it opens no connection and executes nothing.

Step ``001_indicator_schema_v1`` created the legacy support tables. Step
``002_remove_unused_indicator_support_schema`` retired
``indicator_definitions``, ``indicator_param_sets``, and
``indicator_materializations`` with a fail-closed row guard. Indicators now
owns no live tables, and its former private ``persistence/`` package has been
removed. ``INDICATOR_SCHEMA_VERSION = "v1"`` identifies the domain schema
namespace and is not the applied migration count.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_domain_migrations,
)
from app.utils import get_logger

logger = get_logger(__name__)

INDICATOR_SCHEMA_VERSION = "v1"

_INDICATOR_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS indicator_definitions (
        definition_id TEXT PRIMARY KEY,
        indicator_code TEXT NOT NULL,
        version TEXT NOT NULL,
        category TEXT NOT NULL,
        formula_hash TEXT NOT NULL,
        param_schema_json TEXT NOT NULL,
        output_names_json TEXT NOT NULL,
        lookback_bars INTEGER NOT NULL,
        is_causal INTEGER NOT NULL DEFAULT 1 CHECK (is_causal IN (0, 1)),
        state TEXT NOT NULL,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (indicator_code, version)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_indicator_defs_code "
        "ON indicator_definitions(indicator_code, version)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_indicator_defs_lookahead "
        "ON indicator_definitions(indicator_code) WHERE is_causal = 0"
    ),
    """
    CREATE TABLE IF NOT EXISTS indicator_param_sets (
        param_set_id TEXT PRIMARY KEY,
        definition_id TEXT NOT NULL,
        params_json TEXT NOT NULL,
        params_hash TEXT NOT NULL,
        label TEXT NOT NULL DEFAULT '',
        period INTEGER GENERATED ALWAYS AS
            (json_extract(params_json, '$.period')) VIRTUAL,
        source_field TEXT GENERATED ALWAYS AS
            (json_extract(params_json, '$.source')) VIRTUAL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (definition_id, params_hash)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_indicator_params_period "
        "ON indicator_param_sets(definition_id, period)"
    ),
    """
    CREATE TABLE IF NOT EXISTS indicator_materializations (
        materialization_id TEXT PRIMARY KEY,
        definition_id TEXT NOT NULL,
        param_set_id TEXT NOT NULL,
        symbol_id TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        dataset_id TEXT NOT NULL,
        source_dataset_id TEXT,
        source_data_hash TEXT NOT NULL,
        formula_hash TEXT NOT NULL,
        covered_from_utc INTEGER NOT NULL,
        covered_to_utc INTEGER NOT NULL,
        row_count INTEGER NOT NULL DEFAULT 0,
        state TEXT NOT NULL,
        built_at TEXT,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (definition_id, param_set_id, symbol_id, timeframe),
        CHECK (covered_to_utc >= covered_from_utc)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_indicator_mat_stale "
        "ON indicator_materializations(symbol_id, timeframe) "
        "WHERE state IN ('stale', 'invalidated')"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_indicator_mat_lookup "
        "ON indicator_materializations(definition_id, param_set_id) "
        "WHERE state = 'ready'"
    ),
)


_INDICATOR_SCHEMA_V2_RETIREMENT_STATEMENTS = (
    """
    CREATE TEMP TABLE indicator_decommission_guard (
        row_count INTEGER NOT NULL CHECK (row_count = 0)
    ) STRICT
    """.strip(),
    """
    INSERT INTO indicator_decommission_guard (row_count)
    SELECT
        (SELECT COUNT(*) FROM indicator_materializations)
        + (SELECT COUNT(*) FROM indicator_param_sets)
        + (SELECT COUNT(*) FROM indicator_definitions)
    """.strip(),
    "DROP TABLE indicator_materializations",
    "DROP TABLE indicator_param_sets",
    "DROP TABLE indicator_definitions",
    "DROP TABLE indicator_decommission_guard",
)


def _migration_checksum(statements: tuple[str, ...]) -> str:
    """Return a stable checksum for ordered Indicators schema statements.

    Args:
            statements: Ordered additive SQL definitions.

    Returns:
            Lowercase SHA-256 checksum.

    Raises:
        None.
    """
    logger.debug("Calculating Indicators migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


INDICATOR_MIGRATIONS: tuple[Any, ...] = (
    build_migration_step(
        domain="indicators",
        migration_id="001_indicator_schema_v1",
        checksum=_migration_checksum(_INDICATOR_SCHEMA_STATEMENTS),
        statements=_INDICATOR_SCHEMA_STATEMENTS,
    ),
    build_migration_step(
        domain="indicators",
        migration_id="002_remove_unused_indicator_support_schema",
        checksum=_migration_checksum(_INDICATOR_SCHEMA_V2_RETIREMENT_STATEMENTS),
        statements=_INDICATOR_SCHEMA_V2_RETIREMENT_STATEMENTS,
    ),
)


def get_indicator_migrations() -> tuple[object, ...]:
    """Return immutable Indicators-owned migration steps.

    Args:
        None.

    Returns:
            Indicator migration steps in application order.

    Raises:
        None.
    """
    return INDICATOR_MIGRATIONS


def run_indicators_migrations(request_id: str) -> object:
    """Apply the immutable Indicators migration manifest through Data.

    Args:
            request_id: Canonical startup request identifier.

    Returns:
            Data-owned standard migration response.

    Raises:
        None.
    """
    logger.info("Running Indicators-owned schema migrations")
    request = build_migration_request(
        domain="indicators",
        steps=get_indicator_migrations(),
        request_id=request_id,
        complete_manifest=True,
    )
    return run_domain_migrations(request)


__all__ = [
    "INDICATOR_MIGRATIONS",
    "INDICATOR_SCHEMA_VERSION",
    "get_indicator_migrations",
    "run_indicators_migrations",
]
