# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Spread, slippage, and commission cost drag calculations (ANL-NFR-047)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.position_exposure import (
    commission_paid,
    slippage_paid,
)

type TradeRecord = dict[str, Any]


def calculate_spread_cost_impact(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate spread cost drag (ANL-NFR-047)."""
    val = sum(float(t.get("spread_cost") or 0.0) for t in trades)
    return MetricResult(value=val)


def calculate_slippage_impact(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate slippage cost drag (ANL-NFR-048)."""
    res = slippage_paid(trades, config)
    return MetricResult(value=res.value)


def calculate_commission_impact(
    trades: Sequence[TradeRecord],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate commission cost drag (ANL-NFR-049)."""
    res = commission_paid(trades, config)
    return MetricResult(value=res.value)
