"""Execute domain migrations and maintain the immutable migration ledger.

This module owns migration *execution* only: ledger initialisation, checksum
comparison, write-lock acquisition, and step application on behalf of every
domain. Data's own schema definitions live in
``app/services/data/migrations/core.py``.
"""

from __future__ import annotations

import time
from pathlib import Path

from app.composition.logging import get_logger
from app.services.data._settings import DataSettings, get_data_settings
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.migrations.core import DATA_MIGRATION_STEPS
from app.services.data.persistence.contracts import (
    MigrationRequest,
    MigrationResult,
    MigrationStep,
    SqlScalar,
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.locking import _acquire_write_lock_raw
from app.services.data.persistence.transactions import _execute_transaction_raw

logger = get_logger(__name__)

_SQLITE_URL_PREFIX = "sqlite:///"


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
        _execute_transaction_raw(
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
        logger.exception("Failed to initialize migration ledger")
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
        query_result = _execute_transaction_raw(
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
        logger.exception("Failed to query migration ledger")
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
        _execute_transaction_raw(
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
        logger.exception("Failed to execute migration step %s", step.migration_id)
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


def _validate_applied_tombstones_and_orphans(
    request: MigrationRequest,
    applied_migrations: dict[str, str],
) -> None:
    """Validate tombstone checksums and complete-manifest orphan constraints.

    Args:
        request: Migration execution request.
        applied_migrations: Mapping of applied migration IDs to checksums.

    Raises:
        DataError: If checksum mismatch or uninstalled orphan detected.
    """
    tombstone_by_id = {t.migration_id: t for t in request.tombstones}

    # Validate matching tombstones against applied migrations
    for t_id, tombstone in tombstone_by_id.items():
        if t_id in applied_migrations:
            if tombstone.checksum != applied_migrations[t_id]:
                logger.error(
                    "Tombstone checksum mismatch for %s: expected %s, got %s",
                    t_id,
                    applied_migrations[t_id],
                    tombstone.checksum,
                )
                details = {
                    "domain": request.domain,
                    "migration_id": t_id,
                    "stage": "checksum_validation",
                }
                raise DataError(
                    "SCHEMA_MIGRATION_FAILED",
                    safe_details=details,
                    request_id=request.request_id,
                )
            logger.info(
                "Validated retained migration tombstone %s/%s",
                request.domain,
                t_id,
            )

    if request.complete_manifest:
        declared_ids = {step.migration_id for step in request.steps}
        orphaned_ids = sorted(set(applied_migrations) - declared_ids)
        unaccounted_orphans = [
            oid for oid in orphaned_ids if oid not in tombstone_by_id
        ]
        if unaccounted_orphans:
            logger.error(
                "Applied migrations are absent from the complete manifest: %s",
                ", ".join(unaccounted_orphans),
            )
            raise DataError(
                "SCHEMA_MIGRATION_FAILED",
                safe_details={
                    "domain": request.domain,
                    "migration_id": unaccounted_orphans[0],
                    "stage": "manifest_validation",
                },
                request_id=request.request_id,
            )


def _run_domain_migrations_raw(request: MigrationRequest) -> MigrationResult:
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
        logger.exception("Database path resolution failed")
        details = {"operation": "run_domain_migrations", "stage": "configuration"}
        raise DataError(
            "DB_CONNECTION_ERROR",
            safe_details=details,
            request_id=request.request_id,
        ) from None

    try:
        lock = _acquire_write_lock_raw(database_path, request.request_id)
    except DataError:
        logger.exception("Failed to acquire database write lock")
        raise

    applied_ids: list[str] = []
    skipped_ids: list[str] = []

    with lock:
        logger.info("Database write lock acquired")

        # 1. Idempotently create data_migration_ledger table
        _initialize_ledger(request.domain, request.request_id)

        # 2. Fetch applied migrations and validate tombstones/manifest
        applied_migrations = _fetch_applied_migrations(
            request.domain, request.request_id
        )
        _validate_applied_tombstones_and_orphans(request, applied_migrations)
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


def run_domain_migrations(
    request: MigrationRequest,
) -> StandardResponse[MigrationResult]:
    """Validate and execute domain-owned migration steps.

    Args:
        request: Migration request containing domain and ordered steps.

    Returns:
        Standard response carrying applied and skipped migration identifiers.
    """
    return run_data_operation(
        operation="data.persistence.run_domain_migrations",
        request_id=request.request_id,
        start_time=data_start_time(),
        raw=lambda: _run_domain_migrations_raw(request),
    )


def _run_data_migrations_raw(request_id: str) -> MigrationResult:
    """Apply the complete ordered DATA-owned schema manifest.

    Args:
        request_id: Canonical request identifier for migration audit evidence.

    Returns:
        Applied and skipped DATA migration identifiers.
    """
    logger.info("Running the authoritative DATA schema migration manifest")
    # Runtime records remain a registered Data feature and therefore belong to the
    # complete manifest. Its module stays out of migrations/__init__ to avoid the
    # documented import cycle, so resolve its definitions only when the runner fires.
    from app.services.data.migrations.runtime_stores import (
        get_runtime_store_migration_steps,
    )

    complete_steps = tuple(
        sorted(
            (*DATA_MIGRATION_STEPS, *get_runtime_store_migration_steps()),
            key=lambda step: step.migration_id,
        )
    )
    return _run_domain_migrations_raw(
        MigrationRequest(
            domain="data",
            steps=complete_steps,
            request_id=request_id,
            complete_manifest=True,
        )
    )


def run_data_migrations(request_id: str) -> StandardResponse[MigrationResult]:
    """Apply the complete ordered DATA-owned schema manifest.

    Args:
        request_id: Canonical request identifier for migration audit evidence.

    Returns:
        Standard response carrying applied and skipped DATA migration identifiers.
    """
    return run_data_operation(
        operation="data.persistence.run_data_migrations",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _run_data_migrations_raw(request_id),
    )


__all__ = ["DATA_MIGRATION_STEPS", "run_data_migrations", "run_domain_migrations"]
