"""Currency strength implementations and official AI Tools for HaruQuant.

This module computes deterministic FX pair strength and aggregate currency
strength from validated OHLCV data. It supports either a single pair DataFrame
or a mapping of pair symbol to DataFrame/records.

Classes:
    None.

Functions:
    calculate_pair_strength_frame: Internal pair-strength implementation.
    calculate_currency_strength_frame: Internal currency-strength implementation.
    calculate_pair_strength: Official AI Tool for one pair.
    calculate_currency_strength: Official AI Tool for multiple pairs.
    get_top_pairs: Official AI Tool for ranking strongest/weakest pairs.
    currency_strength_indicator: Official AI Tool alias for aggregate strength.

Exported AI Tools:
    calculate_pair_strength, calculate_currency_strength, get_top_pairs,
    currency_strength_indicator.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from tools.utils.standard import ToolSpec, run_indicator_tool
from tools.utils.validators import (
    apply_warmup_policy,
    ensure_dataframe,
    require_columns,
    require_positive_int,
)

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "indicators"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

DEFAULT_CURRENCIES = ("EUR", "GBP", "USD", "JPY", "CHF", "AUD", "NZD", "CAD")


def _split_pair(symbol: str) -> tuple[str, str]:
    normalized = symbol.replace("/", "").replace("_", "").upper()
    if len(normalized) != 6:
        raise ValueError("symbol must be a six-character FX pair such as EURUSD")
    return normalized[:3], normalized[3:]


def calculate_pair_strength_frame(
    data: Any,
    *,
    symbol: str,
    period: int = 14,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
) -> pd.DataFrame:
    """Calculate rolling percentage-change pair strength for one FX pair."""
    require_positive_int(period, name="period")
    _split_pair(symbol)
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    col = output_col or f"{symbol.upper()}_pair_strength_{period}"
    frame[col] = frame[price_col].pct_change(periods=period) * 100.0
    return apply_warmup_policy(
        frame, col, warmup_policy=warmup_policy, fill_value=fill_value
    )


def _series_pair_strength(data: Any, *, period: int, price_col: str) -> pd.Series:
    frame = ensure_dataframe(data)
    require_columns(frame, (price_col,))
    return frame[price_col].pct_change(periods=period) * 100.0


def calculate_currency_strength_frame(
    pair_data: Mapping[str, Any],
    *,
    period: int = 14,
    price_col: str = "close",
    currencies: tuple[str, ...] = DEFAULT_CURRENCIES,
) -> pd.DataFrame:
    """Aggregate individual currency strength from multiple FX pairs.

    Base currency strength receives the pair percentage change. Quote currency
    strength receives the inverse change. Values are averaged across available
    pairs at each timestamp.
    """
    require_positive_int(period, name="period")
    if not isinstance(pair_data, Mapping) or not pair_data:
        raise ValueError("pair_data must be a non-empty mapping of symbol to data")

    currency_series: dict[str, list[pd.Series]] = {
        currency: [] for currency in currencies
    }
    reference_index: pd.Index | None = None

    for symbol, data in pair_data.items():
        base, quote = _split_pair(symbol)
        strength = _series_pair_strength(data, period=period, price_col=price_col)
        if reference_index is None:
            reference_index = strength.index
        strength = strength.reindex(reference_index)
        if base in currency_series:
            currency_series[base].append(strength)
        if quote in currency_series:
            currency_series[quote].append(-strength)

    if reference_index is None:
        raise ValueError("pair_data did not contain usable series")

    result = pd.DataFrame(index=reference_index)
    for currency, series_list in currency_series.items():
        if series_list:
            result[currency] = pd.concat(series_list, axis=1).mean(axis=1)
        else:
            result[currency] = pd.NA
    currency_columns = list(currencies)

    def _idxmax_or_na(row: pd.Series) -> object:
        valid = row.dropna()
        return valid.idxmax() if not valid.empty else pd.NA

    def _idxmin_or_na(row: pd.Series) -> object:
        valid = row.dropna()
        return valid.idxmin() if not valid.empty else pd.NA

    result["strongest_currency"] = result[currency_columns].apply(_idxmax_or_na, axis=1)
    result["weakest_currency"] = result[currency_columns].apply(_idxmin_or_na, axis=1)
    return result


def calculate_pair_strength(
    data: Any,
    symbol: str,
    period: int = 14,
    price_col: str = "close",
    output_col: str | None = None,
    warmup_policy: str = "nan",
    fill_value: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate rolling pair strength as an official AI Tool.

    Use this read-only tool when an agent needs a pair-specific FX strength
    feature before ranking or strategy analysis.
    """
    return run_indicator_tool(
        ToolSpec(tool_name="calculate_pair_strength"),
        lambda: calculate_pair_strength_frame(
            data,
            symbol=symbol,
            period=period,
            price_col=price_col,
            output_col=output_col,
            warmup_policy=warmup_policy,
            fill_value=fill_value,
        ),
        request_id=request_id,
    )


def calculate_currency_strength(
    pair_data: Mapping[str, Any],
    period: int = 14,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Calculate aggregate major-currency strength as an official AI Tool."""
    return run_indicator_tool(
        ToolSpec(tool_name="calculate_currency_strength"),
        lambda: calculate_currency_strength_frame(
            pair_data,
            period=period,
            price_col=price_col,
        ),
        request_id=request_id,
    )


def currency_strength_indicator(
    pair_data: Mapping[str, Any],
    period: int = 14,
    price_col: str = "close",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Alias-style AI Tool for aggregate currency strength calculation."""
    return run_indicator_tool(
        ToolSpec(tool_name="currency_strength_indicator"),
        lambda: calculate_currency_strength_frame(
            pair_data,
            period=period,
            price_col=price_col,
        ),
        request_id=request_id,
    )


def get_top_pairs(
    pair_data: Mapping[str, Any],
    period: int = 14,
    price_col: str = "close",
    top_n: int = 5,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Rank FX pairs by latest absolute pair strength.

    Use this tool when an agent needs the strongest and weakest pairs from a
    validated universe of pair data.
    """

    def _operation() -> dict[str, Any]:
        require_positive_int(top_n, name="top_n")
        rows: list[dict[str, Any]] = []
        for symbol, data in pair_data.items():
            strength = _series_pair_strength(data, period=period, price_col=price_col)
            latest = (
                strength.dropna().iloc[-1] if not strength.dropna().empty else pd.NA
            )
            rows.append({"symbol": symbol.upper(), "latest_strength": latest})
        ranking = pd.DataFrame(rows).sort_values("latest_strength", ascending=False)
        return {
            "top_strength": ranking.head(top_n),
            "top_weakness": ranking.tail(top_n).sort_values("latest_strength"),
        }

    return run_indicator_tool(
        ToolSpec(tool_name="get_top_pairs"),
        _operation,
        request_id=request_id,
    )
