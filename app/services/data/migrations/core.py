"""Data-owned immutable schema definitions.

Data's own tables. The migration *runner* — ledger initialisation, checksum
comparison, write-lock acquisition, and step application — stays in
``app/services/data/persistence/migrations.py`` under the shared-infrastructure
exemption recorded in ``AGENTS.md`` §1; see ``FR-DATA-153``.

``001_initial_data_schema`` and ``002_economic_events`` are **applied steps**.
Their statement tuples are moved byte-for-byte: a checksum is computed over the
ordered statements, so any reformatting here would change the digest and the
ledger would block database access.
"""

from __future__ import annotations

import hashlib

from app.services.data.migrations.data_jobs import DATA_JOBS_ENVIRONMENT_MIGRATION_STEP
from app.services.data.migrations.economic_calendar import (
    ECONOMIC_CALENDAR_V2_MIGRATION_STEP,
)
from app.services.data.migrations.economic_event_definitions import (
    ECONOMIC_EVENT_DEFINITIONS_MIGRATION_STEP,
)
from app.services.data.migrations.research_sources import (
    RESEARCH_PROVIDER_MIGRATION_STEP,
    RESEARCH_SOURCE_MIGRATION_STEP,
)
from app.services.data.persistence.contracts import MigrationStep
from app.utils import get_logger

logger = get_logger(__name__)


_DATA_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE data_cache (
        key TEXT PRIMARY KEY,
        dataset_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        source_revision TEXT NOT NULL,
        raw_data_hash TEXT NOT NULL,
        schema_version TEXT NOT NULL,
        normalization_version TEXT NOT NULL,
        request_id TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_audit_events (
        event_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        domain TEXT NOT NULL,
        action TEXT NOT NULL,
        principal_id TEXT,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        causation_id TEXT,
        payload_json TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_source_attempts (
        source_id TEXT NOT NULL,
        timestamp_ns TEXT NOT NULL CHECK (
            length(timestamp_ns) = 19
            AND timestamp_ns NOT GLOB '*[^0-9]*'
        ),
        request_id TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('SUCCESS', 'FAILURE', 'BLOCKED')),
        error_code TEXT,
        PRIMARY KEY (source_id, timestamp_ns)
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_source_state (
        source_id TEXT PRIMARY KEY,
        readiness TEXT NOT NULL CHECK (
            readiness IN ('disabled', 'staging', 'production')
        ),
        descriptor_revision TEXT NOT NULL,
        updated_at_ns TEXT NOT NULL CHECK (
            length(updated_at_ns) = 19
            AND updated_at_ns NOT GLOB '*[^0-9]*'
        ),
        request_id TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_update_jobs (
        job_id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        symbols_json TEXT NOT NULL,
        timeframes_json TEXT NOT NULL,
        data_kinds_json TEXT NOT NULL,
        start TEXT NOT NULL,
        end TEXT,
        interval_seconds INTEGER,
        enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
        created_at TEXT NOT NULL,
        request_id TEXT NOT NULL,
        state TEXT NOT NULL CHECK (
            state IN ('created', 'running', 'stopped', 'failed', 'blocked')
        ),
        last_run_status TEXT CHECK (
            last_run_status IN ('succeeded', 'failed', 'blocked')
        ),
        last_checkpoint TEXT,
        last_error TEXT,
        next_run_at TEXT,
        lease_owner TEXT,
        lease_expires_at TEXT,
        recovery_state TEXT NOT NULL CHECK (
            recovery_state IN ('clean', 'required', 'recovered', 'blocked')
        )
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_backfill_checkpoints (
        idempotency_key TEXT PRIMARY KEY,
        job_id TEXT NOT NULL,
        chunk_id TEXT NOT NULL,
        committed_start TEXT NOT NULL,
        committed_end TEXT NOT NULL,
        record_count INTEGER NOT NULL,
        content_hash TEXT NOT NULL,
        checkpoint TEXT NOT NULL,
        artifact_temp TEXT NOT NULL,
        artifact_final TEXT NOT NULL,
        publication_state TEXT NOT NULL CHECK (
            publication_state IN ('prepared', 'committed')
        ),
        request_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    "CREATE INDEX idx_checkpoints_job ON data_backfill_checkpoints (job_id)",
    """
    CREATE TABLE data_feeds (
        feed_id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        data_kind TEXT NOT NULL CHECK (data_kind IN ('ohlcv', 'tick', 'spread')),
        timeframe TEXT,
        source_capability TEXT NOT NULL,
        buffer_capacity INTEGER NOT NULL,
        overflow_policy TEXT NOT NULL CHECK (
            overflow_policy IN ('halt', 'drop_and_reconcile', 'backpressure')
        ),
        heartbeat_timeout_seconds INTEGER NOT NULL,
        reconnect_policy_json TEXT NOT NULL,
        state TEXT NOT NULL CHECK (
            state IN ('starting', 'running', 'stopped', 'failed', 'blocked')
        ),
        heartbeat_at TEXT,
        last_event_at TEXT,
        buffer_depth INTEGER NOT NULL,
        dropped_count INTEGER NOT NULL,
        gap_count INTEGER NOT NULL,
        reconnect_count INTEGER NOT NULL,
        breaker_state TEXT NOT NULL CHECK (
            breaker_state IN ('closed', 'open', 'half_open')
        ),
        breaker_opened_at TEXT,
        drift_ms INTEGER,
        last_error TEXT,
        request_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
)


_ECONOMIC_EVENTS_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE data_economic_events (
        provider TEXT NOT NULL,
        provider_event_id TEXT NOT NULL,
        name TEXT NOT NULL,
        category TEXT,
        country TEXT,
        currency TEXT,
        scheduled_at TEXT NOT NULL,
        original_scheduled_at TEXT,
        actual TEXT,
        forecast TEXT,
        previous TEXT,
        revised_previous TEXT,
        actual_raw TEXT,
        forecast_raw TEXT,
        previous_raw TEXT,
        unit TEXT,
        source TEXT,
        source_url TEXT,
        impact INTEGER NOT NULL CHECK (impact BETWEEN 1 AND 4),
        updated_at TEXT,
        PRIMARY KEY (provider, provider_event_id)
    ) STRICT
    """.strip(),
    "CREATE INDEX idx_economic_events_scheduled ON data_economic_events (scheduled_at)",
)


# --- Data catalog (006) -----------------------------------------------------
# Indexes artifacts written by ``persistence/dataset_writer.py``. That writer
# emits one file plus a sidecar ``StorageManifest`` at a caller-supplied path
# and content-addresses it as ``artifact-{sha256}``; it does not partition by
# directory. The catalog therefore prunes by recorded time range rather than by
# path, which is strictly more precise: a range scan on
# ``(dataset_id, min_ts_utc, max_ts_utc)`` needs no filesystem access at all.
#
# Every column here is derivable from a sidecar manifest, so the catalog can be
# dropped and rebuilt by rescanning. ``verify_state`` and ``verified_at`` are the
# deliberate exceptions: they are index-local operational state and a rebuild
# resets them to ``unverified``. See ``FR-DATA-154`` through ``FR-DATA-160``.
_CATALOG_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS data_symbols (
        symbol_id TEXT PRIMARY KEY,
        canonical_symbol TEXT NOT NULL UNIQUE,
        asset_class TEXT NOT NULL,
        base_currency TEXT NOT NULL,
        quote_currency TEXT NOT NULL,
        digits INTEGER NOT NULL,
        tick_size_decimal TEXT NOT NULL,
        min_volume_decimal TEXT NOT NULL,
        max_volume_decimal TEXT NOT NULL,
        volume_step_decimal TEXT NOT NULL,
        contract_size_decimal TEXT NOT NULL DEFAULT '1',
        spec_json TEXT NOT NULL DEFAULT '{}',
        state TEXT NOT NULL,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        deleted_at TEXT
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_symbols_class "
        "ON data_symbols(asset_class, canonical_symbol)"
    ),
    """
    CREATE TABLE IF NOT EXISTS data_providers (
        provider_id TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL UNIQUE,
        provider_kind TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 100,
        trust_tier TEXT NOT NULL,
        rate_limit INTEGER NOT NULL DEFAULT 0,
        rate_window_seconds INTEGER NOT NULL DEFAULT 1,
        license_json TEXT NOT NULL DEFAULT '{}',
        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    """
    CREATE TABLE IF NOT EXISTS data_market_sessions (
        session_id TEXT PRIMARY KEY,
        symbol_id TEXT NOT NULL,
        session_name TEXT NOT NULL,
        day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
        open_time_utc TEXT NOT NULL,
        close_time_utc TEXT NOT NULL,
        is_trading INTEGER NOT NULL DEFAULT 1 CHECK (is_trading IN (0, 1)),
        effective_from TEXT NOT NULL,
        effective_to TEXT,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (symbol_id, session_name, day_of_week, effective_from)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_sessions_active "
        "ON data_market_sessions(symbol_id, day_of_week) "
        "WHERE effective_to IS NULL"
    ),
    """
    CREATE TABLE IF NOT EXISTS data_datasets (
        dataset_id TEXT PRIMARY KEY,
        dataset_kind TEXT NOT NULL,
        owner_domain TEXT NOT NULL,
        symbol_id TEXT,
        timeframe TEXT,
        provider_id TEXT,
        producer_ref TEXT,
        root_path TEXT NOT NULL,
        schema_version TEXT NOT NULL,
        normalization_version TEXT NOT NULL,
        timestamp_semantics TEXT NOT NULL DEFAULT 'bar_open',
        file_count INTEGER NOT NULL DEFAULT 0,
        total_rows INTEGER NOT NULL DEFAULT 0,
        total_bytes INTEGER NOT NULL DEFAULT 0,
        min_ts_utc INTEGER,
        max_ts_utc INTEGER,
        state TEXT NOT NULL,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (dataset_kind, symbol_id, timeframe, provider_id, producer_ref)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_datasets_lookup "
        "ON data_datasets(dataset_kind, symbol_id, timeframe)"
    ),
    """
    CREATE TABLE IF NOT EXISTS data_partition_files (
        file_id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        artifact_id TEXT NOT NULL UNIQUE,
        relative_path TEXT NOT NULL,
        format TEXT NOT NULL CHECK (format IN ('parquet', 'csv')),
        content_hash TEXT NOT NULL,
        row_count INTEGER NOT NULL,
        byte_size INTEGER NOT NULL,
        min_ts_utc INTEGER NOT NULL,
        max_ts_utc INTEGER NOT NULL,
        schema_version TEXT NOT NULL,
        normalization_version TEXT NOT NULL,
        source_revision TEXT NOT NULL,
        provenance_json TEXT NOT NULL DEFAULT '{}',
        license_json TEXT NOT NULL DEFAULT '{}',
        verify_state TEXT NOT NULL DEFAULT 'unverified',
        verified_at TEXT,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE (dataset_id, relative_path),
        CHECK (max_ts_utc >= min_ts_utc)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_files_prune "
        "ON data_partition_files(dataset_id, min_ts_utc, max_ts_utc)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_files_bad "
        "ON data_partition_files(dataset_id) "
        "WHERE verify_state IN ('hash_mismatch', 'missing')"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_files_hash "
        "ON data_partition_files(content_hash)"
    ),
    """
    CREATE TABLE IF NOT EXISTS data_fetch_log (
        fetch_id TEXT PRIMARY KEY,
        provider_id TEXT NOT NULL,
        symbol_id TEXT NOT NULL,
        data_kind TEXT NOT NULL,
        timeframe TEXT,
        range_start_utc INTEGER NOT NULL,
        range_end_utc INTEGER NOT NULL,
        rows_returned INTEGER NOT NULL DEFAULT 0,
        materialized INTEGER NOT NULL DEFAULT 0 CHECK (materialized IN (0, 1)),
        dataset_id TEXT,
        served_from TEXT NOT NULL,
        fetch_latency_ms INTEGER,
        state TEXT NOT NULL,
        error_code TEXT,
        request_id TEXT NOT NULL,
        correlation_id TEXT NOT NULL,
        started_at TEXT NOT NULL,
        finished_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        CHECK (range_end_utc >= range_start_utc),
        CHECK (materialized = 0 OR dataset_id IS NOT NULL)
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_fetch_symbol "
        "ON data_fetch_log(symbol_id, data_kind, started_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_fetch_source "
        "ON data_fetch_log(served_from, started_at DESC)"
    ),
    """
    CREATE TABLE IF NOT EXISTS data_quality_events (
        event_id TEXT PRIMARY KEY,
        symbol_id TEXT NOT NULL,
        dataset_id TEXT,
        file_id TEXT,
        fetch_id TEXT,
        issue_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        action_taken TEXT NOT NULL,
        ts_range_start INTEGER NOT NULL,
        ts_range_end INTEGER NOT NULL,
        affected_rows INTEGER NOT NULL DEFAULT 0,
        detail_json TEXT NOT NULL DEFAULT '{}',
        detected_at TEXT NOT NULL,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_quality_symbol "
        "ON data_quality_events(symbol_id, detected_at DESC)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_data_quality_severe "
        "ON data_quality_events(detected_at DESC) "
        "WHERE severity IN ('error', 'critical')"
    ),
)


def _schema_checksum(statements: tuple[str, ...]) -> str:
    """Return the stable checksum for one ordered migration statement set."""
    logger.debug("Calculating DATA schema migration checksum")
    material = "\n-- statement --\n".join(statements).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


DATA_MIGRATION_STEPS = (
    MigrationStep(
        domain="data",
        migration_id="001_initial_data_schema",
        checksum=_schema_checksum(_DATA_SCHEMA_STATEMENTS),
        statements=_DATA_SCHEMA_STATEMENTS,
    ),
    MigrationStep(
        domain="data",
        migration_id="002_economic_events",
        checksum=_schema_checksum(_ECONOMIC_EVENTS_SCHEMA_STATEMENTS),
        statements=_ECONOMIC_EVENTS_SCHEMA_STATEMENTS,
    ),
    RESEARCH_SOURCE_MIGRATION_STEP,
    RESEARCH_PROVIDER_MIGRATION_STEP,
    MigrationStep(
        domain="data",
        migration_id="006_data_catalog_v1",
        checksum=_schema_checksum(_CATALOG_SCHEMA_STATEMENTS),
        statements=_CATALOG_SCHEMA_STATEMENTS,
    ),
    ECONOMIC_CALENDAR_V2_MIGRATION_STEP,
    DATA_JOBS_ENVIRONMENT_MIGRATION_STEP,
    ECONOMIC_EVENT_DEFINITIONS_MIGRATION_STEP,
)
