"""Private native-method semantics for the local simulation backend.

Description:
    Ported method handlers operate on per-object state and the existing local
    model. No duplicate eight-class facade is defined here. Explicit registries
    bound the available methods; Trading owns public asynchronous forwarding.

Purpose:
    FEAT-SIMULATION-DISPATCH: Preserve local MQL5-oriented operation semantics.

Key Capabilities:
    - FR-SIMULATION-DISPATCH: Execute native operation handlers on isolated state.
      Associated: `execute()`, `_ObjectState`
      Logging: DEBUG dispatch metadata and INFO Print operation metadata only.

Python API Usage:
    Internal helper called by SimulationBackend.call; use Trading publicly.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_simulator.py --no-cov
"""

from __future__ import annotations

import fnmatch
import json
from collections.abc import Callable
from copy import deepcopy
from dataclasses import asdict, dataclass, is_dataclass, replace
from datetime import UTC, datetime
from inspect import signature
from typing import Any, cast

from app.host.logging import get_logger
from app.services.brokers.base import (
    BridgeError,
    BrokerBackend,
    epoch_millis,
    epoch_seconds,
)
from app.services.trading import (
    DEAL_ENTRY_DESCRIPTIONS,
    DEAL_TYPE_DESCRIPTIONS,
    ORDER_FILLING_DESCRIPTIONS,
    ORDER_STATE_DESCRIPTIONS,
    ORDER_TIME_DESCRIPTIONS,
    ORDER_TYPE_DESCRIPTIONS,
    POSITION_TYPE_DESCRIPTIONS,
    AccountSnapshot,
    AccountTradeMode,
    BookType,
    DealEntry,
    DealSnapshot,
    DealType,
    HistoryOrderSnapshot,
    MarginMode,
    OrderFilling,
    OrderSnapshot,
    OrderState,
    OrderTime,
    OrderType,
    PositionSnapshot,
    PositionType,
    StopoutMode,
    SymbolCalcMode,
    SymbolSnapshot,
    SymbolSpec,
    SymbolSwapMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    TerminalSnapshot,
    TradeAction,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradeRetcode,
)

DealEntryEnum = DealEntry
DealTypeEnum = DealType
OrderStateEnum = OrderState
OrderFillingEnum = OrderFilling
OrderTimeEnum = OrderTime
OrderTypeEnum = OrderType

logger = get_logger(__name__)


@dataclass
class _ObjectState:
    """Mutable state for one simulated native object."""

    _async: Any = None
    _backend: Any = None
    _deviation: Any = None
    _filling: Any = None
    _last_check: Any = None
    _last_request: Any = None
    _last_result: Any = None
    _log_level: Any = None
    _magic: Any = None
    symbol_name: Any = None
    selected: Any = None
    _stored_state: Any = None
    scope: Any = None


def _to_epoch(value: Any) -> float:
    """Extract unix timestamp from datetime or numeric value."""
    if isinstance(value, datetime):
        return value.timestamp()
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def record_dict(value: Any) -> dict[str, Any]:
    """Read a local record as an independent field mapping."""
    if value is None:
        return {}
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, dict):
        return dict(value)
    asdict_fn = getattr(value, "_asdict", None)
    if callable(asdict_fn):
        result = asdict_fn()
        if isinstance(result, dict):
            return dict(result)
    return {
        name: getattr(value, name)
        for name in dir(value)
        if not name.startswith("_") and (not callable(getattr(value, name, None)))
    }


def _extract_active_query(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[str | None, str | None, int | None]:
    """Extract symbol, group, and ticket filters from active query parameters."""
    if args and isinstance(args[0], dict):
        d = args[0]
        return d.get("symbol"), d.get("group"), d.get("ticket")
    symbol = (
        str(args[0]) if len(args) > 0 and args[0] is not None else kwargs.get("symbol")
    )
    group = (
        str(args[1]) if len(args) > 1 and args[1] is not None else kwargs.get("group")
    )
    ticket = (
        int(args[2]) if len(args) > 2 and args[2] is not None else kwargs.get("ticket")
    )
    return symbol, group, ticket


def _extract_history_query(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Any, Any, str | None, str | None, int | None, int | None]:
    """Extract interval, symbol, group, ticket, position from history query."""
    if args and isinstance(args[0], dict):
        d = args[0]
        return (
            d.get("date_from"),
            d.get("date_to"),
            d.get("symbol"),
            d.get("group"),
            d.get("ticket"),
            d.get("position"),
        )
    date_from, date_to, symbol, group = None, None, None, None
    if len(args) == 1 and isinstance(args[0], str):
        symbol = args[0]
    elif len(args) >= 2:
        date_from, date_to = args[0], args[1]
        if len(args) > 2:
            group = str(args[2])
    return (
        kwargs.get("date_from", date_from),
        kwargs.get("date_to", date_to),
        kwargs.get("symbol", symbol),
        kwargs.get("group", group),
        kwargs.get("ticket"),
        kwargs.get("position"),
    )


def _retcode_description(code: int) -> str:
    if code == 0:
        return "Done"
    try:
        return TradeRetcode(code).name.replace("_", " ").title()
    except ValueError:
        return f"Unknown retcode {code}"


def _selectionbase___init__(self: _ObjectState, backend: BrokerBackend) -> None:
    self._backend = backend
    self.selected = None
    self._stored_state = None


def _selectionbase__select(self: _ObjectState, value: Any | None) -> bool:
    self.selected = value
    return value is not None


def _selectionbase__require(self: _ObjectState) -> Any:
    if self.selected is None:
        raise RuntimeError(f"No {self.scope or 'record'} selected")
    return self.selected


def _selectionbase__value(self: _ObjectState, name: str, default: Any = 0) -> Any:
    selected = _selectionbase__require(self)
    return getattr(selected, name, default)


def _selectionbase__store(self: _ObjectState) -> None:
    self._stored_state = deepcopy(record_dict(_selectionbase__require(self)))


def _selectionbase__check(self: _ObjectState) -> bool:
    if self._stored_state is None:
        return False
    return cast(
        "bool", self._stored_state == record_dict(_selectionbase__require(self))
    )


def _selectionbase__info(self: _ObjectState, property_id: int | str) -> Any:
    selector: str | int | None = None
    if self.selected is not None:
        selector = getattr(self.selected, "ticket", None) or getattr(
            self.selected, "symbol", None
        )
    value = self._backend.info_value(self.scope, property_id, selector)
    if value is not None:
        return value
    if isinstance(property_id, str):
        normalized = property_id.strip().lower()
        data: dict[str, Any] = (
            record_dict(_selectionbase__require(self))
            if self.selected is not None
            else {}
        )
        if normalized in data:
            return data[normalized]
        aliases = {key.lower(): val for key, val in data.items()}
        return aliases.get(normalized)
    return None


def _accountinfo___init__(self: _ObjectState, backend: BrokerBackend) -> None:
    self._backend = backend


def _accountinfo__a(self: _ObjectState) -> Any:
    return self._backend.account()


def _accountinfo_accountinfo(self: _ObjectState) -> AccountSnapshot:
    account = _accountinfo__a(self)
    if isinstance(account, AccountSnapshot):
        trade_mode = AccountTradeMode(account.trade_mode)
        stopout_mode = StopoutMode(account.stopout_mode)
        margin_mode = MarginMode(account.margin_mode)
        return replace(
            account,
            trade_mode_description=(
                account.trade_mode_description
                or trade_mode.name.replace("_", " ").title()
            ),
            stopout_mode_description=(
                account.stopout_mode_description
                or stopout_mode.name.replace("_", " ").title()
            ),
            margin_mode_description=(
                account.margin_mode_description
                or margin_mode.name.replace("_", " ").title()
            ),
        )
    return cast("AccountSnapshot", account)


def _accountinfo_login(self: _ObjectState) -> int:
    return int(_accountinfo__a(self).login)


def _accountinfo_trademode(self: _ObjectState) -> AccountTradeMode:
    return AccountTradeMode(_accountinfo__a(self).trade_mode)


def _accountinfo_trademodedescription(self: _ObjectState) -> str:
    return _accountinfo_trademode(self).name.replace("_", " ").title()


def _accountinfo_leverage(self: _ObjectState) -> int:
    return int(_accountinfo__a(self).leverage)


def _accountinfo_stopoutmode(self: _ObjectState) -> StopoutMode:
    return StopoutMode(_accountinfo__a(self).stopout_mode)


def _accountinfo_stopoutmodedescription(self: _ObjectState) -> str:
    return _accountinfo_stopoutmode(self).name.replace("_", " ").title()


def _accountinfo_marginmode(self: _ObjectState) -> MarginMode:
    return MarginMode(_accountinfo__a(self).margin_mode)


def _accountinfo_marginmodedescription(self: _ObjectState) -> str:
    return _accountinfo_marginmode(self).name.replace("_", " ").title()


def _accountinfo_tradeallowed(self: _ObjectState) -> bool:
    return bool(_accountinfo__a(self).trade_allowed)


def _accountinfo_tradeexpert(self: _ObjectState) -> bool:
    return bool(_accountinfo__a(self).trade_expert)


def _accountinfo_limitorders(self: _ObjectState) -> int:
    return int(_accountinfo__a(self).limit_orders)


def _accountinfo_balance(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).balance)


def _accountinfo_credit(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).credit)


def _accountinfo_profit(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).profit)


def _accountinfo_equity(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).equity)


def _accountinfo_margin(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).margin)


def _accountinfo_freemargin(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).free_margin)


def _accountinfo_marginlevel(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).margin_level)


def _accountinfo_margincall(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).margin_call)


def _accountinfo_marginstopout(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).margin_stop_out)


def _accountinfo_name(self: _ObjectState) -> str:
    return cast("str", _accountinfo__a(self).name)


def _accountinfo_server(self: _ObjectState) -> str:
    return cast("str", _accountinfo__a(self).server)


def _accountinfo_currency(self: _ObjectState) -> str:
    return cast("str", _accountinfo__a(self).currency)


def _accountinfo_company(self: _ObjectState) -> str:
    return cast("str", _accountinfo__a(self).company)


def _accountinfo_currencydigits(self: _ObjectState) -> int:
    return int(_accountinfo__a(self).currency_digits)


def _accountinfo_fifoclose(self: _ObjectState) -> bool:
    return bool(_accountinfo__a(self).fifo_close)


def _accountinfo_margininitial(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).margin_initial)


def _accountinfo_marginmaintenance(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).margin_maintenance)


def _accountinfo_assets(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).assets)


def _accountinfo_liabilities(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).liabilities)


def _accountinfo_commissionblocked(self: _ObjectState) -> float:
    return float(_accountinfo__a(self).commission_blocked)


def _accountinfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    value = self._backend.info_value("account", property_id)
    if value is None and isinstance(property_id, str):
        value = getattr(_accountinfo__a(self), property_id.strip().lower(), 0)
    return int(value or 0)


def _accountinfo_infodouble(self: _ObjectState, property_id: int | str) -> float:
    value = self._backend.info_value("account", property_id)
    if value is None and isinstance(property_id, str):
        value = getattr(_accountinfo__a(self), property_id.strip().lower(), 0.0)
    return float(value or 0.0)


def _accountinfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    value = self._backend.info_value("account", property_id)
    if value is None and isinstance(property_id, str):
        value = getattr(_accountinfo__a(self), property_id.strip().lower(), "")
    return str(value or "")


def _accountinfo_orderprofitcheck(
    self: _ObjectState,
    symbol: str,
    order_type: OrderType | int,
    volume: float,
    price_open: float,
    price_close: float,
) -> float:
    return cast(
        "float",
        self._backend.order_calc_profit(
            OrderType(order_type), symbol, volume, price_open, price_close
        ),
    )


def _accountinfo_margincheck(
    self: _ObjectState,
    symbol: str,
    order_type: OrderType | int,
    volume: float,
    price: float,
) -> float:
    return cast(
        "float",
        self._backend.order_calc_margin(OrderType(order_type), symbol, volume, price),
    )


def _accountinfo_freemargincheck(
    self: _ObjectState,
    symbol: str,
    order_type: OrderType | int,
    volume: float,
    price: float,
) -> float:
    return _accountinfo_freemargin(self) - _accountinfo_margincheck(
        self, symbol, order_type, volume, price
    )


def _accountinfo_maxlotcheck(
    self: _ObjectState, symbol: str, order_type: OrderType | int, price: float
) -> float:
    spec = self._backend.symbol(symbol)
    if spec is None:
        return 0.0
    low = 0.0
    high = spec.lots_max
    step = max(spec.lots_step, 1e-12)
    free_margin = _accountinfo_freemargin(self)
    for _ in range(64):
        mid = (low + high) / 2.0
        required = _accountinfo_margincheck(self, symbol, order_type, mid, price)
        if required <= free_margin:
            low = mid
        else:
            high = mid
    steps = int((low + 1e-12) / step)
    return float(round(min(float(spec.lots_max), steps * step), 8))


def _dict_to_deal_snapshot(d: dict[str, Any]) -> DealSnapshot:
    deal_type = int(d.get("deal_type", 0))
    entry = int(d.get("entry", 0))
    t_val = d.get("time", 0)
    t_sec = epoch_seconds(t_val) if isinstance(t_val, datetime) else int(t_val or 0)
    deal_type_enum = (
        DealTypeEnum(deal_type)
        if deal_type in DealTypeEnum._value2member_map_
        else None
    )
    deal_type_desc = (
        DEAL_TYPE_DESCRIPTIONS.get(deal_type_enum, "")
        if deal_type_enum is not None
        else ""
    )
    entry_enum = (
        DealEntryEnum(entry) if entry in DealEntryEnum._value2member_map_ else None
    )
    entry_desc = (
        DEAL_ENTRY_DESCRIPTIONS.get(entry_enum, "") if entry_enum is not None else ""
    )
    return DealSnapshot(
        ticket=int(d.get("ticket", 0)),
        order=int(d.get("order", 0)),
        position_id=int(d.get("position_id", 0)),
        symbol=str(d.get("symbol", "")),
        deal_type=deal_type,
        type_description=d.get("type_description") or deal_type_desc,
        entry=entry,
        entry_description=d.get("entry_description") or entry_desc,
        volume=float(d.get("volume", 0.0)),
        price=float(d.get("price", 0.0)),
        commission=float(d.get("commission", 0.0)),
        swap=float(d.get("swap", 0.0)),
        profit=float(d.get("profit", 0.0)),
        magic=int(d.get("magic", 0)),
        comment=str(d.get("comment", "")),
        time=t_sec,
        time_msc=int(d.get("time_msc", t_sec * 1000)),
    )


def _dict_to_order_snapshot(d: dict[str, Any]) -> OrderSnapshot:
    ord_type = int(d.get("order_type", 0))
    state = int(d.get("state", 0))
    filling = int(d.get("type_filling", 0))
    ord_time = int(d.get("type_time", 0))
    t_setup = d.get("time_setup", 0)
    t_setup_sec = (
        epoch_seconds(t_setup) if isinstance(t_setup, datetime) else int(t_setup or 0)
    )
    t_done = d.get("time_done", 0)
    t_done_sec = (
        epoch_seconds(t_done) if isinstance(t_done, datetime) else int(t_done or 0)
    )
    t_exp = d.get("time_expiration", 0)
    t_exp_sec = epoch_seconds(t_exp) if isinstance(t_exp, datetime) else int(t_exp or 0)
    ord_type_enum = (
        OrderTypeEnum(ord_type)
        if ord_type in OrderTypeEnum._value2member_map_
        else None
    )
    ord_type_desc = (
        ORDER_TYPE_DESCRIPTIONS.get(ord_type_enum, "")
        if ord_type_enum is not None
        else ""
    )
    state_enum = (
        OrderStateEnum(state) if state in OrderStateEnum._value2member_map_ else None
    )
    state_desc = (
        ORDER_STATE_DESCRIPTIONS.get(state_enum, "") if state_enum is not None else ""
    )
    filling_enum = (
        OrderFillingEnum(filling)
        if filling in OrderFillingEnum._value2member_map_
        else None
    )
    filling_desc = (
        ORDER_FILLING_DESCRIPTIONS.get(filling_enum, "")
        if filling_enum is not None
        else ""
    )
    ord_time_enum = (
        OrderTimeEnum(ord_time)
        if ord_time in OrderTimeEnum._value2member_map_
        else None
    )
    ord_time_desc = (
        ORDER_TIME_DESCRIPTIONS.get(ord_time_enum, "")
        if ord_time_enum is not None
        else ""
    )
    return OrderSnapshot(
        ticket=int(d.get("ticket", 0)),
        symbol=str(d.get("symbol", "")),
        order_type=ord_type,
        type_description=d.get("type_description") or ord_type_desc,
        state=state,
        state_description=d.get("state_description") or state_desc,
        volume_initial=float(d.get("volume_initial", 0.0)),
        volume_current=float(d.get("volume_current", 0.0)),
        price_open=float(d.get("price_open", 0.0)),
        sl=float(d.get("sl", 0.0)),
        tp=float(d.get("tp", 0.0)),
        price_current=float(d.get("price_current", 0.0)),
        price_stop_limit=float(d.get("price_stop_limit", 0.0)),
        time_setup=t_setup_sec,
        time_setup_msc=int(d.get("time_setup_msc", t_setup_sec * 1000)),
        time_done=t_done_sec,
        time_done_msc=int(d.get("time_done_msc", t_done_sec * 1000)),
        time_expiration=t_exp_sec,
        type_filling=filling,
        type_filling_description=d.get("type_filling_description") or filling_desc,
        type_time=ord_time,
        type_time_description=d.get("type_time_description") or ord_time_desc,
        magic=int(d.get("magic", 0)),
        position_id=int(d.get("position_id", 0)),
        comment=str(d.get("comment", "")),
    )


def _dict_to_position_snapshot(d: dict[str, Any]) -> PositionSnapshot:
    pos_type = int(d.get("position_type", 0))
    time_val = d.get("time", 0)
    time_sec = (
        epoch_seconds(time_val)
        if isinstance(time_val, datetime)
        else int(time_val or 0)
    )
    time_up_val = d.get("time_update", 0)
    time_up_sec = (
        epoch_seconds(time_up_val)
        if isinstance(time_up_val, datetime)
        else int(time_up_val or 0)
    )
    pos_type_enum = (
        PositionType(pos_type) if pos_type in PositionType._value2member_map_ else None
    )
    pos_type_desc = (
        POSITION_TYPE_DESCRIPTIONS.get(
            pos_type_enum, "Buy" if pos_type == 0 else "Sell"
        )
        if pos_type_enum is not None
        else ("Buy" if pos_type == 0 else "Sell")
    )
    return PositionSnapshot(
        ticket=int(d.get("ticket", 0)),
        identifier=int(d.get("identifier", 0)),
        symbol=str(d.get("symbol", "")),
        position_type=pos_type,
        type_description=d.get("type_description") or pos_type_desc,
        volume=float(d.get("volume", 0.0)),
        price_open=float(d.get("price_open", 0.0)),
        price_current=float(d.get("price_current", 0.0)),
        sl=float(d.get("sl", 0.0)),
        tp=float(d.get("tp", 0.0)),
        commission=float(d.get("commission", 0.0)),
        swap=float(d.get("swap", 0.0)),
        profit=float(d.get("profit", 0.0)),
        magic=int(d.get("magic", 0)),
        comment=str(d.get("comment", "")),
        time=time_sec,
        time_msc=int(d.get("time_msc", time_sec * 1000)),
        time_update=time_up_sec,
        time_update_msc=int(d.get("time_update_msc", time_up_sec * 1000)),
    )


def _dealinfo_dealinfo(self: _ObjectState, ticket: int | None = None) -> DealSnapshot:
    if ticket is not None:
        _dealinfo_ticket(self, ticket)
    selected = _selectionbase__require(self)
    if isinstance(selected, DealSnapshot):
        return replace(selected)
    return _dict_to_deal_snapshot(record_dict(selected))


def _dealinfo_asdict(self: _ObjectState, ticket: int | None = None) -> dict[str, Any]:
    return asdict(_dealinfo_dealinfo(self, ticket))


def _dealinfo_ticket(self: _ObjectState, ticket: int | None = None) -> int:
    if ticket is not None:
        _selectionbase__select(
            self, next((d for d in self._backend.deals() if d.ticket == ticket), None)
        )
    return int(_selectionbase__value(self, "ticket"))


def _dealinfo_selectbyindex(self: _ObjectState, index: int) -> bool:
    values = self._backend.deals()
    return _selectionbase__select(
        self, values[index] if 0 <= index < len(values) else None
    )


def _dealinfo_historydealstotal(self: _ObjectState, *args: Any, **kwargs: Any) -> int:
    date_from = args[0] if len(args) > 0 else kwargs.get("date_from")
    date_to = args[1] if len(args) > 1 else kwargs.get("date_to")
    deals = self._backend.deals()
    if date_from is not None and date_to is not None:
        t_from = _to_epoch(date_from)
        t_to = _to_epoch(date_to)
        deals = [d for d in deals if t_from <= _to_epoch(d.time) <= t_to]
    return len(deals)


def _dealinfo_historydealsget(
    self: _ObjectState, *args: Any, **kwargs: Any
) -> list[dict[str, Any]]:
    date_from, date_to, symbol, group, ticket, position = _extract_history_query(
        args, kwargs
    )
    deals = list(self._backend.deals())
    if date_from is not None and date_to is not None:
        t_from, t_to = _to_epoch(date_from), _to_epoch(date_to)
        deals = [d for d in deals if t_from <= _to_epoch(d.time) <= t_to]
    if ticket is not None:
        deals = [d for d in deals if d.ticket == ticket]
    if position is not None:
        deals = [d for d in deals if d.position_id == position]
    if symbol is not None:
        deals = [d for d in deals if d.symbol == symbol]
    if group is not None:
        deals = [d for d in deals if fnmatch.fnmatch(d.symbol, group)]
    return [
        asdict(d)
        if isinstance(d, DealSnapshot)
        else asdict(_dict_to_deal_snapshot(record_dict(d)))
        for d in deals
    ]


def _historyorderinfo_historyorderinfo(
    self: _ObjectState, ticket: int | None = None
) -> HistoryOrderSnapshot:
    if ticket is not None:
        _historyorderinfo_ticket(self, ticket)
    selected = _selectionbase__require(self)
    if isinstance(selected, OrderSnapshot):
        return replace(selected)
    return _dict_to_order_snapshot(record_dict(selected))


def _historyorderinfo_asdict(
    self: _ObjectState, ticket: int | None = None
) -> dict[str, Any]:
    return asdict(_historyorderinfo_historyorderinfo(self, ticket))


def _historyorderinfo_ticket(self: _ObjectState, ticket: int | None = None) -> int:
    if ticket is not None:
        _selectionbase__select(
            self,
            next(
                (o for o in self._backend.history_orders() if o.ticket == ticket), None
            ),
        )
    return int(_selectionbase__value(self, "ticket"))


def _historyorderinfo_selectbyindex(self: _ObjectState, index: int) -> bool:
    values = self._backend.history_orders()
    return _selectionbase__select(
        self, values[index] if 0 <= index < len(values) else None
    )


def _historyorderinfo_historyorderstotal(
    self: _ObjectState, *args: Any, **kwargs: Any
) -> int:
    date_from = args[0] if len(args) > 0 else kwargs.get("date_from")
    date_to = args[1] if len(args) > 1 else kwargs.get("date_to")
    orders = self._backend.history_orders()
    if date_from is not None and date_to is not None:
        t_from = _to_epoch(date_from)
        t_to = _to_epoch(date_to)
        orders = [
            o
            for o in orders
            if t_from <= _to_epoch(o.time_done or o.time_setup) <= t_to
        ]
    return len(orders)


def _historyorderinfo_historyordersget(
    self: _ObjectState, *args: Any, **kwargs: Any
) -> list[dict[str, Any]]:
    date_from, date_to, symbol, group, ticket, position = _extract_history_query(
        args, kwargs
    )
    orders = list(self._backend.history_orders())
    if date_from is not None and date_to is not None:
        t_from, t_to = _to_epoch(date_from), _to_epoch(date_to)
        orders = [
            o
            for o in orders
            if t_from <= _to_epoch(o.time_done or o.time_setup) <= t_to
        ]
    if ticket is not None:
        orders = [o for o in orders if o.ticket == ticket]
    if position is not None:
        orders = [o for o in orders if o.position_id == position]
    if symbol is not None:
        orders = [o for o in orders if o.symbol == symbol]
    if group is not None:
        orders = [o for o in orders if fnmatch.fnmatch(o.symbol, group)]
    return [
        asdict(o)
        if isinstance(o, OrderSnapshot)
        else asdict(_dict_to_order_snapshot(record_dict(o)))
        for o in orders
    ]


def _orderinfo_orderinfo(
    self: _ObjectState, ticket: int | None = None
) -> OrderSnapshot:
    if ticket is not None:
        _orderinfo_select(self, ticket)
    selected = _selectionbase__require(self)
    if isinstance(selected, OrderSnapshot):
        return replace(selected)
    return _dict_to_order_snapshot(record_dict(selected))


def _orderinfo_asdict(self: _ObjectState, ticket: int | None = None) -> dict[str, Any]:
    return asdict(_orderinfo_orderinfo(self, ticket))


def _orderinfo_storestate(self: _ObjectState) -> None:
    _selectionbase__store(self)


def _orderinfo_checkstate(self: _ObjectState) -> bool:
    ticket = int(_selectionbase__value(self, "ticket"))
    _orderinfo_select(self, ticket)
    return _selectionbase__check(self)


def _orderinfo_select(self: _ObjectState, ticket: int) -> bool:
    return _selectionbase__select(
        self, next((o for o in self._backend.orders() if o.ticket == ticket), None)
    )


def _orderinfo_selectbyindex(self: _ObjectState, index: int) -> bool:
    values = self._backend.orders()
    return _selectionbase__select(
        self, values[index] if 0 <= index < len(values) else None
    )


def _orderinfo_orderstotal(self: _ObjectState, *args: Any) -> int:
    del args
    return len(self._backend.orders())


def _orderinfo_ordersget(
    self: _ObjectState, *args: Any, **kwargs: Any
) -> list[dict[str, Any]]:
    symbol, group, ticket = _extract_active_query(args, kwargs)
    orders = list(self._backend.orders())
    if ticket is not None:
        orders = [o for o in orders if o.ticket == ticket]
    if symbol is not None:
        orders = [o for o in orders if o.symbol == symbol]
    if group is not None:
        orders = [o for o in orders if fnmatch.fnmatch(o.symbol, group)]
    return [
        asdict(o)
        if isinstance(o, OrderSnapshot)
        else asdict(_dict_to_order_snapshot(record_dict(o)))
        for o in orders
    ]


def _positioninfo_positioninfo(
    self: _ObjectState, ticket: int | None = None
) -> PositionSnapshot:
    if ticket is not None:
        _positioninfo_selectbyticket(self, ticket)
    selected = _selectionbase__require(self)
    if isinstance(selected, PositionSnapshot):
        return replace(selected)
    return _dict_to_position_snapshot(record_dict(selected))


def _positioninfo_asdict(
    self: _ObjectState, ticket: int | None = None
) -> dict[str, Any]:
    return asdict(_positioninfo_positioninfo(self, ticket))


def _positioninfo_select(self: _ObjectState, symbol: str) -> bool:
    values = [p for p in self._backend.positions() if p.symbol == symbol]
    values.sort(key=lambda p: p.ticket)
    return _selectionbase__select(self, values[0] if values else None)


def _positioninfo_selectbyindex(self: _ObjectState, index: int) -> bool:
    values = self._backend.positions()
    return _selectionbase__select(
        self, values[index] if 0 <= index < len(values) else None
    )


def _positioninfo_selectbymagic(self: _ObjectState, symbol: str, magic: int) -> bool:
    return _selectionbase__select(
        self,
        next(
            (
                p
                for p in self._backend.positions()
                if p.symbol == symbol and p.magic == magic
            ),
            None,
        ),
    )


def _positioninfo_selectbyticket(self: _ObjectState, ticket: int) -> bool:
    return _selectionbase__select(
        self, next((p for p in self._backend.positions() if p.ticket == ticket), None)
    )


def _positioninfo_storestate(self: _ObjectState) -> None:
    _selectionbase__store(self)


def _positioninfo_checkstate(self: _ObjectState) -> bool:
    ticket = int(_selectionbase__value(self, "ticket"))
    _positioninfo_selectbyticket(self, ticket)
    return _selectionbase__check(self)


def _positioninfo_positionstotal(self: _ObjectState, *args: Any) -> int:
    del args
    return len(self._backend.positions())


def _positioninfo_positionsget(
    self: _ObjectState, *args: Any, **kwargs: Any
) -> list[dict[str, Any]]:
    symbol, group, ticket = _extract_active_query(args, kwargs)
    positions = list(self._backend.positions())
    if ticket is not None:
        positions = [p for p in positions if p.ticket == ticket]
    if symbol is not None:
        positions = [p for p in positions if p.symbol == symbol]
    if group is not None:
        positions = [p for p in positions if fnmatch.fnmatch(p.symbol, group)]
    return [
        asdict(p)
        if isinstance(p, PositionSnapshot)
        else asdict(_dict_to_position_snapshot(record_dict(p)))
        for p in positions
    ]


def _symbolinfo___init__(
    self: _ObjectState, backend: BrokerBackend, name: str = ""
) -> None:
    self._backend = backend
    self.symbol_name = name


def _symbolinfo__s(self: _ObjectState) -> Any:
    spec = self._backend.symbol(self.symbol_name)
    if spec is None:
        raise RuntimeError(f"Unknown symbol: {self.symbol_name!r}")
    return spec


def _symbolinfo__t(self: _ObjectState) -> Any:
    return self._backend.tick(self.symbol_name)


def _symbolinfo_refresh(self: _ObjectState) -> bool:
    return bool(self._backend.symbol(self.symbol_name) is not None)


def _symbolinfo_refreshrates(self: _ObjectState) -> bool:
    return bool(self._backend.tick(self.symbol_name) is not None)


def _symbolinfo_name(self: _ObjectState, value: str | None = None) -> str | bool:
    if value is not None:
        if self._backend.symbol(value) is None:
            return False
        self.symbol_name = value
    return cast("str", self.symbol_name)


def _symbolinfo_select(self: _ObjectState, value: bool | None = None) -> bool:
    if value is not None:
        return cast("bool", self._backend.select_symbol(self.symbol_name, value))
    return bool(_symbolinfo__s(self).selected)


def _symbolinfo_issynchronized(self: _ObjectState) -> bool:
    return bool(_symbolinfo__s(self).synchronized)


def _symbolinfo_normalizeprice(self: _ObjectState, price: float) -> float:
    return round(float(price), int(_symbolinfo__s(self).digits))


def _match_symbol_pattern(name: str, group: str | None) -> bool:
    if not group or group == "*":
        return True
    patterns = [p.strip() for p in group.split(",") if p.strip()]
    includes = [p for p in patterns if not p.startswith("!")]
    excludes = [p[1:] for p in patterns if p.startswith("!")]
    if includes and not any(fnmatch.fnmatch(name, p) for p in includes):
        return False
    return not any(fnmatch.fnmatch(name, p) for p in excludes)


def _symbolinfo_symbolstotal(self: _ObjectState, selected: bool = False) -> int:
    symbols_fn = getattr(self._backend, "symbols", None)
    symbols: list[SymbolSpec] = symbols_fn() if callable(symbols_fn) else []
    if selected:
        return sum(1 for s in symbols if getattr(s, "selected", True))
    return len(symbols)


def _symbolinfo_symbolsget(self: _ObjectState, group: str | None = None) -> list[str]:
    symbols_fn = getattr(self._backend, "symbols", None)
    symbols: list[SymbolSpec] = symbols_fn() if callable(symbols_fn) else []
    names = [s.name for s in symbols]
    return [name for name in names if _match_symbol_pattern(name, group)]


def _symbolinfo_symbolinfotick(
    self: _ObjectState, symbol: str | None = None
) -> dict[str, Any] | None:
    sym = symbol or self.symbol_name
    if not sym:
        return None
    tick = self._backend.tick(sym)
    if tick is None:
        return None
    time_sec = epoch_seconds(tick.time)
    time_msc = epoch_millis(tick.time)
    return {
        "time": time_sec,
        "bid": float(tick.bid),
        "ask": float(tick.ask),
        "last": float(tick.last),
        "volume": int(tick.volume),
        "time_msc": time_msc,
        "flags": 6,
        "volume_real": float(tick.volume),
    }


def _symbolinfo_symbolselect(
    self: _ObjectState, name: str | bool | None = None, enable: bool = True
) -> bool:
    if isinstance(name, bool):
        sym = self.symbol_name
        is_enabled = name
    else:
        sym = name or self.symbol_name
        is_enabled = enable
    if not sym:
        return False
    return bool(self._backend.select_symbol(sym, is_enabled))


def _symbolinfo_marketbookadd(self: _ObjectState, symbol: str | None = None) -> bool:
    sym = symbol or self.symbol_name
    if not sym:
        return False
    if self._backend.symbol(sym) is None:
        return False
    subscriptions: set[str] | None = getattr(
        self._backend, "_market_book_subscriptions", None
    )
    if subscriptions is None:
        subscriptions = set()
        self._backend._market_book_subscriptions = subscriptions
    subscriptions.add(sym)
    return True


def _symbolinfo_marketbookrelease(
    self: _ObjectState, symbol: str | None = None
) -> bool:
    sym = symbol or self.symbol_name
    if not sym:
        return False
    subscriptions: set[str] | None = getattr(
        self._backend, "_market_book_subscriptions", None
    )
    if subscriptions is not None:
        subscriptions.discard(sym)
    return True


def _symbolinfo_marketbookget(
    self: _ObjectState, symbol: str | None = None
) -> list[dict[str, Any]]:
    sym = symbol or self.symbol_name
    if not sym:
        return []
    subscriptions: set[str] | None = getattr(
        self._backend, "_market_book_subscriptions", None
    )
    if subscriptions is None or sym not in subscriptions:
        return []
    tick = self._backend.tick(sym)
    if tick is None:
        return []
    spec = self._backend.symbol(sym)
    point = float(spec.point) if spec else 0.00001
    digits = int(spec.digits) if spec else 5
    bid = float(tick.bid)
    ask = float(tick.ask)

    entries: list[dict[str, Any]] = []
    for level in (3, 2, 1):
        price = round(ask + level * point, digits)
        vol = level * 10
        entries.append(
            {
                "type": int(BookType.BOOK_TYPE_SELL),
                "price": price,
                "volume": vol,
                "volume_real": float(vol),
            }
        )
    for level in (0, 1, 2):
        price = round(bid - level * point, digits)
        vol = (level + 1) * 15
        entries.append(
            {
                "type": int(BookType.BOOK_TYPE_BUY),
                "price": price,
                "volume": vol,
                "volume_real": float(vol),
            }
        )
    return entries


def _symbolinfo_asdict(self: _ObjectState) -> dict[str, Any]:
    s = _symbolinfo__s(self)
    tick = _symbolinfo__t(self)
    point = float(s.point)
    spread = (
        round((tick.ask - tick.bid) / point)
        if tick is not None and point > 0
        else int(s.spread)
    )
    return {
        "custom": bool(s.custom),
        "chart_mode": int(s.chart_mode),
        "select": bool(s.selected),
        "visible": bool(s.visible),
        "session_deals": int(s.session_deals),
        "session_buy_orders": int(s.session_buy_orders),
        "session_sell_orders": int(s.session_sell_orders),
        "volume": int(tick.volume if tick else 0),
        "volumehigh": int(getattr(s, "volume_high", tick.volume if tick else 0)),
        "volumelow": int(getattr(s, "volume_low", tick.volume if tick else 0)),
        "time": epoch_seconds(tick.time) if tick else 0,
        "digits": int(s.digits),
        "spread": spread,
        "spread_float": bool(s.spread_float),
        "ticks_bookdepth": int(s.ticks_book_depth),
        "trade_calc_mode": int(s.trade_calc_mode),
        "trade_mode": int(s.trade_mode),
        "start_time": int(s.start_time),
        "expiration_time": int(s.expiration_time),
        "trade_stops_level": int(s.stops_level),
        "trade_freeze_level": int(s.freeze_level),
        "trade_exemode": int(s.trade_execution),
        "swap_mode": int(s.swap_mode),
        "swap_rollover3days": int(s.swap_rollover3days),
        "margin_hedged_use_leg": bool(s.margin_hedged_use_leg),
        "expiration_mode": int(s.expiration_mode),
        "filling_mode": int(s.filling_mode),
        "order_mode": int(s.order_mode),
        "order_gtc_mode": int(s.order_gtc_mode),
        "option_mode": int(s.option_mode),
        "option_right": int(s.option_right),
        "bid": float(tick.bid if tick else 0.0),
        "bidhigh": float(getattr(s, "bid_high", tick.bid if tick else 0.0)),
        "bidlow": float(getattr(s, "bid_low", tick.bid if tick else 0.0)),
        "ask": float(tick.ask if tick else 0.0),
        "askhigh": float(getattr(s, "ask_high", tick.ask if tick else 0.0)),
        "asklow": float(getattr(s, "ask_low", tick.ask if tick else 0.0)),
        "last": float(tick.last if tick else 0.0),
        "lasthigh": float(getattr(s, "last_high", tick.last if tick else 0.0)),
        "lastlow": float(getattr(s, "last_low", tick.last if tick else 0.0)),
        "volume_real": float(s.volume_real),
        "volumehigh_real": float(s.volumehigh_real),
        "volumelow_real": float(s.volumelow_real),
        "option_strike": float(s.option_strike),
        "point": point,
        "trade_tick_value": float(s.tick_value),
        "trade_tick_value_profit": float(s.tick_value_profit),
        "trade_tick_value_loss": float(s.tick_value_loss),
        "trade_tick_size": float(s.tick_size),
        "trade_contract_size": float(s.contract_size),
        "trade_accrued_interest": float(s.trade_accrued_interest),
        "trade_face_value": float(s.trade_face_value),
        "trade_liquidity_rate": float(s.trade_liquidity_rate),
        "volume_min": float(s.lots_min),
        "volume_max": float(s.lots_max),
        "volume_step": float(s.lots_step),
        "volume_limit": float(s.lots_limit),
        "swap_long": float(s.swap_long),
        "swap_short": float(s.swap_short),
        "margin_initial": float(s.margin_initial),
        "margin_maintenance": float(s.margin_maintenance),
        "session_volume": float(s.session_volume),
        "session_turnover": float(s.session_turnover),
        "session_interest": float(s.session_interest),
        "session_buy_orders_volume": float(s.session_buy_orders_volume),
        "session_sell_orders_volume": float(s.session_sell_orders_volume),
        "session_open": float(s.session_open),
        "session_close": float(s.session_close),
        "session_aw": float(s.session_aw),
        "session_price_settlement": float(s.session_price_settlement),
        "session_price_limit_min": float(s.session_price_limit_min),
        "session_price_limit_max": float(s.session_price_limit_max),
        "margin_hedged": float(s.margin_hedged),
        "price_change": float(s.price_change),
        "price_volatility": float(s.price_volatility),
        "price_theoretical": float(s.price_theoretical),
        "price_greeks_delta": float(s.price_greeks_delta),
        "price_greeks_theta": float(s.price_greeks_theta),
        "price_greeks_gamma": float(s.price_greeks_gamma),
        "price_greeks_vega": float(s.price_greeks_vega),
        "price_greeks_rho": float(s.price_greeks_rho),
        "price_greeks_omega": float(s.price_greeks_omega),
        "price_sensitivity": float(s.price_sensitivity),
        "basis": str(s.basis),
        "category": str(s.category),
        "currency_base": str(s.currency_base),
        "currency_profit": str(s.currency_profit),
        "currency_margin": str(s.currency_margin),
        "bank": str(s.bank),
        "description": str(s.description),
        "exchange": str(s.exchange),
        "formula": str(s.formula),
        "isin": str(s.isin),
        "name": str(s.name),
        "page": str(s.page),
        "path": str(s.path),
    }


def _symbolinfo_symbolinfo(
    self: _ObjectState, symbol: str | None = None
) -> SymbolSnapshot:
    if symbol:
        self.symbol_name = symbol
    d = _symbolinfo_asdict(self)
    s = _symbolinfo__s(self)
    calc_mode = (
        SymbolCalcMode(s.trade_calc_mode)
        if s.trade_calc_mode in SymbolCalcMode._value2member_map_
        else None
    )
    trade_mode = (
        SymbolTradeMode(s.trade_mode)
        if s.trade_mode in SymbolTradeMode._value2member_map_
        else None
    )
    trade_ex = (
        SymbolTradeExecution(s.trade_execution)
        if s.trade_execution in SymbolTradeExecution._value2member_map_
        else None
    )
    swap_mode = (
        SymbolSwapMode(s.swap_mode)
        if s.swap_mode in SymbolSwapMode._value2member_map_
        else None
    )
    return SymbolSnapshot(
        trade_calc_mode_description=(
            s.trade_calc_mode_description
            or (calc_mode.name.replace("_", " ").title() if calc_mode else "")
        ),
        trade_mode_description=(
            s.trade_mode_description
            or (trade_mode.name.replace("_", " ").title() if trade_mode else "")
        ),
        trade_execution_description=(
            s.trade_execution_description
            or (trade_ex.name.replace("_", " ").title() if trade_ex else "")
        ),
        swap_mode_description=(
            s.swap_mode_description
            or (swap_mode.name.replace("_", " ").title() if swap_mode else "")
        ),
        swap_rollover3days_description=str(s.swap_rollover3days),
        margin_long=float(s.margin_long),
        margin_short=float(s.margin_short),
        margin_limit=float(s.margin_limit),
        margin_stop=float(s.margin_stop),
        margin_stop_limit=float(s.margin_stop_limit),
        trade_time_flags=int(s.trade_time_flags),
        trade_fill_flags=int(s.trade_fill_flags),
        **d,
    )


def _terminalinfo___init__(self: _ObjectState, backend: BrokerBackend) -> None:
    self._backend = backend


def _terminalinfo_terminalinfo(self: _ObjectState) -> TerminalSnapshot:
    terminal = self._backend.terminal()
    if is_dataclass(terminal) and not isinstance(terminal, type):
        return cast("TerminalSnapshot", terminal)
    if isinstance(terminal, dict):
        return TerminalSnapshot(**terminal)
    raise TypeError(f"unexpected terminal snapshot type: {type(terminal).__name__}")


def _trade___init__(self: _ObjectState, backend: BrokerBackend) -> None:
    self._backend = backend
    self._log_level = 0
    self._magic = 0
    self._deviation = 10
    self._filling = OrderFilling.FOK
    self._async = False
    self._last_request = TradeRequest(action=TradeAction.DEAL)
    self._last_result = TradeResult()
    self._last_check = TradeCheckResult()


def _result_to_dict(res: TradeResult) -> dict[str, Any]:
    return {
        "retcode": res.retcode,
        "deal": res.deal,
        "order": res.order,
        "volume": res.volume,
        "price": res.price,
        "bid": res.bid,
        "ask": res.ask,
        "comment": res.comment,
        "request_id": res.request_id,
        "retcode_external": res.retcode_external,
    }


def _check_result_to_dict(chk: TradeCheckResult) -> dict[str, Any]:
    return {
        "retcode": chk.retcode,
        "balance": chk.balance,
        "equity": chk.equity,
        "profit": chk.profit,
        "margin": chk.margin,
        "margin_free": chk.margin_free,
        "margin_level": chk.margin_level,
        "comment": chk.comment,
    }


def _request_to_dict(req: TradeRequest) -> dict[str, Any]:
    return {
        "action": int(req.action),
        "symbol": req.symbol,
        "volume": req.volume,
        "order_type": int(req.order_type),
        "price": req.price,
        "stoplimit": req.stoplimit,
        "sl": req.sl,
        "tp": req.tp,
        "deviation": req.deviation,
        "magic": req.magic,
        "order": req.order,
        "position": req.position,
        "position_by": req.position_by,
        "type_filling": int(req.type_filling),
        "type_time": int(req.type_time),
        "expiration": int(req.expiration.timestamp()) if req.expiration else None,
        "comment": req.comment,
    }


def _parse_trade_request(self: _ObjectState, data: dict[str, Any]) -> TradeRequest:
    action_val = data.get("action", TradeAction.DEAL)
    action = (
        TradeAction[action_val.removeprefix("TRADE_ACTION_")]
        if isinstance(action_val, str)
        else TradeAction(action_val)
    )
    type_val = data.get("order_type", data.get("type", OrderType.BUY))
    order_type = (
        OrderType[type_val.removeprefix("ORDER_TYPE_")]
        if isinstance(type_val, str)
        else OrderType(type_val)
    )
    fill_raw = data.get("type_filling", data.get("filling", 0))
    fill_val = fill_raw or (self._filling or OrderFilling.FOK)
    filling = (
        OrderFilling[fill_val.removeprefix("ORDER_FILLING_")]
        if isinstance(fill_val, str)
        else OrderFilling(fill_val)
    )
    time_val = data.get("type_time", data.get("time_type", OrderTime.GTC))
    time_type = (
        OrderTime[time_val.removeprefix("ORDER_TIME_")]
        if isinstance(time_val, str)
        else OrderTime(time_val)
    )
    symbol = str(data.get("symbol", self.symbol_name or ""))
    price = float(data.get("price", 0.0))
    if price == 0.0 and action == TradeAction.DEAL and symbol:
        tick = self._backend.tick(symbol)
        if tick is not None:
            price = tick.ask if order_type == OrderType.BUY else tick.bid

    exp = data.get("expiration")
    if isinstance(exp, (int, float)):
        exp_dt = datetime.fromtimestamp(exp, tz=UTC) if exp else None
    elif isinstance(exp, datetime):
        exp_dt = exp
    else:
        exp_dt = None

    magic_req = int(data.get("magic", 0))
    magic = magic_req if magic_req != 0 else (self._magic or 0)
    dev_req = int(data.get("deviation", 0))
    deviation = dev_req if dev_req != 0 else (self._deviation or 10)

    return TradeRequest(
        action=action,
        symbol=symbol,
        volume=float(data.get("volume", 0.0)),
        order_type=order_type,
        price=price,
        stoplimit=float(data.get("stoplimit", 0.0)),
        sl=float(data.get("sl", 0.0)),
        tp=float(data.get("tp", 0.0)),
        deviation=deviation,
        magic=magic,
        order=int(data.get("order", 0)),
        position=int(data.get("position", 0)),
        position_by=int(data.get("position_by", 0)),
        type_filling=filling,
        type_time=time_type,
        expiration=exp_dt,
        comment=str(data.get("comment", "")),
    )


def _trade_ordersend(self: _ObjectState, data: dict[str, Any]) -> dict[str, Any]:
    req = _parse_trade_request(self, data)
    self._last_request = replace(req)
    self._last_check = self._backend.order_check(req)
    if self._last_check.retcode not in {
        0,
        int(TradeRetcode.DONE),
        int(TradeRetcode.PLACED),
        int(TradeRetcode.DONE_PARTIAL),
    }:
        self._last_result = TradeResult(
            retcode=self._last_check.retcode, comment=self._last_check.comment
        )
    else:
        self._last_result = self._backend.order_send(req)
    return _result_to_dict(self._last_result)


def _trade_ordercheck(self: _ObjectState, data: dict[str, Any]) -> dict[str, Any]:
    req = _parse_trade_request(self, data)
    self._last_request = replace(req)
    self._last_check = self._backend.order_check(req)
    return _check_result_to_dict(self._last_check)


def _trade_loglevel(self: _ObjectState, log_level: int) -> bool:
    self._log_level = log_level
    return True


def _trade_setexpertmagicnumber(self: _ObjectState, magic: int) -> bool:
    self._magic = magic
    return True


def _trade_setdeviationinpoints(self: _ObjectState, deviation: int) -> bool:
    self._deviation = deviation
    return True


def _trade_settypefilling(self: _ObjectState, filling: OrderFilling | int) -> bool:
    self._filling = OrderFilling(filling)
    return True


def _trade_settypefillingbysymbol(self: _ObjectState, symbol: str) -> bool:
    spec = self._backend.symbol(symbol)
    if spec is None:
        return False
    flags = int(spec.trade_fill_flags)
    if flags & 1:
        self._filling = OrderFilling.FOK
    elif flags & 2:
        self._filling = OrderFilling.IOC
    else:
        self._filling = OrderFilling.FOK
    return True


def _trade_setasyncmode(self: _ObjectState, mode: bool) -> bool:
    self._async = mode
    return True


def _trade_setmarginmode(self: _ObjectState) -> bool:
    _ = self._backend.account().margin_mode
    return True


def _trade_request(self: _ObjectState) -> dict[str, Any]:
    return _request_to_dict(self._last_request)


def _trade_result(self: _ObjectState) -> dict[str, Any]:
    return _result_to_dict(self._last_result)


def _trade_checkresult(self: _ObjectState) -> dict[str, Any]:
    return _check_result_to_dict(self._last_check)


def _trade_printrequest(self: _ObjectState) -> bool:
    del self
    logger.info("FR-SIMULATION-DISPATCH: native print operation")
    return True


def _trade_printresult(self: _ObjectState) -> bool:
    del self
    logger.info("FR-SIMULATION-DISPATCH: native print operation")
    return True


def _trade_formatrequest(self: _ObjectState) -> str:
    return json.dumps(asdict(self._last_request), default=str, sort_keys=True)


def _trade_formatrequestresult(self: _ObjectState) -> str:
    return json.dumps(
        {
            "request": asdict(self._last_request),
            "check": asdict(self._last_check),
            "result": asdict(self._last_result),
        },
        default=str,
        sort_keys=True,
    )


HANDLERS: dict[str, dict[str, Callable[..., Any]]] = {
    "AccountInfo": {
        "AccountInfo": _accountinfo_accountinfo,
        "OrderProfitCheck": _accountinfo_orderprofitcheck,
        "MarginCheck": _accountinfo_margincheck,
        "FreeMarginCheck": _accountinfo_freemargincheck,
        "MaxLotCheck": _accountinfo_maxlotcheck,
    },
    "DealInfo": {
        "Ticket": _dealinfo_ticket,
        "SelectByIndex": _dealinfo_selectbyindex,
        "HistoryDealsTotal": _dealinfo_historydealstotal,
        "HistoryDealsGet": _dealinfo_historydealsget,
        "DealInfo": _dealinfo_dealinfo,
        "as_dict": _dealinfo_asdict,
    },
    "HistoryOrderInfo": {
        "Ticket": _historyorderinfo_ticket,
        "SelectByIndex": _historyorderinfo_selectbyindex,
        "HistoryOrdersTotal": _historyorderinfo_historyorderstotal,
        "HistoryOrdersGet": _historyorderinfo_historyordersget,
        "HistoryOrderInfo": _historyorderinfo_historyorderinfo,
        "as_dict": _historyorderinfo_asdict,
    },
    "OrderInfo": {
        "StoreState": _orderinfo_storestate,
        "CheckState": _orderinfo_checkstate,
        "Select": _orderinfo_select,
        "SelectByIndex": _orderinfo_selectbyindex,
        "OrdersTotal": _orderinfo_orderstotal,
        "OrdersGet": _orderinfo_ordersget,
        "OrderInfo": _orderinfo_orderinfo,
        "as_dict": _orderinfo_asdict,
    },
    "PositionInfo": {
        "Select": _positioninfo_select,
        "SelectByIndex": _positioninfo_selectbyindex,
        "SelectByMagic": _positioninfo_selectbymagic,
        "SelectByTicket": _positioninfo_selectbyticket,
        "StoreState": _positioninfo_storestate,
        "CheckState": _positioninfo_checkstate,
        "PositionsTotal": _positioninfo_positionstotal,
        "PositionsGet": _positioninfo_positionsget,
        "PositionInfo": _positioninfo_positioninfo,
        "as_dict": _positioninfo_asdict,
    },
    "SymbolInfo": {
        "Refresh": _symbolinfo_refresh,
        "RefreshRates": _symbolinfo_refreshrates,
        "Name": _symbolinfo_name,
        "Select": _symbolinfo_select,
        "IsSynchronized": _symbolinfo_issynchronized,
        "NormalizePrice": _symbolinfo_normalizeprice,
        "SymbolsTotal": _symbolinfo_symbolstotal,
        "SymbolsGet": _symbolinfo_symbolsget,
        "SymbolInfoTick": _symbolinfo_symbolinfotick,
        "SymbolSelect": _symbolinfo_symbolselect,
        "MarketBookAdd": _symbolinfo_marketbookadd,
        "MarketBookGet": _symbolinfo_marketbookget,
        "MarketBookRelease": _symbolinfo_marketbookrelease,
        "SymbolInfo": _symbolinfo_symbolinfo,
        "as_dict": _symbolinfo_asdict,
    },
    "TerminalInfo": {
        "TerminalInfo": _terminalinfo_terminalinfo,
    },
    "Trade": {
        "LogLevel": _trade_loglevel,
        "SetExpertMagicNumber": _trade_setexpertmagicnumber,
        "SetDeviationInPoints": _trade_setdeviationinpoints,
        "SetTypeFilling": _trade_settypefilling,
        "SetTypeFillingBySymbol": _trade_settypefillingbysymbol,
        "SetAsyncMode": _trade_setasyncmode,
        "SetMarginMode": _trade_setmarginmode,
        "OrderSend": _trade_ordersend,
        "OrderCheck": _trade_ordercheck,
        "Request": _trade_request,
        "Result": _trade_result,
        "CheckResult": _trade_checkresult,
        "PrintRequest": _trade_printrequest,
        "PrintResult": _trade_printresult,
        "FormatRequest": _trade_formatrequest,
        "FormatRequestResult": _trade_formatrequestresult,
    },
}
INITIALIZERS: dict[str, Callable[..., Any]] = {
    "AccountInfo": _accountinfo___init__,
    "SymbolInfo": _symbolinfo___init__,
    "TerminalInfo": _terminalinfo___init__,
    "Trade": _trade___init__,
}
SCOPES: dict[str, str] = {
    "AccountInfo": "",
    "DealInfo": "deal",
    "HistoryOrderInfo": "history_order",
    "OrderInfo": "order",
    "PositionInfo": "position",
    "SymbolInfo": "",
    "TerminalInfo": "",
    "Trade": "",
}


def new_state(class_name: str, model: Any) -> _ObjectState:
    """Create one local object's independent mutable state."""
    state = _ObjectState()
    state.scope = SCOPES[class_name]
    init = INITIALIZERS.get(class_name)
    if init is None:
        _selectionbase___init__(state, model)
    else:
        init(state, model)
    return state


def execute(
    state: _ObjectState, class_name: str, method_name: str, args: list[Any]
) -> Any:
    """Bind arguments before executing a bounded local operation."""
    logger.debug(
        "FR-SIMULATION-DISPATCH: executing local operation",
        extra={"class_name": class_name, "method_name": method_name},
    )
    fn = HANDLERS.get(class_name, {}).get(method_name)
    if fn is None:
        raise BridgeError(
            "unsupported simulated operation", code="UNSUPPORTED_OPERATION"
        )
    try:
        bound = signature(fn).bind(state, *args)
    except TypeError as exc:
        raise BridgeError(
            "invalid simulated operation arguments", code="INVALID_ARGUMENTS"
        ) from exc
    expiration = bound.arguments.get("expiration")
    if isinstance(expiration, int):
        bound.arguments["expiration"] = (
            datetime.fromtimestamp(expiration, tz=UTC) if expiration else None
        )
    enum_arguments = {
        "order_type": (OrderType, "ORDER_TYPE_"),
        "type_time": (OrderTime, "ORDER_TIME_"),
        "filling": (OrderFilling, "ORDER_FILLING_"),
    }
    for name, (enum, prefix) in enum_arguments.items():
        value = bound.arguments.get(name)
        if isinstance(value, str):
            bound.arguments[name] = enum[value.removeprefix(prefix)]
    return fn(*bound.args, **bound.kwargs)


def prepare_args(
    state: _ObjectState, model: Any, class_name: str, method_name: str, args: list[Any]
) -> list[Any]:
    """Validate local execution without fabricating missing values."""
    del state, model
    if class_name == "Trade" and method_name == "SetAsyncMode" and args and args[0]:
        raise BridgeError(
            "local model does not support queued asynchronous trade execution",
            code="UNSUPPORTED_OPERATION",
        )
    return args
