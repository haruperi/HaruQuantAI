"""Create operations for Analytics-owned derived records."""

from __future__ import annotations

from typing import Any

from app.services.data import build_transaction_request, execute_transaction
from app.utils import get_logger

logger = get_logger(__name__)

_INSERT_METRIC_DEFINITION = """
INSERT INTO analytics_metric_definitions (
    metric_id, metric_code, version, category, formula_hash, min_sample_size,
    requires_benchmark, higher_is_better, unit, definition_json, state,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_METRIC_VALUE = """
INSERT INTO analytics_metric_values (
    value_id, metric_id, scope_level, scope_key, period_kind,
    period_start_utc, period_end_utc, value_decimal, sample_size,
    confidence_low_decimal, confidence_high_decimal, is_significant,
    insufficient_sample, source_hash, computed_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_TRADE_ANALYSIS = """
INSERT INTO analytics_trade_analysis (
    trade_id, source_kind, run_id, position_id, account_id, symbol_id,
    strategy_version_id, direction, entry_price_decimal, exit_price_decimal,
    quantity_decimal, gross_pnl_decimal, net_pnl_decimal, commission_decimal,
    swap_decimal, slippage_decimal, r_multiple_decimal, mae_decimal,
    mfe_decimal, holding_seconds, bars_held, exit_reason, regime_id,
    entry_at, exit_at, source_hash, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
          ?, ?, ?, ?)
""".strip()

_INSERT_ATTRIBUTION = """
INSERT INTO analytics_pnl_attribution (
    attribution_id, scope_level, scope_key, period_start_utc, period_end_utc,
    factor, contribution_decimal, contribution_percent_decimal, trade_count,
    source_hash, computed_at, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_EQUITY_CURVE = """
INSERT INTO analytics_equity_curves (
    curve_id, scope_level, scope_key, dataset_id, period_start_utc,
    period_end_utc, point_count, start_equity_decimal, end_equity_decimal,
    peak_equity_decimal, trough_equity_decimal, max_drawdown_decimal,
    max_drawdown_percent_decimal, max_drawdown_start_utc,
    max_drawdown_end_utc, recovery_ts_utc, source_hash, state, computed_at,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_REPORT = """
INSERT INTO analytics_reports (
    report_id, report_kind, scope_level, scope_key, period_start_utc,
    period_end_utc, content_json, content_hash, artifact_path, state,
    generated_at, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def create_metric_definition_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Register one metric definition and its minimum sample size.

    ``min_sample_size`` is the catalogue's defence against reporting a ratio
    computed from too few observations: Analytics refuses to emit a value below
    it rather than emitting a number that looks authoritative and means nothing.

    Args:
        parameters: Ordered column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Registering one Analytics metric definition")
    return _execute(
        _INSERT_METRIC_DEFINITION, parameters, request_id=request_id, max_rows=1
    )


def create_metric_value_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Record one computed metric value.

    A row must either carry a value or declare ``insufficient_sample``; the
    schema rejects a null value presented as a real measurement.

    Args:
        parameters: Ordered column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.debug("Recording one Analytics metric value")
    return _execute(_INSERT_METRIC_VALUE, parameters, request_id=request_id, max_rows=1)


def create_trade_analysis_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Record one closed round-trip with its excursion statistics.

    Maximum adverse and favourable excursion are why this exists separately
    from the execution record: a winning trade that first ran three per cent
    against the position is a different trade from one that never did, and only
    excursion data distinguishes them.

    Args:
        parameters: Ordered column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.debug("Recording one Analytics round-trip analysis")
    return _execute(
        _INSERT_TRADE_ANALYSIS, parameters, request_id=request_id, max_rows=1
    )


def create_pnl_attribution_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Record one profit-and-loss attribution factor.

    Factors must sum to total profit and loss, with ``residual`` absorbing the
    remainder. A large residual is itself the signal: it means the attribution
    model is missing a real cost.

    Args:
        parameters: Ordered column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.debug("Recording one Analytics attribution factor")
    return _execute(_INSERT_ATTRIBUTION, parameters, request_id=request_id, max_rows=1)


def create_equity_curve_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Record one equity-curve summary referencing its point series.

    Args:
        parameters: Ordered column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Recording one Analytics equity-curve summary")
    return _execute(_INSERT_EQUITY_CURVE, parameters, request_id=request_id, max_rows=1)


def create_report_record(parameters: tuple[Any, ...], *, request_id: str) -> object:
    """Record one generated report.

    Args:
        parameters: Ordered column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Recording one Analytics report")
    return _execute(_INSERT_REPORT, parameters, request_id=request_id, max_rows=1)
