"""Binance provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from app.contracts.data.timeframes import (
    ENUM_TIMEFRAMES,
    PERIOD_D1,
    PERIOD_H1,
    PERIOD_H2,
    PERIOD_H4,
    PERIOD_H6,
    PERIOD_H8,
    PERIOD_H12,
    PERIOD_M1,
    PERIOD_M3,
    PERIOD_M5,
    PERIOD_M15,
    PERIOD_M30,
    PERIOD_MN1,
    PERIOD_W1,
)


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


TIMEFRAME_MAP: dict[ENUM_TIMEFRAMES, str] = {
    PERIOD_M1: "1m",
    PERIOD_M3: "3m",
    PERIOD_M5: "5m",
    PERIOD_M15: "15m",
    PERIOD_M30: "30m",
    PERIOD_H1: "1h",
    PERIOD_H2: "2h",
    PERIOD_H4: "4h",
    PERIOD_H6: "6h",
    PERIOD_H8: "8h",
    PERIOD_H12: "12h",
    PERIOD_D1: "1d",
    PERIOD_W1: "1w",
    PERIOD_MN1: "1M",
}

_TIMEFRAME_ALIASES: dict[str, ENUM_TIMEFRAMES] = {
    "1M": PERIOD_M1,
    "M1": PERIOD_M1,
    "3M": PERIOD_M3,
    "M3": PERIOD_M3,
    "5M": PERIOD_M5,
    "M5": PERIOD_M5,
    "15M": PERIOD_M15,
    "M15": PERIOD_M15,
    "30M": PERIOD_M30,
    "M30": PERIOD_M30,
    "1H": PERIOD_H1,
    "H1": PERIOD_H1,
    "2H": PERIOD_H2,
    "H2": PERIOD_H2,
    "4H": PERIOD_H4,
    "H4": PERIOD_H4,
    "6H": PERIOD_H6,
    "H6": PERIOD_H6,
    "8H": PERIOD_H8,
    "H8": PERIOD_H8,
    "12H": PERIOD_H12,
    "H12": PERIOD_H12,
    "1D": PERIOD_D1,
    "D1": PERIOD_D1,
    "1W": PERIOD_W1,
    "W1": PERIOD_W1,
    "1MO": PERIOD_MN1,
    "MN1": PERIOD_MN1,
}
_PROVIDER_TIMEFRAME_ALIASES = {"3D": "3d", "D3": "3d"}


def resolve_timeframe(tf: Any) -> str:
    """Resolve timeframe argument into standard Binance interval string.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        Binance interval string (e.g. '1m', '1h', '1d').

    Raises:
        ValueError: If a canonical timeframe is invalid or unsupported.
    """
    if isinstance(tf, bool):
        raise ValueError(f"unsupported Binance timeframe: {tf!r}")
    if isinstance(tf, (ENUM_TIMEFRAMES, int)):
        try:
            period = ENUM_TIMEFRAMES(tf)
        except ValueError as error:
            raise ValueError(f"invalid canonical timeframe: {tf!r}") from error
        try:
            return TIMEFRAME_MAP[period]
        except KeyError as error:
            raise ValueError(
                f"Binance does not support canonical timeframe {period.name}"
            ) from error
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        alias_period = _TIMEFRAME_ALIASES.get(cleaned)
        if alias_period is not None:
            return TIMEFRAME_MAP[alias_period]
        provider_alias = _PROVIDER_TIMEFRAME_ALIASES.get(cleaned)
        if provider_alias is not None:
            return provider_alias
        return tf.lower()
    return "1m"


__all__ = [
    "BINANCE_ERROR_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "BinanceErrorCode",
    "get_binance_error_description",
    "resolve_timeframe",
]
