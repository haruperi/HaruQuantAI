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
from app.services.brokers.contracts import (
    DEAL_ENTRY_DESCRIPTIONS,
    DEAL_TYPE_DESCRIPTIONS,
    ORDER_FILLING_DESCRIPTIONS,
    ORDER_STATE_DESCRIPTIONS,
    ORDER_TIME_DESCRIPTIONS,
    ORDER_TYPE_DESCRIPTIONS,
    POSITION_TYPE_DESCRIPTIONS,
    AccountTradeMode,
    BookType,
    BridgeError,
    BrokerBackend,
    MarginMode,
    OrderFilling,
    OrderTime,
    OrderType,
    PositionType,
    StopoutMode,
    SymbolCalcMode,
    SymbolSpec,
    SymbolSwapMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    TradeAction,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradeRetcode,
    epoch_millis,
    epoch_seconds,
)
from app.services.brokers.contracts import DealEntry as DealEntryEnum
from app.services.brokers.contracts import DealType as DealTypeEnum
from app.services.brokers.contracts import OrderFilling as OrderFillingEnum
from app.services.brokers.contracts import OrderState as OrderStateEnum
from app.services.brokers.contracts import OrderTime as OrderTimeEnum
from app.services.brokers.contracts import OrderType as OrderTypeEnum
from app.services.brokers.contracts import PositionType as PositionTypeEnum

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


def _accountinfo_orderprofitcheck(  # noqa: PLR0917 -- native compatibility signature
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


def _dealinfo_order(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "order"))


def _dealinfo_time(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time", None))


def _dealinfo_timemsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time", None))


def _dealinfo_dealtype(self: _ObjectState) -> DealTypeEnum:
    return DealTypeEnum(_selectionbase__value(self, "deal_type"))


def _dealinfo_typedescription(self: _ObjectState) -> str:
    return DEAL_TYPE_DESCRIPTIONS.get(
        _dealinfo_dealtype(self), _dealinfo_dealtype(self).name
    )


def _dealinfo_entry(self: _ObjectState) -> DealEntryEnum:
    return DealEntryEnum(_selectionbase__value(self, "entry"))


def _dealinfo_entrydescription(self: _ObjectState) -> str:
    return DEAL_ENTRY_DESCRIPTIONS.get(
        _dealinfo_entry(self), _dealinfo_entry(self).name
    )


def _dealinfo_magic(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "magic"))


def _dealinfo_positionid(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "position_id"))


def _dealinfo_volume(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "volume"))


def _dealinfo_price(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price"))


def _dealinfo_commision(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "commission"))


def _dealinfo_commission(self: _ObjectState) -> float:
    """Alias matching the actual CDealInfo method signature/source spelling."""
    return _dealinfo_commision(self)


def _dealinfo_swap(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "swap"))


def _dealinfo_profit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "profit"))


def _dealinfo_symbol(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "symbol", ""))


def _dealinfo_comment(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "comment", ""))


def _dealinfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    return int(_selectionbase__info(self, property_id) or 0)


def _dealinfo_infodouble(self: _ObjectState, property_id: int | str) -> float:
    return float(_selectionbase__info(self, property_id) or 0.0)


def _dealinfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    return str(_selectionbase__info(self, property_id) or "")


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


def _historyorderinfo_timesetup(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_setup", None))


def _historyorderinfo_timesetupmsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time_setup", None))


def _historyorderinfo_ordertype(self: _ObjectState) -> OrderTypeEnum:
    return OrderTypeEnum(_selectionbase__value(self, "order_type"))


def _historyorderinfo_typedescription(self: _ObjectState) -> str:
    return ORDER_TYPE_DESCRIPTIONS.get(
        _historyorderinfo_ordertype(self), _historyorderinfo_ordertype(self).name
    )


def _historyorderinfo_state(self: _ObjectState) -> OrderStateEnum:
    return OrderStateEnum(_selectionbase__value(self, "state"))


def _historyorderinfo_statedescription(self: _ObjectState) -> str:
    return ORDER_STATE_DESCRIPTIONS.get(
        _historyorderinfo_state(self), _historyorderinfo_state(self).name
    )


def _historyorderinfo_timeexpiration(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_expiration", None))


def _historyorderinfo_timedone(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_done", None))


def _historyorderinfo_timedonemsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time_done", None))


def _historyorderinfo_typefilling(self: _ObjectState) -> OrderFillingEnum:
    return OrderFillingEnum(_selectionbase__value(self, "type_filling"))


def _historyorderinfo_typefillingdescription(self: _ObjectState) -> str:
    return ORDER_FILLING_DESCRIPTIONS.get(
        _historyorderinfo_typefilling(self), _historyorderinfo_typefilling(self).name
    )


def _historyorderinfo_typetime(self: _ObjectState) -> OrderTimeEnum:
    return OrderTimeEnum(_selectionbase__value(self, "type_time"))


def _historyorderinfo_typetimedescription(self: _ObjectState) -> str:
    return ORDER_TIME_DESCRIPTIONS.get(
        _historyorderinfo_typetime(self), _historyorderinfo_typetime(self).name
    )


def _historyorderinfo_magic(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "magic"))


def _historyorderinfo_positionid(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "position_id"))


def _historyorderinfo_volumeinitial(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "volume_initial"))


def _historyorderinfo_volumecurrent(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "volume_current"))


def _historyorderinfo_priceopen(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_open"))


def _historyorderinfo_stoploss(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "sl"))


def _historyorderinfo_takeprofit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "tp"))


def _historyorderinfo_pricecurrent(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_current"))


def _historyorderinfo_pricestoplimit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_stop_limit"))


def _historyorderinfo_symbol(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "symbol", ""))


def _historyorderinfo_comment(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "comment", ""))


def _historyorderinfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    return int(_selectionbase__info(self, property_id) or 0)


def _historyorderinfo_infodouble(self: _ObjectState, property_id: int | str) -> float:
    return float(_selectionbase__info(self, property_id) or 0.0)


def _historyorderinfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    return str(_selectionbase__info(self, property_id) or "")


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


def _orderinfo_ticket(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "ticket"))


def _orderinfo_timesetup(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_setup", None))


def _orderinfo_timesetupmsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time_setup", None))


def _orderinfo_ordertype(self: _ObjectState) -> OrderTypeEnum:
    return OrderTypeEnum(_selectionbase__value(self, "order_type"))


def _orderinfo_typedescription(self: _ObjectState) -> str:
    return ORDER_TYPE_DESCRIPTIONS.get(
        _orderinfo_ordertype(self), _orderinfo_ordertype(self).name
    )


def _orderinfo_state(self: _ObjectState) -> OrderStateEnum:
    return OrderStateEnum(_selectionbase__value(self, "state"))


def _orderinfo_statedescription(self: _ObjectState) -> str:
    return ORDER_STATE_DESCRIPTIONS.get(
        _orderinfo_state(self), _orderinfo_state(self).name
    )


def _orderinfo_timeexpiration(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_expiration", None))


def _orderinfo_timedone(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_done", None))


def _orderinfo_timedonemsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time_done", None))


def _orderinfo_typefilling(self: _ObjectState) -> OrderFillingEnum:
    return OrderFillingEnum(_selectionbase__value(self, "type_filling"))


def _orderinfo_typefillingdescription(self: _ObjectState) -> str:
    return ORDER_FILLING_DESCRIPTIONS.get(
        _orderinfo_typefilling(self), _orderinfo_typefilling(self).name
    )


def _orderinfo_typetime(self: _ObjectState) -> OrderTimeEnum:
    return OrderTimeEnum(_selectionbase__value(self, "type_time"))


def _orderinfo_typetimedescription(self: _ObjectState) -> str:
    return ORDER_TIME_DESCRIPTIONS.get(
        _orderinfo_typetime(self), _orderinfo_typetime(self).name
    )


def _orderinfo_magic(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "magic"))


def _orderinfo_positionid(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "position_id"))


def _orderinfo_volumeinitial(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "volume_initial"))


def _orderinfo_volumecurrent(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "volume_current"))


def _orderinfo_priceopen(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_open"))


def _orderinfo_stoploss(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "sl"))


def _orderinfo_takeprofit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "tp"))


def _orderinfo_pricecurrent(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_current"))


def _orderinfo_pricestoplimit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_stop_limit"))


def _orderinfo_symbol(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "symbol", ""))


def _orderinfo_comment(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "comment", ""))


def _orderinfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    value = _selectionbase__info(self, property_id)
    return int(value or 0)


def _orderinfo_infodouble(self: _ObjectState, property_id: int | str) -> float:
    value = _selectionbase__info(self, property_id)
    return float(value or 0.0)


def _orderinfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    value = _selectionbase__info(self, property_id)
    return str(value or "")


def _orderinfo_storestate(self: _ObjectState) -> None:
    _selectionbase__store(self)


def _orderinfo_checkstate(self: _ObjectState) -> bool:
    ticket = _orderinfo_ticket(self)
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


def _positioninfo_time(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time", None))


def _positioninfo_timemsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time", None))


def _positioninfo_timeupdate(self: _ObjectState) -> int:
    return epoch_seconds(_selectionbase__value(self, "time_update", None))


def _positioninfo_timeupdatemsc(self: _ObjectState) -> int:
    return epoch_millis(_selectionbase__value(self, "time_update", None))


def _positioninfo_positiontype(self: _ObjectState) -> PositionTypeEnum:
    return PositionTypeEnum(_selectionbase__value(self, "position_type"))


def _positioninfo_typedescription(self: _ObjectState) -> str:
    return POSITION_TYPE_DESCRIPTIONS.get(
        _positioninfo_positiontype(self), _positioninfo_positiontype(self).name
    )


def _positioninfo_magic(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "magic"))


def _positioninfo_identifier(self: _ObjectState) -> int:
    return int(_selectionbase__value(self, "identifier"))


def _positioninfo_volume(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "volume"))


def _positioninfo_priceopen(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_open"))


def _positioninfo_stoploss(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "sl"))


def _positioninfo_takeprofit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "tp"))


def _positioninfo_pricecurrent(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "price_current"))


def _positioninfo_commission(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "commission"))


def _positioninfo_swap(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "swap"))


def _positioninfo_profit(self: _ObjectState) -> float:
    return float(_selectionbase__value(self, "profit"))


def _positioninfo_symbol(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "symbol", ""))


def _positioninfo_comment(self: _ObjectState) -> str:
    return str(_selectionbase__value(self, "comment", ""))


def _positioninfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    return int(_selectionbase__info(self, property_id) or 0)


def _positioninfo_infodouble(self: _ObjectState, property_id: int | str) -> float:
    return float(_selectionbase__info(self, property_id) or 0.0)


def _positioninfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    return str(_selectionbase__info(self, property_id) or "")


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


def _symbolinfo_volume(self: _ObjectState) -> float:
    tick = _symbolinfo__t(self)
    return float(tick.volume if tick else 0.0)


def _symbolinfo_volumehigh(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "volume_high", self.symbol_name)
    return float(value if value is not None else _symbolinfo_volume(self))


def _symbolinfo_volumelow(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "volume_low", self.symbol_name)
    return float(value if value is not None else _symbolinfo_volume(self))


def _symbolinfo_time(self: _ObjectState) -> int:
    tick = _symbolinfo__t(self)
    return epoch_seconds(tick.time) if tick else 0


def _symbolinfo_spread(self: _ObjectState) -> int:
    tick = _symbolinfo__t(self)
    if tick is not None and _symbolinfo_point(self) > 0:
        spread: float = (tick.ask - tick.bid) / _symbolinfo_point(self)
        return round(spread)
    return int(_symbolinfo__s(self).spread)


def _symbolinfo_spreadfloat(self: _ObjectState) -> bool:
    return bool(_symbolinfo__s(self).spread_float)


def _symbolinfo_ticksbookdepth(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).ticks_book_depth)


def _symbolinfo_stopslevel(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).stops_level)


def _symbolinfo_freezelevel(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).freeze_level)


def _symbolinfo_bid(self: _ObjectState) -> float:
    tick = _symbolinfo__t(self)
    return float(tick.bid if tick else 0.0)


def _symbolinfo_bidhigh(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "bid_high", self.symbol_name)
    return float(value if value is not None else _symbolinfo_bid(self))


def _symbolinfo_bidlow(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "bid_low", self.symbol_name)
    return float(value if value is not None else _symbolinfo_bid(self))


def _symbolinfo_ask(self: _ObjectState) -> float:
    tick = _symbolinfo__t(self)
    return float(tick.ask if tick else 0.0)


def _symbolinfo_askhigh(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "ask_high", self.symbol_name)
    return float(value if value is not None else _symbolinfo_ask(self))


def _symbolinfo_asklow(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "ask_low", self.symbol_name)
    return float(value if value is not None else _symbolinfo_ask(self))


def _symbolinfo_last(self: _ObjectState) -> float:
    tick = _symbolinfo__t(self)
    return float(tick.last if tick else 0.0)


def _symbolinfo_lasthigh(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "last_high", self.symbol_name)
    return float(value if value is not None else _symbolinfo_last(self))


def _symbolinfo_lastlow(self: _ObjectState) -> float:
    value = self._backend.info_value("symbol", "last_low", self.symbol_name)
    return float(value if value is not None else _symbolinfo_last(self))


def _symbolinfo_tradecalcmode(self: _ObjectState) -> SymbolCalcMode:
    return SymbolCalcMode(_symbolinfo__s(self).trade_calc_mode)


def _symbolinfo_tradecalcmodedescription(self: _ObjectState) -> str:
    return _symbolinfo_tradecalcmode(self).name.replace("_", " ").title()


def _symbolinfo_trademode(self: _ObjectState) -> SymbolTradeMode:
    return SymbolTradeMode(_symbolinfo__s(self).trade_mode)


def _symbolinfo_trademodedescription(self: _ObjectState) -> str:
    return _symbolinfo_trademode(self).name.replace("_", " ").title()


def _symbolinfo_tradeexecution(self: _ObjectState) -> SymbolTradeExecution:
    return SymbolTradeExecution(_symbolinfo__s(self).trade_execution)


def _symbolinfo_tradeexecutiondescription(self: _ObjectState) -> str:
    return _symbolinfo_tradeexecution(self).name.replace("_", " ").title()


def _symbolinfo_swapmode(self: _ObjectState) -> SymbolSwapMode:
    return SymbolSwapMode(_symbolinfo__s(self).swap_mode)


def _symbolinfo_swapmodedescription(self: _ObjectState) -> str:
    return _symbolinfo_swapmode(self).name.replace("_", " ").title()


def _symbolinfo_swaprollover3days(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).swap_rollover3days)


def _symbolinfo_swaprollover3daysdescription(self: _ObjectState) -> str:
    days = (
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    )
    value = _symbolinfo_swaprollover3days(self)
    return days[value] if 0 <= value < len(days) else str(value)


def _symbolinfo_margininitial(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_initial)


def _symbolinfo_marginmaintenance(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_maintenance)


def _symbolinfo_marginlong(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_long)


def _symbolinfo_marginshort(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_short)


def _symbolinfo_marginlimit(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_limit)


def _symbolinfo_marginstop(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_stop)


def _symbolinfo_marginstoplimit(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_stop_limit)


def _symbolinfo_tradetimeflags(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).trade_time_flags)


def _symbolinfo_tradefillflags(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).trade_fill_flags)


def _symbolinfo_digits(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).digits)


def _symbolinfo_point(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).point)


def _symbolinfo_tickvalue(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).tick_value)


def _symbolinfo_tickvalueprofit(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).tick_value_profit)


def _symbolinfo_tickvalueloss(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).tick_value_loss)


def _symbolinfo_ticksize(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).tick_size)


def _symbolinfo_contractsize(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).contract_size)


def _symbolinfo_lotsmin(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).lots_min)


def _symbolinfo_lotsmax(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).lots_max)


def _symbolinfo_lotsstep(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).lots_step)


def _symbolinfo_lotslimit(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).lots_limit)


def _symbolinfo_swaplong(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).swap_long)


def _symbolinfo_swapshort(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).swap_short)


def _symbolinfo_currencybase(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).currency_base)


def _symbolinfo_currencyprofit(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).currency_profit)


def _symbolinfo_currencymargin(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).currency_margin)


def _symbolinfo_bank(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).bank)


def _symbolinfo_description(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).description)


def _symbolinfo_path(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).path)


def _symbolinfo_sessiondeals(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).session_deals)


def _symbolinfo_sessionbuyorders(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).session_buy_orders)


def _symbolinfo_sessionsellorders(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).session_sell_orders)


def _symbolinfo_sessionturnover(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_turnover)


def _symbolinfo_sessioninterest(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_interest)


def _symbolinfo_sessionbuyordersvolume(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_buy_orders_volume)


def _symbolinfo_sessionsellordersvolume(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_sell_orders_volume)


def _symbolinfo_sessionopen(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_open)


def _symbolinfo_sessionclose(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_close)


def _symbolinfo_sessionaw(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_aw)


def _symbolinfo_sessionpricesettlement(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_price_settlement)


def _symbolinfo_sessionpricelimitmin(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_price_limit_min)


def _symbolinfo_sessionpricelimitmax(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_price_limit_max)


def _symbolinfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    value = self._backend.info_value("symbol", property_id, self.symbol_name)
    if value is None and isinstance(property_id, str):
        value = getattr(_symbolinfo__s(self), property_id.strip().lower(), 0)
    return int(value or 0)


def _symbolinfo_infodouble(self: _ObjectState, property_id: int | str) -> float:
    value = self._backend.info_value("symbol", property_id, self.symbol_name)
    if value is None and isinstance(property_id, str):
        value = getattr(_symbolinfo__s(self), property_id.strip().lower(), 0.0)
    return float(value or 0.0)


def _symbolinfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    value = self._backend.info_value("symbol", property_id, self.symbol_name)
    if value is None and isinstance(property_id, str):
        value = getattr(_symbolinfo__s(self), property_id.strip().lower(), "")
    return str(value or "")


def _symbolinfo_normalizeprice(self: _ObjectState, price: float) -> float:
    return round(float(price), _symbolinfo_digits(self))


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
        setattr(self._backend, "_market_book_subscriptions", subscriptions)
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


def _symbolinfo_custom(self: _ObjectState) -> bool:
    return bool(_symbolinfo__s(self).custom)


def _symbolinfo_chartmode(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).chart_mode)


def _symbolinfo_visible(self: _ObjectState) -> bool:
    return bool(_symbolinfo__s(self).visible)


def _symbolinfo_starttime(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).start_time)


def _symbolinfo_expirationtime(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).expiration_time)


def _symbolinfo_marginhedgeduseleg(self: _ObjectState) -> bool:
    return bool(_symbolinfo__s(self).margin_hedged_use_leg)


def _symbolinfo_expirationmode(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).expiration_mode)


def _symbolinfo_fillingmode(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).filling_mode)


def _symbolinfo_ordermode(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).order_mode)


def _symbolinfo_ordergtcmode(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).order_gtc_mode)


def _symbolinfo_optionmode(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).option_mode)


def _symbolinfo_optionright(self: _ObjectState) -> int:
    return int(_symbolinfo__s(self).option_right)


def _symbolinfo_volumereal(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).volume_real)


def _symbolinfo_volumehighreal(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).volumehigh_real)


def _symbolinfo_volumelowreal(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).volumelow_real)


def _symbolinfo_optionstrike(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).option_strike)


def _symbolinfo_tradeaccruedinterest(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).trade_accrued_interest)


def _symbolinfo_tradefacevalue(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).trade_face_value)


def _symbolinfo_tradeliquidityrate(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).trade_liquidity_rate)


def _symbolinfo_sessionvolume(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).session_volume)


def _symbolinfo_marginhedged(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).margin_hedged)


def _symbolinfo_pricechange(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_change)


def _symbolinfo_pricevolatility(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_volatility)


def _symbolinfo_pricetheoretical(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_theoretical)


def _symbolinfo_pricegreeksdelta(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_greeks_delta)


def _symbolinfo_pricegreekstheta(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_greeks_theta)


def _symbolinfo_pricegreeksgamma(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_greeks_gamma)


def _symbolinfo_pricegreeksvega(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_greeks_vega)


def _symbolinfo_pricegreeksrho(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_greeks_rho)


def _symbolinfo_pricegreeksomega(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_greeks_omega)


def _symbolinfo_pricesensitivity(self: _ObjectState) -> float:
    return float(_symbolinfo__s(self).price_sensitivity)


def _symbolinfo_basis(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).basis)


def _symbolinfo_category(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).category)


def _symbolinfo_exchange(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).exchange)


def _symbolinfo_formula(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).formula)


def _symbolinfo_isin(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).isin)


def _symbolinfo_page(self: _ObjectState) -> str:
    return cast("str", _symbolinfo__s(self).page)


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


def _terminalinfo___init__(self: _ObjectState, backend: BrokerBackend) -> None:
    self._backend = backend


def _terminalinfo__t(self: _ObjectState) -> Any:
    return self._backend.terminal()


def _terminalinfo_build(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).build)


def _terminalinfo_isconnected(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).connected)


def _terminalinfo_isdllsallowed(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).dlls_allowed)


def _terminalinfo_istradeallowed(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).trade_allowed)


def _terminalinfo_isemailenabled(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).email_enabled)


def _terminalinfo_isftpenabled(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).ftp_enabled)


def _terminalinfo_maxbars(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).max_bars)


def _terminalinfo_codepage(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).code_page)


def _terminalinfo_cpucores(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).cpu_cores)


def _terminalinfo_memoryphysical(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).memory_physical)


def _terminalinfo_memorytotal(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).memory_total)


def _terminalinfo_memoryavailable(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).memory_available)


def _terminalinfo_memoryused(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).memory_used)


def _terminalinfo_isx64(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).is_x64)


def _terminalinfo_openclsupport(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).opencl_support)


def _terminalinfo_diskspace(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).disk_space)


def _terminalinfo_language(self: _ObjectState) -> str:
    return cast("str", _terminalinfo__t(self).language)


def _terminalinfo_name(self: _ObjectState) -> str:
    return cast("str", _terminalinfo__t(self).name)


def _terminalinfo_company(self: _ObjectState) -> str:
    return cast("str", _terminalinfo__t(self).company)


def _terminalinfo_path(self: _ObjectState) -> str:
    return cast("str", _terminalinfo__t(self).path)


def _terminalinfo_datapath(self: _ObjectState) -> str:
    return cast("str", _terminalinfo__t(self).data_path)


def _terminalinfo_commondatapath(self: _ObjectState) -> str:
    return cast("str", _terminalinfo__t(self).common_data_path)


def _terminalinfo_infointeger(self: _ObjectState, property_id: int | str) -> int:
    value = self._backend.info_value("terminal", property_id)
    if value is None and isinstance(property_id, str):
        value = getattr(_terminalinfo__t(self), property_id.strip().lower(), 0)
    return int(value or 0)


def _terminalinfo_infostring(self: _ObjectState, property_id: int | str) -> str:
    value = self._backend.info_value("terminal", property_id)
    if value is None and isinstance(property_id, str):
        value = getattr(_terminalinfo__t(self), property_id.strip().lower(), "")
    return str(value or "")


def _terminalinfo_communityaccount(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).community_account)


def _terminalinfo_communityconnection(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).community_connection)


def _terminalinfo_tradeapidisabled(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).tradeapi_disabled)


def _terminalinfo_notificationsenabled(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).notifications_enabled)


def _terminalinfo_mqid(self: _ObjectState) -> bool:
    return bool(_terminalinfo__t(self).mqid)


def _terminalinfo_pinglast(self: _ObjectState) -> int:
    return int(_terminalinfo__t(self).ping_last)


def _terminalinfo_communitybalance(self: _ObjectState) -> float:
    return float(_terminalinfo__t(self).community_balance)


def _terminalinfo_retransmission(self: _ObjectState) -> float:
    return float(_terminalinfo__t(self).retransmission)


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


def _trade__send(self: _ObjectState, request: TradeRequest) -> bool:
    self._last_request = replace(request)
    self._last_check = self._backend.order_check(request)
    if self._last_check.retcode not in {
        0,
        int(TradeRetcode.DONE),
        int(TradeRetcode.PLACED),
        int(TradeRetcode.DONE_PARTIAL),
    }:
        self._last_result = TradeResult(
            retcode=self._last_check.retcode, comment=self._last_check.comment
        )
        return False
    self._last_result = self._backend.order_send(request)
    return self._last_result.retcode in {
        int(TradeRetcode.DONE),
        int(TradeRetcode.PLACED),
        int(TradeRetcode.DONE_PARTIAL),
        int(TradeRetcode.NO_CHANGES),
    }


def _trade__position(self: _ObjectState, symbol_or_ticket: str | int) -> Any:
    positions = self._backend.positions()
    if isinstance(symbol_or_ticket, int):
        return next((p for p in positions if p.ticket == symbol_or_ticket), None)
    candidates = [p for p in positions if p.symbol == symbol_or_ticket]
    candidates.sort(key=lambda p: p.ticket)
    return candidates[0] if candidates else None


def _trade_loglevel(self: _ObjectState, log_level: int) -> None:
    self._log_level = log_level


def _trade_setexpertmagicnumber(self: _ObjectState, magic: int) -> None:
    self._magic = magic


def _trade_setdeviationinpoints(self: _ObjectState, deviation: int) -> None:
    self._deviation = deviation


def _trade_settypefilling(self: _ObjectState, filling: OrderFilling | int) -> None:
    self._filling = OrderFilling(filling)


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


def _trade_setasyncmode(self: _ObjectState, mode: bool) -> None:
    self._async = mode


def _trade_setmarginmode(self: _ObjectState) -> None:
    _ = self._backend.account().margin_mode


def _trade_orderopen(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    symbol: str,
    order_type: OrderType | int,
    volume: float,
    limit_price: float,
    price: float,
    sl: float = 0.0,
    tp: float = 0.0,
    type_time: OrderTime | int = OrderTime.GTC,
    expiration: datetime | None = None,
    comment: str = "",
) -> bool:
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.PENDING,
            symbol=symbol,
            volume=volume,
            order_type=OrderType(order_type),
            price=price,
            stoplimit=limit_price,
            sl=sl,
            tp=tp,
            deviation=self._deviation,
            magic=self._magic,
            type_filling=self._filling,
            type_time=OrderTime(type_time),
            expiration=expiration,
            comment=comment,
        ),
    )


def _trade_ordermodify(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    ticket: int,
    price: float,
    sl: float,
    tp: float,
    type_time: OrderTime | int = OrderTime.GTC,
    expiration: datetime | None = None,
    stoplimit: float = 0.0,
) -> bool:
    order = next((o for o in self._backend.orders() if o.ticket == ticket), None)
    if order is None:
        self._last_result = TradeResult(
            retcode=int(TradeRetcode.INVALID_ORDER), comment=f"Order {ticket} not found"
        )
        return False
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.MODIFY,
            symbol=order.symbol,
            order=ticket,
            volume=order.volume_current,
            order_type=order.order_type,
            price=price,
            stoplimit=stoplimit,
            sl=sl,
            tp=tp,
            magic=self._magic,
            type_filling=order.type_filling,
            type_time=OrderTime(type_time),
            expiration=expiration,
            comment=order.comment,
        ),
    )


def _trade_orderdelete(self: _ObjectState, ticket: int) -> bool:
    return _trade__send(
        self, TradeRequest(action=TradeAction.REMOVE, order=ticket, magic=self._magic)
    )


def _trade_positionopen(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    symbol: str,
    order_type: OrderType | int,
    volume: float,
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    comment: str = "",
) -> bool:
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.DEAL,
            symbol=symbol,
            volume=volume,
            order_type=OrderType(order_type),
            price=price,
            sl=sl,
            tp=tp,
            deviation=self._deviation,
            magic=self._magic,
            type_filling=self._filling,
            comment=comment,
        ),
    )


def _trade_positionmodify(
    self: _ObjectState, symbol_or_ticket: str | int, sl: float, tp: float
) -> bool:
    position = _trade__position(self, symbol_or_ticket)
    if position is None:
        self._last_result = TradeResult(
            retcode=int(TradeRetcode.POSITION_CLOSED),
            comment=f"Position {symbol_or_ticket!r} not found",
        )
        return False
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.SLTP,
            symbol=position.symbol,
            position=position.ticket,
            sl=sl,
            tp=tp,
            magic=self._magic,
        ),
    )


def _trade_positionclose(
    self: _ObjectState, symbol_or_ticket: str | int, deviation: int | None = None
) -> bool:
    position = _trade__position(self, symbol_or_ticket)
    if position is None:
        self._last_result = TradeResult(
            retcode=int(TradeRetcode.POSITION_CLOSED),
            comment=f"Position {symbol_or_ticket!r} not found",
        )
        return False
    opposite = (
        OrderType.SELL if position.position_type == PositionType.BUY else OrderType.BUY
    )
    tick = self._backend.tick(position.symbol)
    price = 0.0
    if tick is not None:
        price = tick.bid if opposite == OrderType.SELL else tick.ask
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.DEAL,
            symbol=position.symbol,
            position=position.ticket,
            volume=position.volume,
            order_type=opposite,
            price=price,
            deviation=self._deviation if deviation is None else deviation,
            magic=self._magic,
            type_filling=self._filling,
            comment="position close",
        ),
    )


def _trade_positionclosepartial(
    self: _ObjectState,
    symbol_or_ticket: str | int,
    volume: float,
    deviation: int | None = None,
) -> bool:
    position = _trade__position(self, symbol_or_ticket)
    if position is None:
        self._last_result = TradeResult(
            retcode=int(TradeRetcode.POSITION_CLOSED),
            comment=f"Position {symbol_or_ticket!r} not found",
        )
        return False
    opposite = (
        OrderType.SELL if position.position_type == PositionType.BUY else OrderType.BUY
    )
    tick = self._backend.tick(position.symbol)
    price = 0.0
    if tick is not None:
        price = tick.bid if opposite == OrderType.SELL else tick.ask
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.DEAL,
            symbol=position.symbol,
            position=position.ticket,
            volume=volume,
            order_type=opposite,
            price=price,
            deviation=self._deviation if deviation is None else deviation,
            magic=self._magic,
            type_filling=self._filling,
            comment="partial close",
        ),
    )


def _trade_positioncloseby(self: _ObjectState, ticket: int, ticket_by: int) -> bool:
    return _trade__send(
        self,
        TradeRequest(
            action=TradeAction.CLOSE_BY,
            position=ticket,
            position_by=ticket_by,
            magic=self._magic,
        ),
    )


def _trade_buy(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    volume: float,
    symbol: str | None = None,
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    comment: str = "",
) -> bool:
    if not symbol:
        raise ValueError("symbol is required")
    if price == 0.0:
        tick = self._backend.tick(symbol)
        if tick is not None:
            price = tick.ask
    return _trade_positionopen(
        self, symbol, OrderType.BUY, volume, price, sl, tp, comment
    )


def _trade_sell(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    volume: float,
    symbol: str | None = None,
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    comment: str = "",
) -> bool:
    if not symbol:
        raise ValueError("symbol is required")
    if price == 0.0:
        tick = self._backend.tick(symbol)
        if tick is not None:
            price = tick.bid
    return _trade_positionopen(
        self, symbol, OrderType.SELL, volume, price, sl, tp, comment
    )


def _trade_buylimit(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    volume: float,
    price: float,
    symbol: str | None = None,
    sl: float = 0.0,
    tp: float = 0.0,
    type_time: OrderTime | int = OrderTime.GTC,
    expiration: datetime | None = None,
    comment: str = "",
) -> bool:
    if not symbol:
        raise ValueError("symbol is required")
    return _trade_orderopen(
        self,
        symbol,
        OrderType.BUY_LIMIT,
        volume,
        0.0,
        price,
        sl,
        tp,
        type_time,
        expiration,
        comment,
    )


def _trade_buystop(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    volume: float,
    price: float,
    symbol: str | None = None,
    sl: float = 0.0,
    tp: float = 0.0,
    type_time: OrderTime | int = OrderTime.GTC,
    expiration: datetime | None = None,
    comment: str = "",
) -> bool:
    if not symbol:
        raise ValueError("symbol is required")
    return _trade_orderopen(
        self,
        symbol,
        OrderType.BUY_STOP,
        volume,
        0.0,
        price,
        sl,
        tp,
        type_time,
        expiration,
        comment,
    )


def _trade_selllimit(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    volume: float,
    price: float,
    symbol: str | None = None,
    sl: float = 0.0,
    tp: float = 0.0,
    type_time: OrderTime | int = OrderTime.GTC,
    expiration: datetime | None = None,
    comment: str = "",
) -> bool:
    if not symbol:
        raise ValueError("symbol is required")
    return _trade_orderopen(
        self,
        symbol,
        OrderType.SELL_LIMIT,
        volume,
        0.0,
        price,
        sl,
        tp,
        type_time,
        expiration,
        comment,
    )


def _trade_sellstop(  # noqa: PLR0917 -- native compatibility signature
    self: _ObjectState,
    volume: float,
    price: float,
    symbol: str | None = None,
    sl: float = 0.0,
    tp: float = 0.0,
    type_time: OrderTime | int = OrderTime.GTC,
    expiration: datetime | None = None,
    comment: str = "",
) -> bool:
    if not symbol:
        raise ValueError("symbol is required")
    return _trade_orderopen(
        self,
        symbol,
        OrderType.SELL_STOP,
        volume,
        0.0,
        price,
        sl,
        tp,
        type_time,
        expiration,
        comment,
    )


def _trade_request(self: _ObjectState) -> TradeRequest:
    return cast("TradeRequest", replace(self._last_request))


def _trade_requestaction(self: _ObjectState) -> TradeAction:
    return TradeAction(self._last_request.action)


def _trade_requestactiondescription(self: _ObjectState) -> str:
    return _trade_requestaction(self).name.replace("_", " ").title()


def _trade_requestmagic(self: _ObjectState) -> int:
    return int(self._last_request.magic)


def _trade_requestorder(self: _ObjectState) -> int:
    return int(self._last_request.order)


def _trade_requestsymbol(self: _ObjectState) -> str:
    return cast("str", self._last_request.symbol)


def _trade_requestvolume(self: _ObjectState) -> float:
    return float(self._last_request.volume)


def _trade_requestprice(self: _ObjectState) -> float:
    return float(self._last_request.price)


def _trade_requeststoplimit(self: _ObjectState) -> float:
    return float(self._last_request.stoplimit)


def _trade_requestsl(self: _ObjectState) -> float:
    return float(self._last_request.sl)


def _trade_requesttp(self: _ObjectState) -> float:
    return float(self._last_request.tp)


def _trade_requestdeviation(self: _ObjectState) -> int:
    return int(self._last_request.deviation)


def _trade_requesttype(self: _ObjectState) -> OrderType:
    return OrderType(self._last_request.order_type)


def _trade_requesttypedescription(self: _ObjectState) -> str:
    return ORDER_TYPE_DESCRIPTIONS.get(
        _trade_requesttype(self), _trade_requesttype(self).name
    )


def _trade_requesttypefilling(self: _ObjectState) -> OrderFilling:
    return OrderFilling(self._last_request.type_filling)


def _trade_requesttypefillingdescription(self: _ObjectState) -> str:
    return ORDER_FILLING_DESCRIPTIONS.get(
        _trade_requesttypefilling(self), _trade_requesttypefilling(self).name
    )


def _trade_requesttypetime(self: _ObjectState) -> OrderTime:
    return OrderTime(self._last_request.type_time)


def _trade_requesttypetimedescription(self: _ObjectState) -> str:
    return ORDER_TIME_DESCRIPTIONS.get(
        _trade_requesttypetime(self), _trade_requesttypetime(self).name
    )


def _trade_requestexpiration(self: _ObjectState) -> datetime | None:
    return cast("datetime | None", self._last_request.expiration)


def _trade_requestcomment(self: _ObjectState) -> str:
    return cast("str", self._last_request.comment)


def _trade_requestposition(self: _ObjectState) -> int:
    return int(self._last_request.position)


def _trade_requestpositionby(self: _ObjectState) -> int:
    return int(self._last_request.position_by)


def _trade_result(self: _ObjectState) -> TradeResult:
    return cast("TradeResult", replace(self._last_result))


def _trade_resultretcode(self: _ObjectState) -> int:
    return int(self._last_result.retcode)


def _trade_resultretcodedescription(self: _ObjectState) -> str:
    return _retcode_description(_trade_resultretcode(self))


def _trade_resultdeal(self: _ObjectState) -> int:
    return int(self._last_result.deal)


def _trade_resultorder(self: _ObjectState) -> int:
    return int(self._last_result.order)


def _trade_resultvolume(self: _ObjectState) -> float:
    return float(self._last_result.volume)


def _trade_resultprice(self: _ObjectState) -> float:
    return float(self._last_result.price)


def _trade_resultbid(self: _ObjectState) -> float:
    return float(self._last_result.bid)


def _trade_resultask(self: _ObjectState) -> float:
    return float(self._last_result.ask)


def _trade_resultcomment(self: _ObjectState) -> str:
    return cast("str", self._last_result.comment)


def _trade_checkresult(self: _ObjectState) -> TradeCheckResult:
    return cast("TradeCheckResult", replace(self._last_check))


def _trade_checkresultretcode(self: _ObjectState) -> int:
    return int(self._last_check.retcode)


def _trade_checkresultretcodedescription(self: _ObjectState) -> str:
    return _retcode_description(_trade_checkresultretcode(self))


def _trade_checkresultbalance(self: _ObjectState) -> float:
    return float(self._last_check.balance)


def _trade_checkresultequity(self: _ObjectState) -> float:
    return float(self._last_check.equity)


def _trade_checkresultprofit(self: _ObjectState) -> float:
    return float(self._last_check.profit)


def _trade_checkresultmargin(self: _ObjectState) -> float:
    return float(self._last_check.margin)


def _trade_checkresultmarginfree(self: _ObjectState) -> float:
    return float(self._last_check.margin_free)


def _trade_checkresultmarginlevel(self: _ObjectState) -> float:
    return float(self._last_check.margin_level)


def _trade_checkresultcomment(self: _ObjectState) -> str:
    return cast("str", self._last_check.comment)


def _trade_printrequest(self: _ObjectState) -> None:
    del self
    logger.info("FR-SIMULATION-DISPATCH: native print operation")


def _trade_printresult(self: _ObjectState) -> None:
    del self
    logger.info("FR-SIMULATION-DISPATCH: native print operation")


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
        "Login": _accountinfo_login,
        "TradeMode": _accountinfo_trademode,
        "TradeModeDescription": _accountinfo_trademodedescription,
        "Leverage": _accountinfo_leverage,
        "StopoutMode": _accountinfo_stopoutmode,
        "StopoutModeDescription": _accountinfo_stopoutmodedescription,
        "MarginMode": _accountinfo_marginmode,
        "MarginModeDescription": _accountinfo_marginmodedescription,
        "TradeAllowed": _accountinfo_tradeallowed,
        "TradeExpert": _accountinfo_tradeexpert,
        "LimitOrders": _accountinfo_limitorders,
        "Balance": _accountinfo_balance,
        "Credit": _accountinfo_credit,
        "Profit": _accountinfo_profit,
        "Equity": _accountinfo_equity,
        "Margin": _accountinfo_margin,
        "FreeMargin": _accountinfo_freemargin,
        "MarginLevel": _accountinfo_marginlevel,
        "MarginCall": _accountinfo_margincall,
        "MarginStopOut": _accountinfo_marginstopout,
        "Name": _accountinfo_name,
        "Server": _accountinfo_server,
        "Currency": _accountinfo_currency,
        "Company": _accountinfo_company,
        "InfoInteger": _accountinfo_infointeger,
        "InfoDouble": _accountinfo_infodouble,
        "InfoString": _accountinfo_infostring,
        "OrderProfitCheck": _accountinfo_orderprofitcheck,
        "MarginCheck": _accountinfo_margincheck,
        "FreeMarginCheck": _accountinfo_freemargincheck,
        "MaxLotCheck": _accountinfo_maxlotcheck,
        "CurrencyDigits": _accountinfo_currencydigits,
        "FifoClose": _accountinfo_fifoclose,
        "MarginInitial": _accountinfo_margininitial,
        "MarginMaintenance": _accountinfo_marginmaintenance,
        "Assets": _accountinfo_assets,
        "Liabilities": _accountinfo_liabilities,
        "CommissionBlocked": _accountinfo_commissionblocked,
    },
    "DealInfo": {
        "Order": _dealinfo_order,
        "Time": _dealinfo_time,
        "TimeMsc": _dealinfo_timemsc,
        "DealType": _dealinfo_dealtype,
        "TypeDescription": _dealinfo_typedescription,
        "Entry": _dealinfo_entry,
        "EntryDescription": _dealinfo_entrydescription,
        "Magic": _dealinfo_magic,
        "PositionId": _dealinfo_positionid,
        "Volume": _dealinfo_volume,
        "Price": _dealinfo_price,
        "Commision": _dealinfo_commision,
        "Commission": _dealinfo_commission,
        "Swap": _dealinfo_swap,
        "Profit": _dealinfo_profit,
        "Symbol": _dealinfo_symbol,
        "Comment": _dealinfo_comment,
        "InfoInteger": _dealinfo_infointeger,
        "InfoDouble": _dealinfo_infodouble,
        "InfoString": _dealinfo_infostring,
        "Ticket": _dealinfo_ticket,
        "SelectByIndex": _dealinfo_selectbyindex,
    },
    "HistoryOrderInfo": {
        "TimeSetup": _historyorderinfo_timesetup,
        "TimeSetupMsc": _historyorderinfo_timesetupmsc,
        "OrderType": _historyorderinfo_ordertype,
        "TypeDescription": _historyorderinfo_typedescription,
        "State": _historyorderinfo_state,
        "StateDescription": _historyorderinfo_statedescription,
        "TimeExpiration": _historyorderinfo_timeexpiration,
        "TimeDone": _historyorderinfo_timedone,
        "TimeDoneMsc": _historyorderinfo_timedonemsc,
        "TypeFilling": _historyorderinfo_typefilling,
        "TypeFillingDescription": _historyorderinfo_typefillingdescription,
        "TypeTime": _historyorderinfo_typetime,
        "TypeTimeDescription": _historyorderinfo_typetimedescription,
        "Magic": _historyorderinfo_magic,
        "PositionId": _historyorderinfo_positionid,
        "VolumeInitial": _historyorderinfo_volumeinitial,
        "VolumeCurrent": _historyorderinfo_volumecurrent,
        "PriceOpen": _historyorderinfo_priceopen,
        "StopLoss": _historyorderinfo_stoploss,
        "TakeProfit": _historyorderinfo_takeprofit,
        "PriceCurrent": _historyorderinfo_pricecurrent,
        "PriceStopLimit": _historyorderinfo_pricestoplimit,
        "Symbol": _historyorderinfo_symbol,
        "Comment": _historyorderinfo_comment,
        "InfoInteger": _historyorderinfo_infointeger,
        "InfoDouble": _historyorderinfo_infodouble,
        "InfoString": _historyorderinfo_infostring,
        "Ticket": _historyorderinfo_ticket,
        "SelectByIndex": _historyorderinfo_selectbyindex,
    },
    "OrderInfo": {
        "Ticket": _orderinfo_ticket,
        "TimeSetup": _orderinfo_timesetup,
        "TimeSetupMsc": _orderinfo_timesetupmsc,
        "OrderType": _orderinfo_ordertype,
        "TypeDescription": _orderinfo_typedescription,
        "State": _orderinfo_state,
        "StateDescription": _orderinfo_statedescription,
        "TimeExpiration": _orderinfo_timeexpiration,
        "TimeDone": _orderinfo_timedone,
        "TimeDoneMsc": _orderinfo_timedonemsc,
        "TypeFilling": _orderinfo_typefilling,
        "TypeFillingDescription": _orderinfo_typefillingdescription,
        "TypeTime": _orderinfo_typetime,
        "TypeTimeDescription": _orderinfo_typetimedescription,
        "Magic": _orderinfo_magic,
        "PositionId": _orderinfo_positionid,
        "VolumeInitial": _orderinfo_volumeinitial,
        "VolumeCurrent": _orderinfo_volumecurrent,
        "PriceOpen": _orderinfo_priceopen,
        "StopLoss": _orderinfo_stoploss,
        "TakeProfit": _orderinfo_takeprofit,
        "PriceCurrent": _orderinfo_pricecurrent,
        "PriceStopLimit": _orderinfo_pricestoplimit,
        "Symbol": _orderinfo_symbol,
        "Comment": _orderinfo_comment,
        "InfoInteger": _orderinfo_infointeger,
        "InfoDouble": _orderinfo_infodouble,
        "InfoString": _orderinfo_infostring,
        "StoreState": _orderinfo_storestate,
        "CheckState": _orderinfo_checkstate,
        "Select": _orderinfo_select,
        "SelectByIndex": _orderinfo_selectbyindex,
    },
    "PositionInfo": {
        "Time": _positioninfo_time,
        "TimeMsc": _positioninfo_timemsc,
        "TimeUpdate": _positioninfo_timeupdate,
        "TimeUpdateMsc": _positioninfo_timeupdatemsc,
        "PositionType": _positioninfo_positiontype,
        "TypeDescription": _positioninfo_typedescription,
        "Magic": _positioninfo_magic,
        "Identifier": _positioninfo_identifier,
        "Volume": _positioninfo_volume,
        "PriceOpen": _positioninfo_priceopen,
        "StopLoss": _positioninfo_stoploss,
        "TakeProfit": _positioninfo_takeprofit,
        "PriceCurrent": _positioninfo_pricecurrent,
        "Commission": _positioninfo_commission,
        "Swap": _positioninfo_swap,
        "Profit": _positioninfo_profit,
        "Symbol": _positioninfo_symbol,
        "Comment": _positioninfo_comment,
        "InfoInteger": _positioninfo_infointeger,
        "InfoDouble": _positioninfo_infodouble,
        "InfoString": _positioninfo_infostring,
        "Select": _positioninfo_select,
        "SelectByIndex": _positioninfo_selectbyindex,
        "SelectByMagic": _positioninfo_selectbymagic,
        "SelectByTicket": _positioninfo_selectbyticket,
        "StoreState": _positioninfo_storestate,
        "CheckState": _positioninfo_checkstate,
    },
    "SymbolInfo": {
        "Refresh": _symbolinfo_refresh,
        "RefreshRates": _symbolinfo_refreshrates,
        "Name": _symbolinfo_name,
        "Select": _symbolinfo_select,
        "IsSynchronized": _symbolinfo_issynchronized,
        "Volume": _symbolinfo_volume,
        "VolumeHigh": _symbolinfo_volumehigh,
        "VolumeLow": _symbolinfo_volumelow,
        "Time": _symbolinfo_time,
        "Spread": _symbolinfo_spread,
        "SpreadFloat": _symbolinfo_spreadfloat,
        "TicksBookDepth": _symbolinfo_ticksbookdepth,
        "StopsLevel": _symbolinfo_stopslevel,
        "FreezeLevel": _symbolinfo_freezelevel,
        "Bid": _symbolinfo_bid,
        "BidHigh": _symbolinfo_bidhigh,
        "BidLow": _symbolinfo_bidlow,
        "Ask": _symbolinfo_ask,
        "AskHigh": _symbolinfo_askhigh,
        "AskLow": _symbolinfo_asklow,
        "Last": _symbolinfo_last,
        "LastHigh": _symbolinfo_lasthigh,
        "LastLow": _symbolinfo_lastlow,
        "TradeCalcMode": _symbolinfo_tradecalcmode,
        "TradeCalcModeDescription": _symbolinfo_tradecalcmodedescription,
        "TradeMode": _symbolinfo_trademode,
        "TradeModeDescription": _symbolinfo_trademodedescription,
        "TradeExecution": _symbolinfo_tradeexecution,
        "TradeExecutionDescription": _symbolinfo_tradeexecutiondescription,
        "SwapMode": _symbolinfo_swapmode,
        "SwapModeDescription": _symbolinfo_swapmodedescription,
        "SwapRollover3days": _symbolinfo_swaprollover3days,
        "SwapRollover3daysDescription": _symbolinfo_swaprollover3daysdescription,
        "MarginInitial": _symbolinfo_margininitial,
        "MarginMaintenance": _symbolinfo_marginmaintenance,
        "MarginLong": _symbolinfo_marginlong,
        "MarginShort": _symbolinfo_marginshort,
        "MarginLimit": _symbolinfo_marginlimit,
        "MarginStop": _symbolinfo_marginstop,
        "MarginStopLimit": _symbolinfo_marginstoplimit,
        "TradeTimeFlags": _symbolinfo_tradetimeflags,
        "TradeFillFlags": _symbolinfo_tradefillflags,
        "Digits": _symbolinfo_digits,
        "Point": _symbolinfo_point,
        "TickValue": _symbolinfo_tickvalue,
        "TickValueProfit": _symbolinfo_tickvalueprofit,
        "TickValueLoss": _symbolinfo_tickvalueloss,
        "TickSize": _symbolinfo_ticksize,
        "ContractSize": _symbolinfo_contractsize,
        "LotsMin": _symbolinfo_lotsmin,
        "LotsMax": _symbolinfo_lotsmax,
        "LotsStep": _symbolinfo_lotsstep,
        "LotsLimit": _symbolinfo_lotslimit,
        "SwapLong": _symbolinfo_swaplong,
        "SwapShort": _symbolinfo_swapshort,
        "CurrencyBase": _symbolinfo_currencybase,
        "CurrencyProfit": _symbolinfo_currencyprofit,
        "CurrencyMargin": _symbolinfo_currencymargin,
        "Bank": _symbolinfo_bank,
        "Description": _symbolinfo_description,
        "Path": _symbolinfo_path,
        "SessionDeals": _symbolinfo_sessiondeals,
        "SessionBuyOrders": _symbolinfo_sessionbuyorders,
        "SessionSellOrders": _symbolinfo_sessionsellorders,
        "SessionTurnover": _symbolinfo_sessionturnover,
        "SessionInterest": _symbolinfo_sessioninterest,
        "SessionBuyOrdersVolume": _symbolinfo_sessionbuyordersvolume,
        "SessionSellOrdersVolume": _symbolinfo_sessionsellordersvolume,
        "SessionOpen": _symbolinfo_sessionopen,
        "SessionClose": _symbolinfo_sessionclose,
        "SessionAW": _symbolinfo_sessionaw,
        "SessionPriceSettlement": _symbolinfo_sessionpricesettlement,
        "SessionPriceLimitMin": _symbolinfo_sessionpricelimitmin,
        "SessionPriceLimitMax": _symbolinfo_sessionpricelimitmax,
        "InfoInteger": _symbolinfo_infointeger,
        "InfoDouble": _symbolinfo_infodouble,
        "InfoString": _symbolinfo_infostring,
        "NormalizePrice": _symbolinfo_normalizeprice,
        "SymbolsTotal": _symbolinfo_symbolstotal,
        "SymbolsGet": _symbolinfo_symbolsget,
        "SymbolInfoTick": _symbolinfo_symbolinfotick,
        "SymbolSelect": _symbolinfo_symbolselect,
        "MarketBookAdd": _symbolinfo_marketbookadd,
        "MarketBookGet": _symbolinfo_marketbookget,
        "MarketBookRelease": _symbolinfo_marketbookrelease,
        "Custom": _symbolinfo_custom,
        "ChartMode": _symbolinfo_chartmode,
        "Visible": _symbolinfo_visible,
        "StartTime": _symbolinfo_starttime,
        "ExpirationTime": _symbolinfo_expirationtime,
        "MarginHedgedUseLeg": _symbolinfo_marginhedgeduseleg,
        "ExpirationMode": _symbolinfo_expirationmode,
        "FillingMode": _symbolinfo_fillingmode,
        "OrderMode": _symbolinfo_ordermode,
        "OrderGTCMode": _symbolinfo_ordergtcmode,
        "OptionMode": _symbolinfo_optionmode,
        "OptionRight": _symbolinfo_optionright,
        "VolumeReal": _symbolinfo_volumereal,
        "VolumeHighReal": _symbolinfo_volumehighreal,
        "VolumeLowReal": _symbolinfo_volumelowreal,
        "OptionStrike": _symbolinfo_optionstrike,
        "TradeAccruedInterest": _symbolinfo_tradeaccruedinterest,
        "TradeFaceValue": _symbolinfo_tradefacevalue,
        "TradeLiquidityRate": _symbolinfo_tradeliquidityrate,
        "SessionVolume": _symbolinfo_sessionvolume,
        "MarginHedged": _symbolinfo_marginhedged,
        "PriceChange": _symbolinfo_pricechange,
        "PriceVolatility": _symbolinfo_pricevolatility,
        "PriceTheoretical": _symbolinfo_pricetheoretical,
        "PriceGreeksDelta": _symbolinfo_pricegreeksdelta,
        "PriceGreeksTheta": _symbolinfo_pricegreekstheta,
        "PriceGreeksGamma": _symbolinfo_pricegreeksgamma,
        "PriceGreeksVega": _symbolinfo_pricegreeksvega,
        "PriceGreeksRho": _symbolinfo_pricegreeksrho,
        "PriceGreeksOmega": _symbolinfo_pricegreeksomega,
        "PriceSensitivity": _symbolinfo_pricesensitivity,
        "Basis": _symbolinfo_basis,
        "Category": _symbolinfo_category,
        "Exchange": _symbolinfo_exchange,
        "Formula": _symbolinfo_formula,
        "ISIN": _symbolinfo_isin,
        "Page": _symbolinfo_page,
        "as_dict": _symbolinfo_asdict,
    },
    "TerminalInfo": {
        "Build": _terminalinfo_build,
        "IsConnected": _terminalinfo_isconnected,
        "IsDLLsAllowed": _terminalinfo_isdllsallowed,
        "IsTradeAllowed": _terminalinfo_istradeallowed,
        "IsEmailEnabled": _terminalinfo_isemailenabled,
        "IsFtpEnabled": _terminalinfo_isftpenabled,
        "MaxBars": _terminalinfo_maxbars,
        "CodePage": _terminalinfo_codepage,
        "CPUCores": _terminalinfo_cpucores,
        "MemoryPhysical": _terminalinfo_memoryphysical,
        "MemoryTotal": _terminalinfo_memorytotal,
        "MemoryAvailable": _terminalinfo_memoryavailable,
        "MemoryUsed": _terminalinfo_memoryused,
        "IsX64": _terminalinfo_isx64,
        "OpenCLSupport": _terminalinfo_openclsupport,
        "DiskSpace": _terminalinfo_diskspace,
        "Language": _terminalinfo_language,
        "Name": _terminalinfo_name,
        "Company": _terminalinfo_company,
        "Path": _terminalinfo_path,
        "DataPath": _terminalinfo_datapath,
        "CommonDataPath": _terminalinfo_commondatapath,
        "InfoInteger": _terminalinfo_infointeger,
        "InfoString": _terminalinfo_infostring,
        "CommunityAccount": _terminalinfo_communityaccount,
        "CommunityConnection": _terminalinfo_communityconnection,
        "TradeAPIDisabled": _terminalinfo_tradeapidisabled,
        "NotificationsEnabled": _terminalinfo_notificationsenabled,
        "MQID": _terminalinfo_mqid,
        "PingLast": _terminalinfo_pinglast,
        "CommunityBalance": _terminalinfo_communitybalance,
        "Retransmission": _terminalinfo_retransmission,
    },
    "Trade": {
        "LogLevel": _trade_loglevel,
        "SetExpertMagicNumber": _trade_setexpertmagicnumber,
        "SetDeviationInPoints": _trade_setdeviationinpoints,
        "SetTypeFilling": _trade_settypefilling,
        "SetTypeFillingBySymbol": _trade_settypefillingbysymbol,
        "SetAsyncMode": _trade_setasyncmode,
        "SetMarginMode": _trade_setmarginmode,
        "OrderOpen": _trade_orderopen,
        "OrderModify": _trade_ordermodify,
        "OrderDelete": _trade_orderdelete,
        "PositionOpen": _trade_positionopen,
        "PositionModify": _trade_positionmodify,
        "PositionClose": _trade_positionclose,
        "PositionClosePartial": _trade_positionclosepartial,
        "PositionCloseBy": _trade_positioncloseby,
        "Buy": _trade_buy,
        "Sell": _trade_sell,
        "BuyLimit": _trade_buylimit,
        "BuyStop": _trade_buystop,
        "SellLimit": _trade_selllimit,
        "SellStop": _trade_sellstop,
        "Request": _trade_request,
        "RequestAction": _trade_requestaction,
        "RequestActionDescription": _trade_requestactiondescription,
        "RequestMagic": _trade_requestmagic,
        "RequestOrder": _trade_requestorder,
        "RequestSymbol": _trade_requestsymbol,
        "RequestVolume": _trade_requestvolume,
        "RequestPrice": _trade_requestprice,
        "RequestStopLimit": _trade_requeststoplimit,
        "RequestSL": _trade_requestsl,
        "RequestTP": _trade_requesttp,
        "RequestDeviation": _trade_requestdeviation,
        "RequestType": _trade_requesttype,
        "RequestTypeDescription": _trade_requesttypedescription,
        "RequestTypeFilling": _trade_requesttypefilling,
        "RequestTypeFillingDescription": _trade_requesttypefillingdescription,
        "RequestTypeTime": _trade_requesttypetime,
        "RequestTypeTimeDescription": _trade_requesttypetimedescription,
        "RequestExpiration": _trade_requestexpiration,
        "RequestComment": _trade_requestcomment,
        "RequestPosition": _trade_requestposition,
        "RequestPositionBy": _trade_requestpositionby,
        "Result": _trade_result,
        "ResultRetcode": _trade_resultretcode,
        "ResultRetcodeDescription": _trade_resultretcodedescription,
        "ResultDeal": _trade_resultdeal,
        "ResultOrder": _trade_resultorder,
        "ResultVolume": _trade_resultvolume,
        "ResultPrice": _trade_resultprice,
        "ResultBid": _trade_resultbid,
        "ResultAsk": _trade_resultask,
        "ResultComment": _trade_resultcomment,
        "CheckResult": _trade_checkresult,
        "CheckResultRetcode": _trade_checkresultretcode,
        "CheckResultRetcodeDescription": _trade_checkresultretcodedescription,
        "CheckResultBalance": _trade_checkresultbalance,
        "CheckResultEquity": _trade_checkresultequity,
        "CheckResultProfit": _trade_checkresultprofit,
        "CheckResultMargin": _trade_checkresultmargin,
        "CheckResultMarginFree": _trade_checkresultmarginfree,
        "CheckResultMarginLevel": _trade_checkresultmarginlevel,
        "CheckResultComment": _trade_checkresultcomment,
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
    """Validate local property support without fabricating missing values."""
    if class_name == "Trade" and method_name == "SetAsyncMode" and args and args[0]:
        raise BridgeError(
            "local model does not support queued asynchronous trade execution",
            code="UNSUPPORTED_OPERATION",
        )
    if method_name.startswith("Info") and args and isinstance(args[0], int):
        raise BridgeError(
            "numeric property IDs are not supported by the local model",
            code="UNSUPPORTED_OPERATION",
        )
    if method_name in {"InfoInteger", "InfoDouble", "InfoString"} and args:
        scope = {
            "AccountInfo": "account",
            "TerminalInfo": "terminal",
            "SymbolInfo": "symbol",
            "OrderInfo": "order",
            "HistoryOrderInfo": "history_order",
            "PositionInfo": "position",
            "DealInfo": "deal",
        }[class_name]
        key = str(args[0]).lower()
        key = key.removeprefix(scope.replace("history_", "") + "_")
        aliases = {
            "margin_free": "free_margin",
            "margin_so_call": "margin_call",
            "margin_so_so": "margin_stop_out",
            "trade_tick_value": "tick_value",
            "trade_tick_size": "tick_size",
            "trade_contract_size": "contract_size",
            "volume_min": "lots_min",
            "volume_max": "lots_max",
            "volume_step": "lots_step",
        }
        key = aliases.get(key, key)
        selector = (
            state.symbol_name
            if class_name == "SymbolInfo"
            else getattr(state.selected, "ticket", None)
        )
        if model.info_value(scope, key, selector) is None:
            raise BridgeError(
                "unsupported or unavailable simulated property",
                code="UNSUPPORTED_OPERATION",
            )
        args = [key, *args[1:]]
    return args
