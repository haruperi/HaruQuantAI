"""Read operations for temporary Brokers-owned operational records."""

from __future__ import annotations

from typing import Any

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)

_SELECT_ROUTE_RECOVERY = """
SELECT provider_code, account_ref_digest, environment, recovery_cursor,
       uncertainty, updated_at
FROM broker_route_recovery
WHERE route_ref = ?
""".strip()

_SELECT_EVENT_CHECKPOINT = """
SELECT source_cursor, source_sequence, event_digest, updated_at
FROM broker_event_checkpoints
WHERE provider_code = ? AND account_ref_digest = ? AND source_stream = ?
""".strip()


def _execute(
    statement: str, parameters: tuple[Any, ...], *, request_id: str, max_rows: int
) -> object:
    """Execute one bounded Brokers statement.

    Args:
        statement: Single SQL statement.
        parameters: Ordered parameter values.
        request_id: Caller trace identity.
        max_rows: Bounded row ceiling.

    Returns:
        Data-owned transaction result.
    """
    return execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )


def read_route_recovery(route_ref: str, *, request_id: str) -> object:
    """Read one authoritative route recovery cursor.

    Args:
        route_ref: Stable route reference.
        request_id: Caller trace identity.

    Returns:
        Data-owned result carrying at most one route row.
    """
    return _execute(
        _SELECT_ROUTE_RECOVERY, (route_ref,), request_id=request_id, max_rows=1
    )


def read_event_checkpoint(
    provider_code: str,
    account_ref_digest: str,
    source_stream: str,
    *,
    request_id: str,
) -> object:
    """Read one event deduplication checkpoint.

    Args:
        provider_code: Exact provider identity.
        account_ref_digest: Redacted account-reference digest.
        source_stream: Exact provider stream identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned result carrying at most one checkpoint row.
    """
    return _execute(
        _SELECT_EVENT_CHECKPOINT,
        (provider_code, account_ref_digest, source_stream),
        request_id=request_id,
        max_rows=1,
    )
