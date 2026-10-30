"""Deterministic trading simulator with explicitly seeded historical data.

Description:
    Owns in-memory orders, fills, positions, deals, margin and account state.
    External tick feeding advances model time; historical read requests only
    filter immutable seeded records and use the async command/receipt lifecycle.
Purpose:
    FEAT-BROKER-SIMULATION: Local broker semantics for strategy verification.
Key Capabilities:
    - FR-SIMULATION-DISPATCH: Local dispatch with receipts [`SimulatorClient.call()`] (`DEBUG`).
    - FR-SIMULATION-HISTORY: Seed and query bars/ticks [`SimulatorClient.get_bars()`] (`DEBUG`).
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import UTC, datetime
from itertools import count
from typing import Any, TypeVar, override

import pandas as pd  # type: ignore[import-untyped]

from app.core.data.contracts import (
    TIMEFRAME_SECONDS,
    AccountInfo,
    BookInfo,
    BridgeError,
    BridgeEvent,
    DealInfo,
    MarketBar,
    MarketTick,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.core.enums import (
    BookType,
    DealEntry,
    DealType,
    MarginMode,
    OrderFilling,
    OrderState,
    OrderTime,
    OrderType,
    PositionType,
    SymbolTradeMode,
    Timeframe,
    TradeAction,
    TradeRetcode,
)
from app.core.host.logging import get_logger
from app.core.trading.connection.base import TradingClient, epoch_seconds, utc_now
from app.core.trading.simulation.validation import (
    label as _label,
)
from app.core.trading.simulation.validation import (
    make_trade_result as _res,
)
from app.core.trading.simulation.validation import (
    pending_price_valid,
    stops_valid,
    volume_valid,
)
from app.workspace.data_manager.data.conversions import (
    bars_to_dataframe,
    ticks_to_dataframe,
)
from app.workspace.data_manager.data.history import validate_rows
from app.workspace.trading import Trading

logger = get_logger(__name__)
_T = TypeVar("_T", MarketBar, MarketTick)

_A, _R, _OT, _OS = TradeAction, TradeRetcode, OrderType, OrderState
_OF, _OTM, _PT = OrderFilling, OrderTime, PositionType
_DT, _DE = DealType, DealEntry
_STM = SymbolTradeMode
_BUY_TYPES = {_OT.BUY, _OT.BUY_LIMIT, _OT.BUY_STOP, _OT.BUY_STOP_LIMIT}
_SELL_TYPES = {_OT.SELL, _OT.SELL_LIMIT, _OT.SELL_STOP, _OT.SELL_STOP_LIMIT}
_PENDING_BUY_TYPES = {_OT.BUY_LIMIT, _OT.BUY_STOP, _OT.BUY_STOP_LIMIT}


class SimulatorClient(TradingClient):
    """Deterministic in-memory broker simulator with MQL5-oriented execution semantics."""

    def __init__(self, *, name: str = "Simulator", **kwargs: Any) -> None:
        super().__init__(name=name)
        b: Any = kwargs.get("backend")
        g = kwargs.get
        bal = float(b._initial_balance if b else g("initial_balance", 10_000.0))
        lev = int(b._leverage if b else max(1, int(g("leverage", 100))))
        mm: MarginMode = (
            b._margin_mode if b else g("margin_mode", MarginMode.RETAIL_HEDGING)
        )
        cur = str(b._currency if b else g("currency", "USD")).upper()
        comm = float(b._commission_per_lot if b else g("commission_per_lot", 0.0))
        self._initial_balance, self._leverage, self._margin_mode = bal, lev, mm
        self._currency, self._commission_per_lot = cur, comm
        self._armed, self._connected, self._clock = False, True, utc_now()
        self._event_queue: asyncio.Queue[BridgeEvent] = asyncio.Queue()
        self._symbols: dict[str, SymbolInfo] = {}
        self._ticks: dict[str, MarketTick] = {}
        self._bar_history: dict[tuple[str, Timeframe], tuple[MarketBar, ...]] = {}
        self._tick_history: dict[str, tuple[MarketTick, ...]] = {}
        self._orders: dict[int, OrderInfo] = {}
        self._history_orders: list[OrderInfo] = []
        self._positions: dict[int, PositionInfo] = {}
        self._deals: list[DealInfo] = []
        self._order_ids, self._deal_ids = count(1), count(1_000_001)
        self._position_ids = count(10_000_001)
        self._stats: dict[str, dict[str, float]] = {}
        acc = AccountInfo(leverage=lev, margin_mode=mm, currency=cur)
        acc.balance = acc.equity = acc.free_margin = bal
        self._account = acc
        self._terminal = TerminalInfo(
            connected=True, trade_allowed=True, cpu_cores=os.cpu_count() or 1
        )
        t = Trading(self)
        self.trading = t
        self.account_proxy, self.terminal_proxy = t.account, t.terminal
        self.symbol_proxy, self.trade_proxy = t.symbol, t.trade
        self.position_proxy, self.order_proxy = t.position, t.order
        self.history_order_proxy, self.deal_proxy = t.history_order, t.deal

    def _clock_stamp(self) -> tuple[int, int]:
        ts = self._clock.timestamp()
        return int(ts), int(ts * 1000)

    def add_symbol(self, spec: SymbolInfo) -> None:
        """Register a symbol specification with the simulator."""
        self._symbols[spec.name] = deepcopy(spec)
        self._stats.setdefault(spec.name, {})

    def feed_tick(
        self, symbol: str, *, bid: float, ask: float, **kw: Any
    ) -> MarketTick:
        """Advance simulator time and update pricing with a new tick."""
        if symbol not in self._symbols:
            raise KeyError(f"Symbol {symbol!r} has not been registered")
        if ask < bid:
            raise ValueError("ask must be >= bid")
        now: datetime = kw.get("time") or self._clock
        self._clock = now.replace(tzinfo=UTC) if now.tzinfo is None else now
        last_in, vol = kw.get("last"), float(kw.get("volume", 0.0))
        last_p = float(last_in if last_in is not None else (bid + ask) / 2.0)
        ms = int(self._clock.timestamp() * 1000)
        tick = MarketTick(ms, float(bid), float(ask), last_p, int(vol), 0, vol)
        self._ticks[symbol] = tick
        stats = self._stats.setdefault(symbol, {})
        for k, v in (("bid", bid), ("ask", ask), ("last", last_p), ("volume", vol)):
            hk, lk = f"{k}_high", f"{k}_low"
            stats[hk] = max(float(v), stats.get(hk, float(v)))
            stats[lk] = min(float(v), stats.get(lk, float(v)))
        stats.setdefault("session_open", tick.last)
        stats["session_close"] = tick.last
        self._expire_orders()
        self._trigger_pending(symbol, tick)
        self._trigger_stops(symbol, tick)
        self._mark_to_market()
        return tick

    def set_clock(self, now: datetime) -> None:
        """Advance simulated engine clock and process order expirations."""
        self._clock = now.replace(tzinfo=UTC) if now.tzinfo is None else now
        self._expire_orders()
        self._mark_to_market()

    @override
    def connect(self) -> bool:
        self._connected = self._terminal.connected = True
        return True

    @override
    def disconnect(self) -> None:
        self._connected = self._terminal.connected = False

    def terminal(self) -> TerminalInfo:
        """Return simulated terminal snapshot."""
        return replace(self._terminal)

    def account(self) -> AccountInfo:
        """Return simulated account snapshot."""
        self._mark_to_market()
        return replace(self._account)

    def symbol(self, name: str) -> SymbolInfo | None:
        """Return simulated symbol specifications."""
        spec, t = self._symbols.get(name), self._ticks.get(name)
        if spec is None:
            return None
        snapshot = deepcopy(spec)
        if t:
            snapshot.price.bid, snapshot.price.ask = t.bid, t.ask
        return snapshot

    def symbols(self) -> list[SymbolInfo]:
        """Return all simulated symbol specifications."""
        return [s for name in self._symbols if (s := self.symbol(name)) is not None]

    @override
    def select_symbol(self, name: str, selected: bool) -> bool:
        spec = self._symbols.get(name)
        if spec is None:
            return False
        spec.state.selected = selected
        return True

    def tick(self, name: str) -> MarketTick | None:
        """Return latest cached market tick for symbol."""
        val = self._ticks.get(name)
        return replace(val) if val is not None else None

    def orders(self) -> list[OrderInfo]:
        """Return active simulated orders."""
        return [replace(v) for _, v in sorted(self._orders.items())]

    def history_orders(self) -> list[OrderInfo]:
        """Return historical executed/cancelled orders."""
        return [replace(v) for v in self._history_orders]

    def positions(self) -> list[PositionInfo]:
        """Return open positions after mark-to-market revaluation."""
        self._mark_to_market()
        return [replace(v) for _, v in sorted(self._positions.items())]

    def deals(self) -> list[DealInfo]:
        """Return executed historical deals."""
        return [replace(v) for v in self._deals]

    @override
    def get_terminal_info(self) -> TerminalInfo:
        return self.terminal()

    @override
    def get_account_info(self) -> AccountInfo:
        return self.account()

    @override
    def get_symbol_info(self, symbol: str) -> SymbolInfo | None:
        return self.symbol(symbol)

    @override
    def get_symbols(self) -> list[str]:
        return [s.name for s in self.symbols()]

    @override
    def get_positions(self) -> list[PositionInfo]:
        return self.positions()

    @override
    def get_orders(self) -> list[OrderInfo]:
        return self.orders()

    @override
    def get_history_orders(self) -> list[OrderInfo]:
        return self.history_orders()

    @override
    def get_deals(self) -> list[DealInfo]:
        return self.deals()

    @override
    def get_tick(self, name: str) -> MarketTick | None:
        return self.tick(name)

    @override
    def subscribe_book(self, name: str) -> bool:
        del name
        return True

    @override
    def get_book(self, name: str) -> tuple[BookInfo, ...]:
        t = self.get_tick(name)
        if t is None:
            return ()
        b_sell = BookInfo(BookType.BOOK_TYPE_SELL, t.ask, 10, 10.0)
        b_buy = BookInfo(BookType.BOOK_TYPE_BUY, t.bid, 10, 10.0)
        return (b_sell, b_buy)

    @override
    def order_check(self, request: TradeRequest) -> TradeCheckResult:
        self._mark_to_market()
        ret, comment = self._validate_request(request)
        margin, acc = 0.0, self._account
        is_open = request.action in {_A.DEAL, _A.PENDING}
        if ret == _R.DONE and is_open and request.symbol and request.volume > 0:
            p, t = request.price, self._ticks.get(request.symbol)
            if p <= 0 and t is not None:
                p = t.ask if request.order_type in _BUY_TYPES else t.bid
            margin = self.order_calc_margin(
                request.order_type, request.symbol, request.volume, p
            )
            if margin > acc.free_margin:
                ret, comment = _R.NO_MONEY, "Not enough money"
        res = TradeCheckResult(retcode=int(ret), margin=margin, comment=comment)
        res.balance, res.equity, res.profit = acc.balance, acc.equity, acc.profit
        res.margin_free, res.margin_level = (
            max(0.0, acc.free_margin - margin),
            acc.margin_level,
        )
        return res

    @override
    def order_send(self, request: TradeRequest) -> TradeResult:
        check = self.order_check(request)
        if check.retcode != int(_R.DONE):
            return _res(check.retcode, check.comment)
        act = request.action
        if act == _A.DEAL:
            if request.position:
                c = request.comment or "close"
                return self._close_position(request.position, request.volume, comment=c)
            return self._market_open(request)
        if act == _A.PENDING:
            return self._place_pending(request)
        if act == _A.REMOVE:
            return self._remove_order(request.order)
        if act == _A.MODIFY:
            return self._modify_order(request)
        if act == _A.SLTP:
            return self._modify_position(request)
        if act == _A.CLOSE_BY:
            return self._close_by(request.position, request.position_by)
        return _res(_R.INVALID, f"Unsupported action {act}")  # type: ignore[unreachable]

    def order_calc_profit(
        self, ot: OrderType, sym: str, vol: float, p_open: float, p_close: float
    ) -> float:
        """Calculate projected trade profit for given order parameters."""
        spec = self._symbols.get(sym)
        if spec is None:
            return 0.0
        dp = (float(p_close) - float(p_open)) * (1.0 if ot == _OT.BUY else -1.0)
        return dp * float(vol) * spec.price.contract_size

    def order_calc_margin(
        self, ot: OrderType, sym: str, vol: float, price: float
    ) -> float:
        """Calculate required margin for given order parameters."""
        del ot
        spec = self._symbols.get(sym)
        if spec is None or vol <= 0:
            return 0.0
        if spec.margin.initial > 0:
            return spec.margin.initial * vol
        lev = max(1, self._account.leverage)
        return spec.price.contract_size * vol * max(price, spec.price.tick_size) / lev

    def info_value(
        self, scope: str, prop_id: int | str, selector: str | int | None = None
    ) -> Any:
        """Retrieve property value from account, terminal, or symbol scope."""
        if not isinstance(prop_id, str):
            return None
        key = prop_id.strip().lower()
        if scope == "account":
            return asdict(self._account).get(key)
        if scope == "terminal":
            return asdict(self._terminal).get(key)
        if scope == "symbol" and isinstance(selector, str):
            if key in self._stats.get(selector, {}):
                return self._stats[selector][key]
            spec = self._symbols.get(selector)
            return asdict(spec).get(key) if spec is not None else None
        pools: dict[str, Sequence[Any]] = {
            "order": tuple(self._orders.values()),
            "history_order": self._history_orders,
            "position": tuple(self._positions.values()),
            "deal": self._deals,
        }
        for val in pools.get(scope, ()):
            if selector in {getattr(val, "ticket", None), getattr(val, "symbol", None)}:
                return asdict(val).get(key)
        return None

    def _validate_request(self, req: TradeRequest) -> tuple[TradeRetcode, str]:
        if not self._connected:
            return _R.CONNECTION, "No connection"
        if not self._terminal.trade_allowed or not self._account.trade_allowed:
            return _R.TRADE_DISABLED, "Trading is disabled"
        act = req.action
        if act == _A.REMOVE:
            if req.order not in self._orders:
                return _R.INVALID_ORDER, "Order not found"
            return _R.DONE, "Done"
        if act == _A.MODIFY:
            o = self._orders.get(req.order)
            spec = self._symbols.get(o.symbol) if o else None
            if o is None or spec is None:
                return (
                    _R.INVALID_ORDER,
                    "Order not found" if not o else "Unknown symbol",
                )
            cand = replace(req, symbol=o.symbol, volume=o.volume_current)
            cand.order_type, cand.price = _OT(o.order_type), req.price or o.price_open
            cand.stoplimit = req.stoplimit or o.price_stop_limit
            if not self._pending_price_valid(cand, spec):
                return _R.INVALID_PRICE, "Invalid pending order price"
            if not self._stops_valid(cand, spec):
                return _R.INVALID_STOPS, "Invalid stops"
            return _R.DONE, "Done"
        if act == _A.SLTP:
            pos = self._positions.get(req.position)
            if pos is None:
                return _R.POSITION_CLOSED, "Position not found"
            spec, tick = self._symbols.get(pos.symbol), self._ticks.get(pos.symbol)
            if spec is not None and tick is not None:
                m, is_b = (
                    spec.trade.stops_level * spec.price.tick_size,
                    pos.position_type == int(_PT.BUY),
                )
                ref = tick.bid if is_b else tick.ask
                if req.sl and ((ref - req.sl) if is_b else (req.sl - ref)) < m - 1e-12:
                    return _R.INVALID_STOPS, "Invalid stop loss"
                if req.tp and ((req.tp - ref) if is_b else (ref - req.tp)) < m - 1e-12:
                    return _R.INVALID_STOPS, "Invalid take profit"
            return _R.DONE, "Done"
        if act == _A.CLOSE_BY:
            p1, p2 = (
                self._positions.get(req.position),
                self._positions.get(req.position_by),
            )
            if p1 is None or p2 is None:
                return _R.POSITION_CLOSED, "Position not found"
            if p1.symbol != p2.symbol or p1.position_type == p2.position_type:
                return (
                    _R.INVALID_ORDER,
                    "Close By requires opposite positions on same symbol",
                )
            return _R.DONE, "Done"
        if act == _A.DEAL and req.position:
            pos = self._positions.get(req.position)
            if pos is None:
                return _R.POSITION_CLOSED, "Position not found"
            if req.volume <= 0 or req.volume > pos.volume + 1e-12:
                return _R.INVALID_CLOSE_VOLUME, "Invalid close volume"
            return _R.DONE, "Done"
        spec = self._symbols.get(req.symbol)
        if spec is None:
            return _R.INVALID_ORDER, "Unknown symbol"
        tm = {
            "Disabled": _STM.DISABLED,
            "Long only": _STM.LONGONLY,
            "Short only": _STM.SHORTONLY,
            "Close only": _STM.CLOSEONLY,
            "Full access": _STM.FULL,
        }[spec.trade.mode]
        ot = req.order_type
        tf, filling = req.type_filling, spec.trade.filling
        if tm == _STM.DISABLED:
            return _R.TRADE_DISABLED, "Symbol trading is disabled"
        if tm == _STM.CLOSEONLY and not req.position:
            return _R.CLOSE_ONLY, "Symbol is close-only"
        if tm == _STM.LONGONLY and ot in _SELL_TYPES:
            return _R.LONG_ONLY, "Only long positions are allowed"
        if tm == _STM.SHORTONLY and ot in _BUY_TYPES:
            return _R.SHORT_ONLY, "Only short positions are allowed"
        if req.volume <= 0 or not self._volume_valid(spec, req.volume):
            return _R.INVALID_VOLUME, "Invalid volume"
        if act == _A.DEAL and spec.trade.execution == "Market":
            if tf == _OF.FOK and "Fill or Kill" not in filling:
                return _R.INVALID_FILL, "FOK filling is not supported"
            if tf == _OF.IOC and "Immediate or Cancel" not in filling:
                return _R.INVALID_FILL, "IOC filling is not supported"
            if tf == _OF.RETURN:
                return _R.INVALID_FILL, "RETURN is not valid for Market Execution"
        if act == _A.DEAL and req.symbol not in self._ticks:
            return _R.PRICE_OFF, "No market price"
        if act == _A.PENDING:
            if req.price <= 0:
                return _R.INVALID_PRICE, "Pending order requires a positive price"
            if req.symbol not in self._ticks:
                return _R.PRICE_OFF, "No market price"
            if 0 < self._account.limit_orders <= len(self._orders):
                return _R.LIMIT_ORDERS, "Pending-order limit reached"
            exp_bad = req.expiration is None or req.expiration <= self._clock
            if req.type_time in {_OTM.SPECIFIED, _OTM.SPECIFIED_DAY} and exp_bad:
                return _R.INVALID_EXPIRATION, "Invalid expiration"
            if not self._pending_price_valid(req, spec):
                return _R.INVALID_PRICE, "Invalid pending order price"
        if not self._stops_valid(req, spec):
            return _R.INVALID_STOPS, "Invalid stops"
        if spec.volume.limit > 0:
            s, sym, b_pt = ot in _BUY_TYPES, req.symbol, int(_PT.BUY)
            ps = (p for p in self._positions.values() if p.symbol == sym)
            os_ = (o for o in self._orders.values() if o.symbol == sym)
            pv = sum(p.volume for p in ps if (p.position_type == b_pt) == s)
            ov = sum(o.volume_current for o in os_ if (o.order_type in _BUY_TYPES) == s)
            if pv + ov + req.volume > spec.volume.limit + 1e-12:
                return _R.LIMIT_VOLUME, "Symbol volume limit reached"
        return _R.DONE, "Done"

    def _pending_price_valid(self, req: TradeRequest, spec: SymbolInfo) -> bool:
        return pending_price_valid(req, spec, self._ticks.get(req.symbol))

    @staticmethod
    def _volume_valid(spec: SymbolInfo, volume: float) -> bool:
        return volume_valid(spec, volume)

    def _stops_valid(self, req: TradeRequest, spec: SymbolInfo) -> bool:
        return stops_valid(req, spec, self._ticks.get(req.symbol))

    def _build_order(
        self, req: TradeRequest, ticket: int, state: OrderState, **kw: Any
    ) -> OrderInfo:
        now_sec, now_msc = self._clock_stamp()
        o = OrderInfo(
            ticket=ticket, symbol=req.symbol, magic=req.magic, comment=req.comment
        )
        o.order_type, o.type_description = int(req.order_type), _label(req.order_type)
        o.state, o.state_description = int(state), _label(state)
        o.volume_initial, o.volume_current = req.volume, kw.get("vol_cur", 0.0)
        o.price_open, o.price_current = kw["p_open"], kw["p_cur"]
        o.sl, o.tp, o.price_stop_limit = req.sl, req.tp, req.stoplimit
        o.time_setup, o.time_setup_msc = now_sec, now_msc
        if kw.get("done"):
            o.time_done, o.time_done_msc = now_sec, now_msc
        o.time_expiration = epoch_seconds(req.expiration)
        o.type_filling = int(req.type_filling)
        o.type_filling_description = _label(req.type_filling)
        o.type_time, o.type_time_description = int(req.type_time), _label(req.type_time)
        o.position_id = kw.get("pos_id", 0)
        return o

    def _record_deal(
        self, pos: PositionInfo, order: int, entry: DealEntry, **kw: Any
    ) -> DealInfo:
        deal_ticket = next(self._deal_ids)
        now_sec, now_msc = self._clock_stamp()
        is_b = (pos.position_type == int(_PT.BUY)) == (entry == _DE.IN)
        dtype = _DT.BUY if is_b else _DT.SELL
        pos_id = pos.ticket if entry == _DE.IN else pos.identifier
        d = DealInfo(ticket=deal_ticket, order=order, position_id=pos_id)
        d.symbol = pos.symbol
        d.deal_type, d.type_description = int(dtype), _label(dtype)
        d.entry, d.entry_description = int(entry), _label(entry)
        d.volume, d.price = kw["vol"], kw["price"]
        d.commission = -float(kw["comm"])
        d.time, d.time_msc = now_sec, now_msc
        d.magic, d.comment = pos.magic, pos.comment
        self._deals.append(d)
        return d

    @staticmethod
    def _done(
        deal: int, order: int, vol: float, price: float, t: MarketTick
    ) -> TradeResult:
        r = _res(_R.DONE, "Done", deal=deal, order=order, volume=vol, price=price)
        r.bid, r.ask = t.bid, t.ask
        return r

    def _place_pending(self, req: TradeRequest) -> TradeResult:
        ticket, tick = next(self._order_ids), self._ticks.get(req.symbol)
        is_b = req.order_type in _PENDING_BUY_TYPES
        cur = (tick.ask if is_b else tick.bid) if tick else 0.0
        self._orders[ticket] = self._build_order(
            req, ticket, _OS.PLACED, vol_cur=req.volume, p_open=req.price, p_cur=cur
        )
        stats = self._stats.setdefault(req.symbol, {})
        side = "buy" if is_b else "sell"
        key = f"session_{side}_orders"
        stats[key] = stats.get(key, 0) + 1
        stats[key + "_volume"] = stats.get(key + "_volume", 0) + req.volume
        r = _res(
            _R.PLACED, "Order placed", order=ticket, volume=req.volume, price=req.price
        )
        if tick:
            r.bid, r.ask = tick.bid, tick.ask
        return r

    def _remove_order(self, ticket: int) -> TradeResult:
        order = self._orders.pop(ticket, None)
        if order is None:
            return _res(_R.INVALID_ORDER, "Order not found")
        order.state, order.state_description = int(_OS.CANCELED), _label(_OS.CANCELED)
        order.time_done, order.time_done_msc = self._clock_stamp()
        self._history_orders.append(replace(order))
        return _res(_R.DONE, "Order canceled", order=ticket)

    def _modify_order(self, request: TradeRequest) -> TradeResult:
        order = self._orders.get(request.order)
        if order is None:
            return _res(_R.INVALID_ORDER, "Order not found")
        changed, tt = False, request.type_time
        u: list[tuple[str, Any]] = [
            ("price_open", request.price),
            ("sl", request.sl),
            ("tp", request.tp),
            ("price_stop_limit", request.stoplimit),
            ("type_time", int(tt)),
            ("type_time_description", _label(tt)),
        ]
        if request.expiration is not None:
            u.append(("time_expiration", epoch_seconds(request.expiration)))
        for name, value in u:
            if value is not None and getattr(order, name) != value:
                setattr(order, name, value)
                changed = True
        if not changed:
            return _res(_R.NO_CHANGES, "No changes", order=order.ticket)
        return _res(_R.DONE, "Order modified", order=order.ticket)

    def _modify_position(self, request: TradeRequest) -> TradeResult:
        position = self._positions.get(request.position)
        if position is None:
            return _res(_R.POSITION_CLOSED, "Position not found")
        if position.sl == request.sl and position.tp == request.tp:
            return _res(_R.NO_CHANGES, "No changes", order=position.ticket)
        position.sl, position.tp = request.sl, request.tp
        position.time_update, position.time_update_msc = self._clock_stamp()
        return _res(_R.DONE, "Position modified", order=position.ticket)

    def _market_open(self, request: TradeRequest) -> TradeResult:
        tick = self._ticks[request.symbol]
        price = tick.ask if request.order_type == _OT.BUY else tick.bid
        if self._account.margin_mode != MarginMode.RETAIL_HEDGING:
            ps = (p for p in self._positions.values() if p.symbol == request.symbol)
            existing = next(ps, None)
            if existing is not None:
                req_side = _PT.BUY if request.order_type == _OT.BUY else _PT.SELL
                if existing.position_type == int(req_side):
                    return self._netting_add(existing, request, price)
                return self._netting_offset(existing, request, price)
        return self._open_new_position(request, price)

    def _open_new_position(
        self, req: TradeRequest, price: float, ot: int = 0
    ) -> TradeResult:
        tick, order_ticket = self._ticks[req.symbol], ot or next(self._order_ids)
        pos_ticket = next(self._position_ids)
        side = _PT.BUY if req.order_type == _OT.BUY else _PT.SELL
        comm = abs(req.volume) * self._commission_per_lot
        now_sec, now_msc = self._clock_stamp()
        pos = PositionInfo(ticket=pos_ticket, identifier=pos_ticket, symbol=req.symbol)
        pos.position_type, pos.type_description = int(side), _label(side)
        pos.volume, pos.price_open, pos.price_current = req.volume, price, price
        pos.sl, pos.tp, pos.commission = req.sl, req.tp, -comm
        pos.time = pos.time_update = now_sec
        pos.time_msc = pos.time_update_msc = now_msc
        pos.magic, pos.comment = req.magic, req.comment
        self._positions[pos_ticket] = pos
        self._account.balance -= comm
        deal = self._record_deal(
            pos, order_ticket, _DE.IN, vol=req.volume, price=price, comm=comm
        )
        self._append_filled(req, order_ticket, pos_ticket, price)
        spec = self._symbols[req.symbol]
        stats = self._stats.setdefault(req.symbol, {})
        stats["session_deals"] = stats.get("session_deals", 0) + 1
        stats["session_turnover"] = stats.get("session_turnover", 0) + abs(
            price * req.volume * spec.price.contract_size
        )
        self._mark_to_market()
        return self._done(deal.ticket, order_ticket, req.volume, price, tick)

    def _netting_add(
        self, existing: PositionInfo, req: TradeRequest, price: float
    ) -> TradeResult:
        tick, order_ticket = self._ticks[req.symbol], next(self._order_ids)
        old_v, new_v = existing.volume, existing.volume + req.volume
        existing.price_open = (existing.price_open * old_v + price * req.volume) / new_v
        existing.volume, existing.price_current = new_v, price
        existing.time_update, existing.time_update_msc = self._clock_stamp()
        if req.sl:
            existing.sl = req.sl
        if req.tp:
            existing.tp = req.tp
        comm = req.volume * self._commission_per_lot
        existing.commission -= comm
        self._account.balance -= comm
        deal = self._record_deal(
            existing, order_ticket, _DE.IN, vol=req.volume, price=price, comm=comm
        )
        deal.magic, deal.comment = req.magic, req.comment
        self._append_filled(req, order_ticket, existing.ticket, price)
        self._mark_to_market()
        return self._done(deal.ticket, order_ticket, req.volume, price, tick)

    def _netting_offset(
        self, existing: PositionInfo, req: TradeRequest, price: float
    ) -> TradeResult:
        close_vol, c = min(existing.volume, req.volume), req.comment or "netting offset"
        res = self._close_position(existing.ticket, close_vol, comment=c)
        rem = req.volume - close_vol
        if rem > 1e-12:
            return self._open_new_position(replace(req, volume=rem, position=0), price)
        return res

    def _close_position(self, ticket: int, volume: float, **kw: Any) -> TradeResult:
        comment, cp_in = kw.get("comment", "close"), kw.get("close_price")
        pos = self._positions.get(ticket)
        if pos is None:
            return _res(_R.POSITION_CLOSED, "Position not found")
        if volume <= 0 or volume > pos.volume + 1e-12:
            return _res(_R.INVALID_CLOSE_VOLUME, "Invalid close volume")
        tick = self._ticks.get(pos.symbol)
        if tick is None:
            return _res(_R.PRICE_OFF, "No market price")
        is_b = pos.position_type == int(_PT.BUY)
        cp = (tick.bid if is_b else tick.ask) if cp_in is None else float(cp_in)
        profit = self.order_calc_profit(
            _OT.BUY if is_b else _OT.SELL, pos.symbol, volume, pos.price_open, cp
        )
        comm = volume * self._commission_per_lot
        swap = pos.swap * (volume / pos.volume) if pos.volume > 0 else 0.0
        self._account.balance += profit + swap - comm
        order_ticket = next(self._order_ids)
        c_req = TradeRequest(
            action=_A.DEAL, symbol=pos.symbol, volume=volume, comment=comment
        )
        c_req.order_type = _OT.SELL if is_b else _OT.BUY
        c_req.magic, c_req.position = pos.magic, pos.ticket
        self._append_filled(c_req, order_ticket, pos.ticket, cp)
        deal = self._record_deal(
            pos, order_ticket, _DE.OUT, vol=volume, price=cp, comm=comm
        )
        deal.comment, deal.swap, deal.profit = comment, swap, profit
        pos.commission *= max(0.0, 1.0 - volume / pos.volume)
        pos.volume -= volume
        pos.swap -= swap
        pos.time_update, pos.time_update_msc = self._clock_stamp()
        if pos.volume <= 1e-12:
            del self._positions[ticket]
        else:
            pos.price_current = cp
        stats = self._stats.setdefault(pos.symbol, {})
        stats["session_deals"] = stats.get("session_deals", 0) + 1
        self._mark_to_market()
        return self._done(deal.ticket, order_ticket, volume, cp, tick)

    def _close_by(self, ticket: int, ticket_by: int) -> TradeResult:
        p1, p2 = self._positions.get(ticket), self._positions.get(ticket_by)
        if p1 is None or p2 is None:
            return _res(_R.POSITION_CLOSED, "Position not found")
        if p1.symbol != p2.symbol or p1.position_type == p2.position_type:
            msg = "Close By requires opposite positions on same symbol"
            return _res(_R.INVALID_ORDER, msg)
        tick = self._ticks.get(p1.symbol)
        if tick is None:
            return _res(_R.PRICE_OFF, "No market price")
        mid, vol = (tick.bid + tick.ask) / 2.0, min(p1.volume, p2.volume)
        first = self._close_position(ticket, vol, comment="close by", close_price=mid)
        second = self._close_position(
            ticket_by, vol, comment="close by", close_price=mid
        )
        return second if second.retcode != int(_R.DONE) else first

    def _append_filled(self, req: TradeRequest, tkt: int, pid: int, p: float) -> None:
        kw = {"vol_cur": 0.0, "p_open": p, "p_cur": p, "pos_id": pid, "done": True}
        self._history_orders.append(self._build_order(req, tkt, _OS.FILLED, **kw))

    def _expire_orders(self) -> None:
        now_sec, now_msc = self._clock_stamp()
        spec_times = {int(_OTM.SPECIFIED), int(_OTM.SPECIFIED_DAY)}
        for ticket in [
            t
            for t, o in self._orders.items()
            if o.type_time in spec_times and 0 < o.time_expiration <= now_sec
        ]:
            order = self._orders.pop(ticket)
            order.state, order.state_description = int(_OS.EXPIRED), _label(_OS.EXPIRED)
            order.time_done, order.time_done_msc = now_sec, now_msc
            self._history_orders.append(replace(order))

    def _trigger_pending(self, symbol: str, tick: MarketTick) -> None:
        for ticket, order in list(self._orders.items()):
            if order.symbol != symbol:
                continue
            trig, fp, ot = False, order.price_open, order.order_type
            if ot == int(_OT.BUY_LIMIT) and tick.ask <= fp:
                trig, fp = True, min(fp, tick.ask)
            elif ot == int(_OT.SELL_LIMIT) and tick.bid >= fp:
                trig, fp = True, max(fp, tick.bid)
            elif ot == int(_OT.BUY_STOP) and tick.ask >= fp:
                trig, fp = True, tick.ask
            elif ot == int(_OT.SELL_STOP) and tick.bid <= fp:
                trig, fp = True, tick.bid
            elif ot in {int(_OT.BUY_STOP_LIMIT), int(_OT.SELL_STOP_LIMIT)}:
                is_bsl = ot == int(_OT.BUY_STOP_LIMIT)
                if (is_bsl and tick.ask >= fp) or (not is_bsl and tick.bid <= fp):
                    new_ot = _OT.BUY_LIMIT if is_bsl else _OT.SELL_LIMIT
                    order.order_type = int(new_ot)
                    order.type_description = _label(new_ot)
                    order.price_open = order.price_stop_limit or fp
                    order.price_stop_limit = 0.0
                continue
            if not trig:
                continue
            del self._orders[ticket]
            order.state, order.state_description = int(_OS.FILLED), _label(_OS.FILLED)
            order.time_done, order.time_done_msc = self._clock_stamp()
            order.volume_current, order.price_current = 0.0, fp
            self._history_orders.append(replace(order))
            is_b = order.order_type in {int(_OT.BUY_LIMIT), int(_OT.BUY_STOP)}
            tf_m, tt_m = _OF._value2member_map_, _OTM._value2member_map_
            f_in, t_in = order.type_filling, order.type_time
            req = TradeRequest(
                action=_A.DEAL, symbol=order.symbol, volume=order.volume_initial
            )
            req.order_type = _OT.BUY if is_b else _OT.SELL
            req.price, req.sl, req.tp = fp, order.sl, order.tp
            req.magic, req.comment = order.magic, order.comment
            req.type_filling = _OF(f_in) if f_in in tf_m else _OF.FOK
            req.type_time = _OTM(t_in) if t_in in tt_m else _OTM.GTC
            t_exp = order.time_expiration
            req.expiration = datetime.fromtimestamp(t_exp, tz=UTC) if t_exp else None
            if self._account.margin_mode == MarginMode.RETAIL_HEDGING:
                self._open_new_position(req, fp, ticket)
            else:
                self._market_open(replace(req, price=fp))

    def _trigger_stops(self, symbol: str, tick: MarketTick) -> None:
        for pos in list(self._positions.values()):
            if pos.symbol != symbol:
                continue
            is_b = pos.position_type == int(_PT.BUY)
            sl_hit = pos.sl > 0 and (tick.bid <= pos.sl if is_b else tick.ask >= pos.sl)
            tp_hit = pos.tp > 0 and (tick.bid >= pos.tp if is_b else tick.ask <= pos.tp)
            if sl_hit or tp_hit:
                c = "stop loss" if sl_hit else "take profit"
                self._close_position(pos.ticket, pos.volume, comment=c)

    def _mark_to_market(self) -> None:
        floating = margin = 0.0
        for pos in self._positions.values():
            tick = self._ticks.get(pos.symbol)
            if tick is None:
                continue
            is_buy = pos.position_type == int(_PT.BUY)
            cur, ot = (tick.bid, _OT.BUY) if is_buy else (tick.ask, _OT.SELL)
            pos.price_current = cur
            sym, vol, po = pos.symbol, pos.volume, pos.price_open
            pos.profit = self.order_calc_profit(ot, sym, vol, po, cur)
            floating += pos.profit + pos.swap
            margin += self.order_calc_margin(ot, sym, vol, po)
        acc = self._account
        acc.profit, acc.margin = floating, margin
        acc.equity = acc.balance + floating + acc.credit
        acc.free_margin = acc.equity - margin
        acc.margin_level = (acc.equity / margin) * 100.0 if margin > 0 else 0.0

    @override
    async def start(self) -> None:
        logger.debug("FR-SIMULATION-DISPATCH: starting backend")
        self.connect()

    @override
    async def wait_connected(self, timeout: float | None = None) -> None:
        del timeout
        logger.debug("FR-SIMULATION-DISPATCH: checking readiness")
        if not self._connected:
            raise BridgeError("simulator disconnected", code="NOT_CONNECTED")

    @override
    async def close(self) -> None:
        logger.debug("FR-SIMULATION-DISPATCH: closing backend")
        self.disarm()
        self.disconnect()

    @override
    def arm(self) -> None:
        logger.debug("FR-SIMULATION-DISPATCH: arming local execution")
        if not self._connected:
            raise BridgeError("simulator disconnected", code="NOT_CONNECTED")
        self._armed = True

    @override
    def disarm(self) -> None:
        logger.debug("FR-SIMULATION-DISPATCH: disarming local execution")
        self._armed = False

    @override
    async def next_event(self, timeout: float | None = None) -> BridgeEvent:
        async with asyncio.timeout(timeout):
            return await self._event_queue.get()

    @override
    async def await_request_event(
        self, request_id: int, timeout: float | None = None
    ) -> BridgeEvent:
        del request_id, timeout
        msg = "simulator has no native request event correlation"
        raise BridgeError(msg, code="UNSUPPORTED_OPERATION")

    def seed_bar_history(
        self, sym: str, tf: Timeframe, bars: Sequence[MarketBar]
    ) -> None:
        """Register an immutable chronological bar series without advancing time."""
        logger.debug("FR-SIMULATION-HISTORY: seeding bars")
        if sym not in self._symbols or tf not in TIMEFRAME_SECONDS:
            raise BridgeError("invalid history series", code="BAD_REQUEST")
        rows = [asdict(bar) for bar in bars]
        validate_rows(rows, "bars", 0, 2**63 - 1, len(rows))
        self._bar_history[sym, tf] = tuple(bars)

    def seed_tick_history(self, symbol: str, ticks: Sequence[MarketTick]) -> None:
        """Register immutable chronological ticks without replacing the live quote."""
        logger.debug("FR-SIMULATION-HISTORY: seeding ticks")
        if symbol not in self._symbols:
            raise BridgeError("invalid history series", code="BAD_REQUEST")
        rows = [asdict(tick) for tick in ticks]
        validate_rows(rows, "ticks", 0, 2**63 - 1, len(rows))
        self._tick_history[symbol] = tuple(ticks)

    @override
    def calc_margin(self, ot: OrderType, sym: str, vol: float, price: float) -> float:
        return self.order_calc_margin(ot, sym, vol, price)

    @override
    def calc_profit(
        self, ot: OrderType, sym: str, vol: float, p_open: float, p_close: float
    ) -> float:
        return self.order_calc_profit(ot, sym, vol, p_open, p_close)

    def _slice_history(
        self, items: Sequence[_T], ms: bool = False, **kw: Any
    ) -> list[_T]:
        scale, key = (1000, "time_msc") if ms else (1, "time")
        now_v = int(self._clock.timestamp() * scale)
        out = [x for x in items if getattr(x, key) <= now_v]
        d_from, d_to = kw.get("date_from"), kw.get("date_to")
        if d_from or d_to:
            lo = int(d_from.timestamp() * scale) if d_from else 0
            hi = int(d_to.timestamp() * scale) if d_to else now_v
            out = [x for x in out if lo <= getattr(x, key) <= hi]
        cnt, limit = kw.get("count"), int(kw.get("limit", 1000))
        n = cnt if cnt is not None and cnt > 0 else limit
        return list(out[-n:] if n and len(out) > n else out)

    @override
    def get_bars(
        self,
        symbol: str,
        timeframe: Timeframe | str = Timeframe.PERIOD_H1,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        **kw: Any,
    ) -> pd.DataFrame:
        tf = Timeframe(str(timeframe))
        if (symbol, tf) not in self._bar_history:
            raise BridgeError("history is not seeded", code="DATA_NOT_READY")
        bars = self._slice_history(
            self._bar_history[symbol, tf], date_from=date_from, date_to=date_to, **kw
        )
        return bars_to_dataframe(bars)

    @override
    def get_ticks(
        self,
        symbol: str,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        **kw: Any,
    ) -> pd.DataFrame:
        if symbol not in self._tick_history:
            raise BridgeError("history is not seeded", code="DATA_NOT_READY")
        ticks = self._slice_history(
            self._tick_history[symbol], True, date_from=date_from, date_to=date_to, **kw
        )
        return ticks_to_dataframe(ticks)


__all__ = ["SimulatorClient"]
