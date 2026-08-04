"""Update operations for Indicators-owned records."""

from __future__ import annotations

from typing import Any

from app.services.data import build_transaction_request, execute_transaction
from app.utils import get_logger

logger = get_logger(__name__)

_UPDATE_STATE = """
UPDATE indicator_materializations
SET state = ?, built_at = ?, row_count = ?, updated_at = ?
WHERE materialization_id = ?
""".strip()

_INVALIDATE_FOR_SOURCE = """
UPDATE indicator_materializations
SET state = 'invalidated', updated_at = ?
WHERE source_dataset_id = ? AND source_data_hash <> ?
""".strip()


def _execute(
    statement: str, parameters: tuple[Any, ...], *, request_id: str, max_rows: int
) -> object:
    """Execute one bounded Indicators update.

    Args:
        statement: Single SQL statement.
        parameters: Ordered parameter values.
        request_id: Caller trace identity.
        max_rows: Bounded affected-row ceiling.

    Returns:
        Data-owned transaction result.
    """
    return execute_transaction(
        build_transaction_request(
            statements=(statement,),
            parameter_sets=(parameters,),
            max_rows=max_rows,
            request_id=request_id,
        )
    )


def update_indicator_materialization_state(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Advance one materialisation through its build lifecycle.

    Args:
        parameters: Ordered state, build time, row count, update time, identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Updating one Indicators materialisation state")
    return _execute(_UPDATE_STATE, parameters, request_id=request_id, max_rows=1)


def invalidate_indicator_materializations_for_source(
    updated_at: str,
    source_dataset_id: str,
    current_source_hash: str,
    *,
    request_id: str,
) -> object:
    """Invalidate every materialisation built from superseded source bytes.

    Compares the recorded ``source_data_hash`` against the source dataset's
    current hash. A repair that rewrote the underlying bars changes that hash,
    so the derived series is provably stale rather than silently serving values
    computed from data that no longer exists.

    Args:
        updated_at: Update timestamp.
        source_dataset_id: Source dataset identity.
        current_source_hash: Current hash of the source dataset.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Invalidating Indicators materialisations for a changed source")
    return _execute(
        _INVALIDATE_FOR_SOURCE,
        (updated_at, source_dataset_id, current_source_hash),
        request_id=request_id,
        max_rows=10_000,
    )
