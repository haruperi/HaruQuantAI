"""Strategy-owned persistence migration definitions."""

# ruff: noqa: E501

import hashlib
from typing import Any

from app.services.data import (
    build_migration_request,
    build_migration_step,
    run_data_migrations,
    run_domain_migrations,
)
from app.services.strategy.contracts.responses import unwrap_data_response
from app.utils import get_logger

logger = get_logger(__name__)

_STATEMENTS_0001 = (
    """CREATE TABLE IF NOT EXISTS strategy_versions (
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        manifest_json TEXT NOT NULL,
        lifecycle_status TEXT NOT NULL,
        policy_json TEXT NOT NULL,
        record_hash TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        PRIMARY KEY (strategy_id, strategy_version)
    )""",
    """CREATE TABLE IF NOT EXISTS strategy_configs (
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        config_json TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        request_id TEXT NOT NULL,
        PRIMARY KEY (strategy_id, strategy_version, config_hash)
    )""",
    """CREATE TABLE IF NOT EXISTS strategy_checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        checkpoint_json TEXT NOT NULL,
        checksum TEXT NOT NULL,
        authorization_ref TEXT NOT NULL,
        request_id TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS strategy_mutations (
        command_id TEXT PRIMARY KEY,
        mutation_json TEXT NOT NULL,
        publication_pending INTEGER NOT NULL
    )""",
)

_STATEMENTS_0002 = (
    """CREATE TABLE IF NOT EXISTS strategy_definitions (
        strategy_id TEXT PRIMARY KEY,
        evaluator_key TEXT NOT NULL UNIQUE,
        strategy_code TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        strategy_class TEXT NOT NULL CHECK (
            strategy_class IN (
                'trend',
                'mean_reversion',
                'breakout',
                'structure',
                'hedging',
                'basket',
                'composite'
            )
        ),
        owner_ref TEXT NOT NULL,
        description TEXT NOT NULL,
        lifecycle_status TEXT NOT NULL CHECK (
            lifecycle_status IN ('active', 'paused', 'retired')
        ),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        deleted_at TEXT,
        CHECK (
            deleted_at IS NULL
            OR lifecycle_status = 'retired'
        )
    ) STRICT""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_definitions_lifecycle
    ON strategy_definitions(lifecycle_status, strategy_id)""",
    """CREATE TABLE IF NOT EXISTS strategy_versions_v2 (
        version_id TEXT PRIMARY KEY,
        strategy_id TEXT NOT NULL
            REFERENCES strategy_definitions(strategy_id)
            ON DELETE RESTRICT,
        strategy_version TEXT NOT NULL,
        module_path TEXT NOT NULL,
        manifest_json TEXT NOT NULL CHECK (json_valid(manifest_json)),
        lifecycle_status TEXT NOT NULL CHECK (
            lifecycle_status IN (
                'DRAFT',
                'APPROVED',
                'ACTIVE',
                'STOPPED',
                'REVOKED'
            )
        ),
        policy_json TEXT NOT NULL CHECK (json_valid(policy_json)),
        source_hash TEXT NOT NULL,
        artifact_hash TEXT NOT NULL,
        dependency_hash TEXT NOT NULL,
        record_hash TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(strategy_id, strategy_version),
        UNIQUE(strategy_id, source_hash),
        CHECK (length(source_hash) = 64),
        CHECK (length(artifact_hash) = 64),
        CHECK (length(dependency_hash) = 64),
        CHECK (length(record_hash) = 64)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS strategy_configs_v2 (
        config_id TEXT PRIMARY KEY,
        version_id TEXT NOT NULL
            REFERENCES strategy_versions_v2(version_id)
            ON DELETE RESTRICT,
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        config_hash TEXT NOT NULL,
        config_schema_version TEXT NOT NULL,
        config_json TEXT NOT NULL CHECK (json_valid(config_json)),
        policy_version TEXT NOT NULL,
        runtime_profile TEXT NOT NULL CHECK (
            runtime_profile IN ('RESEARCH', 'SIMULATION', 'PAPER', 'LIVE')
        ),
        lifecycle_status TEXT NOT NULL CHECK (
            lifecycle_status IN ('active', 'paused', 'archived')
        ),
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(version_id, config_hash, runtime_profile),
        CHECK (length(config_hash) = 64)
    ) STRICT""",
    """CREATE TABLE IF NOT EXISTS strategy_state (
        config_id TEXT PRIMARY KEY
            REFERENCES strategy_configs_v2(config_id)
            ON DELETE RESTRICT,
        state_version INTEGER NOT NULL CHECK (state_version >= 0),
        evaluation_status TEXT NOT NULL CHECK (
            evaluation_status IN (
                'initialized',
                'ready',
                'evaluating',
                'halted',
                'error'
            )
        ),
        bars_processed INTEGER NOT NULL CHECK (bars_processed >= 0),
        last_evidence_at TEXT,
        last_signal_id TEXT,
        local_state_json TEXT NOT NULL CHECK (json_valid(local_state_json)),
        local_state_hash TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (length(local_state_hash) = 64)
    ) STRICT""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_state_status
    ON strategy_state(evaluation_status, updated_at)""",
    """CREATE TABLE IF NOT EXISTS strategy_checkpoints_v2 (
        checkpoint_id TEXT PRIMARY KEY,
        config_id TEXT NOT NULL
            REFERENCES strategy_configs_v2(config_id)
            ON DELETE RESTRICT,
        state_version INTEGER NOT NULL CHECK (state_version >= 0),
        sequence INTEGER NOT NULL CHECK (sequence >= 0),
        checkpoint_json TEXT NOT NULL CHECK (json_valid(checkpoint_json)),
        checksum TEXT NOT NULL,
        authorization_ref TEXT NOT NULL,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        UNIQUE(config_id, sequence),
        CHECK (length(checksum) = 64)
    ) STRICT""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_checkpoints_latest
    ON strategy_checkpoints_v2(config_id, sequence DESC)""",
    """CREATE TABLE IF NOT EXISTS strategy_signals (
        signal_id TEXT PRIMARY KEY,
        config_id TEXT NOT NULL
            REFERENCES strategy_configs_v2(config_id)
            ON DELETE RESTRICT,
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        sequence INTEGER NOT NULL CHECK (sequence >= 0),
        symbol TEXT NOT NULL,
        signal_name TEXT NOT NULL,
        side TEXT CHECK (side IN ('BUY', 'SELL')),
        active INTEGER NOT NULL CHECK (active IN (0, 1)),
        signal_timestamp TEXT NOT NULL,
        signal_json TEXT NOT NULL CHECK (json_valid(signal_json)),
        lineage_json TEXT NOT NULL CHECK (json_valid(lineage_json)),
        facts_json TEXT NOT NULL CHECK (json_valid(facts_json)),
        intent_id TEXT,
        publication_status TEXT NOT NULL CHECK (
            publication_status IN (
                'generated',
                'submitted',
                'submission_failed',
                'expired_before_submission'
            )
        ),
        risk_submission_ref TEXT,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(config_id, sequence, signal_name),
        CHECK (
            publication_status != 'submitted'
            OR risk_submission_ref IS NOT NULL
        )
    ) STRICT""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_signals_pending
    ON strategy_signals(created_at)
    WHERE publication_status IN ('generated', 'submission_failed')""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_signals_strategy_time
    ON strategy_signals(strategy_id, strategy_version, signal_timestamp DESC)""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_signals_config_sequence
    ON strategy_signals(config_id, sequence)""",
    """CREATE TABLE IF NOT EXISTS strategy_mutations_v2 (
        command_id TEXT PRIMARY KEY,
        mutation_type TEXT NOT NULL CHECK (
            mutation_type IN ('REGISTER_VERSION', 'UPDATE_PARAMETERS')
        ),
        strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL,
        mutation_json TEXT NOT NULL CHECK (json_valid(mutation_json)),
        publication_pending INTEGER NOT NULL CHECK (
            publication_pending IN (0, 1)
        ),
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        published_at TEXT
    ) STRICT""",
    """CREATE INDEX IF NOT EXISTS idx_strategy_mutations_pending
    ON strategy_mutations_v2(created_at)
    WHERE publication_pending = 1""",
    # Backfill definitions from legacy strategy_versions if populated
    """INSERT OR IGNORE INTO strategy_definitions (
        strategy_id, evaluator_key, strategy_code, display_name, strategy_class, owner_ref, description, lifecycle_status, created_at, updated_at
    )
    SELECT
        strategy_id,
        strategy_id,
        strategy_id,
        strategy_id,
        'trend',
        COALESCE(json_extract(manifest_json, '$.owner_ref'), 'owner'),
        'Migrated Strategy definition',
        'active',
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    FROM strategy_versions
    WHERE json_valid(manifest_json)""",
    # Backfill strategy_versions_v2 from legacy strategy_versions
    """INSERT OR IGNORE INTO strategy_versions_v2 (
        version_id, strategy_id, strategy_version, module_path, manifest_json, lifecycle_status, policy_json, source_hash, artifact_hash, dependency_hash, record_hash, request_id, correlation_id, created_at
    )
    SELECT
        strategy_id || '@' || strategy_version,
        strategy_id,
        strategy_version,
        COALESCE(json_extract(manifest_json, '$.module_path'), 'app.services.strategy.evaluators.naive_ma_trend'),
        manifest_json,
        lifecycle_status,
        policy_json,
        COALESCE(json_extract(manifest_json, '$.source_hash'), '0000000000000000000000000000000000000000000000000000000000000000'),
        COALESCE(json_extract(manifest_json, '$.artifact_hash'), '0000000000000000000000000000000000000000000000000000000000000000'),
        COALESCE(json_extract(manifest_json, '$.dependency_hash'), '0000000000000000000000000000000000000000000000000000000000000000'),
        record_hash,
        request_id,
        correlation_id,
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    FROM strategy_versions
    WHERE json_valid(manifest_json)""",
    # Backfill strategy_configs_v2 from legacy strategy_configs
    """INSERT OR IGNORE INTO strategy_configs_v2 (
        config_id, version_id, strategy_id, strategy_version, config_hash, config_schema_version, config_json, policy_version, runtime_profile, lifecycle_status, request_id, correlation_id, created_at
    )
    SELECT
        strategy_id || '@' || strategy_version || '#' || config_hash,
        strategy_id || '@' || strategy_version,
        strategy_id,
        strategy_version,
        config_hash,
        'v1',
        config_json,
        policy_version,
        'RESEARCH',
        'active',
        request_id,
        'cor-00000000-0000-4000-8000-000000000000',
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    FROM strategy_configs
    WHERE json_valid(config_json)""",
    # Backfill strategy_checkpoints_v2 from legacy strategy_checkpoints
    """INSERT OR IGNORE INTO strategy_checkpoints_v2 (
        checkpoint_id, config_id, state_version, sequence, checkpoint_json, checksum, authorization_ref, request_id, correlation_id, created_at
    )
    SELECT
        checkpoint_id,
        COALESCE(json_extract(checkpoint_json, '$.config_id'), 'unknown@1.0.0#' || checksum),
        COALESCE(json_extract(checkpoint_json, '$.state_version'), 0),
        COALESCE(json_extract(checkpoint_json, '$.sequence'), 0),
        checkpoint_json,
        checksum,
        authorization_ref,
        request_id,
        'cor-00000000-0000-4000-8000-000000000000',
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
    FROM strategy_checkpoints
    WHERE json_valid(checkpoint_json)""",
    # Backfill strategy_mutations_v2 from legacy strategy_mutations
    """INSERT OR IGNORE INTO strategy_mutations_v2 (
        command_id, mutation_type, strategy_id, strategy_version, mutation_json, publication_pending, request_id, correlation_id, created_at, published_at
    )
    SELECT
        command_id,
        COALESCE(json_extract(mutation_json, '$.mutation_type'), 'REGISTER_VERSION'),
        COALESCE(json_extract(mutation_json, '$.strategy_id'), 'unknown'),
        COALESCE(json_extract(mutation_json, '$.strategy_version'), '1.0.0'),
        mutation_json,
        publication_pending,
        COALESCE(json_extract(mutation_json, '$.request_id'), 'req-00000000-0000-4000-8000-000000000000'),
        COALESCE(json_extract(mutation_json, '$.correlation_id'), 'cor-00000000-0000-4000-8000-000000000000'),
        strftime('%Y-%m-%dT%H:%M:%SZ', 'now'),
        NULL
    FROM strategy_mutations
    WHERE json_valid(mutation_json)""",
    # Drop legacy 0001 tables after backfill
    "DROP TABLE strategy_versions",
    "DROP TABLE strategy_configs",
    "DROP TABLE strategy_checkpoints",
    "DROP TABLE strategy_mutations",
    # Rename _v2 tables to canonical names
    "ALTER TABLE strategy_versions_v2 RENAME TO strategy_versions",
    "ALTER TABLE strategy_configs_v2 RENAME TO strategy_configs",
    "ALTER TABLE strategy_checkpoints_v2 RENAME TO strategy_checkpoints",
    "ALTER TABLE strategy_mutations_v2 RENAME TO strategy_mutations",
)


def _strategy_migration_steps() -> tuple[Any, ...]:
    """Return ordered immutable Strategy migration definitions.

    Returns:
        The complete ordered Strategy migration tuple.
    """
    logger.debug("Building Strategy migration definitions")
    material_0001 = "\n".join(_STATEMENTS_0001).encode("utf-8")
    material_0002 = "\n".join(_STATEMENTS_0002).encode("utf-8")
    return (
        build_migration_step(
            domain="strategy",
            migration_id="0001_strategy_domain",
            checksum=hashlib.sha256(material_0001).hexdigest(),
            statements=_STATEMENTS_0001,
        ),
        build_migration_step(
            domain="strategy",
            migration_id="0002_strategy_seven_table_runtime",
            checksum=hashlib.sha256(material_0002).hexdigest(),
            statements=_STATEMENTS_0002,
        ),
    )


def _ensure_strategy_storage(request_id: str) -> None:
    """Apply Strategy migrations idempotently through Data.

    Args:
        request_id: Canonical request trace identifier.
    """
    logger.info("Ensuring Strategy-owned persistence schema")
    try:
        from app.utils import validate_id

        valid_req_id = validate_id(request_id, expected_prefix="req")
    except ValueError, TypeError, AttributeError:
        valid_req_id = "req-11111111-1111-4111-8111-111111111111"

    unwrap_data_response(
        run_data_migrations(request_id=valid_req_id),
        operation="data.run_data_migrations",
    )
    unwrap_data_response(
        run_domain_migrations(
            build_migration_request(
                domain="strategy",
                steps=_strategy_migration_steps(),
                request_id=valid_req_id,
            )
        ),
        operation="data.run_domain_migrations.strategy",
    )


__all__: list[str] = []
