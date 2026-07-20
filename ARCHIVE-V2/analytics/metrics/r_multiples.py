# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""R-multiple metrics calculation kernel (ANL-NFR-114).

Calculates R-multiples, return per risk, and aggregate R-space trade metrics.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.trade_outcomes import _get_trade_pnl
from app.utils.logger import logger

type TradeRecord = dict[str, Any]


def get_r_multiples(
    trades: Sequence[TradeRecord],
    config: MetricConfig | None = None,
) -> tuple[list[float], list[str]]:
    """Calculate R-multiples for each trade (ANL-NFR-114).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig | None): Metric configuration.

    Returns:
        Calculated tuple[list[float], list[str]] value.
    """
    logger.debug("get_r_multiples: executed.")
    r_multiples: list[float] = []
    warnings: list[str] = []
    proxy_count = 0
    for t in trades:
        pnl = _get_trade_pnl(t)
        raw_risk = t.get("initial_risk") or t.get("risk") or t.get("risk_amount")
        if raw_risk is None or float(raw_risk) <= 0:
            risk = 1.0
            proxy_count += 1
        else:
            risk = float(raw_risk)
        r_multiples.append(pnl / risk)
    if proxy_count:
        warnings.append(
            f"DEGRADED_CONFIDENCE: {proxy_count} trade(s) lacked"
            " initial_risk; R-multiple proxy (risk=1.0) was used."
            " Treat R-multiple metrics as estimates only."
        )
    return r_multiples, warnings


def avg_return_per_risk_unit(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate average R-multiple per closed trade (ANL-NFR-122).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("avg_return_per_risk_unit: executed.")
    r_mults, _ = get_r_multiples(trades, config)
    val = sum(r_mults) / len(r_mults) if r_mults else 0.0
    return MetricResult(value=val)


def compute_r_trade_metrics(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate trade metrics from R-multiple inputs (ANL-NFR-155).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("compute_r_trade_metrics: executed.")
    r_multiples, _ = get_r_multiples(trades, config)
    if not r_multiples:
        return MetricResult(value={"avg": 0.0, "std": 0.0, "expectancy": 0.0})
    n = len(r_multiples)
    avg = sum(r_multiples) / n
    var = sum((x - avg) ** 2 for x in r_multiples) / max(n - 1, 1)
    val = {"avg": avg, "std": math.sqrt(var), "expectancy": avg}
    return MetricResult(value=val)


def compute_trade_metrics(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate trade metrics from numeric R values and optional MAE/MFE arrays (ANL-NFR-156).

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("compute_trade_metrics: executed.")
    return compute_r_trade_metrics(trades, config)


def _get_r_multiples_flat(trades: Sequence[TradeRecord]) -> list[float]:
    """Helper to extract a flat list of R-multiples.

    Args:
        trades (Sequence[TradeRecord]): Sequence of trade record dictionaries.

    Returns:
        List of float R-multiples.
    """
    logger.debug("_get_r_multiples_flat: executed.")
    return get_r_multiples(trades)[0]
