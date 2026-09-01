"""Update operations for Simulation Workbench-owned catalogue records.

Every statement is static and fully parameterized; mutable transitions are
expressed as purpose-built verbs rather than dynamic column lists so no
SQL text is ever assembled from caller input.
"""

from __future__ import annotations

from app.composition.logging import get_logger
from app.services.api.widgets.simulator.persistence.create import (
    _execute_write,
)

logger = get_logger(__name__)


def transition_simulation_result_completion(
    run_id: str,
    principal_id: str,
    *,
    completed_at: str,
    updated_at: str,
    result_ref: str | None,
    report_id: str | None,
    report_ref: str | None,
    artifact_manifest_ref: str | None,
    quality_status: str | None,
    request_id: str,
) -> int:
    """Complete one queued or running run, recording its evidence refs.

    Args:
        run_id: Canonical run identity.
        principal_id: Authenticated principal.
        completed_at: UTC completion timestamp.
        updated_at: UTC transition timestamp.
        result_ref: Immutable Simulation result reference.
        report_id: Attached Analytics report identity.
        report_ref: Attached Analytics report artifact reference.
        artifact_manifest_ref: Canonical manifest reference.
        quality_status: Owner quality status.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count (zero on unknown, foreign, or terminal runs).
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_results SET status = 'completed', "
            "completed_at = ?, result_ref = ?, report_id = ?, report_ref = ?, "
            "artifact_manifest_ref = ?, quality_status = ?, updated_at = ? "
            "WHERE run_id = ? AND principal_id = ? "
            "AND status IN ('queued', 'running')",
        ),
        (
            (
                completed_at,
                result_ref,
                report_id,
                report_ref,
                artifact_manifest_ref,
                quality_status,
                updated_at,
                run_id,
                principal_id,
            ),
        ),
        request_id=request_id,
    )
    logger.info(
        "Completed Simulation workbench run %s (rows %s)",
        run_id,
        result.affected_rows,
    )
    return result.affected_rows


def annotate_simulation_result_record(
    run_id: str,
    principal_id: str,
    *,
    name: str | None,
    alias: str | None,
    description: str | None,
    tags: str,
    run_reason: str | None,
    updated_at: str,
    request_id: str,
) -> int:
    """Apply one full principal-owned annotation set to a run row.

    Args:
        run_id: Canonical run identity.
        principal_id: Authenticated principal.
        name: Annotated display name.
        alias: Annotated alias.
        description: Annotated description.
        tags: Serialized bounded tag list.
        run_reason: Annotated run reason.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count.
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_results SET name = ?, alias = ?, "
            "description = ?, tags = ?, run_reason = ?, updated_at = ? "
            "WHERE run_id = ? AND principal_id = ?",
        ),
        (
            (
                name,
                alias,
                description,
                tags,
                run_reason,
                updated_at,
                run_id,
                principal_id,
            ),
        ),
        request_id=request_id,
    )
    logger.info(
        "Annotated Simulation workbench run %s (rows %s)",
        run_id,
        result.affected_rows,
    )
    return result.affected_rows


def archive_simulation_result_record(
    run_id: str,
    principal_id: str,
    *,
    updated_at: str,
    request_id: str,
) -> int:
    """Archive one run's catalogue metadata without deleting evidence.

    Args:
        run_id: Canonical run identity.
        principal_id: Authenticated principal.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count.
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_results SET archive_state = 'archived', "
            "updated_at = ? WHERE run_id = ? AND principal_id = ?",
        ),
        ((updated_at, run_id, principal_id),),
        request_id=request_id,
    )
    logger.info(
        "Archived Simulation workbench run %s (rows %s)",
        run_id,
        result.affected_rows,
    )
    return result.affected_rows


def update_simulation_session_record(
    session_id: str,
    principal_id: str,
    *,
    status: str,
    cursor: int,
    tick_count: int,
    completed: int,
    state_hash: str | None,
    closed_at: str | None,
    updated_at: str,
    request_id: str,
) -> int:
    """Write one full resumable-session state snapshot.

    Args:
        session_id: Canonical session identity.
        principal_id: Authenticated principal.
        status: Current session status.
        cursor: Server cursor position.
        tick_count: Total observed ticks.
        completed: Whether the session reached its dataset end.
        state_hash: Current state digest.
        closed_at: UTC close timestamp when closed.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count.
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_sessions SET status = ?, cursor = ?, "
            "tick_count = ?, completed = ?, state_hash = ?, closed_at = ?, "
            "updated_at = ? WHERE session_id = ? AND principal_id = ?",
        ),
        (
            (
                status,
                cursor,
                tick_count,
                completed,
                state_hash,
                closed_at,
                updated_at,
                session_id,
                principal_id,
            ),
        ),
        request_id=request_id,
    )
    logger.info(
        "Updated Simulation workbench session %s (rows %s)",
        session_id,
        result.affected_rows,
    )
    return result.affected_rows


def update_simulation_batch_record(
    batch_id: str,
    principal_id: str,
    *,
    status: str,
    completed_count: int,
    failed_count: int,
    cancelled_count: int,
    finished_at: str | None,
    updated_at: str,
    request_id: str,
) -> int:
    """Write one full batch lifecycle snapshot.

    Args:
        batch_id: Canonical batch identity.
        principal_id: Authenticated principal.
        status: Current batch status.
        completed_count: Completed item count.
        failed_count: Failed item count.
        cancelled_count: Cancelled item count.
        finished_at: UTC finish timestamp when terminal.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count.
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_batches SET status = ?, "
            "completed_count = ?, failed_count = ?, cancelled_count = ?, "
            "finished_at = ?, updated_at = ? "
            "WHERE batch_id = ? AND principal_id = ?",
        ),
        (
            (
                status,
                completed_count,
                failed_count,
                cancelled_count,
                finished_at,
                updated_at,
                batch_id,
                principal_id,
            ),
        ),
        request_id=request_id,
    )
    logger.info(
        "Updated Simulation workbench batch %s (rows %s)",
        batch_id,
        result.affected_rows,
    )
    return result.affected_rows


def cancel_simulation_batch_item_records(
    batch_id: str,
    *,
    reason: str,
    updated_at: str,
    request_id: str,
) -> int:
    """Cancel every non-terminal item of one batch exactly once.

    Args:
        batch_id: Canonical batch identity.
        reason: Safe cancellation reason recorded on each item.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count.
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_batch_items SET status = 'cancelled', "
            "error = ?, updated_at = ? WHERE batch_id = ? "
            "AND status IN ('queued', 'running')",
        ),
        ((reason, updated_at, batch_id),),
        request_id=request_id,
        max_rows=100,
    )
    logger.info(
        "Cancelled Simulation workbench batch items for %s (rows %s)",
        batch_id,
        result.affected_rows,
    )
    return result.affected_rows


def retry_simulation_batch_item_record(
    batch_id: str,
    position: int,
    *,
    job_id: str,
    updated_at: str,
    request_id: str,
) -> int:
    """Requeue exactly one failed batch item under its new job identity.

    Args:
        batch_id: Canonical batch identity.
        position: Ordered item position.
        job_id: New job identity produced by the resubmission.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count (zero unless the item was failed).
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_batch_items SET job_id = ?, "
            "status = 'queued', error = NULL, updated_at = ? "
            "WHERE batch_id = ? AND position = ? AND status = 'failed'",
        ),
        ((job_id, updated_at, batch_id, position),),
        request_id=request_id,
    )
    logger.info(
        "Retried Simulation workbench batch item %s/%d (rows %s)",
        batch_id,
        position,
        result.affected_rows,
    )
    return result.affected_rows


def transition_simulation_batch_item_record(
    batch_id: str,
    position: int,
    *,
    status: str,
    run_id: str | None,
    error: str | None,
    updated_at: str,
    request_id: str,
) -> int:
    """Move exactly one non-terminal batch item to its observed outcome.

    Args:
        batch_id: Canonical batch identity.
        position: Ordered item position.
        status: Observed item status (``running``, ``completed``, or
            ``failed``).
        run_id: Canonical run identity once the item produced one.
        error: Safe failure detail when the item failed.
        updated_at: UTC transition timestamp.
        request_id: Canonical operation request identifier.

    Returns:
        Affected row count (zero once the item is already terminal).
    """
    result = _execute_write(
        (
            "UPDATE api_simulation_batch_items SET status = ?, "
            "run_id = COALESCE(?, run_id), error = ?, updated_at = ? "
            "WHERE batch_id = ? AND position = ? "
            "AND status IN ('queued', 'running')",
        ),
        ((status, run_id, error, updated_at, batch_id, position),),
        request_id=request_id,
    )
    logger.info(
        "Transitioned Simulation workbench batch item %s/%d to %s (rows %s)",
        batch_id,
        position,
        status,
        result.affected_rows,
    )
    return result.affected_rows


__all__ = (
    "annotate_simulation_result_record",
    "archive_simulation_result_record",
    "cancel_simulation_batch_item_records",
    "retry_simulation_batch_item_record",
    "transition_simulation_batch_item_record",
    "transition_simulation_result_completion",
    "update_simulation_batch_record",
    "update_simulation_session_record",
)
