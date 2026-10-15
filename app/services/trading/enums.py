"""Execution status codes, resolution enums, and TradingBackend protocol.

Description:
    Provides broker-neutral enumerations and data structures representing trade
    execution results, receipts, property values, bridge events, and the core
    TradingBackend async communication protocol.

Purpose:
    FEAT-TRADING-ENUMS: Execution statuses, resolutions, and protocol contracts.

Key Capabilities:
    - FR-TRADING-LIFECYCLE-ENUMS: Receipt and resolution enumerations.
      Associated: `ReceiptStatus`, `TradeResolution`, `Receipt`, `BridgeEvent`.
      Logging: Constant definitions and value objects with zero logging overhead.
    - FR-TRADING-MQL5-ENUMS: Standard MQL5-shaped trading and order enums.
      Associated: `AccountTradeMode`, `StopoutMode`, `MarginMode`, `OrderType`,
        `OrderFilling`, `OrderTime`, `TradeAction`, `TradeRetcode`, `BookType`.
      Logging: Constant enumerations and description dictionaries.
    - FR-TRADING-BACKEND-PROTOCOL: Async backend protocol contract.
      Associated: `TradingBackend`.
      Logging: Interface definition only.

Python API Usage:
    ```python
    from app.services.trading.enums import (
        OrderType,
        ReceiptStatus,
        TradeAction,
        TradeRetcode,
    )

    action = TradeAction.DEAL
    retcode = TradeRetcode.DONE
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading.enums
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any, Protocol, runtime_checkable

from app.host.logging import get_logger

__all__ = [
    "BOOK_TYPE_DESCRIPTIONS",
    "DEAL_ENTRY_DESCRIPTIONS",
    "DEAL_TYPE_DESCRIPTIONS",
    "ORDER_FILLING_DESCRIPTIONS",
    "ORDER_STATE_DESCRIPTIONS",
    "ORDER_TIME_DESCRIPTIONS",
    "ORDER_TYPE_DESCRIPTIONS",
    "POSITION_TYPE_DESCRIPTIONS",
    "SWAP_MODE_DESCRIPTIONS",
    "SYMBOL_CALC_MODE_DESCRIPTIONS",
    "SYMBOL_SWAP_MODE_DESCRIPTIONS",
    "SYMBOL_TRADE_EXECUTION_DESCRIPTIONS",
    "SYMBOL_TRADE_MODE_DESCRIPTIONS",
    "AccountTradeMode",
    "BookType",
    "BridgeEvent",
    "DealEntry",
    "DealType",
    "MarginMode",
    "OrderFilling",
    "OrderState",
    "OrderTime",
    "OrderType",
    "PositionType",
    "PropertyValue",
    "Receipt",
    "ReceiptStatus",
    "StopoutMode",
    "SymbolCalcMode",
    "SymbolSwapMode",
    "SymbolTradeExecution",
    "SymbolTradeMode",
    "TradeAction",
    "TradeResolution",
    "TradeRetcode",
    "TradingBackend",
]

logger = get_logger(__name__)


class ReceiptStatus(StrEnum):
    """Lifecycle status for a queued or executed bridge command."""

    CREATED = "created"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    UNCERTAIN = "uncertain"


class TradeResolution(StrEnum):
    """Resolution classification for an executed trading command."""

    DISPATCHED = "dispatched"
    FILLED = "filled"
    PLACED = "placed"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class PropertyValue:
    """Container for a typed scalar property query result or failure."""

    ok: bool
    value: Any = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class Receipt:
    """Immutable audit record tracking the lifecycle of an IPC command."""

    command_id: str
    object_id: str
    class_name: str
    method_name: str
    status: ReceiptStatus
    created_at: float
    sent_at: float | None = None
    acknowledged_at: float | None = None
    resolved_at: float | None = None
    native_request_id: int | None = None
    value: Any = None
    meta: Mapping[str, Any] = field(default_factory=dict)
    error: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class BridgeEvent:
    """Parsed asynchronous event dispatched from the MetaTrader 5 terminal EA."""

    event_type: str
    payload: Mapping[str, Any]
    command_id: str | None = None
    request_id: int | None = None


@runtime_checkable
class TradingBackend(Protocol):
    """Async execution capability consumed by trading and market data APIs."""

    async def start(self) -> None:
        """Backend capability: start."""
        ...

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109 -- backend deadline capability
        """Backend capability: wait connected."""
        ...

    async def close(self) -> None:
        """Backend capability: close."""
        ...

    def arm(self) -> None:
        """Backend capability: arm."""
        ...

    def disarm(self) -> None:
        """Backend capability: disarm."""
        ...

    def last_command_id(self) -> str | None:
        """Backend capability: last command id."""
        ...

    def receipt(self, command_id: str) -> Receipt | None:
        """Backend capability: receipt."""
        ...

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109 -- backend deadline capability
        """Backend capability: next event."""
        ...

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> BridgeEvent:
        """Backend capability: await request event."""
        ...

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> Any:
        """Backend capability: call."""
        ...


class AccountTradeMode(IntEnum):
    """Account trading mode enumeration."""

    DEMO = 0
    CONTEST = 1
    REAL = 2


class StopoutMode(IntEnum):
    """Stopout mode calculation type enumeration."""

    PERCENT = 0
    MONEY = 1


class MarginMode(IntEnum):
    """Account margin calculation mode enumeration."""

    RETAIL_NETTING = 0
    EXCHANGE = 1
    RETAIL_HEDGING = 2


class OrderType(IntEnum):
    """Order type enumeration."""

    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BUY_STOP_LIMIT = 6
    SELL_STOP_LIMIT = 7
    CLOSE_BY = 8


class OrderFilling(IntEnum):
    """Order execution policy type enumeration."""

    FOK = 0
    IOC = 1
    RETURN = 2
    BOC = 3


class OrderTime(IntEnum):
    """Order expiration time type enumeration."""

    GTC = 0
    DAY = 1
    SPECIFIED = 2
    SPECIFIED_DAY = 3


class TradeAction(IntEnum):
    """Trade request action enumeration."""

    DEAL = 1
    PENDING = 5
    SLTP = 6
    MODIFY = 7
    REMOVE = 8
    CLOSE_BY = 10


class TradeRetcode(IntEnum):
    """Trade execution return code enumeration."""

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
    INVALID_ORDER = 10035
    POSITION_CLOSED = 10036
    INVALID_CLOSE_VOLUME = 10038
    CLOSE_ORDER_EXIST = 10039
    LIMIT_POSITIONS = 10040
    REJECT_CANCEL = 10041
    LONG_ONLY = 10042
    SHORT_ONLY = 10043
    CLOSE_ONLY = 10044
    FIFO_CLOSE = 10045
    HEDGE_PROHIBITED = 10046


class BookType(IntEnum):
    """Order book entry type enumeration."""

    BOOK_TYPE_SELL = 1
    BOOK_TYPE_BUY = 2
    BOOK_TYPE_SELL_MARKET = 3
    BOOK_TYPE_BUY_MARKET = 4


ORDER_TYPE_DESCRIPTIONS: dict[OrderType, str] = {
    OrderType.BUY: "Buy",
    OrderType.SELL: "Sell",
    OrderType.BUY_LIMIT: "Buy Limit",
    OrderType.SELL_LIMIT: "Sell Limit",
    OrderType.BUY_STOP: "Buy Stop",
    OrderType.SELL_STOP: "Sell Stop",
    OrderType.BUY_STOP_LIMIT: "Buy Stop Limit",
    OrderType.SELL_STOP_LIMIT: "Sell Stop Limit",
    OrderType.CLOSE_BY: "Close By",
}

ORDER_FILLING_DESCRIPTIONS: dict[OrderFilling, str] = {
    OrderFilling.FOK: "Fill or Kill",
    OrderFilling.IOC: "Immediate or Cancel",
    OrderFilling.RETURN: "Return",
    OrderFilling.BOC: "Book or Cancel",
}

ORDER_TIME_DESCRIPTIONS: dict[OrderTime, str] = {
    OrderTime.GTC: "Good Till Cancelled",
    OrderTime.DAY: "Day",
    OrderTime.SPECIFIED: "Specified",
    OrderTime.SPECIFIED_DAY: "Specified Day",
}

BOOK_TYPE_DESCRIPTIONS: dict[BookType, str] = {
    BookType.BOOK_TYPE_SELL: "Sell",
    BookType.BOOK_TYPE_BUY: "Buy",
    BookType.BOOK_TYPE_SELL_MARKET: "Sell Market",
    BookType.BOOK_TYPE_BUY_MARKET: "Buy Market",
}


class PositionType(IntEnum):
    """Position type enumeration."""

    BUY = 0
    SELL = 1


class OrderState(IntEnum):
    """Order lifecycle state enumeration."""

    STARTED = 0
    PLACED = 1
    CANCELED = 2
    PARTIAL = 3
    FILLED = 4
    REJECTED = 5
    EXPIRED = 6
    REQUEST_ADD = 7
    REQUEST_MODIFY = 8
    REQUEST_CANCEL = 9


class DealType(IntEnum):
    """Deal execution type enumeration."""

    BUY = 0
    SELL = 1
    BALANCE = 2
    CREDIT = 3
    CHARGE = 4
    CORRECTION = 5
    BONUS = 6
    COMMISSION = 7
    COMMISSION_DAILY = 8
    COMMISSION_MONTHLY = 9
    COMMISSION_AGENT_DAILY = 10
    COMMISSION_AGENT_MONTHLY = 11
    INTEREST = 12
    BUY_CANCELED = 13
    SELL_CANCELED = 14
    DIVIDEND = 15
    DIVIDEND_FRANKED = 16
    TAX = 17


class DealEntry(IntEnum):
    """Deal position entry direction enumeration."""

    IN = 0
    OUT = 1
    INOUT = 2
    OUT_BY = 3


class SymbolTradeMode(IntEnum):
    """Symbol trading mode enumeration."""

    DISABLED = 0
    LONGONLY = 1
    SHORTONLY = 2
    CLOSEONLY = 3
    FULL = 4


class SymbolTradeExecution(IntEnum):
    """Symbol order execution policy enumeration."""

    REQUEST = 0
    INSTANT = 1
    MARKET = 2
    EXCHANGE = 3


class SymbolSwapMode(IntEnum):
    """Symbol overnight swap calculation mode."""

    DISABLED = 0
    POINTS = 1
    CURRENCY_SYMBOL = 2
    CURRENCY_MARGIN = 3
    CURRENCY_DEPOSIT = 4
    INTEREST_CURRENT = 5
    INTEREST_OPEN = 6
    REOPEN_CURRENT = 7
    REOPEN_BID = 8


class SymbolCalcMode(IntEnum):
    """Symbol margin and profit calculation mode."""

    FOREX = 0
    FOREX_NO_LEVERAGE = 1
    FUTURES = 2
    CFD = 3
    CFDINDEX = 4
    CFDLEVERAGE = 5
    EXCH_STOCKS = 32
    EXCH_FUTURES = 33


POSITION_TYPE_DESCRIPTIONS: dict[PositionType, str] = {
    PositionType.BUY: "Buy",
    PositionType.SELL: "Sell",
}

ORDER_STATE_DESCRIPTIONS: dict[OrderState, str] = {
    item: item.name.replace("_", " ").title() for item in OrderState
}

DEAL_TYPE_DESCRIPTIONS: dict[DealType, str] = {
    item: item.name.replace("_", " ").title() for item in DealType
}

DEAL_ENTRY_DESCRIPTIONS: dict[DealEntry, str] = {
    item: item.name.replace("_", " ").title() for item in DealEntry
}

SYMBOL_TRADE_MODE_DESCRIPTIONS: dict[SymbolTradeMode, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolTradeMode
}

SYMBOL_TRADE_EXECUTION_DESCRIPTIONS: dict[SymbolTradeExecution, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolTradeExecution
}

SYMBOL_SWAP_MODE_DESCRIPTIONS: dict[SymbolSwapMode, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolSwapMode
}
SWAP_MODE_DESCRIPTIONS = SYMBOL_SWAP_MODE_DESCRIPTIONS

SYMBOL_CALC_MODE_DESCRIPTIONS: dict[SymbolCalcMode, str] = {
    item: item.name.replace("_", " ").title() for item in SymbolCalcMode
}


def main() -> None:
    """Demonstrate trading enums and descriptions."""
    print(f"OrderType.BUY: {OrderType.BUY} ({ORDER_TYPE_DESCRIPTIONS[OrderType.BUY]})")
    print(f"TradeAction.DEAL: {TradeAction.DEAL}")
    receipt = Receipt(
        command_id="cmd-1",
        object_id="obj-1",
        class_name="Trade",
        method_name="OrderSend",
        status=ReceiptStatus.RESOLVED,
        created_at=0.0,
    )
    print(f"Receipt: id={receipt.command_id}, status={receipt.status}")


if __name__ == "__main__":
    main()
