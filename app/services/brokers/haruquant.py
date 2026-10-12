"""Adapter for HaruQuantAI's existing 27-operation ``BaseBroker`` contract.

This is the migration bridge that prevents a second broker stack. Existing
``MetaTraderBroker`` (or another current HaruQuantAI broker) can sit underneath
the new eight-class MQL5-compatible API while the rest of the repository is
migrated incrementally.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services.brokers.contracts import (
    AccountSnapshot,
    AccountTradeMode,
    BrokerBackend,
    DealEntry,
    DealRecord,
    DealType,
    MarginMode,
    OrderRecord,
    OrderState,
    OrderType,
    PositionRecord,
    PositionType,
    StopoutMode,
    SymbolCalcMode,
    SymbolSpec,
    SymbolSwapMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    TerminalSnapshot,
    Tick,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradeRetcode,
)


def _unwrap(response: Any, default: Any = None) -> Any:
    if response is None:
        return default
    unwrap = getattr(response, "unwrap", None)
    if callable(unwrap):
        try:
            return unwrap()
        except Exception:
            return default
    return getattr(response, "data", response)


def _dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if value in (None, 0):
        return datetime.fromtimestamp(0, tz=UTC)
    return datetime.fromtimestamp(float(value), tz=UTC)


def _enum(enum_type: type[Any], value: Any, default: Any) -> Any:
    try:
        return enum_type(int(value))
    except TypeError, ValueError:
        return default


class HaruQuantBackend(BrokerBackend):
    """Wrap an existing ``app.plugins.brokers.contracts.BaseBroker`` instance."""

    def __init__(self, legacy_broker: Any) -> None:
        self.legacy = legacy_broker

    def connect(self) -> bool:
        return bool(_unwrap(self.legacy.connect(), False))

    def disconnect(self) -> None:
        self.legacy.disconnect()

    def terminal(self) -> TerminalSnapshot:
        src = _unwrap(self.legacy.get_terminal_info())
        return TerminalSnapshot(
            build=int(getattr(src, "build", 0) or 0),
            connected=bool(getattr(src, "connected", False)),
            dlls_allowed=bool(getattr(src, "dlls_allowed", False)),
            trade_allowed=bool(getattr(src, "trade_allowed", False)),
            email_enabled=bool(getattr(src, "email_enabled", False)),
            ftp_enabled=bool(getattr(src, "ftp_enabled", False)),
            max_bars=int(getattr(src, "maxbars", 0) or 0),
            code_page=int(getattr(src, "codepage", 0) or 0),
            language=str(getattr(src, "language", "") or ""),
            name=str(getattr(src, "name", "") or ""),
            company=str(getattr(src, "company", "") or ""),
            path=str(getattr(src, "path", "") or ""),
            data_path=str(getattr(src, "data_path", "") or ""),
            common_data_path=str(getattr(src, "commondata_path", "") or ""),
        )

    def account(self) -> AccountSnapshot:
        src = _unwrap(self.legacy.get_account_info())
        return AccountSnapshot(
            login=int(getattr(src, "login", 0) or 0),
            trade_mode=_enum(
                AccountTradeMode, getattr(src, "trade_mode", 0), AccountTradeMode.DEMO
            ),
            leverage=int(getattr(src, "leverage", 0) or 0),
            stopout_mode=_enum(
                StopoutMode, getattr(src, "margin_so_mode", 0), StopoutMode.PERCENT
            ),
            margin_mode=_enum(
                MarginMode, getattr(src, "margin_mode", 2), MarginMode.RETAIL_HEDGING
            ),
            trade_allowed=bool(getattr(src, "trade_allowed", False)),
            trade_expert=bool(getattr(src, "trade_expert", False)),
            limit_orders=int(getattr(src, "limit_orders", 0) or 0),
            balance=float(getattr(src, "balance", 0.0) or 0.0),
            credit=float(getattr(src, "credit", 0.0) or 0.0),
            profit=float(getattr(src, "profit", 0.0) or 0.0),
            equity=float(getattr(src, "equity", 0.0) or 0.0),
            margin=float(getattr(src, "margin", 0.0) or 0.0),
            free_margin=float(getattr(src, "margin_free", 0.0) or 0.0),
            margin_level=float(getattr(src, "margin_level", 0.0) or 0.0),
            margin_call=float(getattr(src, "margin_so_call", 0.0) or 0.0),
            margin_stop_out=float(getattr(src, "margin_so_so", 0.0) or 0.0),
            name=str(getattr(src, "name", "") or ""),
            server=str(getattr(src, "server", "") or ""),
            currency=str(getattr(src, "currency", "") or ""),
            company=str(getattr(src, "company", "") or ""),
        )

    def symbol(self, name: str) -> SymbolSpec | None:
        src = _unwrap(self.legacy.get_symbol_info(name))
        if src is None:
            return None
        return SymbolSpec(
            name=name,
            digits=int(getattr(src, "digits", 5) or 5),
            point=float(getattr(src, "point", 0.00001) or 0.00001),
            spread=int(getattr(src, "spread", 0) or 0),
            spread_float=bool(getattr(src, "spread_float", True)),
            ticks_book_depth=int(getattr(src, "ticks_bookdepth", 0) or 0),
            stops_level=int(getattr(src, "trade_stops_level", 0) or 0),
            freeze_level=int(getattr(src, "trade_freeze_level", 0) or 0),
            trade_calc_mode=_enum(
                SymbolCalcMode, getattr(src, "trade_calc_mode", 0), SymbolCalcMode.FOREX
            ),
            trade_mode=_enum(
                SymbolTradeMode, getattr(src, "trade_mode", 4), SymbolTradeMode.FULL
            ),
            trade_execution=_enum(
                SymbolTradeExecution,
                getattr(src, "trade_exemode", 2),
                SymbolTradeExecution.MARKET,
            ),
            swap_mode=_enum(
                SymbolSwapMode, getattr(src, "swap_mode", 0), SymbolSwapMode.DISABLED
            ),
            swap_rollover3days=int(getattr(src, "swap_rollover3days", 3) or 3),
            margin_initial=float(getattr(src, "margin_initial", 0.0) or 0.0),
            margin_maintenance=float(getattr(src, "margin_maintenance", 0.0) or 0.0),
            tick_value=float(getattr(src, "trade_tick_value", 0.0) or 0.0),
            tick_value_profit=float(
                getattr(src, "trade_tick_value_profit", 0.0) or 0.0
            ),
            tick_value_loss=float(getattr(src, "trade_tick_value_loss", 0.0) or 0.0),
            tick_size=float(getattr(src, "trade_tick_size", 0.0) or 0.0),
            contract_size=float(getattr(src, "trade_contract_size", 0.0) or 0.0),
            lots_min=float(getattr(src, "volume_min", 0.0) or 0.0),
            lots_max=float(getattr(src, "volume_max", 0.0) or 0.0),
            lots_step=float(getattr(src, "volume_step", 0.0) or 0.0),
            lots_limit=float(getattr(src, "volume_limit", 0.0) or 0.0),
            swap_long=float(getattr(src, "swap_long", 0.0) or 0.0),
            swap_short=float(getattr(src, "swap_short", 0.0) or 0.0),
            currency_base=str(getattr(src, "currency_base", "") or ""),
            currency_profit=str(getattr(src, "currency_profit", "") or ""),
            currency_margin=str(getattr(src, "currency_margin", "") or ""),
            bank=str(getattr(src, "bank", "") or ""),
            description=str(getattr(src, "description", "") or ""),
            path=str(getattr(src, "path", "") or ""),
            selected=bool(getattr(src, "select", True)),
            synchronized=bool(getattr(src, "visible", True)),
        )

    def select_symbol(self, name: str, selected: bool) -> bool:
        return bool(_unwrap(self.legacy.enable_symbol(name, selected), False))

    def tick(self, name: str) -> Tick | None:
        src = _unwrap(self.legacy.get_symbol_tick(name))
        if src is None:
            return None
        return Tick(
            symbol=name,
            time=_dt(getattr(src, "time", None)),
            bid=float(getattr(src, "bid", 0.0) or 0.0),
            ask=float(getattr(src, "ask", 0.0) or 0.0),
            last=float(getattr(src, "last", 0.0) or 0.0),
            volume=float(getattr(src, "volume", 0.0) or 0.0),
        )

    def orders(self) -> list[OrderRecord]:
        return [
            self._order(x) for x in (_unwrap(self.legacy.get_order_info(), []) or [])
        ]

    def history_orders(self) -> list[OrderRecord]:
        return [
            self._order(x)
            for x in (_unwrap(self.legacy.get_history_order_info(), []) or [])
        ]

    def positions(self) -> list[PositionRecord]:
        return [
            self._position(x)
            for x in (_unwrap(self.legacy.get_position_info(), []) or [])
        ]

    def deals(self) -> list[DealRecord]:
        return [
            self._deal(x)
            for x in (_unwrap(self.legacy.get_history_deal_info(), []) or [])
        ]

    def _legacy_request(self, request: TradeRequest) -> Any:
        # Imported lazily so this adapter remains importable in the standalone
        # artifact before it is copied into HaruQuantAI.
        from app.plugins.brokers.contracts import (  # type: ignore[import-not-found]
            OrderAction as LegacyAction,
        )
        from app.plugins.brokers.contracts import (
            OrderFilling as LegacyFilling,
        )
        from app.plugins.brokers.contracts import (
            OrderTime as LegacyTime,
        )
        from app.plugins.brokers.contracts import (
            OrderType as LegacyType,
        )
        from app.plugins.brokers.contracts import (
            TradeRequest as LegacyRequest,
        )

        def enum_name(value: Any) -> str:
            return getattr(value, "name", str(value))

        action_name = (
            "CLOSE"
            if request.position and request.action.value == 1
            else enum_name(request.action)
        )
        return LegacyRequest(
            action=LegacyAction[action_name],
            symbol=request.symbol,
            volume=request.volume,
            type=LegacyType[enum_name(request.order_type)],
            price=request.price or None,
            sl=request.sl,
            tp=request.tp,
            deviation=request.deviation,
            magic=request.magic,
            comment=request.comment,
            position=request.position,
            order=request.order,
            type_time=LegacyTime[enum_name(request.type_time)],
            type_filling=LegacyFilling[enum_name(request.type_filling)],
            expiration=request.expiration,
        )

    def order_check(self, request: TradeRequest) -> TradeCheckResult:
        src = _unwrap(self.legacy.check_order(self._legacy_request(request)))
        if src is None:
            return TradeCheckResult(
                retcode=int(TradeRetcode.ERROR), comment="Legacy order check failed"
            )
        return TradeCheckResult(
            retcode=int(getattr(src, "retcode", 0) or 0),
            balance=float(getattr(src, "balance", 0.0) or 0.0),
            equity=float(getattr(src, "equity", 0.0) or 0.0),
            profit=float(getattr(src, "profit", 0.0) or 0.0),
            margin=float(getattr(src, "margin", 0.0) or 0.0),
            margin_free=float(getattr(src, "margin_free", 0.0) or 0.0),
            margin_level=float(getattr(src, "margin_level", 0.0) or 0.0),
            comment=str(getattr(src, "comment", "") or ""),
            raw=src,
        )

    def order_send(self, request: TradeRequest) -> TradeResult:
        src = _unwrap(self.legacy.trade(self._legacy_request(request)))
        if src is None:
            return TradeResult(
                retcode=int(TradeRetcode.ERROR), comment="Legacy trade failed"
            )
        return TradeResult(
            retcode=int(getattr(src, "retcode", int(TradeRetcode.ERROR)) or 0),
            deal=int(getattr(src, "deal", 0) or 0),
            order=int(getattr(src, "order", 0) or 0),
            volume=float(getattr(src, "volume", 0.0) or 0.0),
            price=float(getattr(src, "price", 0.0) or 0.0),
            bid=float(getattr(src, "bid", 0.0) or 0.0),
            ask=float(getattr(src, "ask", 0.0) or 0.0),
            comment=str(getattr(src, "comment", "") or ""),
            request_id=int(getattr(src, "request_id", 0) or 0),
            retcode_external=int(getattr(src, "retcode_external", 0) or 0),
            raw=src,
        )

    def order_calc_profit(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ) -> float:
        return float(
            _unwrap(
                self.legacy.calculate_profit(
                    order_type.name, symbol, volume, price_open, price_close
                ),
                0.0,
            )
            or 0.0
        )

    def order_calc_margin(
        self,
        order_type: OrderType,
        symbol: str,
        volume: float,
        price: float,
    ) -> float:
        return float(
            _unwrap(
                self.legacy.calculate_margin(order_type.name, symbol, volume, price),
                0.0,
            )
            or 0.0
        )

    @staticmethod
    def _order(src: Any) -> OrderRecord:
        return OrderRecord(
            ticket=int(getattr(src, "ticket", 0) or 0),
            symbol=str(getattr(src, "symbol", "") or ""),
            order_type=_enum(OrderType, getattr(src, "type", 0), OrderType.BUY),
            state=_enum(OrderState, getattr(src, "state", 0), OrderState.STARTED),
            volume_initial=float(getattr(src, "volume_initial", 0.0) or 0.0),
            volume_current=float(getattr(src, "volume_current", 0.0) or 0.0),
            price_open=float(getattr(src, "price_open", 0.0) or 0.0),
            sl=float(getattr(src, "sl", 0.0) or 0.0),
            tp=float(getattr(src, "tp", 0.0) or 0.0),
            time_setup=_dt(getattr(src, "time_setup", None)),
            magic=int(getattr(src, "magic", 0) or 0),
            comment=str(getattr(src, "comment", "") or ""),
        )

    @staticmethod
    def _position(src: Any) -> PositionRecord:
        ticket = int(getattr(src, "ticket", 0) or 0)
        raw_type = getattr(src, "type", 0)
        if isinstance(raw_type, str):
            raw_type = 0 if raw_type.upper() == "BUY" else 1
        return PositionRecord(
            ticket=ticket,
            identifier=ticket,
            symbol=str(getattr(src, "symbol", "") or ""),
            position_type=_enum(PositionType, raw_type, PositionType.BUY),
            volume=float(getattr(src, "volume", 0.0) or 0.0),
            price_open=float(getattr(src, "price_open", 0.0) or 0.0),
            price_current=float(getattr(src, "price_current", 0.0) or 0.0),
            sl=float(getattr(src, "sl", 0.0) or 0.0),
            tp=float(getattr(src, "tp", 0.0) or 0.0),
            swap=float(getattr(src, "swap", 0.0) or 0.0),
            profit=float(getattr(src, "profit", 0.0) or 0.0),
            time=_dt(getattr(src, "time", None)),
            magic=int(getattr(src, "magic", 0) or 0),
            comment=str(getattr(src, "comment", "") or ""),
        )

    @staticmethod
    def _deal(src: Any) -> DealRecord:
        raw_type = getattr(src, "type", 0)
        if isinstance(raw_type, str):
            try:
                raw_type = DealType[raw_type.upper()].value
            except KeyError:
                raw_type = 0
        raw_entry = getattr(src, "entry", 0)
        if isinstance(raw_entry, str):
            try:
                raw_entry = DealEntry[raw_entry.upper()].value
            except KeyError:
                raw_entry = 0
        return DealRecord(
            ticket=int(getattr(src, "ticket", 0) or 0),
            order=int(getattr(src, "order", 0) or 0),
            position_id=int(getattr(src, "position_id", 0) or 0),
            symbol=str(getattr(src, "symbol", "") or ""),
            deal_type=_enum(DealType, raw_type, DealType.BUY),
            entry=_enum(DealEntry, raw_entry, DealEntry.IN),
            volume=float(getattr(src, "volume", 0.0) or 0.0),
            price=float(getattr(src, "price", 0.0) or 0.0),
            commission=float(getattr(src, "commission", 0.0) or 0.0),
            swap=float(getattr(src, "swap", 0.0) or 0.0),
            profit=float(getattr(src, "profit", 0.0) or 0.0),
            time=_dt(getattr(src, "time", None)),
            magic=int(getattr(src, "magic", 0) or 0),
            comment=str(getattr(src, "comment", "") or ""),
        )
