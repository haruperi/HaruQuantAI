"""MetaTrader 5 provider-specific contracts, error codes, retcodes, and mappings."""

from __future__ import annotations

from enum import IntEnum
from typing import Any


class MT5TerminalError(IntEnum):
    """MetaTrader 5 terminal and IPC error codes returned by mt5.last_error()."""

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
    """MetaTrader 5 trade server return codes returned in MqlTradeResult.retcode."""

    REQUOTE = 10004
    REJECT = 10006
    CANCEL = 10007
    PLACED = 10008
    DONE = 10009
    DONE_PARTIAL = 10010
    ERROR = 10011
    TIMEOUT = 10012
    INVALID = 10013
    INVALID_VOLUME = 10014
    INVALID_PRICE = 10015
    INVALID_STOPS = 10016
    TRADE_DISABLED = 10017
    MARKET_CLOSED = 10018
    NO_MONEY = 10019
    PRICE_CHANGED = 10020
    PRICE_OFF = 10021
    INVALID_EXPIRATION = 10022
    ORDER_CHANGED = 10023
    TOO_MANY_REQUESTS = 10024
    NO_CHANGES = 10025
    SERVER_DISABLES_AT = 10026
    CLIENT_DISABLES_AT = 10027
    LOCKED = 10028
    FROZEN = 10029
    INVALID_FILL = 10030
    CONNECTION = 10031
    ONLY_REAL = 10032
    LIMIT_ORDERS = 10033
    LIMIT_VOLUME = 10034
    POSITION_CLOSED = 10035
    INVALID_CLOSE_VOLUME = 10036
    CLOSE_ORDER_EXIST = 10038
    LIMIT_POSITIONS = 10039


MT5_TERMINAL_ERROR_DESCRIPTIONS: dict[int, str] = {
    MT5TerminalError.SUCCESS: "Success",
    MT5TerminalError.FAIL: "Generic failure",
    MT5TerminalError.INVALID_PARAMS: "Invalid arguments passed to function",
    MT5TerminalError.NO_MEMORY: "Out of memory",
    MT5TerminalError.NOT_FOUND: "Requested item not found",
    MT5TerminalError.INVALID_VERSION: "Unsupported terminal or Python package version",
    MT5TerminalError.AUTH_FAILED: "Authorization failed",
    MT5TerminalError.UNSUPPORTED: "Unsupported method or call",
    MT5TerminalError.AUTO_TRADING_DISABLED: "Auto-trading is disabled in terminal settings",
    MT5TerminalError.INTERNAL_FAIL: "Internal IPC failure",
    MT5TerminalError.INTERNAL_FAIL_SEND: "Failed to send IPC request to terminal",
    MT5TerminalError.INTERNAL_FAIL_RECV: "Failed to receive IPC response from terminal",
    MT5TerminalError.INTERNAL_FAIL_INIT: "Failed to initialize IPC connection to terminal",
    MT5TerminalError.INTERNAL_FAIL_CONNECT: "Failed to connect to MetaTrader 5 terminal (terminal may not be running)",
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
    MT5TradeRetcode.TRADE_DISABLED: "Trading is disabled on account or instrument",
    MT5TradeRetcode.MARKET_CLOSED: "Market is closed for the instrument",
    MT5TradeRetcode.NO_MONEY: "Insufficient funds to execute trade",
    MT5TradeRetcode.PRICE_CHANGED: "Prices have changed",
    MT5TradeRetcode.PRICE_OFF: "No quotes available to process request",
    MT5TradeRetcode.INVALID_EXPIRATION: "Invalid order expiration date",
    MT5TradeRetcode.ORDER_CHANGED: "Order state has changed",
    MT5TradeRetcode.TOO_MANY_REQUESTS: "Too frequent trade requests",
    MT5TradeRetcode.NO_CHANGES: "No changes specified in modification request",
    MT5TradeRetcode.SERVER_DISABLES_AT: "Auto-trading disabled by server",
    MT5TradeRetcode.CLIENT_DISABLES_AT: "Auto-trading disabled by client terminal",
    MT5TradeRetcode.LOCKED: "Request locked for processing",
    MT5TradeRetcode.FROZEN: "Order or position is frozen",
    MT5TradeRetcode.INVALID_FILL: "Unsupported order execution fill type",
    MT5TradeRetcode.CONNECTION: "No connection with trade server",
    MT5TradeRetcode.ONLY_REAL: "Operation allowed only for live accounts",
    MT5TradeRetcode.LIMIT_ORDERS: "Number of pending orders has reached the limit",
    MT5TradeRetcode.LIMIT_VOLUME: "Volume of orders and positions for symbol reached limit",
    MT5TradeRetcode.POSITION_CLOSED: "Position with specified ticket is already closed",
    MT5TradeRetcode.INVALID_CLOSE_VOLUME: "Close volume exceeds open position volume",
    MT5TradeRetcode.CLOSE_ORDER_EXIST: "Close order already exists for this position",
    MT5TradeRetcode.LIMIT_POSITIONS: "Number of open positions has reached the limit",
}


def get_mt5_error_description(code: int) -> str:
    """Retrieve human-readable description for an MT5 terminal error code.

    Args:
        code: Integer error code.

    Returns:
        Description string.
    """
    return MT5_TERMINAL_ERROR_DESCRIPTIONS.get(code, f"Unknown MT5 error [{code}]")


def get_mt5_retcode_description(retcode: int) -> str:
    """Retrieve human-readable description for an MT5 trade server return code.

    Args:
        retcode: Integer return code.

    Returns:
        Description string.
    """
    return MT5_TRADE_RETCODE_DESCRIPTIONS.get(
        retcode, f"Unknown MT5 trade retcode [{retcode}]"
    )


TIMEFRAME_MAP: dict[str, int] = {
    "1M": 1,
    "M1": 1,
    "2M": 2,
    "M2": 2,
    "3M": 3,
    "M3": 3,
    "4M": 4,
    "M4": 4,
    "5M": 5,
    "M5": 5,
    "6M": 6,
    "M6": 6,
    "10M": 10,
    "M10": 10,
    "12M": 12,
    "M12": 12,
    "15M": 15,
    "M15": 15,
    "20M": 20,
    "M20": 20,
    "30M": 30,
    "M30": 30,
    "1H": 16385,
    "H1": 16385,
    "2H": 16386,
    "H2": 16386,
    "3H": 16387,
    "H3": 16387,
    "4H": 16388,
    "H4": 16388,
    "6H": 16390,
    "H6": 16390,
    "8H": 16392,
    "H8": 16392,
    "12H": 16396,
    "H12": 16396,
    "1D": 16408,
    "D1": 16408,
    "1W": 32769,
    "W1": 32769,
    "1MN": 49153,
    "MN1": 49153,
}


def resolve_timeframe(tf: Any) -> int:
    """Resolve timeframe argument into standard MT5 integer constant.

    Args:
        tf: String (e.g. '1m', 'H1', '1d') or integer constant.

    Returns:
        MT5 integer timeframe constant (defaults to 1 for M1).
    """
    if isinstance(tf, int):
        return tf
    if isinstance(tf, str):
        cleaned = tf.strip().upper()
        if cleaned in TIMEFRAME_MAP:
            return TIMEFRAME_MAP[cleaned]
        if cleaned.isdigit():
            return int(cleaned)
    return 1  # Default to M1


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
