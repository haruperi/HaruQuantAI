"""Read operations for Indicators-owned records."""

from __future__ import annotations

from typing import Any

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)

_SELECT_DEFINITION = """
SELECT definition_id, indicator_code, version, category, formula_hash,
       lookback_bars, is_causal, state
FROM indicator_definitions
WHERE indicator_code = ? AND version = ?
""".strip()

_SELECT_MATERIALIZATION = """
SELECT materialization_id, dataset_id, source_data_hash, formula_hash,
       covered_from_utc, covered_to_utc, row_count, state
FROM indicator_materializations
WHERE definition_id = ? AND param_set_id = ? AND symbol_id = ? AND timeframe = ?
""".strip()

_SELECT_STALE = """
SELECT materialization_id, definition_id, param_set_id, symbol_id, timeframe
FROM indicator_materializations
WHERE state IN ('stale', 'invalidated')
ORDER BY materialization_id
""".strip()


def _execute(
    statement: str, parameters: tuple[Any, ...], *, request_id: str, max_rows: int
) -> object:
    """Execute one bounded Indicators read.

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
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )


def read_indicator_definition(
    indicator_code: str, version: str, *, request_id: str
) -> object:
    """Resolve one indicator definition by code and version.

    Args:
        indicator_code: Canonical indicator code.
        version: Definition version.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result carrying at most one row.
    """
    logger.debug("Reading one Indicators definition")
    return _execute(
        _SELECT_DEFINITION, (indicator_code, version), request_id=request_id, max_rows=1
    )


def read_indicator_materialization(
    definition_id: str,
    param_set_id: str,
    symbol_id: str,
    timeframe: str,
    *,
    request_id: str,
) -> object:
    """Resolve the materialisation for one definition, parameters, and series.

    Args:
        definition_id: Owning definition identity.
        param_set_id: Owning parameter-set identity.
        symbol_id: Canonical symbol identity.
        timeframe: Bar timeframe.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result carrying at most one row.
    """
    logger.debug("Reading one Indicators materialisation")
    return _execute(
        _SELECT_MATERIALIZATION,
        (definition_id, param_set_id, symbol_id, timeframe),
        request_id=request_id,
        max_rows=1,
    )


def read_stale_indicator_materializations(*, request_id: str, limit: int) -> object:
    """List materialisations whose inputs have changed since they were built.

    Args:
        request_id: Caller trace identity.
        limit: Bounded maximum row count.

    Returns:
        Data-owned transaction result carrying stale materialisation rows.
    """
    logger.debug("Listing stale Indicators materialisations")
    return _execute(_SELECT_STALE, (), request_id=request_id, max_rows=limit)
