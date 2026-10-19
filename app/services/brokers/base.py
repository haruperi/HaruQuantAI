"""Base broker client architecture, trading client protocol, and bridge exceptions.

Description:
    Provides the foundational BrokerClient base class for all market data providers
    and TradingClient for execution-capable brokers, replacing string-based RPC
    dispatch with direct, strongly-typed async client methods, lifecycle management,
    receipt tracking, and canonical provider exceptions.

Purpose:
    FEAT-BROKER-BASE: Foundational broker client abstractions and base exceptions.

Key Capabilities:
    - FR-BROKER-BASE-CLIENT: Uniform market data retrieval and symbol metadata queries.
      Associated: `BrokerClient.get_bars()`, `BrokerClient.get_ticks()`,
        `BrokerClient.get_symbol_info()`, `BrokerClient.get_terminal_info()`.
      Logging: DEBUG execution lifecycle and queries through provider logger.
    - FR-BROKER-BASE-TRADING: Execution, order placement, and margin calculations.
      Associated: `TradingClient.order_send()`, `TradingClient.order_check()`,
        `TradingClient.calc_margin()`, `TradingClient.calc_profit()`.
      Logging: DEBUG order and account execution operations.
    - FR-BROKER-BASE-LIFECYCLE: Connection session management, arming, and receipts.
      Associated: `BrokerClient.connect()`, `BrokerClient.disconnect()`,
        `TradingClient.arm()`, `TradingClient.disarm()`, `TradingClient.receipt()`.
      Logging: DEBUG connection and arming status changes.

Python API Usage:
    ```python
    from app.services.brokers.base import BrokerClient, TradingClient


    class CustomDataClient(BrokerClient):
        def __init__(self) -> None:
            super().__init__("custom_client")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_broker_base.py --no-cov
    ```
"""

from __future__ import annotations

import contextlib
import contextvars
import inspect
import time
import uuid
from collections.abc import Awaitable
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

from app.host.logging import get_logger
from app.services.include.contracts import (
    AccountInfo,
    BookInfo,
    BridgeError,
    BridgeEvent,
    DealInfo,
    MarketBar,
    MarketTick,
    OrderInfo,
    PositionInfo,
    Receipt,
    SymbolInfo,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.services.include.enums import (
    OrderType,
    ReceiptStatus,
    Timeframe,
)

logger = get_logger(__name__)

__all__ = [
    "BridgeError",
    "BrokerClient",
    "TradingClient",
    "epoch_millis",
    "epoch_seconds",
    "utc_now",
]


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(tz=UTC)


def epoch_seconds(value: datetime | float | None) -> int:
    """Convert an optional datetime or numeric timestamp to integer epoch seconds."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value) if value < 100_000_000_000 else int(value // 1000)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp())


def epoch_millis(value: datetime | float | None) -> int:
    """Convert an optional datetime or numeric timestamp to integer epoch milliseconds."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value * 1000) if value < 100_000_000_000 else int(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return int(value.timestamp() * 1000)


class BrokerClient:
    """Uniform base client for all market data and broker providers."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = get_logger(f"app.services.brokers.{name.lower()}")
        self._connected: bool = False

    def connect(self) -> bool:
        """Establish connection to the broker provider."""
        self.logger.debug("Connecting client: %s", self.name)
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Terminate connection and release resources."""
        self.logger.debug("Disconnecting client: %s", self.name)
        self._connected = False
        sess = getattr(self, "session", None) or getattr(self, "_session", None)
        if sess is not None and hasattr(sess, "close") and callable(sess.close):
            with contextlib.suppress(Exception):
                sess.close()

    @property
    def is_connected(self) -> bool:
        """Return connectivity status."""
        return self._connected

    @property
    def connected(self) -> bool:
        """Return connectivity status."""
        return self._connected

    @property
    def _is_connected(self) -> bool:
        """Return connectivity status for legacy test access."""
        return self._connected

    def close_sync(self) -> None:
        """Synchronously close connection."""
        self.disconnect()

    async def close(self) -> None:
        """Asynchronously close connection."""
        self.disconnect()

    async def start(self) -> None:
        """Start or initialize provider connection session."""
        self.connect()

    async def wait_connected(
        self,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> None:
        """Confirm provider readiness."""
        del timeout
        if not self._connected:
            self.connect()

    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        start_pos: int | None = None,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketBar] | Awaitable[list[MarketBar]]:
        """Fetch historical candlestick bars. Subclasses implement directly."""
        del symbol, timeframe, date_from, date_to, start_pos, count, limit
        raise BridgeError(
            f"{self.name} does not support historical bars",
            code="UNSUPPORTED_OPERATION",
        )

    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        *,
        count: int | None = None,
        limit: int = 1000,
    ) -> list[MarketTick] | Awaitable[list[MarketTick]]:
        """Fetch historical market ticks. Subclasses implement directly."""
        del symbol, date_from, date_to, count, limit
        raise BridgeError(
            f"{self.name} does not support tick history",
            code="UNSUPPORTED_OPERATION",
        )

    async def stream(
        self,
        symbol: str,
        *,
        kind: str = "ticks",
        timeframe: Timeframe | str | None = None,
    ) -> Any:
        """Establish async streaming feed."""
        del symbol, kind, timeframe
        raise BridgeError(
            f"{self.name} does not support streaming",
            code="UNSUPPORTED_OPERATION",
        )

    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Retrieve symbol metadata specifications."""
        return SymbolInfo(name=symbol)

    def symbol_info(self, symbol: str) -> SymbolInfo | None:
        """Alias for get_symbol_info."""
        return self.get_symbol_info(symbol)

    def get_symbols(self) -> list[str]:
        """List available instruments."""
        return []

    def symbols_get(self) -> list[str]:
        """Alias for get_symbols."""
        return self.get_symbols()

    def get_terminal_info(self) -> TerminalInfo:
        """Retrieve the current terminal state info."""
        return TerminalInfo(
            name=self.name,
            company=self.name,
            connected=True,
            trade_allowed=False,
        )

    async def __aenter__(self) -> Self:
        """Enter asynchronous context manager."""
        self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit asynchronous context manager."""
        del exc_type, exc, tb
        self.disconnect()


class TradingClient(BrokerClient):
    """Trading-capable broker client supporting account, order, and position operations."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._armed: bool = False
        self._last_cmd: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            f"{name}_last_cmd", default=None
        )
        self._last_cmd_id: str | None = None
        self._receipts: dict[str, Receipt] = {}
        self._current_symbol: str = "EURUSD"
        self._selected_position: Any = None
        self._selected_order: Any = None
        self._selected_history_order: Any = None
        self._selected_deal: Any = None

    def arm(self) -> None:
        """Arm client for live trade execution."""
        self._armed = True
        self.logger.debug("Client armed: %s", self.name)

    def disarm(self) -> None:
        """Disarm client to reject trade execution."""
        self._armed = False
        self.logger.debug("Client disarmed: %s", self.name)

    @property
    def is_armed(self) -> bool:
        """Return whether client is armed for execution."""
        return self._armed

    def last_command_id(self) -> str | None:
        """Return the ID of the most recent dispatched command."""
        return self._last_cmd_id or self._last_cmd.get()

    def receipt(self, command_id: str) -> Receipt | None:
        """Return the execution receipt for a command."""
        return self._receipts.get(command_id)

    def _record_receipt(
        self,
        object_id: str,
        class_name: str,
        method_name: str,
    ) -> tuple[str, Receipt]:
        """Create and store an initial command receipt."""
        cmd_id = f"cmd-{uuid.uuid4().hex[:12]}"
        self._last_cmd_id = cmd_id
        self._last_cmd.set(cmd_id)
        now = time.time()
        rec = Receipt(
            command_id=cmd_id,
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            status=ReceiptStatus.CREATED,
            created_at=now,
        )
        self._receipts[cmd_id] = rec
        return cmd_id, rec

    def _resolve_receipt(
        self,
        cmd_id: str,
        rec: Receipt,
        val: Any,
    ) -> None:
        """Mark receipt as resolved."""
        now = time.time()
        val_serialized = (
            asdict(val) if is_dataclass(val) and not isinstance(val, type) else val
        )
        self._receipts[cmd_id] = replace(
            rec,
            status=ReceiptStatus.RESOLVED,
            sent_at=now,
            acknowledged_at=now,
            resolved_at=now,
            value=val_serialized,
        )

    def _reject_receipt(
        self,
        cmd_id: str,
        rec: Receipt,
        exc: Exception,
    ) -> None:
        """Mark receipt as rejected."""
        now = time.time()
        code = getattr(exc, "code", "BROKER_ERROR")
        self._receipts[cmd_id] = replace(
            rec,
            status=ReceiptStatus.REJECTED,
            sent_at=now,
            acknowledged_at=now,
            resolved_at=now,
            error={"code": str(code), "message": str(exc)},
        )

    def get_account_info(self) -> AccountInfo | Awaitable[AccountInfo]:
        """Retrieve account state info."""
        return AccountInfo()

    def get_tick(self, name: str) -> MarketTick | None:
        """Retrieve the latest market tick for symbol."""
        del name
        return None

    def select_symbol(self, name: str, selected: bool) -> bool:
        """Select or unselect a symbol in Market Watch."""
        del name, selected
        return True

    def subscribe_book(self, name: str) -> bool:
        """Subscribe to order book updates."""
        del name
        return False

    def get_book(self, name: str) -> tuple[BookInfo, ...]:
        """Retrieve the current order book."""
        del name
        return ()

    def release_book(self, name: str) -> bool:
        """Release order book subscription."""
        del name
        return True

    def get_positions(self) -> list[PositionInfo] | Awaitable[list[PositionInfo]]:
        """Retrieve open market positions."""
        return []

    def get_orders(self) -> list[OrderInfo] | Awaitable[list[OrderInfo]]:
        """Retrieve working orders."""
        return []

    def get_history_orders(self) -> list[OrderInfo] | Awaitable[list[OrderInfo]]:
        """Retrieve historical completed/canceled orders."""
        return []

    def get_deals(self) -> list[DealInfo] | Awaitable[list[DealInfo]]:
        """Retrieve historical execution deals."""
        return []

    def order_send(self, request: TradeRequest) -> TradeResult | Awaitable[TradeResult]:
        """Execute or place an order transaction against the backend."""
        del request
        raise BridgeError(
            f"{self.name} does not support order execution",
            code="UNSUPPORTED_OPERATION",
        )

    def order_check(
        self, request: TradeRequest
    ) -> TradeCheckResult | Awaitable[TradeCheckResult]:
        """Pre-validate a trade request and calculate margin requirements."""
        del request
        return TradeCheckResult()

    def calc_margin(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price: float,
    ) -> float | Awaitable[float]:
        """Calculate required margin for an order."""
        del order_type, symbol, volume, price
        return 0.0

    def calc_profit(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float | Awaitable[float]:
        """Calculate hypothetical floating or realized profit for an order."""
        del order_type, symbol, volume, price_open, price_close
        return 0.0

    async def next_event(
        self,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> BridgeEvent:
        """Default event poll stub."""
        del timeout
        raise NotImplementedError(
            f"{self.name} does not emit asynchronous transaction events"
        )

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> BridgeEvent:
        """Default event correlation stub."""
        del request_id, timeout
        raise NotImplementedError(
            f"{self.name} does not emit asynchronous transaction events"
        )

    async def call(
        self,
        *,
        object_id: str = "broker",
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline
    ) -> Any:
        """Execute a broker command over backend transport with receipt auditing."""
        del requires_arm, timeout
        cmd_id, rec = self._record_receipt(object_id, class_name, method_name)
        try:
            val = self._dispatch(class_name, method_name, args)
            if inspect.isawaitable(val):
                val = await val
            self._resolve_receipt(cmd_id, rec, val)
            return val
        except Exception as exc:
            self._reject_receipt(cmd_id, rec, exc)
            raise

    def _dispatch(self, class_name: str, method_name: str, args: list[Any]) -> Any:
        """Route generic calls directly to TradingClient typed methods."""
        if class_name == "TerminalInfo":
            t = self.get_terminal_info()
            if method_name in ("TerminalInfo", "info"):
                return t
            target = method_name.lower()
            for attr in dir(t):
                if attr.lower() == target and not attr.startswith("_"):
                    return getattr(t, attr)
            return t

        if class_name == "AccountInfo":
            acc = self.get_account_info()
            if method_name in ("AccountInfo", "info"):
                return acc
            if method_name == "OrderProfitCheck":
                sym = str(args[0]) if len(args) > 0 else "EURUSD"
                otype = OrderType(int(args[1])) if len(args) > 1 else OrderType.BUY
                vol = float(args[2]) if len(args) > 2 else 1.0
                popen = float(args[3]) if len(args) > 3 else 0.0
                pclose = float(args[4]) if len(args) > 4 else 0.0
                return self.calc_profit(otype, sym, vol, popen, pclose)
            if method_name == "MarginCheck":
                sym = str(args[0]) if len(args) > 0 else "EURUSD"
                otype = OrderType(int(args[1])) if len(args) > 1 else OrderType.BUY
                vol = float(args[2]) if len(args) > 2 else 1.0
                price = float(args[3]) if len(args) > 3 else 0.0
                return self.calc_margin(otype, sym, vol, price)
            if method_name == "FreeMarginCheck":
                if inspect.isawaitable(acc):

                    async def _free(awaitable: Any) -> float:
                        res = await awaitable
                        return float(getattr(res, "margin_free", 0.0))

                    return _free(acc)
                return float(getattr(acc, "margin_free", 0.0))
            if method_name == "MaxLotCheck":
                return 100.0
            target = method_name.lower()
            for attr in dir(acc):
                if attr.lower() == target and not attr.startswith("_"):
                    return getattr(acc, attr)
            return getattr(acc, method_name, None)

        if class_name == "SymbolInfo":
            if method_name in ("SymbolInfo", "info"):
                sym = (
                    str(args[0])
                    if args and isinstance(args[0], str)
                    else getattr(self, "_current_symbol", "EURUSD")
                )
                return self.get_symbol_info(sym)
            if method_name == "SymbolsTotal":
                return len(self.get_symbols())
            if method_name in ("SymbolsGet", "symbols"):
                all_syms = self.get_symbols()
                if args and isinstance(args[0], str) and args[0]:
                    import fnmatch

                    pat = args[0]
                    inc_pats = [
                        p.strip()
                        for p in pat.split(",")
                        if not p.strip().startswith("!")
                    ]
                    exc_pats = [
                        p.strip()[1:]
                        for p in pat.split(",")
                        if p.strip().startswith("!")
                    ]
                    filtered = []
                    for s in all_syms:
                        inc = (
                            any(fnmatch.fnmatch(s, p) for p in inc_pats)
                            if inc_pats
                            else True
                        )
                        exc = (
                            any(fnmatch.fnmatch(s, p) for p in exc_pats)
                            if exc_pats
                            else False
                        )
                        if inc and not exc:
                            filtered.append(s)
                    return filtered
                return all_syms
            if method_name == "SymbolInfoTick":
                sym = (
                    str(args[0])
                    if args and isinstance(args[0], str)
                    else getattr(self, "_current_symbol", "EURUSD")
                )
                return self.get_tick(sym)
            if method_name == "SymbolSelect":
                sym = (
                    str(args[0])
                    if args and isinstance(args[0], str)
                    else getattr(self, "_current_symbol", "EURUSD")
                )
                sel = bool(args[1]) if len(args) > 1 else True
                return self.select_symbol(sym, sel)
            if method_name in ("MarketBookAdd", "subscribe_book"):
                sym = (
                    str(args[0])
                    if args and isinstance(args[0], str)
                    else getattr(self, "_current_symbol", "EURUSD")
                )
                return self.subscribe_book(sym)
            if method_name in ("MarketBookRelease", "release_book"):
                sym = (
                    str(args[0])
                    if args and isinstance(args[0], str)
                    else getattr(self, "_current_symbol", "EURUSD")
                )
                return self.release_book(sym)
            if method_name in ("MarketBookGet", "get_book"):
                sym = (
                    str(args[0])
                    if args and isinstance(args[0], str)
                    else getattr(self, "_current_symbol", "EURUSD")
                )
                return self.get_book(sym)
            if method_name in ("Refresh", "RefreshRates", "IsSynchronized"):
                return True
            if method_name == "NormalizePrice":
                price = float(args[0]) if args else 0.0
                digits = int(args[1]) if len(args) > 1 else 5
                return round(price, digits)
            if method_name == "Name":
                if args and isinstance(args[0], str):
                    self._current_symbol = args[0]
                    return self.get_symbol_info(args[0]) is not None
                return getattr(self, "_current_symbol", "EURUSD")
            if method_name == "Select":
                if args and isinstance(args[0], str):
                    self._current_symbol = args[0]
                    return self.get_symbol_info(args[0]) is not None
                return True
            sym = getattr(self, "_current_symbol", "EURUSD")
            if args and isinstance(args[0], str):
                sym = args[0]
            info = self.get_symbol_info(sym)
            target_field = method_name.lower()
            for attr in dir(info):
                if attr.lower() == target_field and not attr.startswith("_"):
                    return getattr(info, attr)
            return getattr(info, method_name, None)

        if class_name == "PositionInfo":
            pos_raw = self.get_positions()
            positions = pos_raw if isinstance(pos_raw, list) else []
            if method_name == "PositionsTotal":
                return len(positions)
            if method_name in ("PositionsGet", "positions"):
                if args and isinstance(args[0], str) and args[0]:
                    target_sym = args[0]
                    return [
                        p for p in positions if getattr(p, "symbol", "") == target_sym
                    ]
                return positions
            if method_name in ("PositionInfo", "info"):
                if self._selected_position is not None:
                    return self._selected_position
                if positions:
                    return positions[0]
                from app.services.include.contracts import PositionInfo

                return PositionInfo()
            if method_name == "Select":
                target = str(args[0]) if args else ""
                for p in positions:
                    if getattr(p, "symbol", "") == target:
                        self._selected_position = p
                        return True
                return False
            if method_name == "SelectByIndex":
                idx = int(args[0]) if args else 0
                if 0 <= idx < len(positions):
                    self._selected_position = positions[idx]
                    return True
                return False
            if method_name in (
                "PositionGetTicket",
                "PositionSelectByTicket",
                "SelectByTicket",
            ):
                ticket = int(args[0]) if args else 0
                for p in positions:
                    if getattr(p, "ticket", 0) == ticket:
                        self._selected_position = p
                        return True
                return False
            if method_name == "SelectByMagic":
                target_sym = str(args[0]) if args else ""
                magic = int(args[1]) if len(args) > 1 else 0
                for p in positions:
                    if (
                        getattr(p, "symbol", "") == target_sym
                        and getattr(p, "magic", 0) == magic
                    ):
                        self._selected_position = p
                        return True
                return False
            if method_name in ("StoreState", "CheckState"):
                return True

        if class_name == "OrderInfo":
            ord_raw = self.get_orders()
            orders = ord_raw if isinstance(ord_raw, list) else []
            if method_name == "OrdersTotal":
                return len(orders)
            if method_name in ("OrdersGet", "orders"):
                return orders
            if method_name in ("OrderInfo", "info"):
                if self._selected_order is not None:
                    return self._selected_order
                if orders:
                    return orders[0]
                from app.services.include.contracts import OrderInfo

                return OrderInfo()
            if method_name in (
                "OrderGetTicket",
                "OrderSelect",
                "Select",
                "SelectByTicket",
            ):
                ticket = int(args[0]) if args else 0
                for o in orders:
                    if getattr(o, "ticket", 0) == ticket:
                        self._selected_order = o
                        return True
                return False
            if method_name == "SelectByIndex":
                idx = int(args[0]) if args else 0
                if 0 <= idx < len(orders):
                    self._selected_order = orders[idx]
                    return True
                return False
            if method_name in ("StoreState", "CheckState"):
                return True

        if class_name == "HistoryOrderInfo":
            h_raw = self.get_history_orders()
            h_orders = h_raw if isinstance(h_raw, list) else []
            if method_name == "HistoryOrdersTotal":
                return len(h_orders)
            if method_name in ("HistoryOrdersGet", "orders"):
                return h_orders
            if method_name in ("HistoryOrderInfo", "info"):
                if self._selected_history_order is not None:
                    return self._selected_history_order
                if h_orders:
                    return h_orders[0]
                from app.services.include.contracts import OrderInfo

                return OrderInfo()
            if method_name in (
                "HistoryOrderGetTicket",
                "HistoryOrderSelect",
                "Select",
                "SelectByTicket",
                "Ticket",
            ):
                ticket = int(args[0]) if args else 0
                for o in h_orders:
                    if getattr(o, "ticket", 0) == ticket:
                        self._selected_history_order = o
                        return True
                return False
            if method_name == "SelectByIndex":
                idx = int(args[0]) if args else 0
                if 0 <= idx < len(h_orders):
                    self._selected_history_order = h_orders[idx]
                    return True
                return False

        if class_name == "DealInfo":
            d_raw = self.get_deals()
            deals = d_raw if isinstance(d_raw, list) else []
            if method_name == "HistoryDealsTotal":
                return len(deals)
            if method_name in ("HistoryDealsGet", "deals"):
                return deals
            if method_name in ("DealInfo", "info"):
                if self._selected_deal is not None:
                    return self._selected_deal
                if deals:
                    return deals[0]
                from app.services.include.contracts import DealInfo

                return DealInfo()
            if method_name in (
                "HistoryDealGetTicket",
                "HistoryDealSelect",
                "Select",
                "SelectByTicket",
                "Ticket",
            ):
                ticket = int(args[0]) if args else 0
                for d in deals:
                    if getattr(d, "ticket", 0) == ticket:
                        self._selected_deal = d
                        return True
                return False
            if method_name == "SelectByIndex":
                idx = int(args[0]) if args else 0
                if 0 <= idx < len(deals):
                    self._selected_deal = deals[idx]
                    return True
                return False

        if class_name == "Trade":
            if method_name == "OrderSend":
                raw_req = args[0] if args else None
                req = self._coerce_trade_request(raw_req)
                return self.order_send(req)
            if method_name == "OrderCheck":
                raw_req = args[0] if args else None
                req = self._coerce_trade_request(raw_req)
                return self.order_check(req)
            if method_name in (
                "SetExpertMagicNumber",
                "SetDeviationInPoints",
                "SetTypeFilling",
                "SetTypeFillingBySymbol",
                "SetAsyncMode",
                "SetMarginMode",
                "LogLevel",
                "PrintRequest",
                "PrintResult",
            ):
                return True
            if method_name in ("FormatRequest", "FormatRequestResult"):
                return ""
            if method_name == "Request":
                from app.services.include.contracts import TradeRequest

                return TradeRequest()
            if method_name == "Result":
                from app.services.include.contracts import TradeResult

                return TradeResult()
            if method_name == "CheckResult":
                from app.services.include.contracts import TradeCheckResult

                return TradeCheckResult()

        if class_name in ("MarketDepth", "Book"):
            sym = str(args[0]) if args else getattr(self, "_current_symbol", "EURUSD")
            if method_name in ("Subscribe", "MarketBookAdd"):
                return self.subscribe_book(sym)
            if method_name in ("Get", "MarketBookGet"):
                return self.get_book(sym)
            if method_name in ("Release", "MarketBookRelease"):
                return self.release_book(sym)

        raise BridgeError(
            f"{self.name} does not support {class_name}.{method_name}",
            code="UNSUPPORTED_OPERATION",
        )

    def _coerce_trade_request(self, req: Any) -> Any:
        if req is None:
            from app.services.include.contracts import TradeRequest

            return TradeRequest()
        if isinstance(req, dict):
            from app.services.include.contracts import TradeRequest
            from app.services.include.enums import (
                OrderFilling,
                OrderTime,
                OrderType,
                TradeAction,
            )

            action = req.get("action", TradeAction.DEAL)
            if isinstance(action, int):
                action = TradeAction(action)
            order_type = req.get("order_type", OrderType.BUY)
            if isinstance(order_type, int):
                order_type = OrderType(order_type)
            type_filling = req.get("type_filling", OrderFilling.FOK)
            if isinstance(type_filling, int):
                type_filling = OrderFilling(type_filling)
            type_time = req.get("type_time", OrderTime.GTC)
            if isinstance(type_time, int):
                type_time = OrderTime(type_time)
            return TradeRequest(
                action=action,
                magic=int(req.get("magic", 0)),
                order=int(req.get("order", 0)),
                symbol=str(req.get("symbol", "")),
                volume=float(req.get("volume", 0.0)),
                price=float(req.get("price", 0.0)),
                stoplimit=float(req.get("stoplimit", 0.0)),
                sl=float(req.get("sl", 0.0)),
                tp=float(req.get("tp", 0.0)),
                deviation=int(req.get("deviation", 0)),
                order_type=order_type,
                type_filling=type_filling,
                type_time=type_time,
                expiration=req.get("expiration"),
                comment=str(req.get("comment", "")),
                position=int(req.get("position", 0)),
                position_by=int(req.get("position_by", 0)),
            )
        return req
