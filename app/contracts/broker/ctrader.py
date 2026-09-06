"""cTrader OpenAPI provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from app.contracts.data.timeframes import (
    ENUM_TIMEFRAMES,
    PERIOD_D1,
    PERIOD_H1,
    PERIOD_H4,
    PERIOD_H12,
    PERIOD_M1,
    PERIOD_M2,
    PERIOD_M3,
    PERIOD_M4,
    PERIOD_M5,
    PERIOD_M10,
    PERIOD_M15,
    PERIOD_M30,
    PERIOD_MN1,
    PERIOD_W1,
)


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


TIMEFRAME_MAP: dict[ENUM_TIMEFRAMES, str] = {
    PERIOD_M1: "m1",
    PERIOD_M2: "m2",
    PERIOD_M3: "m3",
    PERIOD_M4: "m4",
    PERIOD_M5: "m5",
    PERIOD_M10: "m10",
    PERIOD_M15: "m15",
    PERIOD_M30: "m30",
    PERIOD_H1: "h1",
    PERIOD_H4: "h4",
    PERIOD_H12: "h12",
    PERIOD_D1: "d1",
    PERIOD_W1: "w1",
    PERIOD_MN1: "mn1",
}

_TIMEFRAME_ALIASES = {
    alias: period
    for period, aliases in {
        PERIOD_M1: ("1M", "M1"),
        PERIOD_M2: ("2M", "M2"),
        PERIOD_M3: ("3M", "M3"),
        PERIOD_M4: ("4M", "M4"),
        PERIOD_M5: ("5M", "M5"),
        PERIOD_M10: ("10M", "M10"),
        PERIOD_M15: ("15M", "M15"),
        PERIOD_M30: ("30M", "M30"),
        PERIOD_H1: ("1H", "H1"),
        PERIOD_H4: ("4H", "H4"),
        PERIOD_H12: ("12H", "H12"),
        PERIOD_D1: ("1D", "D1"),
        PERIOD_W1: ("1W", "W1"),
        PERIOD_MN1: ("1MN", "MN1"),
    }.items()
    for alias in aliases
}


def resolve_timeframe(tf: Any) -> str:
    """Resolve timeframe argument into standard cTrader trendbar period string.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        cTrader trendbar period string (e.g. 'm1', 'h1', 'd1').

    Raises:
        ValueError: If a canonical timeframe is invalid or unsupported.
    """
    if isinstance(tf, bool):
        raise ValueError(f"unsupported cTrader timeframe: {tf!r}")
    if isinstance(tf, (ENUM_TIMEFRAMES, int)):
        try:
            period = ENUM_TIMEFRAMES(tf)
        except ValueError as error:
            raise ValueError(f"invalid canonical timeframe: {tf!r}") from error
        try:
            return TIMEFRAME_MAP[period]
        except KeyError as error:
            raise ValueError(
                f"cTrader does not support canonical timeframe {period.name}"
            ) from error
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        alias_period = _TIMEFRAME_ALIASES.get(cleaned)
        if alias_period is not None:
            return TIMEFRAME_MAP[alias_period]
        return tf.lower()
    return "m1"


__all__ = [
    "CTRADER_ERROR_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "CTraderErrorCode",
    "get_ctrader_error_description",
    "resolve_timeframe",
]
