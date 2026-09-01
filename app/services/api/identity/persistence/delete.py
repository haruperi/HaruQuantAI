"""Delete operations for Identity-owned database records."""

from __future__ import annotations

from typing import Protocol, cast

from app.composition.logging import get_logger
from app.services.api.identity.persistence import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Fields consumed from Data's normalized transaction result."""

    affected_rows: int


def _execute_delete(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
) -> None:
    """Execute one bounded API delete through Data.

    Args:
        statement: Parameterized delete statement.
        parameters: Bound statement parameters.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
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
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")


def _execute_delete_many(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
) -> int:
    """Execute several bounded API delete statements as one transaction.

    Args:
        statements: Parameterized delete statements.
        parameter_sets: Bound parameters matching the statements.
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows across every statement.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=statements,
                parameter_sets=parameter_sets,
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    result = cast("_TransactionResult", response.data)
    return int(result.affected_rows)


def delete_auth_failure_record(username_hash: str, *, request_id: str) -> None:
    """Delete one authentication-failure window.

    Args:
        username_hash: Non-reversible normalized username digest.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Deleting API authentication failure persistence record")
    _execute_delete(
        "DELETE FROM api_auth_failures WHERE username_hash = ?",
        (username_hash,),
        request_id=request_id,
    )


def delete_idempotency_record(scope_key: str, *, request_id: str) -> None:
    """Delete one expired HTTP idempotency reservation.

    Args:
        scope_key: Canonical request-scope digest.
        request_id: Canonical operation request identifier.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Deleting expired API idempotency persistence record")
    _execute_delete(
        "DELETE FROM api_idempotency WHERE scope_key = ?",
        (scope_key,),
        request_id=request_id,
    )


__all__ = [
    "delete_auth_failure_record",
    "delete_idempotency_record",
]
