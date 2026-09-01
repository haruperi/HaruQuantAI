"""Relational reads for Optimization-owned records."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.optimization.contracts import OptimizationError
from app.services.optimization.evidence import OptimizationResult
from app.services.optimization.state.contracts import OptimizationCheckpoint

logger = get_logger(__name__)


def _read_row(
    statement: str, parameters: tuple[object, ...], request_id: str
) -> Mapping[str, object] | None:
    """Execute one bounded read and return its first normalized row.

    Returns:
        First normalized row or ``None``.

    Raises:
        OptimizationError: If Data rejects the read.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise OptimizationError("OPT_PERSISTENCE_FAILED", "RELATIONAL_READ_FAILED")
    rows = cast("Any", response.data).rows
    return None if not rows else cast("Mapping[str, object]", rows[0])


def read_result(search_id: str, request_id: str) -> OptimizationResult | None:
    """Read one canonical Optimization result.

    Args:
        search_id: Canonical search identifier.
        request_id: Trace identifier for the Data transaction.

    Returns:
        Persisted result or ``None``.

    Raises:
        OptimizationError: If stored evidence is malformed or unavailable.
    """
    logger.info("Reading Optimization result from relational persistence")
    row = _read_row(
        "SELECT result_json FROM optimization_results WHERE search_id = ?",
        (search_id,),
        request_id,
    )
    if row is None:
        return None
    payload = row.get("result_json")
    if not isinstance(payload, str):
        raise OptimizationError("OPT_STATE_CONFLICT", "RESULT_PAYLOAD_INVALID")
    try:
        return OptimizationResult.model_validate_json(payload)
    except (TypeError, ValueError) as exc:
        raise OptimizationError("OPT_STATE_CONFLICT", "RESULT_PAYLOAD_INVALID") from exc


def read_checkpoint(search_id: str, request_id: str) -> OptimizationCheckpoint | None:
    """Read one canonical Optimization checkpoint.

    Args:
        search_id: Canonical search identifier.
        request_id: Trace identifier for the Data transaction.

    Returns:
        Persisted checkpoint or ``None``.

    Raises:
        OptimizationError: If stored evidence is malformed or unavailable.
    """
    logger.info("Reading Optimization checkpoint from relational persistence")
    row = _read_row(
        "SELECT checkpoint_json FROM optimization_checkpoints WHERE search_id = ?",
        (search_id,),
        request_id,
    )
    if row is None:
        return None
    payload = row.get("checkpoint_json")
    if not isinstance(payload, str):
        raise OptimizationError("OPT_STATE_CONFLICT", "CHECKPOINT_PAYLOAD_INVALID")
    try:
        return OptimizationCheckpoint.model_validate_json(payload)
    except (TypeError, ValueError) as exc:
        raise OptimizationError(
            "OPT_STATE_CONFLICT", "CHECKPOINT_PAYLOAD_INVALID"
        ) from exc


__all__: list[str] = []
