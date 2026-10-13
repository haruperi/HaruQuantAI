"""Deterministic trading simulator with explicitly seeded historical data.

Description:
    Own in-memory orders, fills, positions, deals, margin and account state.
    External tick feeding advances model time; historical read requests only
    filter immutable seeded records and use the async command/receipt lifecycle.

Purpose:
    FEAT-BROKER-SIMULATION: Local broker semantics for strategy verification.

Key Capabilities:
    - FR-SIMULATION-DISPATCH: Execute native-shaped operations with receipts.
      Associated: `SimulationBackend.call()`
      Logging: DEBUG every dispatch with class/method metadata, never arguments.
    - FR-SIMULATION-HISTORY: Seed and query historical bars and ticks.
      Associated: `seed_bar_history()`, `seed_tick_history()`, `_market_data()`
      Logging: DEBUG each seeding/read attempt, without row contents.

Python API Usage:
    Supply SimulationBackend to Trading; feed symbols/ticks and seed history
    explicitly before querying. No data is fabricated by historical requests.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_simulator.py --no-cov
"""

# ruff: noqa: C901, PLR0911, PLR0912, PLR0915, PLR2004, SIM102, D, DOC

from __future__ import annotations

import asyncio
import contextvars
import os
import uuid
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass, replace
from datetime import UTC, datetime
from enum import IntEnum
from itertools import count
from typing import Any, override

from app.host.logging import get_logger
from app.services.brokers._simulation_api import (
    HANDLERS,
    _ObjectState,
    execute,
    new_state,
    prepare_args,
)
from app.services.brokers.contracts import (
    AccountSnapshot,
    BridgeError,
    BridgeEvent,
    BrokerBackend,
    DealEntry,
    DealRecord,
    DealType,
    MarginMode,
    MarketBar,
    MarketTick,
    OrderFilling,
    OrderRecord,
    OrderState,
    OrderTime,
    OrderType,
    PositionRecord,
    PositionType,
    Receipt,
    ReceiptStatus,
    SymbolSpec,
    SymbolTradeExecution,
    SymbolTradeMode,
    TerminalSnapshot,
    Tick,
    Timeframe,
    TradeAction,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradeRetcode,
    utc_now,
)

logger = get_logger(__name__)


class SimulationBackend(BrokerBackend):
    """In-memory broker simulator with MT5-oriented execution semantics."""

    def __init__(
        self,
        *,
        initial_balance: float = 10_000.0,
        leverage: int = 100,
        margin_mode: MarginMode = MarginMode.RETAIL_HEDGING,
        currency: str = "USD",
        commission_per_lot: float = 0.0,
    ) -> None:
        self._objects: dict[str, tuple[str, _ObjectState]] = {}
        self._receipts: dict[str, Receipt] = {}
        self._last_command: contextvars.ContextVar[str | None] = contextvars.ContextVar(
            "simulation_last_command", default=None
        )
        self._armed = False
        self._event_queue: asyncio.Queue[BridgeEvent] = asyncio.Queue()
        self._connected = True
        self._clock = utc_now()
        self._symbols: dict[str, SymbolSpec] = {}
        self._ticks: dict[str, Tick] = {}
        self._bar_history: dict[tuple[str, Timeframe], tuple[MarketBar, ...]] = {}
        self._tick_history: dict[str, tuple[MarketTick, ...]] = {}
        self._orders: dict[int, OrderRecord] = {}
        self._history_orders: list[OrderRecord] = []
        self._positions: dict[int, PositionRecord] = {}
        self._deals: list[DealRecord] = []
        self._order_ids = count(1)
        self._deal_ids = count(1_000_001)
        self._position_ids = count(10_000_001)
        self._commission_per_lot = float(commission_per_lot)
        self._stats: dict[str, dict[str, float]] = {}
        self._account = AccountSnapshot(
            leverage=leverage,
            margin_mode=margin_mode,
            balance=float(initial_balance),
            equity=float(initial_balance),
            free_margin=float(initial_balance),
            currency=currency,
        )
        self._terminal = TerminalSnapshot(
            connected=True,
            trade_allowed=True,
            cpu_cores=os.cpu_count() or 1,
        )

    # ------------------------------------------------------------------
    # Configuration / market feed
    # ------------------------------------------------------------------

    def add_symbol(self, spec: SymbolSpec) -> None:
        """Register a symbol specification with the simulator."""
        self._symbols[spec.name] = replace(spec)
        self._stats.setdefault(spec.name, {})

    def feed_tick(
        self,
        symbol: str,
        *,
        bid: float,
        ask: float,
        time: datetime | None = None,
        last: float | None = None,
        volume: float = 0.0,
    ) -> Tick:
        """Advance simulator time and update pricing with a new tick."""
        if symbol not in self._symbols:
            raise KeyError(f"Symbol {symbol!r} has not been registered")
        if ask < bid:
            raise ValueError("ask must be >= bid")
        now = time or self._clock
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        self._clock = now
        tick = Tick(
            symbol=symbol,
            time=now,
            bid=float(bid),
            ask=float(ask),
            last=float(last if last is not None else (bid + ask) / 2.0),
            volume=float(volume),
        )
        self._ticks[symbol] = tick
        stats = self._stats.setdefault(symbol, {})
        for key, value in (
            ("bid", bid),
            ("ask", ask),
            ("last", tick.last),
            ("volume", volume),
        ):
            high_key, low_key = f"{key}_high", f"{key}_low"
            stats[high_key] = max(float(value), stats.get(high_key, float(value)))
            stats[low_key] = min(float(value), stats.get(low_key, float(value)))

        spec = self._symbols[symbol]
        if spec.session_open == 0.0:
            spec.session_open = tick.last
        spec.session_close = tick.last

        self._expire_orders()
        self._trigger_pending(symbol, tick)
        self._trigger_stops(symbol, tick)
        self._mark_to_market()
        return tick

    @override
    def set_clock(self, now: datetime) -> None:
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        self._clock = now
        self._expire_orders()
        self._mark_to_market()

    # ------------------------------------------------------------------
    # BrokerBackend
    # ------------------------------------------------------------------

    @override
    def connect(self) -> bool:
        self._connected = True
        self._terminal.connected = True
        return True

    @override
    def disconnect(self) -> None:
        self._connected = False
        self._terminal.connected = False

    @override
    def terminal(self) -> TerminalSnapshot:
        return replace(self._terminal)

    @override
    def account(self) -> AccountSnapshot:
        self._mark_to_market()
        return replace(self._account)

    @override
    def symbol(self, name: str) -> SymbolSpec | None:
        spec = self._symbols.get(name)
        return replace(spec) if spec is not None else None

    @override
    def symbols(self) -> list[SymbolSpec]:
        return [replace(v) for v in self._symbols.values()]

    @override
    def select_symbol(self, name: str, selected: bool) -> bool:
        spec = self._symbols.get(name)
        if spec is None:
            return False
        spec.selected = selected
        return True

    @override
    def tick(self, name: str) -> Tick | None:
        value = self._ticks.get(name)
        return replace(value) if value is not None else None

    @override
    def orders(self) -> list[OrderRecord]:
        return [replace(v) for _, v in sorted(self._orders.items())]

    @override
    def history_orders(self) -> list[OrderRecord]:
        return [replace(v) for v in self._history_orders]

    @override
    def positions(self) -> list[PositionRecord]:
        self._mark_to_market()
        return [replace(v) for _, v in sorted(self._positions.items())]

    @override
    def deals(self) -> list[DealRecord]:
        return [replace(v) for v in self._deals]

    @override
    def order_check(self, request: TradeRequest) -> TradeCheckResult:
        self._mark_to_market()
        retcode, comment = self._validate_request(request)
        margin = 0.0
        if (
            retcode == TradeRetcode.DONE
            and request.action in {TradeAction.DEAL, TradeAction.PENDING}
            and request.symbol
            and request.volume > 0
        ):
            price = request.price
            tick = self._ticks.get(request.symbol)
            if price <= 0 and tick is not None:
                price = (
                    tick.ask
                    if request.order_type
                    in {
                        OrderType.BUY,
                        OrderType.BUY_LIMIT,
                        OrderType.BUY_STOP,
                        OrderType.BUY_STOP_LIMIT,
                    }
                    else tick.bid
                )
            margin = self.order_calc_margin(
                request.order_type, request.symbol, request.volume, price
            )
            if margin > self._account.free_margin:
                retcode = TradeRetcode.NO_MONEY
                comment = "Not enough money"

        return TradeCheckResult(
            retcode=int(retcode),
            balance=self._account.balance,
            equity=self._account.equity,
            profit=self._account.profit,
            margin=margin,
            margin_free=max(0.0, self._account.free_margin - margin),
            margin_level=self._account.margin_level,
            comment=comment,
        )

    @override
    def order_send(self, request: TradeRequest) -> TradeResult:
        check = self.order_check(request)
        if check.retcode != int(TradeRetcode.DONE):
            return TradeResult(retcode=check.retcode, comment=check.comment)

        if request.action == TradeAction.DEAL:
            if request.position:
                return self._close_position(
                    request.position,
                    request.volume,
                    comment=request.comment or "close",
                )
            return self._market_open(request)
        if request.action == TradeAction.PENDING:
            return self._place_pending(request)
        if request.action == TradeAction.REMOVE:
            return self._remove_order(request.order)
        if request.action == TradeAction.MODIFY:
            return self._modify_order(request)
        if request.action == TradeAction.SLTP:
            return self._modify_position(request)
        if request.action == TradeAction.CLOSE_BY:
            return self._close_by(request.position, request.position_by)
        # Raw external action IDs can be outside the statically exhaustive enum.
        return TradeResult(  # type: ignore[unreachable]
            retcode=int(TradeRetcode.INVALID),
            comment=f"Unsupported action {request.action}",
        )

    @override
    def order_calc_profit(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float:
        spec = self._symbols.get(symbol)
        if spec is None:
            return 0.0
        direction = 1.0 if order_type == OrderType.BUY else -1.0
        return (
            (float(price_close) - float(price_open))
            * direction
            * float(volume)
            * spec.contract_size
        )

    @override
    def order_calc_margin(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price: float,
    ) -> float:
        del order_type
        spec = self._symbols.get(symbol)
        if spec is None or volume <= 0:
            return 0.0
        if spec.margin_initial > 0:
            return spec.margin_initial * volume
        leverage = max(1, self._account.leverage)
        return spec.contract_size * volume * max(price, spec.point) / leverage

    @override
    def info_value(
        self,
        scope: str,
        property_id: int | str,
        selector: str | int | None = None,
    ) -> Any:
        if not isinstance(property_id, str):
            return None
        key = property_id.strip().lower()
        if scope == "account":
            return asdict(self._account).get(key)
        if scope == "terminal":
            return asdict(self._terminal).get(key)
        if scope == "symbol" and isinstance(selector, str):
            if key in self._stats.get(selector, {}):
                return self._stats[selector][key]
            spec = self._symbols.get(selector)
            return asdict(spec).get(key) if spec is not None else None
        collections: dict[str, list[Any]] = {
            "order": list(self._orders.values()),
            "history_order": self._history_orders,
            "position": list(self._positions.values()),
            "deal": self._deals,
        }
        values = collections.get(scope, [])
        for value in values:
            ticket = getattr(value, "ticket", None)
            symbol = getattr(value, "symbol", None)
            if selector in {ticket, symbol}:
                return asdict(value).get(key)
        return None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_request(self, request: TradeRequest) -> tuple[TradeRetcode, str]:
        if not self._connected:
            return TradeRetcode.CONNECTION, "No connection"
        if not self._terminal.trade_allowed or not self._account.trade_allowed:
            return TradeRetcode.TRADE_DISABLED, "Trading is disabled"

        if request.action == TradeAction.REMOVE:
            if request.order not in self._orders:
                return TradeRetcode.INVALID_ORDER, "Order not found"
            return TradeRetcode.DONE, "Done"

        if request.action == TradeAction.MODIFY:
            order = self._orders.get(request.order)
            if order is None:
                return TradeRetcode.INVALID_ORDER, "Order not found"
            spec = self._symbols.get(order.symbol)
            if spec is None:
                return TradeRetcode.INVALID_ORDER, "Unknown symbol"
            candidate = replace(
                request,
                symbol=order.symbol,
                volume=order.volume_current,
                order_type=order.order_type,
                price=request.price or order.price_open,
                stoplimit=request.stoplimit or order.price_stop_limit,
            )
            if not self._pending_price_valid(candidate, spec):
                return TradeRetcode.INVALID_PRICE, "Invalid pending order price"
            if not self._stops_valid(candidate, spec):
                return TradeRetcode.INVALID_STOPS, "Invalid stops"
            return TradeRetcode.DONE, "Done"

        if request.action == TradeAction.SLTP:
            position = self._positions.get(request.position)
            if position is None:
                return TradeRetcode.POSITION_CLOSED, "Position not found"
            spec = self._symbols.get(position.symbol)
            tick = self._ticks.get(position.symbol)
            if spec is not None and tick is not None:
                minimum = spec.stops_level * spec.point
                if position.position_type == PositionType.BUY:
                    if request.sl and tick.bid - request.sl < minimum - 1e-12:
                        return TradeRetcode.INVALID_STOPS, "Invalid stop loss"
                    if request.tp and request.tp - tick.bid < minimum - 1e-12:
                        return TradeRetcode.INVALID_STOPS, "Invalid take profit"
                else:
                    if request.sl and request.sl - tick.ask < minimum - 1e-12:
                        return TradeRetcode.INVALID_STOPS, "Invalid stop loss"
                    if request.tp and tick.ask - request.tp < minimum - 1e-12:
                        return TradeRetcode.INVALID_STOPS, "Invalid take profit"
            return TradeRetcode.DONE, "Done"

        if request.action == TradeAction.CLOSE_BY:
            p1 = self._positions.get(request.position)
            p2 = self._positions.get(request.position_by)
            if p1 is None or p2 is None:
                return TradeRetcode.POSITION_CLOSED, "Position not found"
            if p1.symbol != p2.symbol or p1.position_type == p2.position_type:
                return (
                    TradeRetcode.INVALID_ORDER,
                    "Close By requires opposite positions on same symbol",
                )
            return TradeRetcode.DONE, "Done"

        if request.action == TradeAction.DEAL and request.position:
            position = self._positions.get(request.position)
            if position is None:
                return TradeRetcode.POSITION_CLOSED, "Position not found"
            if request.volume <= 0 or request.volume > position.volume + 1e-12:
                return TradeRetcode.INVALID_CLOSE_VOLUME, "Invalid close volume"
            return TradeRetcode.DONE, "Done"

        spec = self._symbols.get(request.symbol)
        if spec is None:
            return TradeRetcode.INVALID_ORDER, "Unknown symbol"
        if spec.trade_mode == SymbolTradeMode.DISABLED:
            return TradeRetcode.TRADE_DISABLED, "Symbol trading is disabled"
        if spec.trade_mode == SymbolTradeMode.CLOSEONLY and not request.position:
            return TradeRetcode.CLOSE_ONLY, "Symbol is close-only"
        if spec.trade_mode == SymbolTradeMode.LONGONLY and request.order_type in {
            OrderType.SELL,
            OrderType.SELL_LIMIT,
            OrderType.SELL_STOP,
            OrderType.SELL_STOP_LIMIT,
        }:
            return TradeRetcode.LONG_ONLY, "Only long positions are allowed"
        if spec.trade_mode == SymbolTradeMode.SHORTONLY and request.order_type in {
            OrderType.BUY,
            OrderType.BUY_LIMIT,
            OrderType.BUY_STOP,
            OrderType.BUY_STOP_LIMIT,
        }:
            return TradeRetcode.SHORT_ONLY, "Only short positions are allowed"

        if request.volume <= 0 or not self._volume_valid(spec, request.volume):
            return TradeRetcode.INVALID_VOLUME, "Invalid volume"

        if (
            request.action == TradeAction.DEAL
            and spec.trade_execution == SymbolTradeExecution.MARKET
        ):
            flags = spec.trade_fill_flags
            if request.type_filling == OrderFilling.FOK and not (flags & 1):
                return TradeRetcode.INVALID_FILL, "FOK filling is not supported"
            if request.type_filling == OrderFilling.IOC and not (flags & 2):
                return TradeRetcode.INVALID_FILL, "IOC filling is not supported"
            if request.type_filling == OrderFilling.RETURN:
                return (
                    TradeRetcode.INVALID_FILL,
                    "RETURN is not valid for Market Execution",
                )

        if request.action == TradeAction.DEAL and request.symbol not in self._ticks:
            return TradeRetcode.PRICE_OFF, "No market price"

        if request.action == TradeAction.PENDING:
            if request.price <= 0:
                return (
                    TradeRetcode.INVALID_PRICE,
                    "Pending order requires a positive price",
                )
            if request.symbol not in self._ticks:
                return TradeRetcode.PRICE_OFF, "No market price"
            if (
                self._account.limit_orders > 0
                and len(self._orders) >= self._account.limit_orders
            ):
                return TradeRetcode.LIMIT_ORDERS, "Pending-order limit reached"
            if request.type_time in {OrderTime.SPECIFIED, OrderTime.SPECIFIED_DAY}:
                if request.expiration is None or request.expiration <= self._clock:
                    return TradeRetcode.INVALID_EXPIRATION, "Invalid expiration"
            if not self._pending_price_valid(request, spec):
                return TradeRetcode.INVALID_PRICE, "Invalid pending order price"

        if not self._stops_valid(request, spec):
            return TradeRetcode.INVALID_STOPS, "Invalid stops"

        if spec.lots_limit > 0:
            buy_types = {
                OrderType.BUY,
                OrderType.BUY_LIMIT,
                OrderType.BUY_STOP,
                OrderType.BUY_STOP_LIMIT,
            }
            same_side = request.order_type in buy_types
            used = sum(
                p.volume
                for p in self._positions.values()
                if p.symbol == request.symbol
                and ((p.position_type == PositionType.BUY) == same_side)
            ) + sum(
                o.volume_current
                for o in self._orders.values()
                if o.symbol == request.symbol
                and ((o.order_type in buy_types) == same_side)
            )
            if used + request.volume > spec.lots_limit + 1e-12:
                return TradeRetcode.LIMIT_VOLUME, "Symbol volume limit reached"

        return TradeRetcode.DONE, "Done"

    def _pending_price_valid(self, request: TradeRequest, spec: SymbolSpec) -> bool:
        if request.action not in {TradeAction.PENDING, TradeAction.MODIFY}:
            return True
        tick = self._ticks.get(request.symbol)
        if tick is None:
            return False
        minimum = spec.stops_level * spec.point
        price = request.price
        if request.order_type == OrderType.BUY_LIMIT:
            return price <= tick.ask - minimum + 1e-12
        if request.order_type == OrderType.SELL_LIMIT:
            return price >= tick.bid + minimum - 1e-12
        if request.order_type == OrderType.BUY_STOP:
            return price >= tick.ask + minimum - 1e-12
        if request.order_type == OrderType.SELL_STOP:
            return price <= tick.bid - minimum + 1e-12
        if request.order_type == OrderType.BUY_STOP_LIMIT:
            return (
                price >= tick.ask + minimum - 1e-12
                and request.stoplimit > 0
                and request.stoplimit <= price + 1e-12
            )
        if request.order_type == OrderType.SELL_STOP_LIMIT:
            return (
                price <= tick.bid - minimum + 1e-12
                and request.stoplimit > 0
                and request.stoplimit >= price - 1e-12
            )
        return False

    @staticmethod
    def _volume_valid(spec: SymbolSpec, volume: float) -> bool:
        if volume < spec.lots_min - 1e-12 or volume > spec.lots_max + 1e-12:
            return False
        step = max(spec.lots_step, 1e-12)
        n = (volume - spec.lots_min) / step
        return abs(n - round(n)) <= 1e-7

    def _stops_valid(self, request: TradeRequest, spec: SymbolSpec) -> bool:
        minimum = spec.stops_level * spec.point
        if minimum <= 0:
            return True
        tick = self._ticks.get(request.symbol)
        if tick is None:
            return True
        buy_types = {
            OrderType.BUY,
            OrderType.BUY_LIMIT,
            OrderType.BUY_STOP,
            OrderType.BUY_STOP_LIMIT,
        }
        sell_types = {
            OrderType.SELL,
            OrderType.SELL_LIMIT,
            OrderType.SELL_STOP,
            OrderType.SELL_STOP_LIMIT,
        }
        if request.action == TradeAction.DEAL:
            entry = tick.ask if request.order_type == OrderType.BUY else tick.bid
        elif request.action in {TradeAction.PENDING, TradeAction.MODIFY}:
            entry = request.price
        else:
            return True
        if request.order_type in buy_types:
            if request.sl and entry - request.sl < minimum - 1e-12:
                return False
            if request.tp and request.tp - entry < minimum - 1e-12:
                return False
        elif request.order_type in sell_types:
            if request.sl and request.sl - entry < minimum - 1e-12:
                return False
            if request.tp and entry - request.tp < minimum - 1e-12:
                return False
        return True

    # ------------------------------------------------------------------
    # Order operations
    # ------------------------------------------------------------------

    def _place_pending(self, request: TradeRequest) -> TradeResult:
        ticket = next(self._order_ids)
        tick = self._ticks.get(request.symbol)
        current = 0.0
        if tick is not None:
            current = (
                tick.ask
                if request.order_type
                in {OrderType.BUY_LIMIT, OrderType.BUY_STOP, OrderType.BUY_STOP_LIMIT}
                else tick.bid
            )
        record = OrderRecord(
            ticket=ticket,
            symbol=request.symbol,
            order_type=request.order_type,
            state=OrderState.PLACED,
            volume_initial=request.volume,
            volume_current=request.volume,
            price_open=request.price,
            sl=request.sl,
            tp=request.tp,
            price_current=current,
            price_stop_limit=request.stoplimit,
            time_setup=self._clock,
            time_expiration=request.expiration,
            type_filling=request.type_filling,
            type_time=request.type_time,
            magic=request.magic,
            comment=request.comment,
        )
        self._orders[ticket] = record
        spec = self._symbols[request.symbol]
        if request.order_type in {
            OrderType.BUY_LIMIT,
            OrderType.BUY_STOP,
            OrderType.BUY_STOP_LIMIT,
        }:
            spec.session_buy_orders += 1
            spec.session_buy_orders_volume += request.volume
        else:
            spec.session_sell_orders += 1
            spec.session_sell_orders_volume += request.volume
        return TradeResult(
            retcode=int(TradeRetcode.PLACED),
            order=ticket,
            volume=request.volume,
            price=request.price,
            bid=tick.bid if tick else 0.0,
            ask=tick.ask if tick else 0.0,
            comment="Order placed",
        )

    def _remove_order(self, ticket: int) -> TradeResult:
        order = self._orders.pop(ticket, None)
        if order is None:
            return TradeResult(
                retcode=int(TradeRetcode.INVALID_ORDER), comment="Order not found"
            )
        order.state = OrderState.CANCELED
        order.time_done = self._clock
        self._history_orders.append(replace(order))
        return TradeResult(
            retcode=int(TradeRetcode.DONE), order=ticket, comment="Order canceled"
        )

    def _modify_order(self, request: TradeRequest) -> TradeResult:
        order = self._orders.get(request.order)
        if order is None:
            return TradeResult(
                retcode=int(TradeRetcode.INVALID_ORDER), comment="Order not found"
            )
        changed = False
        for name, value in (
            ("price_open", request.price),
            ("sl", request.sl),
            ("tp", request.tp),
            ("price_stop_limit", request.stoplimit),
            ("time_expiration", request.expiration),
            ("type_time", request.type_time),
        ):
            if value is not None and getattr(order, name) != value:
                setattr(order, name, value)
                changed = True
        if not changed:
            return TradeResult(
                retcode=int(TradeRetcode.NO_CHANGES),
                order=order.ticket,
                comment="No changes",
            )
        return TradeResult(
            retcode=int(TradeRetcode.DONE),
            order=order.ticket,
            comment="Order modified",
        )

    def _modify_position(self, request: TradeRequest) -> TradeResult:
        position = self._positions.get(request.position)
        if position is None:
            return TradeResult(
                retcode=int(TradeRetcode.POSITION_CLOSED), comment="Position not found"
            )
        if position.sl == request.sl and position.tp == request.tp:
            return TradeResult(
                retcode=int(TradeRetcode.NO_CHANGES),
                order=position.ticket,
                comment="No changes",
            )
        position.sl = request.sl
        position.tp = request.tp
        position.time_update = self._clock
        return TradeResult(
            retcode=int(TradeRetcode.DONE),
            order=position.ticket,
            comment="Position modified",
        )

    # ------------------------------------------------------------------
    # Market execution
    # ------------------------------------------------------------------

    def _market_open(self, request: TradeRequest) -> TradeResult:
        tick = self._ticks[request.symbol]
        price = tick.ask if request.order_type == OrderType.BUY else tick.bid

        if self._account.margin_mode != MarginMode.RETAIL_HEDGING:
            existing = next(
                (p for p in self._positions.values() if p.symbol == request.symbol),
                None,
            )
            if existing is not None:
                requested_side = (
                    PositionType.BUY
                    if request.order_type == OrderType.BUY
                    else PositionType.SELL
                )
                if existing.position_type == requested_side:
                    return self._netting_add(existing, request, price, tick)
                return self._netting_offset(existing, request, price, tick)

        return self._open_new_position(request, price, tick)

    def _open_new_position(
        self,
        request: TradeRequest,
        price: float,
        tick: Tick,
        *,
        order_ticket: int | None = None,
    ) -> TradeResult:
        order_ticket = order_ticket or next(self._order_ids)
        position_ticket = next(self._position_ids)
        deal_ticket = next(self._deal_ids)
        side = (
            PositionType.BUY
            if request.order_type == OrderType.BUY
            else PositionType.SELL
        )
        commission = abs(request.volume) * self._commission_per_lot

        position = PositionRecord(
            ticket=position_ticket,
            identifier=position_ticket,
            symbol=request.symbol,
            position_type=side,
            volume=request.volume,
            price_open=price,
            price_current=price,
            sl=request.sl,
            tp=request.tp,
            commission=commission,
            time=self._clock,
            time_update=self._clock,
            magic=request.magic,
            comment=request.comment,
        )
        self._positions[position_ticket] = position
        self._account.balance -= commission

        deal = DealRecord(
            ticket=deal_ticket,
            order=order_ticket,
            position_id=position_ticket,
            symbol=request.symbol,
            deal_type=DealType.BUY if side == PositionType.BUY else DealType.SELL,
            entry=DealEntry.IN,
            volume=request.volume,
            price=price,
            commission=-commission,
            time=self._clock,
            magic=request.magic,
            comment=request.comment,
        )
        self._deals.append(deal)
        self._append_filled_order(request, order_ticket, position_ticket, price)
        spec = self._symbols[request.symbol]
        spec.session_deals += 1
        spec.session_turnover += abs(price * request.volume * spec.contract_size)
        self._mark_to_market()
        return TradeResult(
            retcode=int(TradeRetcode.DONE),
            deal=deal_ticket,
            order=order_ticket,
            volume=request.volume,
            price=price,
            bid=tick.bid,
            ask=tick.ask,
            comment="Done",
        )

    def _netting_add(
        self,
        existing: PositionRecord,
        request: TradeRequest,
        price: float,
        tick: Tick,
    ) -> TradeResult:
        order_ticket = next(self._order_ids)
        deal_ticket = next(self._deal_ids)
        old_volume = existing.volume
        new_volume = old_volume + request.volume
        existing.price_open = (
            existing.price_open * old_volume + price * request.volume
        ) / new_volume
        existing.volume = new_volume
        existing.price_current = price
        existing.time_update = self._clock
        if request.sl:
            existing.sl = request.sl
        if request.tp:
            existing.tp = request.tp
        commission = request.volume * self._commission_per_lot
        existing.commission += commission
        self._account.balance -= commission

        side = existing.position_type
        self._deals.append(
            DealRecord(
                ticket=deal_ticket,
                order=order_ticket,
                position_id=existing.ticket,
                symbol=existing.symbol,
                deal_type=DealType.BUY if side == PositionType.BUY else DealType.SELL,
                entry=DealEntry.IN,
                volume=request.volume,
                price=price,
                commission=-commission,
                time=self._clock,
                magic=request.magic,
                comment=request.comment,
            )
        )
        self._append_filled_order(request, order_ticket, existing.ticket, price)
        self._mark_to_market()
        return TradeResult(
            retcode=int(TradeRetcode.DONE),
            deal=deal_ticket,
            order=order_ticket,
            volume=request.volume,
            price=price,
            bid=tick.bid,
            ask=tick.ask,
            comment="Done",
        )

    def _netting_offset(
        self,
        existing: PositionRecord,
        request: TradeRequest,
        price: float,
        tick: Tick,
    ) -> TradeResult:
        close_volume = min(existing.volume, request.volume)
        result = self._close_position(
            existing.ticket,
            close_volume,
            comment=request.comment or "netting offset",
        )
        remainder = request.volume - close_volume
        if remainder > 1e-12:
            reverse_request = replace(request, volume=remainder, position=0)
            return self._open_new_position(reverse_request, price, tick)
        return result

    def _close_position(
        self,
        ticket: int,
        volume: float,
        *,
        comment: str,
        close_price: float | None = None,
    ) -> TradeResult:
        position = self._positions.get(ticket)
        if position is None:
            return TradeResult(
                retcode=int(TradeRetcode.POSITION_CLOSED), comment="Position not found"
            )
        if volume <= 0 or volume > position.volume + 1e-12:
            return TradeResult(
                retcode=int(TradeRetcode.INVALID_CLOSE_VOLUME),
                comment="Invalid close volume",
            )
        tick = self._ticks.get(position.symbol)
        if tick is None:
            return TradeResult(
                retcode=int(TradeRetcode.PRICE_OFF), comment="No market price"
            )
        if close_price is None:
            close_price = (
                tick.bid if position.position_type == PositionType.BUY else tick.ask
            )
        original_order_type = (
            OrderType.BUY
            if position.position_type == PositionType.BUY
            else OrderType.SELL
        )
        profit = self.order_calc_profit(
            original_order_type,
            position.symbol,
            volume,
            position.price_open,
            close_price,
        )
        commission = volume * self._commission_per_lot
        allocated_swap = (
            position.swap * (volume / position.volume) if position.volume > 0 else 0.0
        )
        self._account.balance += profit + allocated_swap - commission

        order_ticket = next(self._order_ids)
        deal_ticket = next(self._deal_ids)
        close_order_type = (
            OrderType.SELL
            if position.position_type == PositionType.BUY
            else OrderType.BUY
        )
        close_request = TradeRequest(
            action=TradeAction.DEAL,
            symbol=position.symbol,
            volume=volume,
            order_type=close_order_type,
            magic=position.magic,
            position=position.ticket,
            comment=comment,
        )
        self._append_filled_order(
            close_request, order_ticket, position.ticket, close_price
        )
        self._deals.append(
            DealRecord(
                ticket=deal_ticket,
                order=order_ticket,
                position_id=position.identifier,
                symbol=position.symbol,
                deal_type=DealType.SELL
                if position.position_type == PositionType.BUY
                else DealType.BUY,
                entry=DealEntry.OUT,
                volume=volume,
                price=close_price,
                commission=-commission,
                swap=allocated_swap,
                profit=profit,
                time=self._clock,
                magic=position.magic,
                comment=comment,
            )
        )

        position.volume -= volume
        position.swap -= allocated_swap
        position.time_update = self._clock
        if position.volume <= 1e-12:
            del self._positions[ticket]
        else:
            position.price_current = close_price

        self._symbols[position.symbol].session_deals += 1
        self._mark_to_market()
        return TradeResult(
            retcode=int(TradeRetcode.DONE),
            deal=deal_ticket,
            order=order_ticket,
            volume=volume,
            price=close_price,
            bid=tick.bid,
            ask=tick.ask,
            comment="Done",
        )

    def _close_by(self, ticket: int, ticket_by: int) -> TradeResult:
        p1 = self._positions.get(ticket)
        p2 = self._positions.get(ticket_by)
        if p1 is None or p2 is None:
            return TradeResult(
                retcode=int(TradeRetcode.POSITION_CLOSED), comment="Position not found"
            )
        if p1.symbol != p2.symbol or p1.position_type == p2.position_type:
            return TradeResult(
                retcode=int(TradeRetcode.INVALID_ORDER),
                comment="Close By requires opposite positions on same symbol",
            )
        tick = self._ticks.get(p1.symbol)
        if tick is None:
            return TradeResult(
                retcode=int(TradeRetcode.PRICE_OFF), comment="No market price"
            )
        # Close By is modelled at the midpoint to avoid charging another spread.
        midpoint = (tick.bid + tick.ask) / 2.0
        volume = min(p1.volume, p2.volume)
        first = self._close_position(
            ticket, volume, comment="close by", close_price=midpoint
        )
        second = self._close_position(
            ticket_by, volume, comment="close by", close_price=midpoint
        )
        if second.retcode != int(TradeRetcode.DONE):
            return second
        return first

    def _append_filled_order(
        self,
        request: TradeRequest,
        ticket: int,
        position_id: int,
        price: float,
    ) -> None:
        self._history_orders.append(
            OrderRecord(
                ticket=ticket,
                symbol=request.symbol,
                order_type=request.order_type,
                state=OrderState.FILLED,
                volume_initial=request.volume,
                volume_current=0.0,
                price_open=price,
                sl=request.sl,
                tp=request.tp,
                price_current=price,
                price_stop_limit=request.stoplimit,
                time_setup=self._clock,
                time_done=self._clock,
                time_expiration=request.expiration,
                type_filling=request.type_filling,
                type_time=request.type_time,
                magic=request.magic,
                position_id=position_id,
                comment=request.comment,
            )
        )

    # ------------------------------------------------------------------
    # Tick processing
    # ------------------------------------------------------------------

    def _expire_orders(self) -> None:
        expired = [
            ticket
            for ticket, order in self._orders.items()
            if order.type_time in {OrderTime.SPECIFIED, OrderTime.SPECIFIED_DAY}
            and order.time_expiration is not None
            and self._clock >= order.time_expiration
        ]
        for ticket in expired:
            order = self._orders.pop(ticket)
            order.state = OrderState.EXPIRED
            order.time_done = self._clock
            self._history_orders.append(replace(order))

    def _trigger_pending(self, symbol: str, tick: Tick) -> None:
        for ticket, order in list(self._orders.items()):
            if order.symbol != symbol:
                continue

            triggered = False
            fill_price = order.price_open
            if order.order_type == OrderType.BUY_LIMIT and tick.ask <= order.price_open:
                triggered = True
                fill_price = min(order.price_open, tick.ask)
            elif (
                order.order_type == OrderType.SELL_LIMIT
                and tick.bid >= order.price_open
            ):
                triggered = True
                fill_price = max(order.price_open, tick.bid)
            elif (
                order.order_type == OrderType.BUY_STOP and tick.ask >= order.price_open
            ):
                triggered = True
                fill_price = tick.ask
            elif (
                order.order_type == OrderType.SELL_STOP and tick.bid <= order.price_open
            ):
                triggered = True
                fill_price = tick.bid
            elif (
                order.order_type == OrderType.BUY_STOP_LIMIT
                and tick.ask >= order.price_open
            ):
                order.order_type = OrderType.BUY_LIMIT
                order.price_open = order.price_stop_limit or order.price_open
                order.price_stop_limit = 0.0
                continue
            elif (
                order.order_type == OrderType.SELL_STOP_LIMIT
                and tick.bid <= order.price_open
            ):
                order.order_type = OrderType.SELL_LIMIT
                order.price_open = order.price_stop_limit or order.price_open
                order.price_stop_limit = 0.0
                continue

            if not triggered:
                continue

            del self._orders[ticket]
            order.state = OrderState.FILLED
            order.time_done = self._clock
            order.volume_current = 0.0
            order.price_current = fill_price
            self._history_orders.append(replace(order))

            request = TradeRequest(
                action=TradeAction.DEAL,
                symbol=order.symbol,
                volume=order.volume_initial,
                order_type=OrderType.BUY
                if order.order_type in {OrderType.BUY_LIMIT, OrderType.BUY_STOP}
                else OrderType.SELL,
                price=fill_price,
                sl=order.sl,
                tp=order.tp,
                magic=order.magic,
                type_filling=order.type_filling,
                type_time=order.type_time,
                expiration=order.time_expiration,
                comment=order.comment,
            )
            if self._account.margin_mode == MarginMode.RETAIL_HEDGING:
                self._open_new_position(request, fill_price, tick, order_ticket=ticket)
            else:
                # Netting may generate its own history order; remove the duplicate
                # entry added above only for the common open-new case.
                self._market_open(replace(request, price=fill_price))

    def _trigger_stops(self, symbol: str, tick: Tick) -> None:
        for position in list(self._positions.values()):
            if position.symbol != symbol:
                continue
            reason = ""
            if position.position_type == PositionType.BUY:
                if position.sl > 0 and tick.bid <= position.sl:
                    reason = "stop loss"
                elif position.tp > 0 and tick.bid >= position.tp:
                    reason = "take profit"
            elif position.sl > 0 and tick.ask >= position.sl:
                reason = "stop loss"
            elif position.tp > 0 and tick.ask <= position.tp:
                reason = "take profit"
            if reason:
                self._close_position(position.ticket, position.volume, comment=reason)

    def _mark_to_market(self) -> None:
        floating = 0.0
        margin = 0.0
        for position in self._positions.values():
            tick = self._ticks.get(position.symbol)
            if tick is None:
                continue
            current = (
                tick.bid if position.position_type == PositionType.BUY else tick.ask
            )
            position.price_current = current
            order_type = (
                OrderType.BUY
                if position.position_type == PositionType.BUY
                else OrderType.SELL
            )
            position.profit = self.order_calc_profit(
                order_type,
                position.symbol,
                position.volume,
                position.price_open,
                current,
            )
            floating += position.profit + position.swap
            margin += self.order_calc_margin(
                order_type,
                position.symbol,
                position.volume,
                position.price_open,
            )
        self._account.profit = floating
        self._account.margin = margin
        self._account.equity = self._account.balance + floating + self._account.credit
        self._account.free_margin = self._account.equity - margin
        self._account.margin_level = (
            (self._account.equity / margin) * 100.0 if margin > 0 else 0.0
        )

    async def start(self) -> None:
        """Start the local backend without advancing simulated time."""
        logger.debug("FR-SIMULATION-DISPATCH: starting backend")
        self.connect()

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109 -- backend deadline capability
        """Check readiness without I/O or clock advancement."""
        del timeout
        logger.debug("FR-SIMULATION-DISPATCH: checking readiness")
        if not self._connected:
            raise BridgeError("simulator disconnected", code="NOT_CONNECTED")

    async def close(self) -> None:
        """Disconnect local execution and revoke mutation permission."""
        logger.debug("FR-SIMULATION-DISPATCH: closing backend")
        self.disarm()
        self.disconnect()

    def arm(self) -> None:
        """Permit local simulated mutations; grants no live authority."""
        logger.debug("FR-SIMULATION-DISPATCH: arming local execution")
        if not self._connected:
            raise BridgeError("simulator disconnected", code="NOT_CONNECTED")
        self._armed = True

    def disarm(self) -> None:
        """Revoke local mutation permission."""
        logger.debug("FR-SIMULATION-DISPATCH: disarming local execution")
        self._armed = False

    def last_command_id(self) -> str | None:
        """Return the current async task's last simulated command ID."""
        return self._last_command.get()

    def receipt(self, command_id: str) -> Receipt | None:
        """Read an immutable in-memory command receipt."""
        return self._receipts.get(command_id)

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109 -- backend deadline capability
        """Wait for locally emitted transaction events."""
        async with asyncio.timeout(timeout):
            return await self._event_queue.get()

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> BridgeEvent:
        """Reject unsupported native-request correlation explicitly."""
        del request_id, timeout
        raise BridgeError(
            "simulator has no native request event correlation",
            code="UNSUPPORTED_OPERATION",
        )

    def seed_bar_history(
        self,
        symbol: str,
        timeframe: Timeframe,
        bars: Sequence[MarketBar],
    ) -> None:
        """Register an immutable chronological bar series without advancing time."""
        from app.services.libs.data import TIMEFRAME_SECONDS, validate_rows

        logger.debug("FR-SIMULATION-HISTORY: seeding bars")
        if symbol not in self._symbols or timeframe not in TIMEFRAME_SECONDS:
            raise BridgeError("invalid history series", code="BAD_REQUEST")
        rows = [asdict(bar) for bar in bars]
        validate_rows(rows, "bars", 0, 2**63 - 1, len(rows))
        self._bar_history[symbol, timeframe] = tuple(bars)

    def seed_tick_history(self, symbol: str, ticks: Sequence[MarketTick]) -> None:
        """Register immutable chronological ticks without replacing the live quote."""
        from app.services.libs.data import validate_rows

        logger.debug("FR-SIMULATION-HISTORY: seeding ticks")
        if symbol not in self._symbols:
            raise BridgeError("invalid history series", code="BAD_REQUEST")
        rows = [asdict(tick) for tick in ticks]
        validate_rows(rows, "ticks", 0, 2**63 - 1, len(rows))
        self._tick_history[symbol] = tuple(ticks)

    def _market_data(self, method: str, args: list[Any]) -> list[dict[str, Any]]:
        from app.services.libs.data import MAX_POSITION, validate_request

        logger.debug("FR-SIMULATION-HISTORY: reading seeded history")
        bars = method == "Bars"
        if bars:
            symbol, frame, mode, start, end, count, limit = args
            try:
                timeframe = Timeframe(frame)
            except ValueError as exc:
                raise BridgeError(
                    "unsupported timeframe", code="UNSUPPORTED_TIMEFRAME"
                ) from exc
            validate_request(
                symbol,
                start if mode != "position" else 0,
                end if mode == "range" else (start if mode == "date_count" else 0),
                limit,
                timeframe,
            )
            if (symbol, timeframe) not in self._bar_history:
                raise BridgeError("history is not seeded", code="DATA_NOT_READY")
            records = [
                asdict(row)
                for row in self._bar_history[symbol, timeframe]
                if row.time <= int(self._clock.timestamp())
            ]
        else:
            symbol, mode, start, end, count, limit = args
            validate_request(
                symbol,
                1 if mode == "latest" else start,
                end if mode == "range" else (start if mode == "date_count" else 1),
                limit,
            )
            if symbol not in self._tick_history:
                raise BridgeError("history is not seeded", code="DATA_NOT_READY")
            records = [
                asdict(row)
                for row in self._tick_history[symbol]
                if row.time_msc <= int(self._clock.timestamp() * 1000)
            ]
        if (
            mode
            not in (
                {"range", "date_count", "position"}
                if bars
                else {"range", "date_count", "latest"}
            )
            or type(count) is not int
            or type(start) is not int
            or start < 0
            or (mode == "latest" and start != 0)
            or (mode == "position" and start > MAX_POSITION)
            or (mode == "range" and count != 0)
            or (mode != "range" and not 1 <= count <= limit)
        ):
            raise BridgeError("invalid history route", code="BAD_REQUEST")
        key = "time" if bars else "time_msc"
        if mode == "range":
            selected = [row for row in records if start <= row[key] <= end]
        elif mode == "date_count":
            selected = [row for row in records if row[key] >= start][:count]
        elif mode == "position":
            stop = max(0, len(records) - start)
            selected = records[max(0, stop - count) : stop]
        else:
            selected = records[-count:]
        if len(selected) > limit:
            raise BridgeError("narrow the date range", code="DATA_LIMIT_EXCEEDED")
        return selected

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
        """Execute a bounded native-style operation against local model state."""
        logger.debug(
            "FR-SIMULATION-DISPATCH: dispatching",
            extra={"class_name": class_name, "method_name": method_name},
        )
        if timeout is not None and timeout <= 0:
            raise BridgeError(
                "simulation command deadline expired", code="COMMAND_TIMEOUT"
            )
        if not self._connected:
            raise BridgeError("simulator disconnected", code="NOT_CONNECTED")
        market_data = class_name == "MarketData" and method_name in {"Bars", "Ticks"}
        if not market_data and (
            class_name not in HANDLERS or method_name not in HANDLERS[class_name]
        ):
            raise BridgeError(
                "unsupported simulated operation", code="UNSUPPORTED_OPERATION"
            )
        mutation = class_name == "Trade" and method_name in {
            "OrderSend",
            "Buy",
            "Sell",
            "BuyLimit",
            "BuyStop",
            "SellLimit",
            "SellStop",
            "OrderOpen",
            "OrderModify",
            "OrderDelete",
            "PositionOpen",
            "PositionModify",
            "PositionClose",
            "PositionClosePartial",
            "PositionCloseBy",
        }
        if (requires_arm or mutation) and not self._armed:
            raise BridgeError("simulation backend is disarmed", code="DISARMED")
        existing = self._objects.get(object_id)
        if existing is not None and existing[0] != class_name:
            raise BridgeError("object class mismatch", code="INVALID_OBJECT")
        state = (
            existing[1]
            if existing is not None
            else new_state("SymbolInfo" if market_data else class_name, self)
        )
        self._objects[object_id] = (class_name, state)
        if not market_data:
            args = prepare_args(state, self, class_name, method_name, args)
        command_id = uuid.uuid4().hex
        self._last_command.set(command_id)
        now = self._clock.timestamp()
        receipt = Receipt(
            command_id=command_id,
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            status=ReceiptStatus.CREATED,
            created_at=now,
        )
        self._receipts[command_id] = receipt
        try:
            value = (
                self._market_data(method_name, args)
                if market_data
                else execute(state, class_name, method_name, args)
            )
        except (ValueError, TypeError, RuntimeError, KeyError) as exc:
            self._receipts[command_id] = replace(
                receipt,
                status=ReceiptStatus.REJECTED,
                resolved_at=now,
                error={"code": "SIMULATION_OPERATION_FAILED"},
            )
            if isinstance(exc, BridgeError):
                raise
            raise BridgeError(
                "simulation operation failed",
                code="SIMULATION_OPERATION_FAILED",
                command_id=command_id,
            ) from exc
        value = _normalize_result(value, class_name, method_name, args)
        self._receipts[command_id] = replace(
            receipt,
            status=ReceiptStatus.RESOLVED,
            sent_at=now,
            acknowledged_at=now,
            resolved_at=now,
            value=value,
        )
        is_success = value is True or (
            isinstance(value, dict) and value.get("retcode") in {10008, 10009}
        )
        if mutation and is_success:
            await self._event_queue.put(
                BridgeEvent(
                    event_type="simulation_transaction",
                    payload={"method": method_name},
                    command_id=command_id,
                )
            )
        return value


def _normalize_result(
    value: Any, class_name: str, method_name: str, args: list[Any]
) -> Any:
    """Adapt local model output to the native public result contract."""
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
        value.pop("raw", None)
        if method_name == "Request":
            value["type"] = value.pop("order_type")
            expiration = value.get("expiration")
            value["expiration"] = (
                int(expiration.timestamp()) if isinstance(expiration, datetime) else 0
            )
    if (
        class_name == "Trade"
        and (
            method_name.startswith("Set")
            or method_name in {"LogLevel", "PrintRequest", "PrintResult"}
        )
        and value is None
    ):
        value = True
    if method_name == "StoreState":
        value = True
    if class_name == "SymbolInfo" and method_name == "Name" and args:
        value = value is not False
    if (
        class_name in {"HistoryOrderInfo", "DealInfo"}
        and method_name == "Ticket"
        and args
    ):
        value = True
    # Generic selected-object properties have the same envelope as native MT5.
    if class_name in {
        "SymbolInfo",
        "OrderInfo",
        "HistoryOrderInfo",
        "PositionInfo",
        "DealInfo",
    } and method_name in {"InfoInteger", "InfoDouble", "InfoString"}:
        value = {"ok": True, "value": value}
    return _wire_result(value)


def _wire_result(value: Any) -> Any:
    """Normalize local enums and compound values to native wire result types."""
    if isinstance(value, IntEnum):
        return int(value)
    if isinstance(value, dict):
        return {key: _wire_result(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_wire_result(item) for item in value]
    return value
