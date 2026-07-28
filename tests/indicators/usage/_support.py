"""Shared response helpers for Indicators usage evidence."""

from __future__ import annotations

from typing import TypeVar

from app.services.data import MarketDataset, unwrap_data_response
from app.utils import StandardResponse

_ResponseT = TypeVar("_ResponseT")


def unwrap_indicator_response(response: StandardResponse[_ResponseT]) -> _ResponseT:
    """Return successful Indicators data or fail with its safe error message."""
    if response.status != "success" or response.data is None:
        error = response.error
        detail = error.message if error is not None else "unknown indicator failure"
        raise RuntimeError(detail)
    return response.data


def unwrap_market_data_response(
    response: StandardResponse[MarketDataset],
) -> MarketDataset:
    """Return Data's raw dataset while preserving DataError failures."""
    return unwrap_data_response(
        response,
        operation="indicators.usage.get_market_data",
        request_id=response.metadata.request_id,
    )


__all__ = ["unwrap_indicator_response", "unwrap_market_data_response"]
