"""Update operations for Watchlists-owned records."""

from typing import Final, Protocol, cast

from app.services.api.identity import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)

_ITEM_WITH_ASSET_CLASS_LEN: Final = 4


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
    items: tuple[tuple[str, str, int, str] | tuple[str, str, int], ...],
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
        "(watchlist_id, source_id, symbol, sort_order, asset_class, created_at) "
        "SELECT ?, ?, ?, ?, ?, ? WHERE EXISTS "
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
                item[0],
                item[1],
                item[2],
                item[3] if len(item) >= _ITEM_WITH_ASSET_CLASS_LEN else "",
                updated_at,
                watchlist_id,
                account_id,
            )
            for item in items
        ),
        (updated_at, watchlist_id, account_id),
    )
    return _execute_update_many(statements, parameter_sets, request_id=request_id)


__all__ = (
    "backfill_empty_item_asset_classes_record",
    "rename_watchlist_record",
    "reorder_watchlists_record",
    "replace_watchlist_items_record",
    "set_default_watchlist_record",
)


def backfill_empty_item_asset_classes_record(
    item_updates: tuple[tuple[str, str, str, str], ...],
    *,
    request_id: str,
) -> int:
    """Update empty asset_class columns in api_watchlist_items.

    Args:
        item_updates: Tuples of (asset_class, watchlist_id, source_id, symbol).
        request_id: Canonical operation request identifier.

    Returns:
        Number of affected rows.
    """
    if not item_updates:
        return 0
    logger.debug("Backfilling API watchlist item asset_class records")
    statement = (
        "UPDATE api_watchlist_items SET asset_class = ? "
        "WHERE watchlist_id = ? AND source_id = ? AND symbol = ? AND asset_class = ''"
    )
    statements = tuple(statement for _ in item_updates)
    parameter_sets = item_updates
    return _execute_update_many(statements, parameter_sets, request_id=request_id)
