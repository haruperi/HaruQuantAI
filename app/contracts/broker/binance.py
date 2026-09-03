"""Binance provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class BinanceErrorCode(IntEnum):
    """Binance REST and WebSocket API error codes."""

    SUCCESS = 0
    UNKNOWN = -1000
    DISCONNECTED = -1001
    UNAUTHORIZED = -1002
    TOO_MANY_REQUESTS = -1003
    UNEXPECTED_RESP = -1006
    TIMEOUT = -1007
    INVALID_MESSAGE = -1013
    UNKNOWN_ORDER_COMPOSITION = -1014
    TOO_MANY_ORDERS = -1015
    SERVICE_SHUTTING_DOWN = -1016
    UNSUPPORTED_OPERATION = -1020
    INVALID_TIMESTAMP = -1021
    INVALID_SIGNATURE = -1022
    ILLEGAL_CHARS = -1100
    MANDATORY_PARAM_EMPTY_OR_MALFORMED = -1102
    INVALID_LISTEN_KEY = -1125
    INSUFFICIENT_BALANCE = -2010
    CANCEL_ALL_FAIL = -2012
    NO_SUCH_ORDER = -2013
    BAD_API_KEY_FMT = -2014
    REJECTED_MBX_KEY = -2015


BINANCE_ERROR_DESCRIPTIONS: dict[int, str] = {
    BinanceErrorCode.SUCCESS: "Success",
    BinanceErrorCode.UNKNOWN: "An unknown error occurred while processing the request",
    BinanceErrorCode.DISCONNECTED: "Internal error; unable to process your request. Please try again",
    BinanceErrorCode.UNAUTHORIZED: "You are not authorized to execute this request",
    BinanceErrorCode.TOO_MANY_REQUESTS: "Too many requests queued or request rate limit exceeded",
    BinanceErrorCode.UNEXPECTED_RESP: "An unexpected response was received from the message bus",
    BinanceErrorCode.TIMEOUT: "Execution status unknown; request timed out",
    BinanceErrorCode.INVALID_MESSAGE: "Illegal characters or invalid parameters found in request",
    BinanceErrorCode.UNKNOWN_ORDER_COMPOSITION: "Unsupported order combination",
    BinanceErrorCode.TOO_MANY_ORDERS: "Too many new orders queued",
    BinanceErrorCode.SERVICE_SHUTTING_DOWN: "Binance service is shutting down",
    BinanceErrorCode.UNSUPPORTED_OPERATION: "Unsupported operation",
    BinanceErrorCode.INVALID_TIMESTAMP: "Timestamp for this request is outside of the recvWindow",
    BinanceErrorCode.INVALID_SIGNATURE: "Signature for this request is not valid",
    BinanceErrorCode.ILLEGAL_CHARS: "Illegal characters found in parameter",
    BinanceErrorCode.MANDATORY_PARAM_EMPTY_OR_MALFORMED: "Mandatory parameter was empty or malformed",
    BinanceErrorCode.INVALID_LISTEN_KEY: "This listenKey does not exist",
    BinanceErrorCode.INSUFFICIENT_BALANCE: "Account has insufficient balance for requested action",
    BinanceErrorCode.CANCEL_ALL_FAIL: "Unable to cancel all orders",
    BinanceErrorCode.NO_SUCH_ORDER: "Order does not exist",
    BinanceErrorCode.BAD_API_KEY_FMT: "API-key format invalid",  # pragma: allowlist secret
    BinanceErrorCode.REJECTED_MBX_KEY: "Invalid API-key, IP, or permissions for action",
}


def get_binance_error_description(code: int) -> str:
    """Retrieve human-readable description for a Binance error code.

    Args:
        code: Integer error code.

    Returns:
        Description string.
    """
    return BINANCE_ERROR_DESCRIPTIONS.get(code, f"Unknown Binance error [{code}]")


TIMEFRAME_MAP: dict[str, str] = {
    "1M": "1m",
    "M1": "1m",
    "3M": "3m",
    "M3": "3m",
    "5M": "5m",
    "M5": "5m",
    "15M": "15m",
    "M15": "15m",
    "30M": "30m",
    "M30": "30m",
    "1H": "1h",
    "H1": "1h",
    "2H": "2h",
    "H2": "2h",
    "4H": "4h",
    "H4": "4h",
    "6H": "6h",
    "H6": "6h",
    "8H": "8h",
    "H8": "8h",
    "12H": "12h",
    "H12": "12h",
    "1D": "1d",
    "D1": "1d",
    "3D": "3d",
    "D3": "3d",
    "1W": "1w",
    "W1": "1w",
    "1MO": "1M",
    "MN1": "1M",
}


def resolve_timeframe(tf: Any) -> str:
    """Resolve timeframe argument into standard Binance interval string.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        Binance interval string (e.g. '1m', '1h', '1d').
    """
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        if cleaned in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[cleaned]
        return tf.lower()
    return "1m"


__all__ = [
    "BINANCE_ERROR_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "BinanceErrorCode",
    "get_binance_error_description",
    "resolve_timeframe",
]
