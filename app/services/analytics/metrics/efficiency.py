# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100, ANN401
"""MAE/MFE and return-efficiency calculations (ANL-NFR-121)."""

from __future__ import annotations

import datetime
import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.position_exposure import time_in_market_duration
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    classify_trades,
    get_closed_trades,
    get_ordered_closed_trades,
    parse_utc_time,
)
from app.utils.logger import logger

type TradeRecord = dict[str, Any]
type Duration = datetime.timedelta | float


def metrics_efficiency_boundary() -> dict[str, bool]:
    """Describe efficiency metric boundary declarations.

    Returns:
        Boundary evidence that efficiency helpers are pure analytics kernels.
    """
    logger.debug("metrics_efficiency_boundary: executed.")
    return {
        "file_specific_non_functional_requirements_defined": False,
        "file_specific_testing_requirements_defined": False,
        "read_only": True,
        "pure_metric_kernel": True,
    }


def _get_trade_duration(trade: dict[str, Any]) -> float:
    """Calculate trade duration in hours from open/close timestamps.

    Args:
        trade (dict[str, Any]): Input parameter `trade`.

    Returns:
        Calculated float value.
    """
    logger.debug("_get_trade_duration: executed.")
    ot = parse_utc_time(trade.get("open_time") or trade.get("open_timestamp"))
    ct = parse_utc_time(trade.get("close_time") or trade.get("close_timestamp"))
    if ot and ct:
        return max((ct - ot).total_seconds() / 3600.0, 0.0)
    return 0.0


def _sorted_median(values: list[float]) -> float:
    """Expose behavior for `_sorted_median`.

    Args:
        values (list[float]): Sequence of numeric values.

    Returns:
        Calculated float value.
    """
    logger.debug("_sorted_median: executed.")
    n = len(values)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return values[n // 2]
    return (values[n // 2 - 1] + values[n // 2]) / 2.0


def avg_trade_notional_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate mean PnL per unit of notional exposure (ANL-NFR-121).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_trade_notional_efficiency: executed.")
    closed = get_closed_trades(trades)
    if not closed:
        return MetricResult(value=0.0)
    effs = []
    for t in closed:
        pnl = abs(_get_trade_pnl(t))
        exposure = float(t.get("size") or t.get("volume") or 0.0) * float(
            t.get("open_price", 1.0)
        )
        if exposure > 0:
            effs.append(pnl / exposure)
    val = sum(effs) / len(effs) if effs else 0.0
    return MetricResult(value=val)


def return_per_trade_hour(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit per hour spent in active trades (ANL-NFR-123).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_per_trade_hour: executed.")
    closed = get_closed_trades(trades)
    pnl = sum(_get_trade_pnl(t) for t in closed)
    tot_hours = sum(_get_trade_duration(t) for t in closed)
    val = pnl / tot_hours if tot_hours > 0 else 0.0
    return MetricResult(value=val)


def return_per_market_hour(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit per hour where at least one trade was open (ANL-NFR-124).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_per_market_hour: executed.")
    closed = get_closed_trades(trades)
    pnl = sum(_get_trade_pnl(t) for t in closed)
    tot_hours = time_in_market_duration(trades)
    val = pnl / tot_hours if tot_hours > 0 else 0.0
    return MetricResult(value=val)


def trades_per_day(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average number of closed trades per calendar day (ANL-NFR-125).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("trades_per_day: executed.")
    closed = get_closed_trades(trades)
    # Default 30.0 days if not set
    duration_days = float(
        config.metadata.get("duration_days", 30.0) if config else 30.0
    )
    if duration_days <= 0:
        return MetricResult(value=0.0)
    val = len(closed) / duration_days
    return MetricResult(value=val)


def profit_per_trade_per_day(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit normalized by both trades and calendar days (ANL-NFR-126).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("profit_per_trade_per_day: executed.")
    closed = get_closed_trades(trades)
    duration_days = float(
        config.metadata.get("duration_days", 30.0) if config else 30.0
    )
    if not closed or duration_days <= 0:
        return MetricResult(value=0.0)
    # Expectancy is mean PnL per trade
    expectancy = sum(_get_trade_pnl(t) for t in closed) / len(closed)
    val = expectancy / duration_days
    return MetricResult(value=val)


def mfe_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average percentage of MFE captured by winning trades (ANL-NFR-127).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("mfe_efficiency: executed.")
    wins = classify_trades(trades, config)["wins"]
    if not wins:
        return MetricResult(value=1.0)
    effs = []
    for t in wins:
        mfe = float(t.get("mfe") or 0.0)
        pnl = _get_trade_pnl(t)
        if mfe > 0:
            effs.append(pnl / mfe)
    val = sum(effs) / len(effs) if effs else 1.0
    return MetricResult(value=val)


def aggregate_mfe_capture_ratio(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate aggregate MFE capture ratio for winning trades (ANL-NFR-128).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("aggregate_mfe_capture_ratio: executed.")
    return mfe_efficiency(trades, config)


def mae_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate realized-loss-to-MAE efficiency for losing trades (ANL-NFR-129).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("mae_efficiency: executed.")
    losses = classify_trades(trades, config)["losses"]
    if not losses:
        return MetricResult(value=1.0)
    effs = []
    for t in losses:
        mae = float(t.get("mae") or 0.0)
        pnl = abs(_get_trade_pnl(t))
        if mae > 0:
            effs.append(pnl / mae)
    val = sum(effs) / len(effs) if effs else 1.0
    return MetricResult(value=val)


def aggregate_loss_containment_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate aggregate loss containment for losing trades (ANL-NFR-130).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("aggregate_loss_containment_efficiency: executed.")
    losses = classify_trades(trades, config)["losses"]
    if not losses:
        return MetricResult(value=1.0)
    efficiencies = []
    for t in losses:
        mae = abs(float(t.get("mae") or 0.0))
        pnl = abs(_get_trade_pnl(t))
        if mae > 0:
            eff = (mae - pnl) / mae
            efficiencies.append(max(min(eff, 1.0), 0.0))
    val = sum(efficiencies) / len(efficiencies) if efficiencies else 1.0
    return MetricResult(value=val)


def position_size_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate relationship between position size and normalized trade outcome (ANL-NFR-131).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("position_size_efficiency: executed.")
    closed = get_closed_trades(trades)
    if len(closed) < 2:
        return MetricResult(value=0.0)
    sizes = [float(t.get("size") or t.get("volume") or 0.0) for t in closed]
    pnls = [_get_trade_pnl(t) for t in closed]
    n = len(closed)
    mean_s = sum(sizes) / n
    mean_p = sum(pnls) / n
    num = sum((sizes[i] - mean_s) * (pnls[i] - mean_p) for i in range(n))
    den_s = sum((x - mean_s) ** 2 for x in sizes)
    den_p = sum((x - mean_p) ** 2 for x in pnls)
    if den_s == 0 or den_p == 0:
        return MetricResult(value=0.0)
    val = num / math.sqrt(den_s * den_p)
    return MetricResult(value=val)


def calculate_efficiency_metrics(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate aggregate MAE/MFE efficiency context from trades (ANL-NFR-132).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("calculate_efficiency_metrics: executed.")
    mfe_eff = mfe_efficiency(trades, config).value or 0.0
    mae_eff = mae_efficiency(trades, config).value or 0.0
    return MetricResult(value={"mfe_efficiency": mfe_eff, "mae_efficiency": mae_eff})


def trade_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate realized outcome relative to maximum favorable excursion (ANL-NFR-157).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("trade_efficiency: executed.")
    # Note: Target signature uses Sequence[TradeRecord] but expects single trade.
    # We will handle both cases: if trades has elements, evaluate first element.
    if not trades:
        return MetricResult(value=0.0)
    trade = trades[0]
    pnl = _get_trade_pnl(trade)
    mfe = float(trade.get("mfe") or 0.0)
    if mfe <= 0:
        return MetricResult(value=0.0)
    val = max(pnl / mfe, -1.0)
    return MetricResult(value=val)


def longest_flat_period_duration(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate longest period without an active trade (ANL-NFR-159).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("longest_flat_period_duration: executed.")
    ordered = get_ordered_closed_trades(trades)
    if not ordered:
        return MetricResult(value=0.0)
    max_flat = 0.0
    period_start = config.metadata.get("period_start") if config else None
    period_end = config.metadata.get("period_end") if config else None
    prev_close = parse_utc_time(period_start) if period_start else None
    for t in ordered:
        ot = parse_utc_time(t.get("open_time") or t.get("open_timestamp"))
        ct = parse_utc_time(t.get("close_time") or t.get("close_timestamp"))
        if prev_close and ot:
            flat = (ot - prev_close).total_seconds() / 3600.0
            max_flat = max(max_flat, flat)
        prev_close = ct
    if period_end and prev_close:
        end = parse_utc_time(period_end)
        if end:
            flat = (end - prev_close).total_seconds() / 3600.0
            max_flat = max(max_flat, flat)
    return MetricResult(value=max_flat)


def capital_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate return per unit of nominal capital deployed (ANL-NFR-368).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("capital_efficiency: executed.")
    closed = get_closed_trades(trades)
    net_p = sum(_get_trade_pnl(t) for t in closed)
    nominal_capital_deployed = float(
        config.metadata.get("nominal_capital_deployed", 10000.0) if config else 10000.0
    )
    if nominal_capital_deployed <= 0:
        return MetricResult(value=0.0)
    val = net_p / nominal_capital_deployed
    return MetricResult(value=val)


def return_per_unit_mae(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate total return relative to adverse excursion experienced (ANL-NFR-369).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_per_unit_mae: executed.")
    closed = get_closed_trades(trades)
    net_prof = sum(_get_trade_pnl(t) for t in closed)
    total_mae = sum(abs(float(t.get("mae") or 0.0)) for t in closed)
    if total_mae <= 0:
        return MetricResult(value=0.0)
    val = net_prof / total_mae
    return MetricResult(value=val)


def return_per_calendar_day(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate net profit per calendar day in the test period (ANL-NFR-370).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("return_per_calendar_day: executed.")
    closed = get_closed_trades(trades)
    net_p = sum(_get_trade_pnl(t) for t in closed)
    duration_days = float(
        config.metadata.get("duration_days", 30.0) if config else 30.0
    )
    if duration_days <= 0:
        return MetricResult(value=0.0)
    val = net_p / duration_days
    return MetricResult(value=val)


def exit_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate combined win-capture and loss-containment efficiency (ANL-NFR-371).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("exit_efficiency: executed.")
    win_eff = mfe_efficiency(trades, config).value or 0.0
    loss_eff = aggregate_loss_containment_efficiency(trades, config).value or 0.0
    val = (win_eff + loss_eff) / 2.0
    return MetricResult(value=val)


def loss_containment_efficiency(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate how well realized losses stayed above their adverse excursion (ANL-NFR-372).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("loss_containment_efficiency: executed.")
    return aggregate_loss_containment_efficiency(trades, config)


def median_mae_mfe(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate median MAE and MFE values (ANL-NFR-375).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("median_mae_mfe: executed.")
    maes = sorted(float(t.get("mae") or 0.0) for t in trades if "mae" in t)
    mfes = sorted(float(t.get("mfe") or 0.0) for t in trades if "mfe" in t)
    val = {"mae": _sorted_median(maes), "mfe": _sorted_median(mfes)}
    return MetricResult(value=val)


def get_mae_mfe_r(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> tuple[dict[str, float], ...]:
    """Calculate MAE and MFE normalized to R-space (ANL-NFR-376).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        Calculated tuple[dict[str, float], ...] value.
    """
    logger.debug("get_mae_mfe_r: executed.")
    result = []
    for t in trades:
        risk = float(t.get("initial_risk") or 1.0)
        mae = float(t.get("mae") or 0.0)
        mfe = float(t.get("mfe") or 0.0)
        result.append({"mae_r": mae / risk, "mfe_r": mfe / risk})
    return tuple(result)


def median_mae_r(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate median MAE in R-multiple terms (ANL-NFR-377).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("median_mae_r: executed.")
    r_maes = sorted(
        float(t.get("mae") or 0.0) / float(t.get("initial_risk") or 1.0) for t in trades
    )
    val = _sorted_median(r_maes)
    return MetricResult(value=val)


def median_mfe_r(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate median MFE in R-multiple terms (ANL-NFR-378).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("median_mfe_r: executed.")
    r_mfes = sorted(
        float(t.get("mfe") or 0.0) / float(t.get("initial_risk") or 1.0) for t in trades
    )
    val = _sorted_median(r_mfes)
    return MetricResult(value=val)
