"""Delete operations for Indicators-owned records.

Unlike most domains, Indicators **does** permit deletion. A materialisation is
derived data: it is deterministically recomputable from bars plus the
definition's ``formula_hash``, so purging one destroys no evidence. Definitions
and parameter sets are never deleted — they are the provenance a materialisation
points back to.
"""

from __future__ import annotations

from typing import Any

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)

_DELETE_MATERIALIZATION = """
DELETE FROM indicator_materializations WHERE materialization_id = ?
""".strip()

_DELETE_STALE = """
DELETE FROM indicator_materializations
WHERE state IN ('stale', 'invalidated') AND covered_to_utc < ?
""".strip()


def _execute(
    statement: str, parameters: tuple[Any, ...], *, request_id: str, max_rows: int
) -> object:
    """Execute one bounded Indicators delete.

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
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )


def delete_indicator_materialization_record(
    materialization_id: str, *, request_id: str
) -> object:
    """Purge one materialisation reference.

    Deleting the catalogue row does not delete the artifact; artifact removal is
    a separate Data-owned operation.

    Args:
        materialization_id: Materialisation identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Purging one Indicators materialisation reference")
    return _execute(
        _DELETE_MATERIALIZATION,
        (materialization_id,),
        request_id=request_id,
        max_rows=1,
    )


def delete_stale_indicator_materializations(
    older_than_utc: int, *, request_id: str
) -> object:
    """Purge stale or invalidated materialisations older than a cutoff.

    Args:
        older_than_utc: Exclusive upper bound on covered range end.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Purging stale Indicators materialisations")
    return _execute(
        _DELETE_STALE, (older_than_utc,), request_id=request_id, max_rows=10_000
    )
