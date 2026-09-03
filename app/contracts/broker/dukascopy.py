"""Dukascopy JForex provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class DukascopyErrorCode(IntEnum):
    """Dukascopy JForex API error codes."""

    SUCCESS = 0
    GENERIC_ERROR = -1
    INVALID_CREDENTIALS = -2
    CONNECTION_FAILED = -3
    SUBSCRIPTION_FAILED = -4
    ORDER_REJECTED = -5
    INSTRUMENT_NOT_FOUND = -6
    POSITION_NOT_FOUND = -7
    TIMEOUT = -8
    DATA_UNAVAILABLE = -9


DUKASCOPY_ERROR_DESCRIPTIONS: dict[int, str] = {
    DukascopyErrorCode.SUCCESS: "Success",
    DukascopyErrorCode.GENERIC_ERROR: "Generic Dukascopy JForex error",
    DukascopyErrorCode.INVALID_CREDENTIALS: "Username or password invalid for Dukascopy feed",
    DukascopyErrorCode.CONNECTION_FAILED: "Failed to establish session with Dukascopy server",
    DukascopyErrorCode.SUBSCRIPTION_FAILED: "Failed to subscribe to tick or bar feed",
    DukascopyErrorCode.ORDER_REJECTED: "Order submission rejected by Dukascopy gateway",
    DukascopyErrorCode.INSTRUMENT_NOT_FOUND: "Instrument is not available in Dukascopy catalog",
    DukascopyErrorCode.POSITION_NOT_FOUND: "Specified position ticket could not be found",
    DukascopyErrorCode.TIMEOUT: "JForex gateway request timed out",
    DukascopyErrorCode.DATA_UNAVAILABLE: "Historical tick or bar data not available for range",
}


def get_dukascopy_error_description(code: int) -> str:
    """Retrieve human-readable description for a Dukascopy error code.

    Args:
        code: Integer error code.

    Returns:
        Description string.
    """
    return DUKASCOPY_ERROR_DESCRIPTIONS.get(code, f"Unknown Dukascopy error [{code}]")


TIMEFRAME_MAP: dict[str, str] = {
    "1M": "1m",
    "M1": "1m",
    "5M": "5m",
    "M5": "5m",
    "10M": "10m",
    "M10": "10m",
    "15M": "15m",
    "M15": "15m",
    "30M": "30m",
    "M30": "30m",
    "1H": "1h",
    "H1": "1h",
    "4H": "4h",
    "H4": "4h",
    "1D": "1d",
    "D1": "1d",
    "1W": "1w",
    "W1": "1w",
    "1MN": "1mn",
    "MN1": "1mn",
}


def resolve_timeframe(tf: Any) -> str:
    """Resolve timeframe argument into standard Dukascopy periodicity string.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        Dukascopy period string (e.g. '1m', '1h', '1d').
    """
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        if cleaned in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[cleaned]
        return tf.lower()
    return "1m"


__all__ = [
    "DUKASCOPY_ERROR_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "DukascopyErrorCode",
    "get_dukascopy_error_description",
    "resolve_timeframe",
]
