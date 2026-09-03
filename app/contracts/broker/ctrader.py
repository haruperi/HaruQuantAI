"""cTrader OpenAPI provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class CTraderErrorCode(IntEnum):
    """cTrader OpenAPI error and return codes."""

    SUCCESS = 0
    GENERIC_ERROR = -1
    AUTHENTICATION_FAILED = -2
    INVALID_REQUEST = -3
    RATE_LIMIT_EXCEEDED = -4
    ORDER_NOT_FOUND = -5
    POSITION_NOT_FOUND = -6
    SYMBOL_NOT_FOUND = -7
    INSUFFICIENT_FUNDS = -8
    MARKET_CLOSED = -9
    TIMEOUT = -10
    NETWORK_ERROR = -11


CTRADER_ERROR_DESCRIPTIONS: dict[int, str] = {
    CTraderErrorCode.SUCCESS: "Success",
    CTraderErrorCode.GENERIC_ERROR: "Generic cTrader OpenAPI failure",
    CTraderErrorCode.AUTHENTICATION_FAILED: "Client authorization or access token expired",
    CTraderErrorCode.INVALID_REQUEST: "Malformed protocol buffer message or missing field",
    CTraderErrorCode.RATE_LIMIT_EXCEEDED: "cTrader OpenAPI rate limit exceeded",
    CTraderErrorCode.ORDER_NOT_FOUND: "Specified order could not be found",
    CTraderErrorCode.POSITION_NOT_FOUND: "Specified position could not be found",
    CTraderErrorCode.SYMBOL_NOT_FOUND: "Specified symbol not supported by cTrader broker",
    CTraderErrorCode.INSUFFICIENT_FUNDS: "Insufficient account balance to execute order",
    CTraderErrorCode.MARKET_CLOSED: "Market is currently closed for the instrument",
    CTraderErrorCode.TIMEOUT: "cTrader OpenAPI response timed out",
    CTraderErrorCode.NETWORK_ERROR: "TCP socket or TLS connection to cTrader proxy failed",
}


def get_ctrader_error_description(code: int) -> str:
    """Retrieve human-readable description for a cTrader error code.

    Args:
        code: Integer error code.

    Returns:
        Description string.
    """
    return CTRADER_ERROR_DESCRIPTIONS.get(code, f"Unknown cTrader error [{code}]")


TIMEFRAME_MAP: dict[str, str] = {
    "1M": "m1",
    "M1": "m1",
    "2M": "m2",
    "M2": "m2",
    "3M": "m3",
    "M3": "m3",
    "4M": "m4",
    "M4": "m4",
    "5M": "m5",
    "M5": "m5",
    "10M": "m10",
    "M10": "m10",
    "15M": "m15",
    "M15": "m15",
    "30M": "m30",
    "M30": "m30",
    "1H": "h1",
    "H1": "h1",
    "4H": "h4",
    "H4": "h4",
    "12H": "h12",
    "H12": "h12",
    "1D": "d1",
    "D1": "d1",
    "1W": "w1",
    "W1": "w1",
    "1MN": "mn1",
    "MN1": "mn1",
}


def resolve_timeframe(tf: Any) -> str:
    """Resolve timeframe argument into standard cTrader trendbar period string.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        cTrader trendbar period string (e.g. 'm1', 'h1', 'd1').
    """
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        if cleaned in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[cleaned]
        return tf.lower()
    return "m1"


__all__ = [
    "CTRADER_ERROR_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "CTraderErrorCode",
    "get_ctrader_error_description",
    "resolve_timeframe",
]
