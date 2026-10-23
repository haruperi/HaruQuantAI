"""Domain enumeration definitions and execution statuses."""

from __future__ import annotations

from enum import IntEnum, StrEnum

__all__ = [
    "AccountTradeMode",
    "BookType",
    "DealEntry",
    "DealType",
    "MarginMode",
    "OrderFilling",
    "OrderState",
    "OrderTime",
    "OrderType",
    "PositionType",
    "ReceiptStatus",
    "StopoutMode",
    "SymbolCalcMode",
    "SymbolSwapMode",
    "SymbolTradeExecution",
    "SymbolTradeMode",
    "Timeframe",
    "TradeAction",
    "TradeResolution",
    "TradeRetcode",
]


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


class Timeframe(StrEnum):
    """Chart and series timeframe enumeration."""

    PERIOD_CURRENT = "CURRENT"
    PERIOD_M1 = "M1"
    PERIOD_M2 = "M2"
    PERIOD_M3 = "M3"
    PERIOD_M4 = "M4"
    PERIOD_M5 = "M5"
    PERIOD_M6 = "M6"
    PERIOD_M10 = "M10"
    PERIOD_M12 = "M12"
    PERIOD_M15 = "M15"
    PERIOD_M20 = "M20"
    PERIOD_M30 = "M30"
    PERIOD_H1 = "H1"
    PERIOD_H2 = "H2"
    PERIOD_H3 = "H3"
    PERIOD_H4 = "H4"
    PERIOD_H6 = "H6"
    PERIOD_H8 = "H8"
    PERIOD_H12 = "H12"
    PERIOD_D1 = "D1"
    PERIOD_W1 = "W1"
    PERIOD_MN1 = "MN1"

    def to_seconds(self) -> int:
        """Convert timeframe duration to whole seconds."""
        val = self.value
        if val.startswith("M") and self != Timeframe.PERIOD_MN1:
            return int(val[1:]) * 60
        if val.startswith("H"):
            return int(val[1:]) * 3600
        fixed = {
            Timeframe.PERIOD_D1: 86400,
            Timeframe.PERIOD_W1: 604800,
            Timeframe.PERIOD_MN1: 2419200,
        }
        return fixed.get(self, 0)

    def to_minutes(self) -> int:
        """Convert timeframe duration to whole minutes."""
        return self.to_seconds() // 60

    @classmethod
    def from_string(cls, name: str | Timeframe) -> Timeframe:
        """Parse timeframe from common string representations."""
        if isinstance(name, cls):
            return name
        cleaned = name.strip().upper()
        mapping: dict[str, Timeframe] = {
            "M1": cls.PERIOD_M1,
            "1M": cls.PERIOD_M1,
            "1MIN": cls.PERIOD_M1,
            "M2": cls.PERIOD_M2,
            "2M": cls.PERIOD_M2,
            "M3": cls.PERIOD_M3,
            "3M": cls.PERIOD_M3,
            "M4": cls.PERIOD_M4,
            "4M": cls.PERIOD_M4,
            "M5": cls.PERIOD_M5,
            "5M": cls.PERIOD_M5,
            "5MIN": cls.PERIOD_M5,
            "M6": cls.PERIOD_M6,
            "6M": cls.PERIOD_M6,
            "M10": cls.PERIOD_M10,
            "10M": cls.PERIOD_M10,
            "M12": cls.PERIOD_M12,
            "12M": cls.PERIOD_M12,
            "M15": cls.PERIOD_M15,
            "15M": cls.PERIOD_M15,
            "15MIN": cls.PERIOD_M15,
            "M20": cls.PERIOD_M20,
            "20M": cls.PERIOD_M20,
            "M30": cls.PERIOD_M30,
            "30M": cls.PERIOD_M30,
            "30MIN": cls.PERIOD_M30,
            "H1": cls.PERIOD_H1,
            "1H": cls.PERIOD_H1,
            "60M": cls.PERIOD_H1,
            "H2": cls.PERIOD_H2,
            "2H": cls.PERIOD_H2,
            "H3": cls.PERIOD_H3,
            "3H": cls.PERIOD_H3,
            "H4": cls.PERIOD_H4,
            "4H": cls.PERIOD_H4,
            "240M": cls.PERIOD_H4,
            "H6": cls.PERIOD_H6,
            "6H": cls.PERIOD_H6,
            "H8": cls.PERIOD_H8,
            "8H": cls.PERIOD_H8,
            "H12": cls.PERIOD_H12,
            "12H": cls.PERIOD_H12,
            "D1": cls.PERIOD_D1,
            "1D": cls.PERIOD_D1,
            "DAY": cls.PERIOD_D1,
            "W1": cls.PERIOD_W1,
            "1W": cls.PERIOD_W1,
            "WEEK": cls.PERIOD_W1,
            "MN1": cls.PERIOD_MN1,
            "1MN": cls.PERIOD_MN1,
            "MONTH": cls.PERIOD_MN1,
        }
        if cleaned in mapping:
            return mapping[cleaned]
        raise ValueError(f"Unknown timeframe identifier: {name!r}")

    @classmethod
    def resolve(
        cls, val: str | Timeframe | None, default: Timeframe | None = None
    ) -> Timeframe:
        """Safely resolve a timeframe representation to a canonical Timeframe enum."""
        target_default = default if default is not None else cls.PERIOD_M1
        if val is None:
            return target_default
        if isinstance(val, cls):
            return val
        try:
            return cls.from_string(val)
        except ValueError, TypeError:
            return target_default
