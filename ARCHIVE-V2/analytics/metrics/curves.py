# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Balance and equity curve construction (ANL-NFR-167)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.trade_outcomes import (
    _get_trade_pnl,
    get_ordered_closed_trades,
    parse_utc_time,
)
from app.utils.logger import logger

type TradeRecord = dict[str, Any]


def balance_curve_from_closed_trades(
    trades: Sequence[TradeRecord],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Build an equity curve dict-list from ordered closed trades (ANL-NFR-167).

    Args:
        trades: Sequence of trade record dictionaries.
        initial_balance: Starting balance for the account.
        currency: Account currency.

    Returns:
        List of dictionaries with keys "timestamp", "equity", and "currency".
    """
    logger.debug("balance_curve_from_closed_trades: starting curve construction.")
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
    logger.debug(
        f"balance_curve_from_closed_trades: created curve with {len(curve)} points."
    )
    return curve


def balance_curve(
    trades: Sequence[TradeRecord],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Alias for balance_curve_from_closed_trades (ANL-NFR-168).

    Args:
        trades: Sequence of trade record dictionaries.
        initial_balance: Starting balance for the account.
        currency: Account currency.

    Returns:
        List of dictionaries representing the balance curve.
    """
    res = balance_curve_from_closed_trades(trades, initial_balance, currency)
    logger.debug(f"balance_curve: generated curve of length {len(res)}")
    return res


def balance_curve_metric(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[list[dict[str, Any]]]:
    """Expose balance-curve behavior as a metric (ANL-NFR-168).

    Args:
        input_value: Sequence of trade record dictionaries.
        config: Metric configuration.

    Returns:
        MetricResult containing list of dictionaries representing the balance curve.
    """
    logger.debug("balance_curve_metric: starting metric calculation.")
    trades = input_value if isinstance(input_value, Sequence) else ()
    initial_balance = float(
        config.metadata.get("initial_balance", 10000.0) if config else 10000.0
    )
    currency = str(config.metadata.get("currency", "USD") if config else "USD")
    val = balance_curve(trades, initial_balance, currency)
    logger.debug("balance_curve_metric: metric calculation finished.")
    return MetricResult(value=val)


def equity_curve(
    trades: Sequence[TradeRecord],
    initial_balance: float = 10000.0,
    currency: str = "USD",
) -> list[dict[str, Any]]:
    """Alias for balance_curve_from_closed_trades (ANL-NFR-169).

    Args:
        trades: Sequence of trade record dictionaries.
        initial_balance: Starting balance for the account.
        currency: Account currency.

    Returns:
        List of dictionaries representing the equity curve.
    """
    res = balance_curve_from_closed_trades(trades, initial_balance, currency)
    logger.debug(f"equity_curve: generated curve of length {len(res)}")
    return res


def equity_curve_metric(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[list[dict[str, Any]]]:
    """Expose equity-curve behavior as a metric (ANL-NFR-169).

    Args:
        input_value: Sequence of trade record dictionaries.
        config: Metric configuration.

    Returns:
        MetricResult containing list of dictionaries representing the equity curve.
    """
    res = balance_curve_metric(input_value, config)
    logger.debug("equity_curve_metric: metric calculation finished.")
    return res
