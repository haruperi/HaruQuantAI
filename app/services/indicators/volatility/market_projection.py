"""Market-row volatility and range projection owned by Indicators."""

from __future__ import annotations

import math
from typing import Any, cast

from app.services.indicators.volatility.adr import adr
from app.services.indicators.volatility.rolling_volatility import rolling_volatility

_ADR_PERIOD = 10
_VOLATILITY_PERIOD = 10
_ANNUALIZATION_FACTOR = 252.0
_FRACTIONAL_PIP_DIGITS = frozenset({3, 5})
_PRIOR_VALUE_MIN_LENGTH = 2


def _prior_value(result: object) -> float | None:
    """Return the prior settled value from an indicator response.

    Args:
        result: Indicators standard response.

    Returns:
        Prior settled numeric value, or ``None`` when unavailable.
    """
    data = getattr(result, "data", None)
    output_columns = getattr(data, "output_columns", ())
    values = getattr(data, "values", None)
    prior: object | None = None
    try:
        if (
            getattr(result, "status", None) == "success"
            and output_columns
            and values is not None
        ):
            series = values[output_columns[0]]
            if len(series) >= _PRIOR_VALUE_MIN_LENGTH:
                prior = series.iloc[-2] if hasattr(series, "iloc") else series[-2]
    except AttributeError, IndexError, KeyError, TypeError:
        return None
    if prior is None:
        return None
    try:
        numeric = float(cast("Any", prior))
    except TypeError, ValueError:
        return None
    return numeric if math.isfinite(numeric) else None


def project_market_overlay(
    dataset: object,
    *,
    digits: int,
    point: float,
    last_price: float | None,
) -> dict[str, float | None]:
    """Project a market row from settled volatility and price evidence.

    Args:
        dataset: Data-owned market dataset accepted by public indicators.
        digits: Broker quote precision.
        point: Broker point size in price units.
        last_price: Current quote price, when available.

    Returns:
        Nullable display evidence for the API markets gateway.

    Raises:
        ValueError: If quote precision or dataset evidence is invalid.
    """
    if point <= 0:
        raise ValueError("point must be positive")
    records = cast("tuple[Any, ...]", getattr(dataset, "records", ()))
    if len(records) < _ADR_PERIOD + 2:
        raise ValueError("insufficient settled bars")

    latest = records[-1]
    open_price = float(latest.open)
    high = float(latest.high)
    low = float(latest.low)
    pip_size = point * 10.0 if digits in _FRACTIONAL_PIP_DIGITS else point
    volatility_raw = _prior_value(
        rolling_volatility(
            cast("Any", dataset),
            period=_VOLATILITY_PERIOD,
            annualization_factor=_ANNUALIZATION_FACTOR,
        )
    )
    adr_raw = _prior_value(adr(cast("Any", dataset), period=_ADR_PERIOD))
    change = last_price - open_price if last_price is not None else None

    return {
        "open": open_price,
        "high": high,
        "low": low,
        "change": change,
        "change_percent": (
            change / open_price * 100.0
            if change is not None and open_price != 0
            else None
        ),
        "change_pips": change / pip_size if change is not None else None,
        "volatility": volatility_raw,
        "adr": round(adr_raw / pip_size, 1) if adr_raw and adr_raw > 0 else None,
        "range_percent_of_adr": (
            round(((high - low) / adr_raw) * 100.0, 1)
            if adr_raw and adr_raw > 0
            else None
        ),
    }


__all__ = ("project_market_overlay",)
