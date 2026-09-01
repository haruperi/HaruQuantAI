"""Delete operations for Watchlists-owned records."""

from typing import Protocol, cast

from app.composition.logging import get_logger
from app.services.api.identity import IdentityError
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Required transaction-result surface."""

    affected_rows: int


def delete_watchlist_record(
    *, watchlist_id: str, account_id: str, request_id: str
) -> int:
    """Delete one account-owned watchlist and its items atomically.

    Returns:
        Number of affected rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    logger.debug("Deleting API watchlist and item persistence records")
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(
                    "DELETE FROM api_watchlist_items WHERE watchlist_id = ? AND EXISTS "
                    "(SELECT 1 FROM api_watchlists WHERE watchlist_id = ? "
                    "AND account_id = ?)",
                    "DELETE FROM api_watchlists "
                    "WHERE watchlist_id = ? AND account_id = ?",
                ),
                parameter_sets=(
                    (watchlist_id, watchlist_id, account_id),
                    (watchlist_id, account_id),
                ),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    return int(cast("_TransactionResult", response.data).affected_rows)


__all__ = ("delete_watchlist_record",)
