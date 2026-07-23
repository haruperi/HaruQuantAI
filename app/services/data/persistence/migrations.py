"""Module for executing domain migrations and maintaining migration ledger."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

from app.services.data._settings import DataSettings, get_data_settings
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    MigrationRequest,
    MigrationResult,
    MigrationStep,
    SqlScalar,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.locking import acquire_write_lock
from app.services.data.persistence.transactions import execute_transaction
from app.utils import logger

_SQLITE_URL_PREFIX = "sqlite:///"

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
)


def _resolve_database_path(settings: DataSettings) -> Path:
    """Resolve database file path from typed DATA configuration.

    Args:
        settings: Validated DATA-domain settings.

    Returns:
        Resolved Path to the SQLite database.

    Raises:
        ValueError: If configuration is invalid.
    """
    logger.info("Resolving database path from typed DATA configuration")
    database_url = settings.database_url
    data_directory = settings.data_dir
    if database_url is None or data_directory is None:
        raise ValueError("required database settings are missing")

    if not database_url.startswith(_SQLITE_URL_PREFIX):
        raise ValueError("unsupported database URL")
    relative_value = database_url.removeprefix(_SQLITE_URL_PREFIX)
    if not relative_value or relative_value == ":memory:" or "?" in relative_value:
        raise ValueError("database URL must contain a relative file path")

    relative_path = Path(relative_value)
    if relative_path.is_absolute() or relative_path.drive:
        raise ValueError("database path must be relative")

    data_directory = data_directory.expanduser().resolve()
    if not data_directory.is_dir():
        raise ValueError("DATA_DIR must be an existing directory")

    database_path = (data_directory / relative_path).resolve()
    if not database_path.is_relative_to(data_directory):
        raise ValueError("database path escapes DATA_DIR")
    if not database_path.parent.is_dir():
        raise ValueError("database parent directory must already exist")

    return database_path


def _timestamp_text(value: int) -> str:
    """Encode Unix-nanosecond timestamp as ordered fixed-width text.

    Args:
        value: Nanosecond timestamp.

    Returns:
        Fixed-width 19-digit string representation.
    """
    logger.debug("Running DATA function: _timestamp_text")
    return f"{value:019d}"


def _initialize_ledger(domain: str, request_id: str) -> None:
    """Initialize migration ledger table if it doesn't exist.

    Args:
        domain: Migration domain name.
        request_id: Operation request identifier.

    Raises:
        DataError: If ledger creation fails.
    """
    create_ledger_table_sql = """
    CREATE TABLE IF NOT EXISTS data_migration_ledger (
        domain TEXT NOT NULL,
        migration_id TEXT NOT NULL,
        checksum TEXT NOT NULL,
        applied_at_ns TEXT NOT NULL CHECK (
            length(applied_at_ns) = 19
            AND applied_at_ns NOT GLOB '*[^0-9]*'
        ),
        PRIMARY KEY (domain, migration_id)
    ) STRICT
    """.strip()

    try:
        logger.info("Initializing migration ledger table if not exists")
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(create_ledger_table_sql,),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )
    except DataError as error:
        logger.error("Failed to initialize migration ledger")
        if error.code == "CONCURRENT_WRITE_LOCKED":
            raise
        details = {"domain": domain, "stage": "ledger_initialization"}
        raise DataError(
            "SCHEMA_MIGRATION_FAILED",
            safe_details=details,
            request_id=request_id,
        ) from error


def _fetch_applied_migrations(domain: str, request_id: str) -> dict[str, str]:
    """Retrieve already applied migrations from ledger.

    Args:
        domain: Migration domain name.
        request_id: Operation request identifier.

    Returns:
        Dictionary mapping applied migration IDs to their checksums.

    Raises:
        DataError: If query fails.
    """
    logger.info("Querying applied migrations for domain %s", domain)
    sql = (
        "SELECT migration_id, checksum FROM data_migration_ledger "
        "WHERE domain = ? ORDER BY migration_id"
    )
    try:
        query_result = execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=(sql,),
                    parameter_sets=((domain,),),
                    max_rows=10000,
                ),
                request_id=request_id,
            )
        )
    except DataError as error:
        logger.error("Failed to query migration ledger")
        if error.code == "CONCURRENT_WRITE_LOCKED":
            raise
        details = {"domain": domain, "stage": "ledger_query"}
        raise DataError(
            "SCHEMA_MIGRATION_FAILED",
            safe_details=details,
            request_id=request_id,
        ) from error

    return {str(row["migration_id"]): str(row["checksum"]) for row in query_result.rows}


def _apply_step(step: MigrationStep, request_id: str) -> None:
    """Apply one migration step and record it in the ledger.

    Args:
        step: Migration step to execute.
        request_id: Operation request identifier.

    Raises:
        DataError: If execution fails.
    """
    logger.info("Applying migration step %s", step.migration_id)
    statements = list(step.statements)
    parameter_sets: list[tuple[SqlScalar, ...]] = [
        () for _ in range(len(step.statements))
    ]

    insert_ledger_sql = (
        "INSERT INTO data_migration_ledger "
        "(domain, migration_id, checksum, applied_at_ns) "
        "VALUES (?, ?, ?, ?)"
    )
    statements.append(insert_ledger_sql)

    applied_at_ns = _timestamp_text(time.time_ns())
    parameter_sets.append(
        (step.domain, step.migration_id, step.checksum, applied_at_ns)
    )

    try:
        execute_transaction(
            TransactionRequest(
                plan=StatementPlan(
                    statements=tuple(statements),
                    parameter_sets=tuple(parameter_sets),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        )
    except DataError as error:
        logger.error("Failed to execute migration step %s", step.migration_id)
        if error.code == "CONCURRENT_WRITE_LOCKED":
            raise
        details = {
            "domain": step.domain,
            "migration_id": step.migration_id,
            "stage": "step_execution",
        }
        raise DataError(
            "SCHEMA_MIGRATION_FAILED",
            safe_details=details,
            request_id=request_id,
        ) from error


def run_domain_migrations(request: MigrationRequest) -> MigrationResult:
    """Validate and execute domain-owned migration steps.

    Args:
        request: Migration request containing domain and ordered steps.

    Returns:
        MigrationResult specifying applied and skipped migration IDs.

    Raises:
        DataError: If configuration, lock acquisition, execution, order, or
            checksum validation fails.
    """
    msg = (
        f"Starting migrations for domain: {request.domain} "
        f"request: {request.request_id}"
    )
    logger.info(msg)

    try:
        database_path = _resolve_database_path(get_data_settings())
    except OSError, ValueError:
        logger.error("Database path resolution failed")
        details = {"operation": "run_domain_migrations", "stage": "configuration"}
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details=details,
            request_id=request.request_id,
        ) from None

    try:
        lock = acquire_write_lock(database_path, request.request_id)
    except DataError:
        logger.error("Failed to acquire database write lock")
        raise

    applied_ids: list[str] = []
    skipped_ids: list[str] = []

    with lock:
        logger.info("Database write lock acquired")

        # 1. Idempotently create data_migration_ledger table
        _initialize_ledger(request.domain, request.request_id)

        # 2. Fetch applied migrations for this domain
        applied_migrations = _fetch_applied_migrations(
            request.domain, request.request_id
        )
        max_applied_id = max(applied_migrations.keys()) if applied_migrations else None

        # 3. Validate and apply/skip steps
        for step in request.steps:
            logger.debug("Processing migration step %s", step.migration_id)

            # Reject modifications of applied migrations (checksum mismatch)
            if step.migration_id in applied_migrations:
                if step.checksum != applied_migrations[step.migration_id]:
                    msg = (
                        f"Checksum mismatch for migration {step.migration_id}. "
                        f"Expected: {applied_migrations[step.migration_id]} "
                        f"Got: {step.checksum}"
                    )
                    logger.error(msg)
                    details = {
                        "domain": request.domain,
                        "migration_id": step.migration_id,
                        "stage": "checksum_validation",
                    }
                    raise DataError(
                        "SCHEMA_MIGRATION_FAILED",
                        safe_details=details,
                        request_id=request.request_id,
                    )
                logger.info("Migration %s already applied; skipping", step.migration_id)
                skipped_ids.append(step.migration_id)
            else:
                # Reject out-of-order execution
                if max_applied_id is not None and step.migration_id < max_applied_id:
                    msg = (
                        f"Migration {step.migration_id} out of order. "
                        f"Max: {max_applied_id}"
                    )
                    logger.error(msg)
                    details = {
                        "domain": request.domain,
                        "migration_id": step.migration_id,
                        "stage": "order_validation",
                    }
                    raise DataError(
                        "SCHEMA_MIGRATION_FAILED",
                        safe_details=details,
                        request_id=request.request_id,
                    )

                # Apply the step
                _apply_step(step, request.request_id)
                applied_ids.append(step.migration_id)
                max_applied_id = step.migration_id

    msg = (
        f"Completed domain: {request.domain} "
        f"applied: {len(applied_ids)} skipped: {len(skipped_ids)}"
    )
    logger.info(msg)

    return MigrationResult(
        domain=request.domain,
        applied_ids=tuple(applied_ids),
        skipped_ids=tuple(skipped_ids),
        request_id=request.request_id,
    )


def run_data_migrations(request_id: str) -> MigrationResult:
    """Apply the complete ordered DATA-owned schema manifest.

    Args:
        request_id: Canonical request identifier for migration audit evidence.

    Returns:
        Applied and skipped DATA migration identifiers.
    """
    logger.info("Running the authoritative DATA schema migration manifest")
    return run_domain_migrations(
        MigrationRequest(
            domain="data",
            steps=DATA_MIGRATION_STEPS,
            request_id=request_id,
        )
    )


__all__ = ["DATA_MIGRATION_STEPS", "run_data_migrations", "run_domain_migrations"]
