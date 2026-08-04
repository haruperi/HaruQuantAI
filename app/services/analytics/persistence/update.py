"""Update operations for Analytics-owned derived records."""

from __future__ import annotations

from typing import Any

from app.services.data import build_transaction_request, execute_transaction
from app.utils import get_logger

logger = get_logger(__name__)

_MARK_CURVE_STALE = """
UPDATE analytics_equity_curves
SET state = 'stale', updated_at = ?
WHERE scope_level = ? AND scope_key = ? AND source_hash <> ?
""".strip()

_UPDATE_REPORT_STATE = """
UPDATE analytics_reports
SET state = ?, generated_at = ?, updated_at = ?
WHERE report_id = ?
""".strip()


def _execute(
    statement: str, parameters: tuple[Any, ...], *, request_id: str, max_rows: int
) -> object:
    """Execute one bounded Analytics statement.

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
            statements=(statement,),
            parameter_sets=(parameters,),
            max_rows=max_rows,
            request_id=request_id,
        )
    )


def mark_equity_curves_stale(
    updated_at: str,
    scope_level: str,
    scope_key: str,
    current_source_hash: str,
    *,
    request_id: str,
) -> object:
    """Mark equity curves whose inputs have changed as stale.

    Args:
        updated_at: Update timestamp.
        scope_level: Scope level.
        scope_key: Scope identity within the level.
        current_source_hash: Current hash of the underlying inputs.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Marking Analytics equity curves stale")
    return _execute(
        _MARK_CURVE_STALE,
        (updated_at, scope_level, scope_key, current_source_hash),
        request_id=request_id,
        max_rows=10_000,
    )


def update_report_state(parameters: tuple[Any, ...], *, request_id: str) -> object:
    """Advance one report through its generation lifecycle.

    Args:
        parameters: Ordered state, generation time, update time, identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.debug("Updating one Analytics report state")
    return _execute(_UPDATE_REPORT_STATE, parameters, request_id=request_id, max_rows=1)
