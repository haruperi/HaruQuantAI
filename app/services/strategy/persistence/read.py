"""Read operations for Strategy-owned database records."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.services.strategy.contracts.responses import unwrap_data_response
from app.utils import get_logger

logger = get_logger(__name__)


def _read_rows(
    statement: str,
    parameters: tuple[object, ...],
    *,
    max_rows: int,
    request_id: str,
    operation: str,
) -> tuple[Mapping[str, object], ...]:
    """Execute one bounded Strategy read and return normalized rows.

    Args:
        statement: Parameterized SQL read statement.
        parameters: Bound statement parameters.
        max_rows: Maximum accepted result rows.
        request_id: Request trace identifier.
        operation: Safe dependency-operation label.

    Returns:
        Ordered normalized database rows.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    result = unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(statement,),
                    parameter_sets=(parameters,),
                    max_rows=max_rows,
                ),
                request_id=request_id,
            )
        ),
        operation=operation,
    )
    return tuple(result.rows)


def read_strategy_mutation_record(
    command_id: str, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one Strategy mutation by idempotency command identifier.

    Args:
        command_id: Stable caller command identifier.
        request_id: Request trace identifier.

    Returns:
        Zero or one normalized mutation rows.
    """
    logger.debug("Reading Strategy mutation persistence record")
    return _read_rows(
        "SELECT mutation_json FROM strategy_mutations WHERE command_id = ?",
        (command_id,),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_mutation_lookup",
    )


def read_strategy_policy_record(
    strategy_id: str,
    strategy_version: str,
    request_id: str,
) -> tuple[Mapping[str, object], ...]:
    """Read the policy stored with one exact Strategy version.

    Args:
        strategy_id: Exact Strategy identifier.
        strategy_version: Exact immutable version.
        request_id: Request trace identifier.

    Returns:
        Zero or one normalized policy rows.
    """
    logger.debug("Reading Strategy policy persistence record")
    return _read_rows(
        "SELECT policy_json FROM strategy_versions WHERE strategy_id = ? "
        "AND strategy_version = ?",
        (strategy_id, strategy_version),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_policy_lookup",
    )


def read_strategy_version_records(
    strategy_id: str | None,
    request_id: str,
    *,
    include_trace_ids: bool = False,
) -> tuple[Mapping[str, object], ...]:
    """Read ordered Strategy registry records.

    Args:
        strategy_id: Optional exact Strategy identifier.
        request_id: Request trace identifier.
        include_trace_ids: Whether stored request and correlation IDs are required.

    Returns:
        Ordered normalized registry rows.
    """
    logger.debug("Reading Strategy version persistence records")
    columns = "manifest_json, lifecycle_status, policy_json, record_hash"
    if include_trace_ids:
        columns = f"{columns}, request_id, correlation_id"
    statement = f"SELECT {columns} FROM strategy_versions"  # noqa: S608
    parameters: tuple[object, ...] = ()
    if strategy_id is not None:
        statement = f"{statement} WHERE strategy_id = ?"
        parameters = (strategy_id,)
    statement = f"{statement} ORDER BY strategy_id, strategy_version"
    return _read_rows(
        statement,
        parameters,
        max_rows=1_000,
        request_id=request_id,
        operation="data.execute_transaction.strategy_registry",
    )


def read_strategy_checkpoint_record(
    checkpoint_id: str, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one Strategy checkpoint by immutable identifier.

    Args:
        checkpoint_id: Immutable checkpoint identifier.
        request_id: Request trace identifier.

    Returns:
        Zero or one normalized checkpoint rows.
    """
    logger.debug("Reading Strategy checkpoint persistence record")
    return _read_rows(
        "SELECT checkpoint_json FROM strategy_checkpoints WHERE checkpoint_id = ?",
        (checkpoint_id,),
        max_rows=1,
        request_id=request_id,
        operation="data.execute_transaction.strategy_checkpoint_read",
    )


__all__ = [
    "read_strategy_checkpoint_record",
    "read_strategy_mutation_record",
    "read_strategy_policy_record",
    "read_strategy_version_records",
]
