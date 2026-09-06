"""MetaTrader provider-specific errors and canonical boundary conversions."""

from __future__ import annotations

import re
from enum import IntEnum
from typing import Any

from app.contracts.broker import trade_retcodes as canonical
from app.contracts.data.timeframes import ENUM_TIMEFRAMES, PERIOD_M1


class MT5TerminalError(IntEnum):
    """MetaTrader terminal and IPC error codes returned by ``last_error``."""

    SUCCESS = 1
    FAIL = -1
    INVALID_PARAMS = -2
    NO_MEMORY = -3
    NOT_FOUND = -4
    INVALID_VERSION = -5
    AUTH_FAILED = -6
    UNSUPPORTED = -7
    AUTO_TRADING_DISABLED = -8
    INTERNAL_FAIL = -10000
    INTERNAL_FAIL_SEND = -10001
    INTERNAL_FAIL_RECV = -10002
    INTERNAL_FAIL_INIT = -10003
    INTERNAL_FAIL_CONNECT = -10004
    INTERNAL_FAIL_TIMEOUT = -10005


class MT5TradeRetcode(IntEnum):
    """Complete MetaTrader trade-server return-code sequence."""

    REQUOTE = canonical.TRADE_RETCODE_REQUOTE
    REJECT = canonical.TRADE_RETCODE_REJECT
    CANCEL = canonical.TRADE_RETCODE_CANCEL
    PLACED = canonical.TRADE_RETCODE_PLACED
    DONE = canonical.TRADE_RETCODE_DONE
    DONE_PARTIAL = canonical.TRADE_RETCODE_DONE_PARTIAL
    ERROR = canonical.TRADE_RETCODE_ERROR
    TIMEOUT = canonical.TRADE_RETCODE_TIMEOUT
    INVALID = canonical.TRADE_RETCODE_INVALID
    INVALID_VOLUME = canonical.TRADE_RETCODE_INVALID_VOLUME
    INVALID_PRICE = canonical.TRADE_RETCODE_INVALID_PRICE
    INVALID_STOPS = canonical.TRADE_RETCODE_INVALID_STOPS
    TRADE_DISABLED = canonical.TRADE_RETCODE_TRADE_DISABLED
    MARKET_CLOSED = canonical.TRADE_RETCODE_MARKET_CLOSED
    NO_MONEY = canonical.TRADE_RETCODE_NO_MONEY
    PRICE_CHANGED = canonical.TRADE_RETCODE_PRICE_CHANGED
    PRICE_OFF = canonical.TRADE_RETCODE_PRICE_OFF
    INVALID_EXPIRATION = canonical.TRADE_RETCODE_INVALID_EXPIRATION
    ORDER_CHANGED = canonical.TRADE_RETCODE_ORDER_CHANGED
    TOO_MANY_REQUESTS = canonical.TRADE_RETCODE_TOO_MANY_REQUESTS
    NO_CHANGES = canonical.TRADE_RETCODE_NO_CHANGES
    SERVER_DISABLES_AT = canonical.TRADE_RETCODE_SERVER_DISABLES_AT
    CLIENT_DISABLES_AT = canonical.TRADE_RETCODE_CLIENT_DISABLES_AT
    LOCKED = canonical.TRADE_RETCODE_LOCKED
    FROZEN = canonical.TRADE_RETCODE_FROZEN
    INVALID_FILL = canonical.TRADE_RETCODE_INVALID_FILL
    CONNECTION = canonical.TRADE_RETCODE_CONNECTION
    ONLY_REAL = canonical.TRADE_RETCODE_ONLY_REAL
    LIMIT_ORDERS = canonical.TRADE_RETCODE_LIMIT_ORDERS
    LIMIT_VOLUME = canonical.TRADE_RETCODE_LIMIT_VOLUME
    INVALID_ORDER = canonical.TRADE_RETCODE_INVALID_ORDER
    POSITION_CLOSED = canonical.TRADE_RETCODE_POSITION_CLOSED
    INVALID_CLOSE_VOLUME = canonical.TRADE_RETCODE_INVALID_CLOSE_VOLUME
    CLOSE_ORDER_EXIST = canonical.TRADE_RETCODE_CLOSE_ORDER_EXIST
    LIMIT_POSITIONS = canonical.TRADE_RETCODE_LIMIT_POSITIONS
    REJECT_CANCEL = canonical.TRADE_RETCODE_REJECT_CANCEL
    LONG_ONLY = canonical.TRADE_RETCODE_LONG_ONLY
    SHORT_ONLY = canonical.TRADE_RETCODE_SHORT_ONLY
    CLOSE_ONLY = canonical.TRADE_RETCODE_CLOSE_ONLY
    FIFO_CLOSE = canonical.TRADE_RETCODE_FIFO_CLOSE
    HEDGE_PROHIBITED = canonical.TRADE_RETCODE_HEDGE_PROHIBITED


MT5_TERMINAL_ERROR_DESCRIPTIONS: dict[int, str] = {
    MT5TerminalError.SUCCESS: "Success",
    MT5TerminalError.FAIL: "Generic failure",
    MT5TerminalError.INVALID_PARAMS: "Invalid arguments passed to function",
    MT5TerminalError.NO_MEMORY: "Out of memory",
    MT5TerminalError.NOT_FOUND: "Requested item not found",
    MT5TerminalError.INVALID_VERSION: "Unsupported terminal or package version",
    MT5TerminalError.AUTH_FAILED: "Authorization failed",
    MT5TerminalError.UNSUPPORTED: "Unsupported method or call",
    MT5TerminalError.AUTO_TRADING_DISABLED: "Auto-trading is disabled",
    MT5TerminalError.INTERNAL_FAIL: "Internal IPC failure",
    MT5TerminalError.INTERNAL_FAIL_SEND: "Failed to send IPC request",
    MT5TerminalError.INTERNAL_FAIL_RECV: "Failed to receive IPC response",
    MT5TerminalError.INTERNAL_FAIL_INIT: "Failed to initialize IPC connection",
    MT5TerminalError.INTERNAL_FAIL_CONNECT: (
        "Failed to connect to MetaTrader 5 terminal (terminal may not be running)"
    ),
    MT5TerminalError.INTERNAL_FAIL_TIMEOUT: "IPC communication timed out",
}

MT5_TRADE_RETCODE_DESCRIPTIONS: dict[int, str] = {
    MT5TradeRetcode.REQUOTE: "Requote",
    MT5TradeRetcode.REJECT: "Request rejected",
    MT5TradeRetcode.CANCEL: "Request canceled by trader",
    MT5TradeRetcode.PLACED: "Order placed successfully",
    MT5TradeRetcode.DONE: "Request completed successfully",
    MT5TradeRetcode.DONE_PARTIAL: "Only part of the request completed",
    MT5TradeRetcode.ERROR: "Request processing error",
    MT5TradeRetcode.TIMEOUT: "Request canceled by timeout",
    MT5TradeRetcode.INVALID: "Invalid request structure or parameters",
    MT5TradeRetcode.INVALID_VOLUME: "Invalid order volume",
    MT5TradeRetcode.INVALID_PRICE: "Invalid order price",
    MT5TradeRetcode.INVALID_STOPS: "Invalid stop loss or take profit price",
    MT5TradeRetcode.TRADE_DISABLED: "Trading is disabled",
    MT5TradeRetcode.MARKET_CLOSED: "Market is closed",
    MT5TradeRetcode.NO_MONEY: "Insufficient funds to execute trade",
    MT5TradeRetcode.PRICE_CHANGED: "Prices have changed",
    MT5TradeRetcode.PRICE_OFF: "No quotes are available",
    MT5TradeRetcode.INVALID_EXPIRATION: "Invalid order expiration date",
    MT5TradeRetcode.ORDER_CHANGED: "Order state has changed",
    MT5TradeRetcode.TOO_MANY_REQUESTS: "Too frequent trade requests",
    MT5TradeRetcode.NO_CHANGES: "No changes specified",
    MT5TradeRetcode.SERVER_DISABLES_AT: "Auto-trading disabled by server",
    MT5TradeRetcode.CLIENT_DISABLES_AT: "Auto-trading disabled by client",
    MT5TradeRetcode.LOCKED: "Request locked for processing",
    MT5TradeRetcode.FROZEN: "Order or position is frozen",
    MT5TradeRetcode.INVALID_FILL: "Unsupported order fill type",
    MT5TradeRetcode.CONNECTION: "No connection with trade server",
    MT5TradeRetcode.ONLY_REAL: "Operation allowed only for real accounts",
    MT5TradeRetcode.LIMIT_ORDERS: "Pending-order limit reached",
    MT5TradeRetcode.LIMIT_VOLUME: "Symbol volume limit reached",
    MT5TradeRetcode.INVALID_ORDER: "Unsupported or prohibited order type",
    MT5TradeRetcode.POSITION_CLOSED: "Position is already closed",
    MT5TradeRetcode.INVALID_CLOSE_VOLUME: "Close volume exceeds position volume",
    MT5TradeRetcode.CLOSE_ORDER_EXIST: "Close order already exists",
    MT5TradeRetcode.LIMIT_POSITIONS: "Open-position limit reached",
    MT5TradeRetcode.REJECT_CANCEL: "Pending-order activation rejected",
    MT5TradeRetcode.LONG_ONLY: "Only long positions are allowed",
    MT5TradeRetcode.SHORT_ONLY: "Only short positions are allowed",
    MT5TradeRetcode.CLOSE_ONLY: "Only position closing is allowed",
    MT5TradeRetcode.FIFO_CLOSE: "Positions must be closed FIFO",
    MT5TradeRetcode.HEDGE_PROHIBITED: "Opposite positions are prohibited",
}

TIMEFRAME_MAP: dict[ENUM_TIMEFRAMES, int] = {
    timeframe: int(timeframe) for timeframe in ENUM_TIMEFRAMES
}


def _timeframe_aliases() -> dict[str, ENUM_TIMEFRAMES]:
    aliases: dict[str, ENUM_TIMEFRAMES] = {}
    for timeframe in ENUM_TIMEFRAMES:
        name = timeframe.name.removeprefix("PERIOD_")
        aliases[name] = timeframe
        match = re.fullmatch(r"([MHDW])(\d+)", name)
        if match:
            unit, multiple = match.groups()
            aliases[f"{multiple}{unit}"] = timeframe
        elif name == "MN1":
            aliases["1MN"] = timeframe
    return aliases


_TIMEFRAME_ALIASES = _timeframe_aliases()


def get_mt5_error_description(code: int) -> str:
    """Return the description of one terminal error code."""
    return MT5_TERMINAL_ERROR_DESCRIPTIONS.get(code, f"Unknown MT5 error [{code}]")


def get_mt5_retcode_description(retcode: int) -> str:
    """Return the description of one trade-server result code."""
    return MT5_TRADE_RETCODE_DESCRIPTIONS.get(
        retcode, f"Unknown MT5 trade retcode [{retcode}]"
    )


def resolve_timeframe(value: Any) -> int:
    """Encode a canonical or boundary timeframe as a MetaTrader integer.

    Raises:
        ValueError: If a boolean is supplied as a timeframe.
    """
    if isinstance(value, bool):
        raise ValueError(f"unsupported MetaTrader timeframe: {value!r}")
    if isinstance(value, ENUM_TIMEFRAMES):
        return TIMEFRAME_MAP[value]
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.strip().upper()
        timeframe = _TIMEFRAME_ALIASES.get(cleaned)
        if timeframe is not None:
            return TIMEFRAME_MAP[timeframe]
        if cleaned.isdigit():
            return int(cleaned)
    return TIMEFRAME_MAP[PERIOD_M1]


__all__ = [
    "MT5_TERMINAL_ERROR_DESCRIPTIONS",
    "MT5_TRADE_RETCODE_DESCRIPTIONS",
    "TIMEFRAME_MAP",
    "MT5TerminalError",
    "MT5TradeRetcode",
    "get_mt5_error_description",
    "get_mt5_retcode_description",
    "resolve_timeframe",
]
