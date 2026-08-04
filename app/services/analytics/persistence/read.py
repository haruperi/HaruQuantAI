"""Read operations for Analytics-owned derived records."""

from __future__ import annotations

from typing import Any

from app.services.data import build_transaction_request, execute_transaction
from app.utils import get_logger

logger = get_logger(__name__)

_SELECT_METRIC_VALUE = """
SELECT value_id, value_decimal, sample_size, insufficient_sample,
       confidence_low_decimal, confidence_high_decimal, source_hash
FROM analytics_metric_values
WHERE metric_id = ? AND scope_level = ? AND scope_key = ?
  AND period_start_utc = ? AND period_end_utc = ?
""".strip()

_SELECT_STALE_VALUES = """
SELECT value_id, metric_id, scope_level, scope_key
FROM analytics_metric_values
WHERE source_hash <> ?
ORDER BY value_id
""".strip()

_SELECT_TRADES_FOR_STRATEGY = """
SELECT trade_id, net_pnl_decimal, r_multiple_decimal, mae_decimal,
       mfe_decimal, exit_reason, exit_at
FROM analytics_trade_analysis
WHERE strategy_version_id = ? AND exit_at >= ? AND exit_at <= ?
ORDER BY exit_at DESC
""".strip()

_SELECT_WORST_DRAWDOWNS = """
SELECT curve_id, scope_key, max_drawdown_percent_decimal, recovery_ts_utc
FROM analytics_equity_curves
WHERE scope_level = ? AND state = 'ready'
ORDER BY max_drawdown_percent_decimal DESC
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


def read_metric_value(
    metric_id: str,
    scope_level: str,
    scope_key: str,
    period_start_utc: int,
    period_end_utc: int,
    *,
    request_id: str,
) -> object:
    """Resolve one computed metric value for a scope and period.

    Args:
        metric_id: Metric definition identity.
        scope_level: Scope level.
        scope_key: Scope identity within the level.
        period_start_utc: Inclusive period start.
        period_end_utc: Inclusive period end.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result carrying at most one row.
    """
    logger.debug("Reading one Analytics metric value")
    return _execute(
        _SELECT_METRIC_VALUE,
        (metric_id, scope_level, scope_key, period_start_utc, period_end_utc),
        request_id=request_id,
        max_rows=1,
    )


def read_stale_metric_values(
    current_source_hash: str, *, request_id: str, limit: int
) -> object:
    """List metric values computed from inputs that have since changed.

    Args:
        current_source_hash: Current hash of the underlying inputs.
        request_id: Caller trace identity.
        limit: Bounded maximum row count.

    Returns:
        Data-owned transaction result carrying stale value rows.
    """
    logger.debug("Listing stale Analytics metric values")
    return _execute(
        _SELECT_STALE_VALUES,
        (current_source_hash,),
        request_id=request_id,
        max_rows=limit,
    )


def read_trades_for_strategy(
    strategy_version_id: str,
    from_at: str,
    to_at: str,
    *,
    request_id: str,
    limit: int,
) -> object:
    """List closed round-trips for one strategy version within a window.

    Args:
        strategy_version_id: Owning strategy version.
        from_at: Inclusive lower bound on exit time.
        to_at: Inclusive upper bound on exit time.
        request_id: Caller trace identity.
        limit: Bounded maximum row count.

    Returns:
        Data-owned transaction result carrying round-trip rows.
    """
    logger.debug("Listing Analytics round-trips for a strategy version")
    return _execute(
        _SELECT_TRADES_FOR_STRATEGY,
        (strategy_version_id, from_at, to_at),
        request_id=request_id,
        max_rows=limit,
    )


def read_worst_drawdowns(scope_level: str, *, request_id: str, limit: int) -> object:
    """Rank equity curves by worst drawdown within one scope level.

    Ranks over summary rows rather than curve points, which is why the points
    live in an artifact and the summary lives here.

    Args:
        scope_level: Scope level to rank within.
        request_id: Caller trace identity.
        limit: Bounded maximum row count.

    Returns:
        Data-owned transaction result carrying ranked curve rows.
    """
    logger.debug("Ranking Analytics equity curves by drawdown")
    return _execute(
        _SELECT_WORST_DRAWDOWNS, (scope_level,), request_id=request_id, max_rows=limit
    )
