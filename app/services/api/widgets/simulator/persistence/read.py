"""Read operations for Simulation Workbench-owned catalogue records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

from app.composition.logging import get_logger
from app.services.api.widgets.simulator.persistence.create import (
    SimulationWorkbenchPersistenceError,
)
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Required transaction-result surface."""

    rows: tuple[Mapping[str, object], ...]


_RESULT_SELECT = (
    "SELECT run_id, principal_id, origin_kind, origin_id, job_id, batch_id, "
    "session_id, strategy_id, strategy_version, strategy_label, symbols, "
    "timeframe, measurement_start, measurement_end, status, result_ref, "
    "report_id, report_ref, artifact_manifest_ref, quality_status, "
    "evidence_class, created_at, completed_at, name, alias, description, tags, "
    "run_reason, archive_state, updated_at FROM api_simulation_results"
)

_SESSION_SELECT = (
    "SELECT session_id, principal_id, run_id, mode, evidence_class, status, "
    "cursor, tick_count, completed, durable, state_hash, closed_at, "
    "created_at, updated_at FROM api_simulation_sessions"
)

_BATCH_SELECT = (
    "SELECT batch_id, principal_id, status, concurrency, name, total_count, "
    "completed_count, failed_count, cancelled_count, finished_at, created_at, "
    "updated_at FROM api_simulation_batches"
)

_BATCH_ITEM_SELECT = (
    "SELECT batch_id, position, run_id, job_id, status, error, created_at, "
    "updated_at FROM api_simulation_batch_items"
)


def _read_rows(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> tuple[Mapping[str, object], ...]:
    """Execute one bounded principal-scoped read through Data.

    Args:
        statement: Parameterized read statement.
        parameters: Bound parameters.
        request_id: Canonical operation request identifier.
        max_rows: Maximum returned rows.

    Returns:
        Normalized result rows.

    Raises:
        SimulationWorkbenchPersistenceError: If Data cannot confirm the read.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise SimulationWorkbenchPersistenceError
    return tuple(cast("_TransactionResult", response.data).rows)


def read_simulation_result_record(
    run_id: str,
    principal_id: str,
    *,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Read one principal-owned catalogue run row.

    Args:
        run_id: Canonical run identity.
        principal_id: Authenticated principal.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized row.

    Raises:
        SimulationWorkbenchPersistenceError: If the store cannot confirm.
    """
    logger.debug("Reading Simulation workbench run %s", run_id)
    return _read_rows(
        f"{_RESULT_SELECT} WHERE run_id = ? AND principal_id = ?",
        (run_id, principal_id),
        request_id=request_id,
    )


def read_simulation_results_page(
    principal_id: str,
    *,
    limit: int,
    offset: int,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Read one descending catalogue page for a principal.

    Args:
        principal_id: Authenticated principal.
        limit: Page size.
        offset: Page offset.
        request_id: Canonical operation request identifier.

    Returns:
        Normalized rows ordered by ``(created_at, run_id)`` descending.

    Raises:
        SimulationWorkbenchPersistenceError: If the store cannot confirm.
    """
    logger.debug("Reading Simulation workbench page (limit %d)", limit)
    return _read_rows(
        f"{_RESULT_SELECT} WHERE principal_id = ? "
        "ORDER BY created_at DESC, run_id DESC LIMIT ? OFFSET ?",
        (principal_id, limit, offset),
        request_id=request_id,
        max_rows=limit,
    )


def read_simulation_session_record(
    session_id: str,
    principal_id: str,
    *,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Read one principal-owned live-session row.

    Args:
        session_id: Canonical session identity.
        principal_id: Authenticated principal.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized row.

    Raises:
        SimulationWorkbenchPersistenceError: If the store cannot confirm.
    """
    logger.debug("Reading Simulation workbench session %s", session_id)
    return _read_rows(
        f"{_SESSION_SELECT} WHERE session_id = ? AND principal_id = ?",
        (session_id, principal_id),
        request_id=request_id,
    )


def read_simulation_sessions(
    principal_id: str,
    *,
    request_id: str,
    limit: int = 200,
) -> tuple[Mapping[str, object], ...]:
    """Read a principal's sessions, newest first.

    Args:
        principal_id: Authenticated principal.
        request_id: Canonical operation request identifier.
        limit: Maximum returned rows.

    Returns:
        Normalized session rows.

    Raises:
        SimulationWorkbenchPersistenceError: If the store cannot confirm.
    """
    logger.debug("Reading Simulation workbench sessions for principal")
    return _read_rows(
        f"{_SESSION_SELECT} WHERE principal_id = ? ORDER BY created_at DESC LIMIT ?",
        (principal_id, limit),
        request_id=request_id,
        max_rows=limit,
    )


def read_simulation_batch_record(
    batch_id: str,
    principal_id: str,
    *,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Read one principal-owned batch row.

    Args:
        batch_id: Canonical batch identity.
        principal_id: Authenticated principal.
        request_id: Canonical operation request identifier.

    Returns:
        Zero or one normalized row.

    Raises:
        SimulationWorkbenchPersistenceError: If the store cannot confirm.
    """
    logger.debug("Reading Simulation workbench batch %s", batch_id)
    return _read_rows(
        f"{_BATCH_SELECT} WHERE batch_id = ? AND principal_id = ?",
        (batch_id, principal_id),
        request_id=request_id,
    )


def read_simulation_batch_items(
    batch_id: str,
    principal_id: str,
    *,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Read one owned batch's ordered membership rows.

    Args:
        batch_id: Canonical batch identity.
        principal_id: Authenticated principal.
        request_id: Canonical operation request identifier.

    Returns:
        Normalized item rows ordered by position.

    Raises:
        SimulationWorkbenchPersistenceError: If the store cannot confirm.
    """
    logger.debug("Reading Simulation workbench batch items for %s", batch_id)
    return _read_rows(
        "SELECT item.batch_id, item.position, item.run_id, item.job_id, "
        "item.status, item.error, item.created_at, item.updated_at "
        "FROM api_simulation_batch_items item "
        "JOIN api_simulation_batches batch ON batch.batch_id = item.batch_id "
        "WHERE item.batch_id = ? AND batch.principal_id = ? "
        "ORDER BY item.position",
        (batch_id, principal_id),
        request_id=request_id,
        max_rows=100,
    )


__all__ = (
    "read_simulation_batch_items",
    "read_simulation_batch_record",
    "read_simulation_result_record",
    "read_simulation_results_page",
    "read_simulation_session_record",
    "read_simulation_sessions",
)
