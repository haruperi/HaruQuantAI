"""Dukascopy JForex provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from app.contracts.data.timeframes import (
    ENUM_TIMEFRAMES,
    PERIOD_D1,
    PERIOD_H1,
    PERIOD_H4,
    PERIOD_M1,
    PERIOD_M5,
    PERIOD_M10,
    PERIOD_M15,
    PERIOD_M30,
    PERIOD_MN1,
    PERIOD_W1,
)


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


TIMEFRAME_MAP: dict[ENUM_TIMEFRAMES, str] = {
    PERIOD_M1: "1m",
    PERIOD_M5: "5m",
    PERIOD_M10: "10m",
    PERIOD_M15: "15m",
    PERIOD_M30: "30m",
    PERIOD_H1: "1h",
    PERIOD_H4: "4h",
    PERIOD_D1: "1d",
    PERIOD_W1: "1w",
    PERIOD_MN1: "1mn",
}

_TIMEFRAME_ALIASES = {
    alias: period
    for period, aliases in {
        PERIOD_M1: ("1M", "M1"),
        PERIOD_M5: ("5M", "M5"),
        PERIOD_M10: ("10M", "M10"),
        PERIOD_M15: ("15M", "M15"),
        PERIOD_M30: ("30M", "M30"),
        PERIOD_H1: ("1H", "H1"),
        PERIOD_H4: ("4H", "H4"),
        PERIOD_D1: ("1D", "D1"),
        PERIOD_W1: ("1W", "W1"),
        PERIOD_MN1: ("1MN", "MN1"),
    }.items()
    for alias in aliases
}


def resolve_timeframe(tf: Any) -> str:
    """Resolve timeframe argument into standard Dukascopy periodicity string.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        Dukascopy period string (e.g. '1m', '1h', '1d').

    Raises:
        ValueError: If a canonical timeframe is invalid or unsupported.
    """
    if isinstance(tf, bool):
        raise ValueError(f"unsupported Dukascopy timeframe: {tf!r}")
    if isinstance(tf, (ENUM_TIMEFRAMES, int)):
        try:
            period = ENUM_TIMEFRAMES(tf)
        except ValueError as error:
            raise ValueError(f"invalid canonical timeframe: {tf!r}") from error
        try:
            return TIMEFRAME_MAP[period]
        except KeyError as error:
            raise ValueError(
                f"Dukascopy does not support canonical timeframe {period.name}"
            ) from error
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        alias_period = _TIMEFRAME_ALIASES.get(cleaned)
        if alias_period is not None:
            return TIMEFRAME_MAP[alias_period]
        return tf.lower()
    return "1m"


__all__ = [
    "DUKASCOPY_ERROR_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "DukascopyErrorCode",
    "get_dukascopy_error_description",
    "resolve_timeframe",
]
