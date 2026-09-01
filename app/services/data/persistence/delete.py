"""Delete operations for Data-owned database records."""

from __future__ import annotations

from app.composition.logging import get_logger
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
    TransactionResult,
)
from app.services.data.persistence.transactions import _execute_transaction_raw

logger = get_logger(__name__)


def delete_cache_records(
    keys: tuple[str, ...], *, request_id: str
) -> TransactionResult:
    """Delete a bounded explicit set of cache records.

    Args:
        keys: The ``keys`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.
    """
    placeholders = ",".join("?" for _ in keys)
    statement = f"DELETE FROM data_cache WHERE key IN ({placeholders})"  # noqa: S608
    logger.debug("Deleting Data cache persistence records")
    return _execute_transaction_raw(
        TransactionRequest(
            plan=StatementPlan(
                statements=(statement,),
                parameter_sets=(keys,),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )


__all__ = ["delete_cache_records"]
