"""Relational checkpoint updates for Optimization-owned state."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.optimization.contracts import OptimizationError
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.optimization.state.contracts import OptimizationCheckpoint


def upsert_checkpoint(
    checkpoint: OptimizationCheckpoint,
    *,
    request_id: str,
    correlation_id: str,
) -> None:
    """Create or advance one exact-identity checkpoint atomically.

    Args:
        checkpoint: Validated checkpoint evidence.
        request_id: Trace identifier.
        correlation_id: Cross-operation trace identifier.

    Raises:
        OptimizationError: If Data rejects the atomic update.
    """
    logger.info("Upserting Optimization checkpoint relationally")
    timestamp = checkpoint.created_at.isoformat()
    statement = """INSERT INTO optimization_checkpoints (
        search_id, schema_version, reproducibility_hash,
        completed_candidate_position, checkpoint_json, created_at, updated_at,
        request_id, correlation_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(search_id) DO UPDATE SET
        completed_candidate_position = excluded.completed_candidate_position,
        checkpoint_json = excluded.checkpoint_json,
        updated_at = excluded.updated_at,
        request_id = excluded.request_id,
        correlation_id = excluded.correlation_id
    WHERE optimization_checkpoints.schema_version = excluded.schema_version
      AND optimization_checkpoints.reproducibility_hash =
          excluded.reproducibility_hash"""
    parameters = (
        checkpoint.search_id,
        checkpoint.schema_version,
        checkpoint.reproducibility_hash,
        checkpoint.completed_candidate_position,
        canonical_json(checkpoint.model_dump(mode="json"), max_items=None),
        timestamp,
        timestamp,
        request_id,
        correlation_id,
    )
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(cast("tuple[Any, ...]", parameters),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise OptimizationError("OPT_PERSISTENCE_FAILED", "CHECKPOINT_WRITE_FAILED")
    if cast("Any", response.data).affected_rows != 1:
        raise OptimizationError("OPT_STATE_CONFLICT", "CHECKPOINT_IDENTITY_MISMATCH")


__all__: list[str] = []
