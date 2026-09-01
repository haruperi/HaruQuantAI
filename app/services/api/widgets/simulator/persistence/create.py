"""Create operations for Simulation Workbench-owned catalogue records."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, cast

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Fields consumed from Data's normalized transaction result."""

    affected_rows: int


class SimulationWorkbenchPersistenceError(Exception):
    """Raised when the catalogue store cannot confirm a write or read."""

    def __init__(self) -> None:
        """Initialize with the stable store-unavailable code."""
        super().__init__("SIMULATION_WORKBENCH_STORE_UNAVAILABLE")


#: Immutable evidence-reference columns of ``api_simulation_results``.
RESULT_COLUMNS: tuple[str, ...] = (
    "run_id",
    "principal_id",
    "origin_kind",
    "origin_id",
    "job_id",
    "batch_id",
    "session_id",
    "strategy_id",
    "strategy_version",
    "strategy_label",
    "symbols",
    "timeframe",
    "measurement_start",
    "measurement_end",
    "status",
    "result_ref",
    "report_id",
    "report_ref",
    "artifact_manifest_ref",
    "quality_status",
    "evidence_class",
    "created_at",
    "completed_at",
    "name",
    "alias",
    "description",
    "tags",
    "run_reason",
    "archive_state",
    "updated_at",
)

#: Resumable-session columns of ``api_simulation_sessions``.
SESSION_COLUMNS: tuple[str, ...] = (
    "session_id",
    "principal_id",
    "run_id",
    "mode",
    "evidence_class",
    "status",
    "cursor",
    "tick_count",
    "completed",
    "durable",
    "state_hash",
    "closed_at",
    "created_at",
    "updated_at",
)

#: Batch identity columns of ``api_simulation_batches``.
BATCH_COLUMNS: tuple[str, ...] = (
    "batch_id",
    "principal_id",
    "status",
    "concurrency",
    "name",
    "total_count",
    "completed_count",
    "failed_count",
    "cancelled_count",
    "finished_at",
    "created_at",
    "updated_at",
)


_RESULT_INSERT = (
    "INSERT OR IGNORE INTO api_simulation_results "
    "(run_id, principal_id, origin_kind, origin_id, job_id, batch_id, "
    "session_id, strategy_id, strategy_version, strategy_label, symbols, "
    "timeframe, measurement_start, measurement_end, status, result_ref, "
    "report_id, report_ref, artifact_manifest_ref, quality_status, "
    "evidence_class, created_at, completed_at, name, alias, description, tags, "
    "run_reason, archive_state, updated_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_SESSION_INSERT = (
    "INSERT OR IGNORE INTO api_simulation_sessions "
    "(session_id, principal_id, run_id, mode, evidence_class, status, cursor, "
    "tick_count, completed, durable, state_hash, closed_at, created_at, "
    "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_BATCH_INSERT = (
    "INSERT OR IGNORE INTO api_simulation_batches "
    "(batch_id, principal_id, status, concurrency, name, total_count, "
    "completed_count, failed_count, cancelled_count, finished_at, created_at, "
    "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_BATCH_ITEM_INSERT = (
    "INSERT OR IGNORE INTO api_simulation_batch_items "
    "(batch_id, position, run_id, job_id, status, error, created_at, "
    "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)


def _execute_write(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> _TransactionResult:
    """Execute one bounded Simulation Workbench write plan through Data.

    Args:
        statements: Parameterized write statements.
        parameter_sets: Bound parameters matching the statements.
        request_id: Canonical operation request identifier.
        max_rows: Maximum affected rows per statement.

    Returns:
        Normalized committed transaction result.

    Raises:
        SimulationWorkbenchPersistenceError: If Data cannot confirm the write.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=statements,
                parameter_sets=parameter_sets,
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise SimulationWorkbenchPersistenceError
    return cast("_TransactionResult", response.data)


def _require_keys(values: Mapping[str, object], columns: tuple[str, ...]) -> None:
    """Require one exact column-value mapping.

    Args:
        values: Caller-supplied column values.
        columns: Expected column names.

    Raises:
        SimulationWorkbenchPersistenceError: If keys are missing or unknown.
    """
    if set(values) != set(columns):
        raise SimulationWorkbenchPersistenceError


def create_simulation_result_record(
    values: Mapping[str, object],
    *,
    request_id: str,
) -> int:
    """Create one catalogue run row identity-idempotently.

    Args:
        values: Exact ``RESULT_COLUMNS`` column values.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count (zero when the identity already exists).

    Raises:
        SimulationWorkbenchPersistenceError: If keys or the store disagree.
    """
    _require_keys(values, RESULT_COLUMNS)
    result = _execute_write(
        (_RESULT_INSERT,),
        (tuple(values[column] for column in RESULT_COLUMNS),),
        request_id=request_id,
    )
    logger.info(
        "Created Simulation workbench catalogue row (run %s, rows %s)",
        values["run_id"],
        result.affected_rows,
    )
    return result.affected_rows


def create_simulation_session_record(
    values: Mapping[str, object],
    *,
    request_id: str,
) -> int:
    """Create one live-session catalogue row identity-idempotently.

    Args:
        values: Exact ``SESSION_COLUMNS`` column values.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count (zero when the identity already exists).

    Raises:
        SimulationWorkbenchPersistenceError: If keys or the store disagree.
    """
    _require_keys(values, SESSION_COLUMNS)
    result = _execute_write(
        (_SESSION_INSERT,),
        (tuple(values[column] for column in SESSION_COLUMNS),),
        request_id=request_id,
    )
    logger.info(
        "Created Simulation workbench session row (session %s, rows %s)",
        values["session_id"],
        result.affected_rows,
    )
    return result.affected_rows


def create_simulation_batch_record(
    values: Mapping[str, object],
    *,
    request_id: str,
) -> int:
    """Create one batch catalogue row identity-idempotently.

    Args:
        values: Exact ``BATCH_COLUMNS`` column values.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count (zero when the identity already exists).

    Raises:
        SimulationWorkbenchPersistenceError: If keys or the store disagree.
    """
    _require_keys(values, BATCH_COLUMNS)
    result = _execute_write(
        (_BATCH_INSERT,),
        (tuple(values[column] for column in BATCH_COLUMNS),),
        request_id=request_id,
    )
    logger.info(
        "Created Simulation workbench batch row (batch %s, rows %s)",
        values["batch_id"],
        result.affected_rows,
    )
    return result.affected_rows


def create_simulation_batch_item_records(
    rows: Sequence[Mapping[str, object]],
    *,
    request_id: str,
) -> int:
    """Create ordered batch membership rows identity-idempotently.

    Args:
        rows: Sequenced rows with keys ``batch_id``, ``position``, ``run_id``,
            ``job_id``, ``status``, ``error``, ``created_at``, ``updated_at``.
        request_id: Canonical operation request identifier.

    Returns:
        Total affected row count.

    Raises:
        SimulationWorkbenchPersistenceError: If keys or the store disagree.
    """
    columns = (
        "batch_id",
        "position",
        "run_id",
        "job_id",
        "status",
        "error",
        "created_at",
        "updated_at",
    )
    for row in rows:
        _require_keys(row, columns)
    result = _execute_write(
        tuple(_BATCH_ITEM_INSERT for _ in rows),
        tuple(tuple(row[column] for column in columns) for row in rows),
        request_id=request_id,
        max_rows=len(rows) or 1,
    )
    logger.info(
        "Created Simulation workbench batch item rows (count %d, rows %s)",
        len(rows),
        result.affected_rows,
    )
    return result.affected_rows


__all__ = (
    "BATCH_COLUMNS",
    "RESULT_COLUMNS",
    "SESSION_COLUMNS",
    "SimulationWorkbenchPersistenceError",
    "create_simulation_batch_item_records",
    "create_simulation_batch_record",
    "create_simulation_result_record",
    "create_simulation_session_record",
)
