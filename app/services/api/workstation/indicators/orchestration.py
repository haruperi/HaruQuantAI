"""Uncached Data-to-Indicators orchestration for chart series."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from app.services.api.workstation.indicators.schemas import (
    ChartIndicatorId,
    IndicatorSource,
    build_indicator_series_response,
)
from app.services.api.workstation.markets import resolve_runtime_source_id
from app.services.data import build_market_data_request, get_market_data
from app.services.indicators import ema, rsi


def orchestrate_indicator_series(
    *,
    indicator_id: ChartIndicatorId,
    symbol: str,
    timeframe: str,
    period: int,
    source: IndicatorSource,
    limit: int,
    start: datetime | None,
    end: datetime | None,
    source_id: str | None,
    request_id: str,
) -> object:
    """Fetch uncached bars and delegate one official indicator calculation.

    Returns:
        API response carrying the projected owner result.
    """
    resolved_source_id = resolve_runtime_source_id(source_id, request_id=request_id)
    market_response = get_market_data(
        cast(
            "Any",
            build_market_data_request(
                source_id=resolved_source_id,
                symbol=symbol,
                data_kind="bars",
                timeframe=timeframe,
                limit=limit,
                start=start,
                end=end,
                use_cache=False,
                quality_failure_behavior="warn",
                workflow_context="research",
                precision_policy="decimal_string",
                request_id=request_id,
            ),
        )
    )
    dataset = getattr(market_response, "data", None)
    if getattr(market_response, "status", None) != "success" or dataset is None:
        return build_indicator_series_response(
            market_response,
            indicator_id=indicator_id,
            symbol=symbol,
            timeframe=timeframe,
            period=period,
            source=source,
            source_id=resolved_source_id,
            request_id=request_id,
        )

    calculation = ema if indicator_id == "ema" else rsi
    response = calculation(dataset, period=period, source=source)
    return build_indicator_series_response(
        response,
        indicator_id=indicator_id,
        symbol=symbol,
        timeframe=timeframe,
        period=period,
        source=source,
        source_id=resolved_source_id,
        request_id=request_id,
    )


__all__ = ("orchestrate_indicator_series",)
