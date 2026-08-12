"""Update operations for Watchlists-owned records."""

from typing import Protocol, cast

from app.services.api.identity import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Required transaction-result surface."""

    affected_rows: int


def _execute_update_many(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
) -> int:
    """Execute one atomic Watchlists-owned update plan.

    Returns:
        Number of affected rows.

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
    return int(cast("_TransactionResult", response.data).affected_rows)


def _execute_update(
    statement: str, parameters: tuple[object, ...], *, request_id: str
) -> int:
    """Execute one Watchlists-owned update statement.

    Returns:
        Number of affected rows.
    """
    return _execute_update_many((statement,), (parameters,), request_id=request_id)


def rename_watchlist_record(
    *,
    watchlist_id: str,
    account_id: str,
    name: str,
    updated_at: str,
    request_id: str,
) -> int:
    """Rename one account-owned watchlist.

    Returns:
        Number of affected rows.
    """
    logger.debug("Renaming API watchlist persistence record")
    return _execute_update(
        "UPDATE api_watchlists SET name = ?, updated_at = ? "
        "WHERE watchlist_id = ? AND account_id = ?",
        (name, updated_at, watchlist_id, account_id),
        request_id=request_id,
    )


def reorder_watchlists_record(
    *,
    account_id: str,
    watchlist_id: str,
    sort_order: int,
    updated_at: str,
    request_id: str,
) -> int:
    """Reposition one account-owned watchlist.

    Returns:
        Number of affected rows.
    """
    logger.debug("Reordering API watchlist persistence record")
    return _execute_update(
        "UPDATE api_watchlists SET sort_order = ?, updated_at = ? "
        "WHERE watchlist_id = ? AND account_id = ?",
        (sort_order, updated_at, watchlist_id, account_id),
        request_id=request_id,
    )


def set_default_watchlist_record(
    *, account_id: str, watchlist_id: str, updated_at: str, request_id: str
) -> int:
    """Atomically move an account's default flag to one watchlist.

    Returns:
        Number of affected rows.
    """
    logger.debug("Updating API default-watchlist persistence assignment")
    return _execute_update_many(
        (
            "UPDATE api_watchlists SET is_default = 0, updated_at = ? "
            "WHERE account_id = ? AND is_default = 1 AND watchlist_id != ?",
            "UPDATE api_watchlists SET is_default = 1, updated_at = ? "
            "WHERE watchlist_id = ? AND account_id = ?",
        ),
        (
            (updated_at, account_id, watchlist_id),
            (updated_at, watchlist_id, account_id),
        ),
        request_id=request_id,
    )


def replace_watchlist_items_record(
    *,
    watchlist_id: str,
    account_id: str,
    items: tuple[tuple[str, str, int], ...],
    updated_at: str,
    request_id: str,
) -> int:
    """Atomically replace one account-owned watchlist's items.

    Returns:
        Number of affected rows.
    """
    logger.debug("Replacing API watchlist item persistence records")
    item_statement = (
        "INSERT INTO api_watchlist_items "
        "(watchlist_id, source_id, symbol, sort_order, created_at) "
        "SELECT ?, ?, ?, ?, ? WHERE EXISTS "
        "(SELECT 1 FROM api_watchlists WHERE watchlist_id = ? AND account_id = ?)"
    )
    statements = (
        "DELETE FROM api_watchlist_items WHERE watchlist_id = ? AND EXISTS "
        "(SELECT 1 FROM api_watchlists WHERE watchlist_id = ? AND account_id = ?)",
        *(item_statement for _ in items),
        "UPDATE api_watchlists SET updated_at = ? "
        "WHERE watchlist_id = ? AND account_id = ?",
    )
    parameter_sets = (
        (watchlist_id, watchlist_id, account_id),
        *(
            (
                watchlist_id,
                source_id,
                symbol,
                sort_order,
                updated_at,
                watchlist_id,
                account_id,
            )
            for source_id, symbol, sort_order in items
        ),
        (updated_at, watchlist_id, account_id),
    )
    return _execute_update_many(statements, parameter_sets, request_id=request_id)


__all__ = (
    "rename_watchlist_record",
    "reorder_watchlists_record",
    "replace_watchlist_items_record",
    "set_default_watchlist_record",
)
