"""Indicator-series query contracts and owner-result projection."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Literal, cast

import pandas as pd

from app.services.api import build_api_metadata, build_api_response

type ChartIndicatorId = Literal["ema", "rsi"]
type IndicatorSource = Literal["open", "high", "low", "close"]


def _json_value(value: object) -> float | None:
    """Return one finite indicator value or an explicit unavailable marker."""
    if value is None or pd.isna(value):
        return None
    number = float(cast("Any", value))
    return number if math.isfinite(number) else None


def build_indicator_series_response(
    response: object,
    *,
    indicator_id: ChartIndicatorId,
    symbol: str,
    timeframe: str,
    period: int,
    source: IndicatorSource,
    source_id: str,
    request_id: str,
) -> object:
    """Project one Indicators-owned result without recalculating its values.

    Returns:
        API response carrying timestamp-aligned values and owner metadata.
    """
    status = str(getattr(response, "status", "error"))
    result = getattr(response, "data", None)
    upstream_error = getattr(response, "error", None)
    error = None
    payload = None

    if status == "success" and result is not None:
        from app.services.indicators import (
            get_indicator_result_metadata,
            get_indicator_result_values,
        )

        frame = get_indicator_result_values(result)
        metadata = get_indicator_result_metadata(result)
        output_columns = cast("tuple[str, ...]", metadata["output_columns"])
        value_column = str(output_columns[0])
        points = []
        for timestamp, row in frame.iterrows():
            reason = row.get("unavailable_reason")
            points.append(
                {
                    "time": timestamp.isoformat(),
                    "value": _json_value(row[value_column]),
                    "unavailable_reason": (
                        None if reason is None or pd.isna(reason) else str(reason)
                    ),
                }
            )
        valid_count = sum(point["value"] is not None for point in points)
        payload = {
            "indicator_id": indicator_id,
            "name": "Exponential Moving Average"
            if indicator_id == "ema"
            else "Relative Strength Index",
            "symbol": symbol,
            "timeframe": timeframe,
            "source_id": source_id,
            "parameters": {"period": period, "source": source},
            "points": points,
            "count": len(points),
            "valid_count": valid_count,
            "availability": "available" if valid_count else "insufficient_history",
            "unavailable_reason": None if valid_count else "warmup",
            "indicator_version": str(metadata["indicator_version"]),
            "formula_version": str(metadata["formula_version"]),
            "request_id": request_id,
        }
    else:
        details = getattr(upstream_error, "details", {})
        error = {
            "code": "INDICATOR_UNAVAILABLE",
            "message": str(getattr(upstream_error, "message", "Indicator unavailable")),
            "details": dict(details) if isinstance(details, Mapping) else {},
            "retryable": bool(getattr(upstream_error, "retryable", False)),
            "request_id": request_id,
            "trace_id": None,
        }

    return build_api_response(
        status=status,
        message="Indicator series calculated"
        if payload is not None
        else "Indicator unavailable",
        data=payload,
        error=error,
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/indicators/{indicator_id}/series",
            operation="api.indicators.series",
            side_effect="read",
        ),
    )


__all__ = (
    "ChartIndicatorId",
    "IndicatorSource",
    "build_indicator_series_response",
)
