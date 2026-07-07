# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Balance and equity curve construction (ANL-NFR-167)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.analytics._helpers import parse_utc_time
from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    get_ordered_closed_trades,
)

type TradeRecord = dict[str, Any]


def balance_curve_from_closed_trades(
    trades: Sequence[TradeRecord],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Build an equity curve dict-list from ordered closed trades (ANL-NFR-167)."""
    ordered = get_ordered_closed_trades(trades)
    curve: list[dict[str, Any]] = []
    current_balance = initial_balance
    start_time = "1970-01-01T00:00:00+00:00"
    if ordered:
        ot_raw = ordered[0].get("open_time") or ordered[0].get("open_timestamp")
        dt = parse_utc_time(ot_raw)
        if dt:
            start_time = dt.isoformat()
        elif isinstance(ot_raw, str):
            start_time = ot_raw
    curve.append(
        {
            "timestamp": start_time,
            "equity": current_balance,
            "currency": currency,
        }
    )
    for t in ordered:
        current_balance += _get_trade_pnl(t)
        ct_raw = t.get("close_time") or t.get("close_timestamp")
        dt = parse_utc_time(ct_raw)
        if dt:
            timestamp = dt.isoformat()
        elif isinstance(ct_raw, str):
            timestamp = ct_raw
        else:
            timestamp = "1970-01-01T00:00:00+00:00"
        curve.append(
            {
                "timestamp": timestamp,
                "equity": current_balance,
                "currency": currency,
            }
        )
    return curve


def balance_curve(
    trades: Sequence[TradeRecord],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Alias for balance_curve_from_closed_trades (ANL-NFR-168)."""
    return balance_curve_from_closed_trades(trades, initial_balance, currency)


def balance_curve_metric(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[list[dict[str, Any]]]:
    """Expose balance-curve behavior as a metric (ANL-NFR-168)."""
    # Assuming input_value is trades Sequence
    trades = input_value if isinstance(input_value, Sequence) else ()
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    currency = str(config.metadata.get("currency", "USD") if config else "USD")
    val = balance_curve(trades, initial_balance, currency)
    return MetricResult(value=val)


def equity_curve(
    trades: Sequence[TradeRecord],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Alias for balance_curve_from_closed_trades (ANL-NFR-169)."""
    return balance_curve_from_closed_trades(trades, initial_balance, currency)


def equity_curve_metric(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[list[dict[str, Any]]]:
    """Expose equity-curve behavior as a metric (ANL-NFR-169)."""
    return balance_curve_metric(input_value, config)
