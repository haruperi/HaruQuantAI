"""Create operations for Watchlists-owned records."""

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


def _execute_create(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    request_id: str,
) -> int:
    """Execute one Watchlists-owned create transaction.

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


def create_watchlist_record(
    *,
    watchlist_id: str,
    account_id: str,
    name: str,
    is_default: bool,
    sort_order: int,
    created_at: str,
    request_id: str,
) -> int:
    """Create one watchlist row.

    Returns:
        Number of affected rows.
    """
    logger.debug("Creating API watchlist persistence record")
    statement = (
        "INSERT INTO api_watchlists "
        "(watchlist_id, account_id, name, is_default, sort_order, "
        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(account_id, name) DO NOTHING"
    )
    return _execute_create(
        (statement,),
        (
            (
                watchlist_id,
                account_id,
                name,
                int(is_default),
                sort_order,
                created_at,
                created_at,
            ),
        ),
        request_id=request_id,
    )


def create_watchlist_items(
    *,
    watchlist_id: str,
    items: tuple[tuple[str, str, int], ...],
    created_at: str,
    request_id: str,
) -> int:
    """Create one watchlist's ordered items atomically.

    Returns:
        Number of affected rows.
    """
    if not items:
        return 0
    logger.debug("Creating API watchlist item persistence records")
    statement = (
        "INSERT INTO api_watchlist_items "
        "(watchlist_id, source_id, symbol, sort_order, created_at) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(watchlist_id, source_id, symbol) DO NOTHING"
    )
    return _execute_create(
        tuple(statement for _ in items),
        tuple(
            (watchlist_id, source_id, symbol, sort_order, created_at)
            for source_id, symbol, sort_order in items
        ),
        request_id=request_id,
    )


__all__ = ("create_watchlist_items", "create_watchlist_record")
