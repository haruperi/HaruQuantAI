# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100, ANN401, TRY301, BLE001, C901
"""Drawdown statistics, underwater series, recovery duration, and ratios (ANL-NFR-115)."""

from __future__ import annotations

import collections
import math
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.errors import AnalyticsValidationError as ValidationError
from app.services.analytics.metrics.efficiency import _sorted_median
from app.services.analytics.metrics.equity import (
    _parse_equity_curve,
    return_volatility,
    returns_series,
)
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    get_closed_trades,
    get_ordered_closed_trades,
    parse_utc_time,
)
from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.logger import logger


def validate_request_id_strict(request_id: str | None) -> None:
    """Raise ``ValidationError`` when ``request_id`` is present but invalid."""
    if request_id is None:
        return
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValidationError("request_id must be a non-empty string when supplied.")


type TradeRecord = dict[str, Any]
type EquityPoint = Any
type ReturnPoint = Any


def metrics_drawdown_boundary() -> dict[str, bool]:
    """Describe drawdown metric boundary declarations.

    Returns:
        Boundary evidence that drawdown helpers are pure analytics kernels.
    """
    logger.debug("metrics_drawdown_boundary: executed.")
    return {
        "file_specific_non_functional_requirements_defined": False,
        "file_specific_testing_requirements_defined": False,
        "read_only": True,
        "pure_metric_kernel": True,
    }


def drawdown_series(equity_values: Sequence[float]) -> list[float]:
    """Compute peak-to-trough fractional drawdown series.

    Args:
        equity_values (Sequence[float]): Sequence of numeric values.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("drawdown_series: executed.")
    if not equity_values:
        return []
    peak = equity_values[0]
    series: list[float] = []
    for eq in equity_values:
        peak = max(peak, eq)
        if peak <= 0:
            series.append(0.0)
        else:
            series.append((peak - eq) / peak)
    return series


def drawdown_duration_series(equity_curve: Any) -> list[float]:
    """Compute hours-since-peak drawdown duration at each equity point.

    Args:
        equity_curve (Any): Sequence of equity values or curve.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("drawdown_duration_series: executed.")
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        return []
    durations: list[float] = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    for dt, eq in parsed:
        if eq >= peak:
            peak = eq
            peak_time = dt
            durations.append(0.0)
        else:
            durations.append((dt - peak_time).total_seconds() / 3600.0)
    return durations


def trade_pnl_distribution(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate a statistical summary of realized trade PnL (ANL-NFR-115).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("trade_pnl_distribution: executed.")
    # Note: Expects trades sequence from config or input_value.
    # We will extract closed trades and compute mean/std/min/max/median.
    trades = config.metadata.get("trades", [])
    pnls = sorted(_get_trade_pnl(t) for t in get_closed_trades(trades))
    if not pnls:
        return MetricResult(value={})
    n = len(pnls)
    mean = sum(pnls) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in pnls) / max(n - 1, 1))
    val = {
        "mean": mean,
        "std": std,
        "min": pnls[0],
        "max": pnls[-1],
        "median": _sorted_median(pnls),
    }
    return MetricResult(value=val)


def trade_level_drawdowns(
    trades: Sequence[TradeRecord],
) -> list[float]:
    """Compute balance-drawdown series at each trade close (ANL-NFR-116).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("trade_level_drawdowns: executed.")
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return []
    balance = 10000.0
    balances = [balance]
    for t in closed:
        balance += _get_trade_pnl(t)
        balances.append(balance)
    peak = balances[0]
    drawdowns = []
    for b in balances:
        peak = max(peak, b)
        drawdowns.append(peak - b)
    return drawdowns


def trade_level_drawdowns_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Expose trade_level_drawdowns as a metric (ANL-NFR-116).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[float value.
    """
    logger.debug("trade_level_drawdowns_metric: executed.")
    trades = config.metadata.get("trades", [])
    val = trade_level_drawdowns(trades)
    return MetricResult(value=val)


def max_close_to_close_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum trade-level peak-to-valley decline (ANL-NFR-117).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_close_to_close_drawdown: executed.")
    trades = config.metadata.get("trades", [])
    val = max(trade_level_drawdowns(trades), default=0.0)
    return MetricResult(value=val)


def avg_trade_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean trade-level close-to-close drawdown depth (ANL-NFR-118).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_trade_drawdown: executed.")
    trades = config.metadata.get("trades", [])
    dds = trade_level_drawdowns(trades)
    val = sum(dds) / len(dds) if dds else 0.0
    return MetricResult(value=val)


def max_consecutive_drawdown_trades(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[int]:
    """Calculate maximum number of consecutive trades inside drawdown (ANL-NFR-119).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated int value.
    """
    logger.debug("max_consecutive_drawdown_trades: executed.")
    trades = config.metadata.get("trades", [])
    dds = trade_level_drawdowns(trades)
    max_con = 0
    curr_con = 0
    for d in dds:
        if d > 0:
            curr_con += 1
            max_con = max(max_con, curr_con)
        else:
            curr_con = 0
    return MetricResult(value=max_con)


def max_close_to_close_drawdown_date(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[str]:
    """Identify the timestamp of deepest trade-level valley (ANL-NFR-120).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated str value.
    """
    logger.debug("max_close_to_close_drawdown_date: executed.")
    _fallback = "1970-01-01T00:00:00+00:00"
    trades = config.metadata.get("trades", [])
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return MetricResult(value=_fallback)
    dds = trade_level_drawdowns(trades)
    if not dds:
        return MetricResult(value=_fallback)
    max_dd = max(dds)
    max_idx = dds.index(max_dd)
    if max_idx == 0:
        return MetricResult(value=_fallback)
    t = closed[max_idx - 1]
    ct_raw = t.get("close_time") or t.get("close_timestamp")
    dt = parse_utc_time(ct_raw)
    val = dt.isoformat() if dt else _fallback
    return MetricResult(value=val)


def relative_drawdown_series(
    equity: Any,
    config: Any = None,
) -> Any:
    """Generate relative underperformance between strategy and benchmark (ANL-NFR-182).

    Args:
        equity: Sequence of equity values/curve.
        config: MetricConfig for V2, or benchmark values list for V1.

    Returns:
        MetricResult in V2 mode. Calculated list[float] in V1 mode.
    """
    logger.debug("relative_drawdown_series: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed_strat = _parse_equity_curve(equity)
        benchmark_equity = config.metadata.get("benchmark_equity", [])
        parsed_bench = _parse_equity_curve(benchmark_equity)
        if not parsed_strat or not parsed_bench:
            return MetricResult(value=[])
        # Align length
        n = min(len(parsed_strat), len(parsed_bench))
        rel_dd = []
        strat_vals = [x[1] for x in parsed_strat[:n]]
        bench_vals = [x[1] for x in parsed_bench[:n]]
        # Normalized relative underperformance
        strat_dd = drawdown_series(strat_vals)
        bench_dd = drawdown_series(bench_vals)
        for i in range(n):
            rel_dd.append(max(0.0, strat_dd[i] - bench_dd[i]))
        return MetricResult(value=rel_dd)

    # V1 compatibility path
    equity_values = equity
    benchmark_values = config
    if not equity_values or not benchmark_values:
        return []
    n = min(len(equity_values), len(benchmark_values))
    strat_dd = drawdown_series(equity_values[:n])
    bench_dd = drawdown_series(benchmark_values[:n])
    rel_dd = []
    for i in range(n):
        rel_dd.append(max(0.0, strat_dd[i] - bench_dd[i]))
    return rel_dd


def drawdown_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate drawdown values from an equity curve (ANL-NFR-183).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[float value.
    """
    logger.debug("drawdown_series_metric: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=[])
    eq_vals = [eq for _, eq in parsed]
    val = drawdown_series(eq_vals)
    return MetricResult(value=val)


def drawdown_duration_series_metric(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate drawdown duration values from an equity curve (ANL-NFR-184).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[float value.
    """
    logger.debug("drawdown_duration_series_metric: executed.")
    val = drawdown_duration_series(equity)
    return MetricResult(value=val)


def max_drawdown_duration_from_equity(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate maximum drawdown duration from equity values (ANL-NFR-185).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("max_drawdown_duration_from_equity: executed.")
    if config is not None and isinstance(config, MetricConfig):
        val = max(drawdown_duration_series(equity), default=0.0)
        return MetricResult(value=val)

    # V1 compatibility path
    return max(drawdown_duration_series(equity), default=0.0)


def max_strategy_drawdown_date(
    equity: Any,
    config: Any = None,
) -> Any:
    """Identify the timestamp of deepest strategy equity valley (ANL-NFR-186).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated str value in V1 mode.
    """
    logger.debug("max_strategy_drawdown_date: executed.")
    _fallback = "1970-01-01T00:00:00+00:00"
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity)
        if not parsed:
            return MetricResult(value=_fallback)
        equities = [eq for _, eq in parsed]
        if not equities:
            return MetricResult(value=_fallback)
        peak = equities[0]
        max_dd = 0.0
        valley_idx = 0
        for i, eq in enumerate(equities):
            peak = max(peak, eq)
            if peak > 0:
                dd = (peak - eq) / peak
                if dd > max_dd:
                    max_dd = dd
                    valley_idx = i
        val = parsed[valley_idx][0].isoformat()
        return MetricResult(value=val)

    # V1 compatibility path
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return _fallback
    equities = [eq for _, eq in parsed]
    if not equities:
        return _fallback
    peak = equities[0]
    max_dd = 0.0
    valley_idx = 0
    for i, eq in enumerate(equities):
        peak = max(peak, eq)
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
                valley_idx = i
    val = parsed[valley_idx][0].isoformat()
    # Check if valley has offset, otherwise add UTC offset
    if "+" not in val and "-" not in val and not val.endswith("Z"):
        val += "+00:00"
    return val


def avg_underwater_drawdown_percent(
    equity: Any,
    config: Any = None,
) -> Any:
    """Calculate average drawdown depth while equity is below peak (ANL-NFR-187).

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or None for V1.

    Returns:
        MetricResult in V2 mode. Calculated float value in V1 mode.
    """
    logger.debug("avg_underwater_drawdown_percent: executed.")
    if config is not None and isinstance(config, MetricConfig):
        parsed = _parse_equity_curve(equity)
        if not parsed:
            return MetricResult(value=0.0)
        equities = [eq for _, eq in parsed]
        dds = drawdown_series(equities)
        active_dds = [d for d in dds if d > 0]
        val = (sum(active_dds) / len(active_dds)) * 100.0 if active_dds else 0.0
        return MetricResult(value=val)

    # V1 compatibility path
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    return (sum(active_dds) / len(active_dds)) * 100.0 if active_dds else 0.0


def calculate_drawdown_metrics(
    equity: Any,
    config: Any = None,
    request_id: str | None = None,
) -> Any:
    """Compute a full drawdown metric bundle from an equity curve.

    Args:
        equity: Sequence of equity values or curve.
        config: MetricConfig for V2, or optional request_id string for V1.
        request_id: Optional request_id for V1 keyword argument calls.

    Returns:
        MetricResult in V2 mode. StandardResponse or dict in V1 mode.
    """
    logger.debug("calculate_drawdown_metrics: executed.")
    if config is not None and isinstance(config, MetricConfig):
        max_dd = max_strategy_drawdown_percent(equity, config).value or 0.0
        avg_dd = avg_drawdown(equity, config).value or 0.0
        max_dur = max_drawdown_duration(equity, config).value or 0.0
        underwater = avg_underwater_drawdown_percent(equity, config).value or 0.0
        val = {
            "max_drawdown_percent": max_dd,
            "avg_drawdown_percent": avg_dd,
            "max_drawdown_duration_hours": max_dur,
            "avg_underwater_drawdown_percent": underwater,
            "max_drawdown_date": max_strategy_drawdown_date(equity, config).value or "",
        }
        return MetricResult(value=val)

    # V1 compatibility path
    if (
        request_id is None
        and config is not None
        and not isinstance(config, MetricConfig)
    ):
        request_id = config
    parsed = _parse_equity_curve(equity)
    if not parsed:
        data = {}
    else:
        eq_vals = [eq for _, eq in parsed]
        dd_vals = drawdown_series(eq_vals)
        max_dd = max(dd_vals, default=0.0)
        durations = drawdown_duration_series(equity)
        max_dur = max(durations, default=0.0)
        underwater = avg_underwater_drawdown_percent(equity)
        max_dd_date = max_strategy_drawdown_date(equity)
        data = {
            "max_drawdown_percent": max_dd * 100.0,
            "max_drawdown_duration_hours": max_dur,
            "avg_underwater_drawdown_percent": underwater,
            "max_drawdown_date": max_dd_date,
        }

    if request_id is not None:
        meta = build_metadata(
            tool_name="calculate_drawdown_metrics",
            tool_category="analytics",
            tool_risk_level="low",
            request_id=request_id,
            reads=True,
        )
        return success_response(
            message="Successfully calculated drawdown metrics.",
            data=data,
            metadata=meta,
        )
    return data


def max_relative_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum relative underperformance as a positive percentage (ANL-NFR-220).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_relative_drawdown_percent: executed.")
    res = relative_drawdown_series(equity, config)
    val = max(res.value, default=0.0) * 100.0 if res.value else 0.0
    return MetricResult(value=val)


def max_strategy_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate deepest peak-to-valley decline in currency units (ANL-NFR-221).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_strategy_drawdown: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
    return MetricResult(value=max_dd)


def max_strategy_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate deepest percentage decline relative to running peak (ANL-NFR-222).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_strategy_drawdown_percent: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak)
    val = max_dd * 100.0
    return MetricResult(value=val)


def max_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown from returns (ANL-NFR-223).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_drawdown: executed.")
    return max_strategy_drawdown_percent(equity, config)


def avg_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average drawdown depth (ANL-NFR-224).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_drawdown: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    val = (sum(active_dds) / len(active_dds)) * 100.0 if active_dds else 0.0
    return MetricResult(value=val)


def drawdown_distribution(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate detailed drawdown distribution statistics (ANL-NFR-225).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("drawdown_distribution: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value={})
    equities = [eq for _, eq in parsed]
    dds = sorted(drawdown_series(equities))
    if not dds:
        return MetricResult(value={})
    n = len(dds)
    mean = sum(dds) / n
    val = {
        "mean": mean * 100.0,
        "std": return_volatility(dds) * 100.0,
        "max": dds[-1] * 100.0,
        "median": _sorted_median(dds) * 100.0,
    }
    return MetricResult(value=val)


def max_drawdown_duration_from_returns(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown duration from return values (ANL-NFR-226).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_drawdown_duration_from_returns: executed.")
    return max_drawdown_duration(equity, config)


def max_drawdown_duration(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate maximum drawdown duration (ANL-NFR-227).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_drawdown_duration: executed.")
    val = max(drawdown_duration_series(equity), default=0.0)
    return MetricResult(value=val)


def avg_drawdown_duration(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average duration of drawdown episodes (ANL-NFR-228).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_drawdown_duration: executed.")
    durs = drawdown_duration_series(equity)
    if not durs:
        return MetricResult(value=0.0)
    # Collect distinct underwater episode durations
    episodes = []
    curr_dur = 0.0
    for d in durs:
        if d > 0:
            curr_dur = d
        elif curr_dur > 0:
            episodes.append(curr_dur)
            curr_dur = 0.0
    if curr_dur > 0:
        episodes.append(curr_dur)
    val = sum(episodes) / len(episodes) if episodes else 0.0
    return MetricResult(value=val)


def time_to_recovery(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Calculate recovery periods for unique drawdowns (ANL-NFR-229).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated list[float value.
    """
    logger.debug("time_to_recovery: executed.")
    durs = drawdown_duration_series(equity)
    episodes = []
    curr_dur = 0.0
    for d in durs:
        if d > 0:
            curr_dur = d
        elif curr_dur > 0:
            episodes.append(curr_dur)
            curr_dur = 0.0
    if curr_dur > 0:
        episodes.append(curr_dur)
    return MetricResult(value=episodes)


def recovery_factor(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit relative to maximum drawdown (ANL-NFR-230).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("recovery_factor: executed.")
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    val = net_p / max_dd if max_dd > 0 else 0.0
    return MetricResult(value=val)


def max_close_to_close_drawdown_percent(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate close-to-close drawdown as a percentage (ANL-NFR-231).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("max_close_to_close_drawdown_percent: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    val = max(dds, default=0.0) * 100.0
    return MetricResult(value=val)


def account_size_required(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate capital required to withstand max close-to-close dips (ANL-NFR-232).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("account_size_required: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    # Estimate capital based on max strategy drawdown + 10% safety buffer
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    val = max_dd * 1.10
    return MetricResult(value=val)


def avg_yearly_max_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Average the maximum drawdown observed in each year (ANL-NFR-233).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_yearly_max_drawdown: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    by_year: dict[int, list[tuple[Any, float]]] = collections.defaultdict(list)
    for dt, eq in parsed:
        by_year[dt.year].append((dt, eq))
    yearly_dds = [
        max_strategy_drawdown_percent(curve, config).value or 0.0
        for curve in by_year.values()
    ]
    val = sum(yearly_dds) / len(yearly_dds) if yearly_dds else 0.0
    return MetricResult(value=val)


def ulcer_index(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate squared-drawdown-based ulcer index (ANL-NFR-234).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("ulcer_index: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return MetricResult(value=0.0)
    val = math.sqrt(sum(d**2 for d in dds) / len(dds)) * 100.0
    return MetricResult(value=val)


def pain_index(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean absolute percentage drawdown (ANL-NFR-235).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("pain_index: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return MetricResult(value=0.0)
    val = (sum(dds) / len(dds)) * 100.0
    return MetricResult(value=val)


def pain_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return relative to pain index (ANL-NFR-236).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("pain_ratio: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        if rets and product > 0
        else 0.0
    )
    pain_idx = pain_index(equity, config).value or 0.0
    if pain_idx <= 0:
        return MetricResult(value=0.0)
    val = ann_ret / pain_idx
    return MetricResult(value=val)


def calmar_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate annualized return relative to maximum drawdown (ANL-NFR-237).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("calmar_ratio: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        if rets and product > 0
        else 0.0
    )
    max_dd = max_strategy_drawdown_percent(equity, config).value or 0.0
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = ann_ret / max_dd
    return MetricResult(value=val)


def fouse_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate Fouse drawdown-index-style ratio (ANL-NFR-238).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("fouse_ratio: executed.")
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    eq_vals = [eq for _, eq in parsed]
    rets = returns_series(eq_vals)
    periods_per_year = int(config.annualization_periods if config else 252)
    product = 1.0
    for r in rets:
        product *= 1.0 + r
    ann_ret = (
        (math.pow(product, periods_per_year / len(rets)) - 1.0) * 100.0
        if rets and product > 0
        else 0.0
    )
    ulcer = ulcer_index(equity, config).value or 0.0
    if ulcer <= 0:
        return MetricResult(value=0.0)
    val = ann_ret / ulcer
    return MetricResult(value=val)


def sterling_ratio(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate CAGR relative to adjusted average yearly maximum drawdown (ANL-NFR-239).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("sterling_ratio: executed.")
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    initial_balance = parsed[0][1]
    net_p = parsed[-1][1] - parsed[0][1]
    final_balance = initial_balance + net_p
    years = float(config.metadata.get("years", 1.0) if config else 1.0)
    cagr_val = 0.0
    if initial_balance > 0 and final_balance > 0 and years > 0:
        cagr_val = (
            math.pow(final_balance / initial_balance, 1.0 / years) - 1.0
        ) * 100.0
    avg_yearly_max_dd = avg_yearly_max_drawdown(equity, config).value or 0.0
    denom = avg_yearly_max_dd + 10.0  # standard Sterling adjustment adds 10%
    if denom <= 0:
        return MetricResult(value=0.0)
    val = cagr_val / denom
    return MetricResult(value=val)


def rina_index(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate select net profit relative to average drawdown and time in market (ANL-NFR-240).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("rina_index: executed.")
    # Exposing placeholder for RINA index calculation
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    avg_dd = avg_drawdown(equity, config).value or 0.0
    if avg_dd <= 0:
        return MetricResult(value=0.0)
    val = net_p / avg_dd
    return MetricResult(value=val)


def adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate adjusted net profit as a percentage of max strategy drawdown (ANL-NFR-241).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("adjusted_net_profit_as_percent_of_max_strategy_drawdown: executed.")
    # Under metrics rules we extract adj_net_profit
    trades = config.metadata.get("trades", [])
    from app.services.analytics.metrics.pnl import adjusted_net_profit

    adj_net = adjusted_net_profit(trades, config).value or 0.0
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = (adj_net / max_dd) * 100.0
    return MetricResult(value=val)


def net_profit_as_percent_of_max_strategy_drawdown(
    net_profit: float,
    max_dd_usd: float,
) -> float:
    """Express net profit as a percentage of maximum strategy drawdown.

    Args:
        net_profit: Total net profit in account currency.
        max_dd_usd: Maximum strategy drawdown in account currency.

    Returns:
        Ratio as a percentage (net_profit / max_dd_usd * 100), or 0.0 when
        max_dd_usd is non-positive.
    """
    logger.debug("net_profit_as_percent_of_max_strategy_drawdown: executed.")
    return _raw_net_profit_as_percent_of_max_strategy_drawdown(net_profit, max_dd_usd)


def select_net_profit_as_percent_of_max_strategy_drawdown(
    select_net_profit: float,
    max_dd_usd: float,
) -> float:
    """Express trimmed/select net profit as a percentage of maximum strategy drawdown.

    Args:
        select_net_profit: Trimmed net profit (e.g. excluding outlier trades).
        max_dd_usd: Maximum strategy drawdown in account currency.

    Returns:
        Ratio as a percentage, or 0.0 when max_dd_usd is non-positive.
    """
    logger.debug("select_net_profit_as_percent_of_max_strategy_drawdown: executed.")
    return _raw_select_net_profit_as_percent_of_max_strategy_drawdown(
        select_net_profit, max_dd_usd
    )


def return_on_max_strategy_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return relative to maximum strategy drawdown (ANL-NFR-242).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_on_max_strategy_drawdown: executed.")
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    max_dd = max_strategy_drawdown(equity, config).value or 0.0
    if max_dd <= 0:
        return MetricResult(value=0.0)
    val = (net_p / max_dd) * 100.0
    return MetricResult(value=val)


def return_on_max_close_to_close_drawdown(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit relative to maximum close-to-close drawdown (ANL-NFR-243).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_on_max_close_to_close_drawdown: executed.")
    parsed = _parse_equity_curve(equity)
    if len(parsed) < 2:
        return MetricResult(value=0.0)
    net_p = parsed[-1][1] - parsed[0][1]
    trades = config.metadata.get("trades", [])
    max_close_dd = max(trade_level_drawdowns(trades), default=0.0)
    if max_close_dd <= 0:
        return MetricResult(value=0.0)
    val = net_p / max_close_dd
    return MetricResult(value=val)


def drawdown_probability(
    equity: Sequence[EquityPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate probability of drawdown exceeding a threshold (ANL-NFR-244).

    Args:
        equity (Sequence[EquityPoint]): Sequence of equity values or curve.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("drawdown_probability: executed.")
    threshold = float(
        config.metadata.get("drawdown_threshold", 0.10) if config else 0.10
    )
    parsed = _parse_equity_curve(equity)
    if not parsed:
        return MetricResult(value=0.0)
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        return MetricResult(value=0.0)
    exceeded = sum(1 for d in dds if d >= threshold)
    val = exceeded / len(dds)
    return MetricResult(value=val)


# ---------------------------------------------------------------------------
# Backward-compatible Raw Calculation Kernels
# ---------------------------------------------------------------------------


def _raw_max_strategy_drawdown(equity_curve: Any) -> float:
    """Compute maximum absolute (currency) drawdown from equity curve."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("max_strategy_drawdown: empty equity curve, returning 0.0")
        return 0.0
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        max_dd = max(max_dd, peak - eq)
    logger.debug(f"max_strategy_drawdown: computed max absolute drawdown: {max_dd}")
    return max_dd


def _raw_max_strategy_drawdown_percent(equity_curve: Any) -> float:
    """Compute maximum percentage drawdown from equity curve."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("max_strategy_drawdown_percent: empty equity curve, returning 0.0")
        return 0.0
    peak = parsed[0][1]
    max_dd = 0.0
    for _, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak)
    res = max_dd * 100.0
    logger.debug(
        f"max_strategy_drawdown_percent: computed max strategy drawdown percent: {res}"
    )
    return res


def _raw_max_relative_drawdown_percent(
    strategy_equity: list[float],
    benchmark_equity: list[float],
) -> float:
    """Compute maximum relative drawdown of strategy versus benchmark."""
    parsed_strat = _parse_equity_curve(strategy_equity)
    parsed_bench = _parse_equity_curve(benchmark_equity)
    if not parsed_strat or not parsed_bench:
        return 0.0
    n = min(len(parsed_strat), len(parsed_bench))
    strat_vals = [x[1] for x in parsed_strat[:n]]
    bench_vals = [x[1] for x in parsed_bench[:n]]
    strat_dd = drawdown_series(strat_vals)
    bench_dd = drawdown_series(bench_vals)
    rel_dd = []
    for i in range(n):
        rel_dd.append(max(0.0, strat_dd[i] - bench_dd[i]))
    res = max(rel_dd, default=0.0) * 100.0
    logger.debug(
        f"max_relative_drawdown_percent: computed max relative drawdown percent: {res}"
    )
    return res


def _raw_max_drawdown(returns: list[float]) -> float:
    """Compute maximum drawdown from a return series."""
    if not returns:
        logger.debug("max_drawdown: empty returns, returning 0.0")
        return 0.0
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    dds = drawdown_series(eq)
    res = max(dds, default=0.0) * 100.0
    logger.debug(f"max_drawdown: computed max drawdown from return series: {res}")
    return res


def _raw_avg_drawdown(equity_curve: Any) -> float:
    """Compute average percentage drawdown across all underwater periods."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("avg_drawdown: empty equity curve, returning 0.0")
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    active_dds = [d for d in dds if d > 0]
    if not active_dds:
        logger.debug("avg_drawdown: no active drawdowns, returning 0.0")
        return 0.0
    res = (sum(active_dds) / len(active_dds)) * 100.0
    logger.debug(f"avg_drawdown: computed average drawdown: {res}")
    return res


def _raw_drawdown_distribution(equity_curve: Any) -> dict[str, float]:
    """Compute descriptive statistics of the drawdown distribution."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("drawdown_distribution: empty equity curve, returning empty dict")
        return {}
    equities = [eq for _, eq in parsed]
    dds = [d * 100.0 for d in drawdown_series(equities)]
    if not dds:
        logger.debug(
            "drawdown_distribution: no drawdowns calculated, returning empty dict"
        )
        return {}
    sorted_dds = sorted(dds)
    n = len(sorted_dds)
    mean = sum(dds) / n
    stats = {
        "mean": mean,
        "std": math.sqrt(sum((x - mean) ** 2 for x in dds) / max(n - 1, 1)),
        "50th": sorted_dds[int(n * 0.50)],
        "90th": sorted_dds[int(n * 0.90)],
        "95th": sorted_dds[int(n * 0.95)],
        "99th": sorted_dds[int(n * 0.99)],
    }
    logger.debug(f"drawdown_distribution: computed statistics: {stats}")
    return stats


def _raw_max_drawdown_duration_from_returns(returns: list[float]) -> float:
    """Compute maximum drawdown duration in hours from a return series."""
    if not returns:
        logger.debug("max_drawdown_duration_from_returns: empty returns, returning 0.0")
        return 0.0
    eq = [10000.0]
    for r in returns:
        eq.append(eq[-1] * (1.0 + r))
    from datetime import UTC

    eq_curve = [(datetime.fromtimestamp(i * 3600, UTC), eq[i]) for i in range(len(eq))]
    res = max(drawdown_duration_series(eq_curve), default=0.0)
    logger.debug(f"max_drawdown_duration_from_returns: computed max duration: {res}")
    return res


def _raw_max_drawdown_duration(equity_curve: Any) -> float:
    """Compute maximum drawdown duration in hours from an equity curve."""
    res = max(drawdown_duration_series(equity_curve), default=0.0)
    logger.debug(f"max_drawdown_duration: computed max duration from equity: {res}")
    return res


def _raw_avg_drawdown_duration(equity_curve: Any) -> float:
    """Compute average drawdown-episode length in hours."""
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        logger.debug("avg_drawdown_duration: fewer than 2 data points, returning 0.0")
        return 0.0
    durations = drawdown_duration_series(equity_curve)
    episodes: list[float] = []
    in_episode = False
    episode_max = 0.0
    for d in durations:
        if d > 0:
            in_episode = True
            episode_max = max(episode_max, d)
        elif in_episode:
            episodes.append(episode_max)
            in_episode = False
            episode_max = 0.0
    if in_episode:
        episodes.append(episode_max)
    res = sum(episodes) / len(episodes) if episodes else 0.0
    logger.debug(f"avg_drawdown_duration: computed average duration: {res}")
    return res


def _raw_time_to_recovery(equity_curve: Any) -> list[float]:
    """Compute recovery time (hours) for each drawdown episode."""
    parsed = _parse_equity_curve(equity_curve)
    if len(parsed) < 2:
        logger.debug("time_to_recovery: fewer than 2 data points, returning []")
        return []
    recovery_times: list[float] = []
    peak = parsed[0][1]
    peak_time = parsed[0][0]
    in_drawdown = False
    for dt, eq in parsed[1:]:
        if eq >= peak:
            if in_drawdown:
                recovery_times.append((dt - peak_time).total_seconds() / 3600.0)
                in_drawdown = False
            peak = eq
            peak_time = dt
        else:
            in_drawdown = True
    logger.debug(
        f"time_to_recovery: calculated recovery times for {len(recovery_times)} episodes."
    )
    return recovery_times


def _raw_recovery_factor(
    net_profit: float,
    max_drawdown_val: float,
) -> float:
    """Compute the recovery factor (net profit / max drawdown)."""
    if max_drawdown_val <= 0:
        logger.debug("recovery_factor: max drawdown is <= 0, returning 0.0")
        return 0.0
    res = net_profit / max_drawdown_val
    logger.debug(f"recovery_factor: calculated factor: {res}")
    return res


def _raw_max_close_to_close_drawdown_percent(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
) -> float:
    """Compute max close-to-close drawdown percentage from trade list."""
    from app.services.analytics.metrics.curves import balance_curve

    curve = balance_curve(trades, initial_balance)
    equities = [c["equity"] for c in curve]
    dds = drawdown_series(equities)
    res = max(dds, default=0.0) * 100.0
    logger.debug(
        f"max_close_to_close_drawdown_percent: computed drawdown percent: {res}"
    )
    return res


def _raw_account_size_required(
    trades: list[dict[str, Any]],
    initial_balance: float = 10000.0,
) -> float:
    """Estimate minimum account size to avoid margin calls."""
    from app.services.analytics.metrics.curves import balance_curve

    curve = balance_curve(trades, initial_balance)
    max_dd_usd = _raw_max_strategy_drawdown(curve)
    res = initial_balance + max_dd_usd
    logger.debug(f"account_size_required: estimated required account size: {res}")
    return res


def _raw_avg_yearly_max_drawdown(equity_curve: Any) -> float:
    """Compute average of per-year maximum drawdowns."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("avg_yearly_max_drawdown: empty equity curve, returning 0.0")
        return 0.0
    by_year: dict[int, list[tuple[datetime, float]]] = {}
    for dt, eq in parsed:
        by_year.setdefault(dt.year, []).append((dt, eq))
    yearly_dds = [
        _raw_max_strategy_drawdown_percent(curve) for curve in by_year.values()
    ]
    res = sum(yearly_dds) / len(yearly_dds) if yearly_dds else 0.0
    logger.debug(
        f"avg_yearly_max_drawdown: computed average yearly max drawdown: {res}"
    )
    return res


def _raw_ulcer_index(equity_curve: Any) -> float:
    """Compute the Ulcer Index from an equity curve."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("ulcer_index: empty equity curve, returning 0.0")
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        logger.debug("ulcer_index: no drawdowns, returning 0.0")
        return 0.0
    res = math.sqrt(sum(d**2 for d in dds) / len(dds)) * 100.0
    logger.debug(f"ulcer_index: computed ulcer index: {res}")
    return res


def _raw_pain_index(equity_curve: Any) -> float:
    """Compute the Pain Index from an equity curve."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("pain_index: empty equity curve, returning 0.0")
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = drawdown_series(equities)
    if not dds:
        logger.debug("pain_index: no drawdowns, returning 0.0")
        return 0.0
    res = (sum(dds) / len(dds)) * 100.0
    logger.debug(f"pain_index: computed pain index: {res}")
    return res


def _raw_pain_ratio(
    annualized_ret: float,
    pain_idx: float,
) -> float:
    """Compute the Pain Ratio (annualized return / pain index)."""
    if pain_idx <= 0:
        logger.debug("pain_ratio: pain index is <= 0, returning 0.0")
        return 0.0
    res = annualized_ret / pain_idx
    logger.debug(f"pain_ratio: computed pain ratio: {res}")
    return res


def _raw_calmar_ratio(
    annualized_ret: float,
    max_dd: float,
) -> float:
    """Compute the Calmar Ratio (annualized return / max drawdown)."""
    if max_dd <= 0:
        logger.debug("calmar_ratio: max drawdown is <= 0, returning 0.0")
        return 0.0
    res = annualized_ret / max_dd
    logger.debug(f"calmar_ratio: computed calmar ratio: {res}")
    return res


def _raw_fouse_ratio(
    annualized_ret: float,
    ulcer_idx: float,
) -> float:
    """Compute the Fouse Ratio (annualized return / ulcer index)."""
    if ulcer_idx <= 0:
        logger.debug("fouse_ratio: ulcer index is <= 0, returning 0.0")
        return 0.0
    res = annualized_ret / ulcer_idx
    logger.debug(f"fouse_ratio: computed fouse ratio: {res}")
    return res


def _raw_sterling_ratio(
    cagr_val: float,
    avg_yearly_max_dd: float,
) -> float:
    """Compute the Sterling Ratio."""
    denom = abs(avg_yearly_max_dd) + 10.0
    if denom <= 0:
        logger.debug("sterling_ratio: denominator is <= 0, returning 0.0")
        return 0.0
    res = cagr_val / denom
    logger.debug(f"sterling_ratio: computed sterling ratio: {res}")
    return res


def _raw_rina_index(
    select_net_prof: float,
    avg_dd: float,
    time_in_market: float,
) -> float:
    """Compute the RINA Index."""
    denom = avg_dd * time_in_market
    if denom <= 0:
        logger.debug("rina_index: denominator is <= 0, returning 0.0")
        return 0.0
    res = select_net_prof / denom
    logger.debug(f"rina_index: computed RINA index: {res}")
    return res


def _raw_net_profit_as_percent_of_max_strategy_drawdown(
    net_prof: float,
    max_dd_usd: float,
) -> float:
    """Express net profit as a percentage of max strategy drawdown."""
    if max_dd_usd <= 0:
        logger.debug(
            "net_profit_as_percent_of_max_strategy_drawdown: max_dd_usd is <= 0, returning 0.0"
        )
        return 0.0
    res = (net_prof / max_dd_usd) * 100.0
    logger.debug(
        f"net_profit_as_percent_of_max_strategy_drawdown: computed percentage: {res}"
    )
    return res


def _raw_select_net_profit_as_percent_of_max_strategy_drawdown(
    select_net_prof: float,
    max_dd_usd: float,
) -> float:
    """Express trimmed net profit as a percentage of max strategy drawdown."""
    res = _raw_net_profit_as_percent_of_max_strategy_drawdown(
        select_net_prof, max_dd_usd
    )
    logger.debug(
        f"select_net_profit_as_percent_of_max_strategy_drawdown: computed percentage: {res}"
    )
    return res


def _raw_adjusted_net_profit_as_percent_of_max_strategy_drawdown(
    adj_net_prof: float,
    max_dd_usd: float,
) -> float:
    """Express adjusted net profit as a percentage of max strategy drawdown."""
    res = _raw_net_profit_as_percent_of_max_strategy_drawdown(adj_net_prof, max_dd_usd)
    logger.debug(
        f"adjusted_net_profit_as_percent_of_max_strategy_drawdown: computed percentage: {res}"
    )
    return res


def _raw_return_on_max_strategy_drawdown(
    total_ret: float,
    max_dd_pct: float,
) -> float:
    """Compute return / max-drawdown ratio."""
    if max_dd_pct <= 0:
        logger.debug(
            "return_on_max_strategy_drawdown: max_dd_pct is <= 0, returning 0.0"
        )
        return 0.0
    res = total_ret / max_dd_pct
    logger.debug(
        f"return_on_max_strategy_drawdown: computed return on max strategy drawdown: {res}"
    )
    return res


def _raw_return_on_max_close_to_close_drawdown(
    net_prof: float,
    max_close_dd_usd: float,
) -> float:
    """Compute return / max close-to-close drawdown ratio."""
    if max_close_dd_usd <= 0:
        logger.debug(
            "return_on_max_close_to_close_drawdown: max_close_dd_usd is <= 0, returning 0.0"
        )
        return 0.0
    res = net_prof / max_close_dd_usd
    logger.debug(
        f"return_on_max_close_to_close_drawdown: computed return on max close to close drawdown: {res}"
    )
    return res


def _raw_drawdown_probability(
    equity_curve: Any,
    threshold: float,
) -> float:
    """Compute fraction of time spent in drawdown exceeding a threshold."""
    parsed = _parse_equity_curve(equity_curve)
    if not parsed:
        logger.debug("drawdown_probability: empty equity curve, returning 0.0")
        return 0.0
    equities = [eq for _, eq in parsed]
    dds = [d * 100.0 for d in drawdown_series(equities)]
    if not dds:
        logger.debug("drawdown_probability: no drawdowns, returning 0.0")
        return 0.0
    res = sum(1 for d in dds if d >= threshold) / len(dds)
    logger.debug(
        f"drawdown_probability: computed drawdown probability for threshold {threshold}: {res}"
    )
    return res


def _raw_calculate_drawdown_metrics(
    equity_curve: Any,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate aggregate drawdown metrics from an equity curve."""
    logger.info(
        f"calculate_drawdown_metrics: starting calculation for request_id: {request_id}"
    )
    validate_request_id_strict(request_id)
    meta = build_metadata(
        tool_name="calculate_drawdown_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        parsed = _parse_equity_curve(equity_curve)
        if not parsed:
            raise ValidationError(
                "equity_curve must contain at least one valid data point."
            )
        equities = [eq for _, eq in parsed]
        dds = drawdown_series(equities)
        max_dd = max(dds, default=0.0) * 100.0
        durations = drawdown_duration_series(equity_curve)
        max_dur = max(durations, default=0.0)
        avg_dd_pct = _raw_avg_drawdown(equity_curve)
        data = {
            "max_drawdown_percent": max_dd,
            "max_drawdown_duration_hours": max_dur,
            "avg_drawdown_percent": avg_dd_pct,
            "avg_drawdown_duration_hours": _raw_avg_drawdown_duration(equity_curve),
            "ulcer_index": _raw_ulcer_index(equity_curve),
            "pain_index": _raw_pain_index(equity_curve),
            "drawdown_date": _raw_max_strategy_drawdown_date_from_parsed(parsed),
        }
        logger.info("calculate_drawdown_metrics: successfully calculated metrics.")
        return success_response(
            message="Successfully calculated drawdown metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as exc:
        logger.error(f"calculate_drawdown_metrics: error during calculation: {exc}")
        return response_from_exception(exception=exc, metadata=meta)


def _raw_max_strategy_drawdown_date_from_parsed(
    parsed: list[tuple[Any, float]],
) -> str:
    """Extract the ISO-8601 UTC timestamp at the deepest drawdown trough."""
    _fallback = "1970-01-01T00:00:00+00:00"
    if not parsed:
        logger.debug(
            "max_strategy_drawdown_date_from_parsed: empty parsed list, returning fallback"
        )
        return _fallback
    peak = parsed[0][1]
    max_dd = 0.0
    valley_time = parsed[0][0]
    for dt, eq in parsed:
        peak = max(peak, eq)
        if peak > 0:
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
                valley_time = dt
    res = valley_time.isoformat() if hasattr(valley_time, "isoformat") else _fallback
    logger.debug(f"max_strategy_drawdown_date_from_parsed: valley date is {res}")
    return res


def select_net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float,
    max_dd: float,
) -> float:
    """Express select net profit as a percentage of max drawdown.

    Args:
        net_prof: Net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio * 100; 0.0 when max_dd <= 0.
    """
    logger.debug("select_net_profit_as_percent_of_max_trade_drawdown: executed.")
    if max_dd <= 0:
        return 0.0
    return (net_prof / max_dd) * 100.0


def adjusted_net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float,
    max_dd: float,
) -> float:
    """Express adjusted net profit as a percentage of max drawdown.

    Args:
        net_prof: Adjusted net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio * 100; 0.0 when max_dd <= 0.
    """
    logger.debug("adjusted_net_profit_as_percent_of_max_trade_drawdown: executed.")
    if max_dd <= 0:
        return 0.0
    return (net_prof / max_dd) * 100.0


def net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float,
    max_dd: float,
) -> float:
    """Express net profit as a percentage of max drawdown.

    Args:
        net_prof: Net profit value.
        max_dd: Maximum drawdown value.

    Returns:
        Ratio * 100; 0.0 when max_dd <= 0.
    """
    logger.debug("net_profit_as_percent_of_max_trade_drawdown: executed.")
    if max_dd <= 0:
        return 0.0
    return (net_prof / max_dd) * 100.0
