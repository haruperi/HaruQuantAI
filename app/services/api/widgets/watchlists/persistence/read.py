"""Read operations for Watchlists-owned records."""

from collections.abc import Mapping
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

    rows: tuple[Mapping[str, object], ...]


def _read_rows(
    statement: str,
    parameters: tuple[object, ...],
    *,
    request_id: str,
    max_rows: int = 1,
) -> tuple[Mapping[str, object], ...]:
    """Execute one bounded Watchlists-owned read.

    Returns:
        Normalized result rows.

    Raises:
        IdentityError: If Data cannot confirm the transaction.
    """
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise IdentityError("IDENTITY_STORE_UNAVAILABLE")
    return tuple(cast("_TransactionResult", response.data).rows)


def read_watchlist_record(
    watchlist_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one watchlist by identifier.

    Returns:
        Zero or one normalized watchlist rows.
    """
    logger.debug("Reading API watchlist persistence record")
    return _read_rows(
        "SELECT watchlist_id, account_id, name, is_default, sort_order, "
        "created_at, updated_at FROM api_watchlists WHERE watchlist_id = ?",
        (watchlist_id,),
        request_id=request_id,
    )


def read_watchlists_for_account(
    account_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read an account's ordered watchlists.

    Returns:
        Normalized watchlist rows.
    """
    logger.debug("Reading API account watchlist persistence records")
    return _read_rows(
        "SELECT watchlist_id, account_id, name, is_default, sort_order, "
        "created_at, updated_at FROM api_watchlists WHERE account_id = ? "
        "ORDER BY sort_order, created_at",
        (account_id,),
        request_id=request_id,
        max_rows=200,
    )


def read_watchlist_items(
    watchlist_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one watchlist's ordered items.

    Returns:
        Normalized watchlist-item rows.
    """
    logger.debug("Reading API watchlist item persistence records")
    return _read_rows(
        "SELECT watchlist_id, source_id, symbol, sort_order, asset_class, "
        "created_at FROM api_watchlist_items WHERE watchlist_id = ? "
        "ORDER BY sort_order",
        (watchlist_id,),
        request_id=request_id,
        max_rows=1000,
    )


def read_watchlist_items_for_account(
    account_id: str, *, request_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read every ordered watchlist item owned by one account.

    Returns:
        Normalized watchlist-item rows.
    """
    logger.debug("Reading API account watchlist item persistence records")
    return _read_rows(
        "SELECT i.watchlist_id, i.source_id, i.symbol, i.sort_order, "
        "i.asset_class, i.created_at FROM api_watchlist_items AS i "
        "JOIN api_watchlists AS w ON w.watchlist_id = i.watchlist_id "
        "WHERE w.account_id = ? ORDER BY i.watchlist_id, i.sort_order",
        (account_id,),
        request_id=request_id,
        max_rows=5000,
    )


__all__ = (
    "read_watchlist_items",
    "read_watchlist_items_for_account",
    "read_watchlist_record",
    "read_watchlists_for_account",
)
