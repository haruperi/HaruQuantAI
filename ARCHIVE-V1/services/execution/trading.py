"""Flat public trading tools.

Purpose:
    Flat public trading tools.

Classes:
    None.

Functions:
    trading_connect: Public function defined by this module.
    trading_disconnect: Public function defined by this module.
    trading_is_connected: Public function defined by this module.
    trading_place_order: Public function defined by this module.
    place_market_order: Public function defined by this module.
    place_pending_order: Public function defined by this module.
    modify_position: Public function defined by this module.
    modify_pending_order: Public function defined by this module.
    close_position: Public function defined by this module.
    cancel_pending_order: Public function defined by this module.
    trading_position_info: Public function defined by this module.
    trading_order_info: Public function defined by this module.
    trading_history_order_info: Public function defined by this module.
    trading_symbol_info: Public function defined by this module.
    trading_terminal_info: Public function defined by this module.
    trading_order_calc_margin: Public function defined by this module.
    trading_order_calc_profit: Public function defined by this module.
    trading_deal_history: Public function defined by this module.
    trading_account_info: Public function defined by this module.
    _json_safe: Internal helper function defined by this module.
    _get_first: Internal helper function defined by this module.
    _to_float: Internal helper function defined by this module.
    _to_int: Internal helper function defined by this module.
    _to_datetime: Internal helper function defined by this module.
    _split_symbols: Internal helper function defined by this module.
    _resolve_provider: Internal helper function defined by this module.
    _is_ctrader_provider: Internal helper function defined by this module.
    _bridge_name: Internal helper function defined by this module.
    _blocked_action: Internal helper function defined by this module.
    _execution_bridge: Internal helper function defined by this module.
    _get_mt5_client: Internal helper function defined by this module.
    _connection_snapshot: Internal helper function defined by this module.
    _close_active_connection: Internal helper function defined by this module.
    _mt5_client_rows: Internal helper function defined by this module.
    _account_summary: Internal helper function defined by this module.
    _normalize_order: Internal helper function defined by this module.
    _normalize_position: Internal helper function defined by this module.
    _normalize_symbol: Internal helper function defined by this module.
    _normalize_terminal: Internal helper function defined by this module.
    _deal_value: Internal helper function defined by this module.
    _normalize_deal: Internal helper function defined by this module.
    _deal_summary: Internal helper function defined by this module.
    _account_payload: Internal helper function defined by this module.
    _deal_payload: Internal helper function defined by this module.
    _rows_payload: Internal helper function defined by this module.
    _filtered_limited_rows: Internal helper function defined by this module.
    _mt5_trading_account_info: Internal helper function defined by this module.
    _mt5_trading_position_info: Internal helper function defined by this module.
    _mt5_trading_order_info: Internal helper function defined by this module.
    _mt5_trading_history_order_info: Internal helper function defined by this module.
    _mt5_trading_symbol_info: Internal helper function defined by this module.
    _mt5_trading_terminal_info: Internal helper function defined by this module.
    _mt5_trading_order_calc_margin: Internal helper function defined by this module.
    _mt5_trading_order_calc_profit: Internal helper function defined by this module.
    _mt5_trading_deal_history: Internal helper function defined by this module.
    _ctrader_trading_account_info: Internal helper function defined by this module.

Notes:
    External-facing exports are collected in the owning package __init__.py.
    private underscore helpers remain implementation details unless preserved for API compatibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, cast

_ACTIVE_CONNECTION: dict[str, Any] | None = None


def _mt5_api() -> Any:
    from app.services.brokers.mt5 import get_mt5_api

    return get_mt5_api()


def _mt5_const(name: str, default: int) -> int:
    mt5 = _mt5_api()
    return int(getattr(mt5, name, default) if mt5 is not None else default)


@dataclass
class TradeResult:
    """Small result object returned by low-level trading operations."""

    retcode: int = 0
    deal: int = 0
    order: int = 0
    volume: float = 0.0
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    comment: str = ""

    def __bool__(self) -> bool:
        return int(self.retcode) in (
            _mt5_const("TRADE_RETCODE_DONE", 10009),
            _mt5_const("TRADE_RETCODE_PLACED", 10008),
        )


class Trade:
    """Low-level MT5/simulator trade adapter retained inside trading.py."""

    def __init__(self, api: Any | None = None) -> None:
        self._api = api if api is not None else _mt5_api()
        self._magic = 0
        self._deviation = 0
        self._type_filling: int | None = None
        self._type_filling_by_symbol: dict[str, int] = {}
        self._type_time: int | None = None
        self._last_request: dict[str, Any] = {}
        self._last_check: dict[str, Any] = {}
        self._last_result: dict[str, Any] = {}

    @staticmethod
    def _obj_to_dict(obj: Any) -> dict[str, Any]:
        if obj is None:
            return {}
        if hasattr(obj, "_asdict"):
            return dict(obj._asdict())
        if isinstance(obj, Mapping):
            return dict(obj)
        try:
            return dict(vars(obj))
        except TypeError:
            return {}

    @staticmethod
    def _normalize_result(result: Any) -> dict[str, Any]:
        if result is None:
            return {}
        if hasattr(result, "_asdict"):
            return dict(result._asdict())
        if isinstance(result, Mapping):
            return dict(result)
        return Trade._obj_to_dict(result) or {"result": result}

    def _resolve_order_type(self, order_type: Any) -> int:
        if isinstance(order_type, int):
            return int(order_type)
        token = str(order_type).strip().upper().replace("-", "_").replace(" ", "_")
        token = token.removeprefix("ORDER_TYPE_")
        mapping = {
            "BUY": _mt5_const("ORDER_TYPE_BUY", 0),
            "SELL": _mt5_const("ORDER_TYPE_SELL", 1),
            "BUY_LIMIT": _mt5_const("ORDER_TYPE_BUY_LIMIT", 2),
            "SELL_LIMIT": _mt5_const("ORDER_TYPE_SELL_LIMIT", 3),
            "BUY_STOP": _mt5_const("ORDER_TYPE_BUY_STOP", 4),
            "SELL_STOP": _mt5_const("ORDER_TYPE_SELL_STOP", 5),
            "BUY_STOP_LIMIT": _mt5_const("ORDER_TYPE_BUY_STOP_LIMIT", 6),
            "SELL_STOP_LIMIT": _mt5_const("ORDER_TYPE_SELL_STOP_LIMIT", 7),
            "CLOSE_BY": _mt5_const("ORDER_TYPE_CLOSE_BY", 8),
        }
        if token not in mapping:
            raise ValueError(f"Unsupported order_type: {order_type}")
        return mapping[token]

    def _resolve_order_filling(self, filling: Any) -> int:
        if isinstance(filling, int):
            return int(filling)
        token = str(filling).strip().upper().replace("-", "_").replace(" ", "_")
        token = token.removeprefix("ORDER_FILLING_")
        mapping = {
            "FOK": _mt5_const("ORDER_FILLING_FOK", 0),
            "IOC": _mt5_const("ORDER_FILLING_IOC", 1),
            "RETURN": _mt5_const("ORDER_FILLING_RETURN", 2),
        }
        if token not in mapping:
            raise ValueError(f"Unsupported filling: {filling}")
        return mapping[token]

    def _resolve_order_time(self, type_time: Any) -> int:
        if isinstance(type_time, int):
            return int(type_time)
        token = str(type_time).strip().upper().replace("-", "_").replace(" ", "_")
        token = token.removeprefix("ORDER_TIME_")
        mapping = {
            "GTC": _mt5_const("ORDER_TIME_GTC", 0),
            "DAY": _mt5_const("ORDER_TIME_DAY", 1),
            "SPECIFIED": _mt5_const("ORDER_TIME_SPECIFIED", 2),
            "SPECIFIED_DAY": _mt5_const("ORDER_TIME_SPECIFIED_DAY", 3),
        }
        if token not in mapping:
            raise ValueError(f"Unsupported type_time: {type_time}")
        return mapping[token]

    def _request_base(self, symbol: str | None = None) -> dict[str, Any]:
        if symbol and hasattr(self._api, "symbol_select"):
            self._api.symbol_select(symbol, True)
        request: dict[str, Any] = {
            "magic": self._magic,
            "deviation": self._deviation,
        }
        if symbol:
            request["symbol"] = symbol
            filling = self._type_filling_by_symbol.get(symbol.upper())
            if filling is not None:
                request["type_filling"] = int(filling)
        if "type_filling" not in request and self._type_filling is not None:
            request["type_filling"] = int(self._type_filling)
        if self._type_time is not None:
            request["type_time"] = int(self._type_time)
        return request

    def _perform_check(self, request: dict[str, Any]) -> dict[str, Any]:
        if not hasattr(self._api, "order_check"):
            return {}
        try:
            return self._normalize_result(self._api.order_check(request))
        except Exception:
            return {}

    def _send_request(self, request: dict[str, Any]) -> TradeResult:
        self._last_request = dict(request)
        self._last_check = self._perform_check(request)
        result = self._api.order_send(request)
        self._last_result = self._normalize_result(result)
        return TradeResult(
            retcode=int(self._last_result.get("retcode", 0) or 0),
            deal=int(self._last_result.get("deal", 0) or 0),
            order=int(self._last_result.get("order", 0) or 0),
            volume=float(self._last_result.get("volume", 0.0) or 0.0),
            price=float(self._last_result.get("price", 0.0) or 0.0),
            bid=float(self._last_result.get("bid", 0.0) or 0.0),
            ask=float(self._last_result.get("ask", 0.0) or 0.0),
            comment=str(self._last_result.get("comment", "") or ""),
        )

    def _tick_data(self, symbol: str) -> dict[str, Any]:
        if not hasattr(self._api, "symbol_info_tick"):
            return {}
        return self._obj_to_dict(self._api.symbol_info_tick(symbol))

    def _get_position(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
    ) -> Any | None:
        if not hasattr(self._api, "positions_get"):
            return None
        if ticket is not None:
            rows = self._api.positions_get(ticket=int(ticket))
            if rows:
                return rows[0]
        rows = (
            self._api.positions_get(symbol=symbol)
            if symbol
            else self._api.positions_get()
        )
        if not rows:
            return None
        return rows[0]

    def SetExpertMagicNumber(self, magic: int) -> None:
        self._magic = int(magic)

    def LogLevel(self, level: int | None = None) -> int:
        _ = level
        return 0

    def SetDeviationInPoints(self, deviation: int) -> None:
        self._deviation = int(deviation)

    def SetTypeFilling(self, filling: Any) -> None:
        self._type_filling = self._resolve_order_filling(filling)

    def SetTypeFillingBySymbol(self, symbol: str) -> bool:
        self._type_filling_by_symbol[str(symbol).upper()] = (
            self._type_filling
            if self._type_filling is not None
            else _mt5_const("ORDER_FILLING_IOC", 1)
        )
        return True

    def SetTypeTime(self, type_time: Any) -> None:
        self._type_time = self._resolve_order_time(type_time)

    def SetAsyncMode(self, mode: bool) -> None:
        _ = mode

    def SetMarginMode(self) -> bool:
        return True

    def PositionOpen(
        self,
        symbol: str,
        order_type: Any,
        volume: float,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        resolved_type = self._resolve_order_type(order_type)
        if price <= 0.0:
            tick = self._tick_data(symbol)
            price = float(
                tick.get(
                    "ask"
                    if resolved_type == _mt5_const("ORDER_TYPE_BUY", 0)
                    else "bid",
                    0.0,
                )
                or 0.0
            )
        request = self._request_base(symbol)
        request.update(
            {
                "action": _mt5_const("TRADE_ACTION_DEAL", 1),
                "type": resolved_type,
                "volume": float(volume),
                "price": float(price),
                "sl": float(sl),
                "tp": float(tp),
                "comment": comment,
            }
        )
        return self._send_request(request)

    def OrderOpen(
        self,
        symbol: str,
        order_type: Any,
        volume: float,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        stoplimit: float = 0.0,
        type_time: Any | None = None,
        expiration: datetime | None = None,
        comment: str = "",
    ) -> TradeResult:
        request = self._request_base(symbol)
        request.update(
            {
                "action": _mt5_const("TRADE_ACTION_PENDING", 5),
                "type": self._resolve_order_type(order_type),
                "volume": float(volume),
                "price": float(price),
                "sl": float(sl),
                "tp": float(tp),
                "stoplimit": float(stoplimit),
                "comment": comment,
            }
        )
        if type_time is not None:
            request["type_time"] = self._resolve_order_time(type_time)
        if expiration is not None:
            request["expiration"] = int(expiration.timestamp())
        return self._send_request(request)

    def OrderModify(
        self,
        ticket: int,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        stoplimit: float = 0.0,
        type_time: Any | None = None,
        expiration: datetime | None = None,
    ) -> TradeResult:
        request = {
            "action": _mt5_const("TRADE_ACTION_MODIFY", 7),
            "order": int(ticket),
            "price": float(price),
            "sl": float(sl),
            "tp": float(tp),
            "stoplimit": float(stoplimit),
        }
        if type_time is not None:
            request["type_time"] = self._resolve_order_time(type_time)
        if expiration is not None:
            request["expiration"] = int(expiration.timestamp())
        return self._send_request(request)

    def OrderDelete(self, ticket: int) -> TradeResult:
        return self._send_request(
            {"action": _mt5_const("TRADE_ACTION_REMOVE", 8), "order": int(ticket)}
        )

    def PositionModify(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        sl: float = 0.0,
        tp: float = 0.0,
    ) -> TradeResult:
        request: dict[str, Any] = {
            "action": _mt5_const("TRADE_ACTION_SLTP", 6),
            "sl": float(sl),
            "tp": float(tp),
        }
        if symbol:
            request["symbol"] = symbol
        if ticket is not None:
            request["position"] = int(ticket)
        return self._send_request(request)

    def PositionClose(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
    ) -> TradeResult:
        position = self._get_position(symbol=symbol, ticket=ticket)
        if position is None:
            self._last_result = {"retcode": 10036, "comment": "Position not found"}
            return TradeResult(retcode=10036, comment="Position not found")
        data = self._obj_to_dict(position)
        symbol_name = str(data.get("symbol") or symbol or "")
        tick = self._tick_data(symbol_name)
        position_type = data.get("type")
        is_buy = int(position_type or 0) == _mt5_const("POSITION_TYPE_BUY", 0)
        close_type = (
            _mt5_const("ORDER_TYPE_SELL", 1)
            if is_buy
            else _mt5_const("ORDER_TYPE_BUY", 0)
        )
        price = float(
            tick.get("bid" if is_buy else "ask", data.get("price_current", 0.0)) or 0.0
        )
        position_id = int(data.get("id") or data.get("ticket") or ticket or 0)
        request = self._request_base(symbol_name)
        request.update(
            {
                "action": _mt5_const("TRADE_ACTION_DEAL", 1),
                "type": close_type,
                "position": position_id,
                "volume": float(data.get("volume", 0.0) or 0.0),
                "price": price,
            }
        )
        return self._send_request(request)

    def PositionClosePartial(
        self,
        symbol: str | None = None,
        ticket: int | None = None,
        volume: float = 0.0,
    ) -> TradeResult:
        position = self._get_position(symbol=symbol, ticket=ticket)
        if position is None:
            self._last_result = {"retcode": 10036, "comment": "Position not found"}
            return TradeResult(retcode=10036, comment="Position not found")
        data = self._obj_to_dict(position)
        data["volume"] = float(volume)
        symbol_name = str(data.get("symbol") or symbol or "")
        tick = self._tick_data(symbol_name)
        is_buy = int(data.get("type") or 0) == _mt5_const("POSITION_TYPE_BUY", 0)
        request = self._request_base(symbol_name)
        request.update(
            {
                "action": _mt5_const("TRADE_ACTION_DEAL", 1),
                "type": _mt5_const("ORDER_TYPE_SELL", 1)
                if is_buy
                else _mt5_const("ORDER_TYPE_BUY", 0),
                "position": int(data.get("id") or data.get("ticket") or ticket or 0),
                "volume": float(volume),
                "price": float(tick.get("bid" if is_buy else "ask", 0.0) or 0.0),
            }
        )
        return self._send_request(request)

    def PositionCloseBy(self, ticket: int, ticket_by: int) -> TradeResult:
        return self._send_request(
            {
                "action": _mt5_const("TRADE_ACTION_DEAL", 1),
                "type": _mt5_const("ORDER_TYPE_CLOSE_BY", 8),
                "position": int(ticket),
                "position_by": int(ticket_by),
            }
        )

    def Buy(
        self,
        volume: float,
        symbol: str,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        return self.PositionOpen(symbol, "BUY", volume, price, sl, tp, comment)

    def Sell(
        self,
        volume: float,
        symbol: str,
        price: float = 0.0,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        return self.PositionOpen(symbol, "SELL", volume, price, sl, tp, comment)

    def BuyLimit(
        self,
        volume: float,
        symbol: str,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        return self.OrderOpen(
            symbol, "BUY_LIMIT", volume, price, sl, tp, comment=comment
        )

    def BuyStop(
        self,
        volume: float,
        symbol: str,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        return self.OrderOpen(
            symbol, "BUY_STOP", volume, price, sl, tp, comment=comment
        )

    def SellLimit(
        self,
        volume: float,
        symbol: str,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        return self.OrderOpen(
            symbol, "SELL_LIMIT", volume, price, sl, tp, comment=comment
        )

    def SellStop(
        self,
        volume: float,
        symbol: str,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "",
    ) -> TradeResult:
        return self.OrderOpen(
            symbol, "SELL_STOP", volume, price, sl, tp, comment=comment
        )

    def Request(self) -> dict[str, Any]:
        return dict(self._last_request)

    def RequestAction(self) -> int:
        return int(self._last_request.get("action", 0) or 0)

    def RequestOrder(self) -> int:
        return int(self._last_request.get("order", 0) or 0)

    def RequestSymbol(self) -> str:
        return str(self._last_request.get("symbol", "") or "")

    def RequestVolume(self) -> float:
        return float(self._last_request.get("volume", 0.0) or 0.0)

    def RequestPrice(self) -> float:
        return float(self._last_request.get("price", 0.0) or 0.0)

    def CheckResult(self) -> dict[str, Any]:
        return dict(self._last_check)

    def CheckResultRetcode(self) -> int:
        return int(self._last_check.get("retcode", 0) or 0)

    def Result(self) -> dict[str, Any]:
        return dict(self._last_result)

    def ResultRetcode(self) -> int:
        return int(self._last_result.get("retcode", 0) or 0)

    def ResultRetcodeDescription(self) -> str:
        if hasattr(self._api, "trade_retcode_description"):
            return str(self._api.trade_retcode_description(self.ResultRetcode()))
        descriptions = {
            10008: "TRADE_RETCODE_PLACED",
            10009: "TRADE_RETCODE_DONE",
            10036: "TRADE_RETCODE_POSITION_CLOSED",
        }
        return descriptions.get(self.ResultRetcode(), str(self.ResultRetcode()))

    def ResultOrder(self) -> int:
        return int(self._last_result.get("order", 0) or 0)

    def ResultDeal(self) -> int:
        return int(self._last_result.get("deal", 0) or 0)

    def ResultVolume(self) -> float:
        return float(self._last_result.get("volume", 0.0) or 0.0)

    def ResultPrice(self) -> float:
        return float(self._last_result.get("price", 0.0) or 0.0)

    def ResultBid(self) -> float:
        return float(self._last_result.get("bid", 0.0) or 0.0)

    def ResultAsk(self) -> float:
        return float(self._last_result.get("ask", 0.0) or 0.0)

    def ResultComment(self) -> str:
        return str(self._last_result.get("comment", "") or "")


def _json_safe(value: Any) -> Any:
    """Return a JSON-safe representation of service-layer values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if hasattr(value, "_asdict"):
        return _json_safe(value._asdict())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "__dict__"):
        return {
            str(key): _json_safe(item)
            for key, item in vars(value).items()
            if not str(key).startswith("_")
        }
    return str(value)


def _get_first(payload: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    """Return the first present value from a mapping."""
    for name in names:
        if name in payload:
            return payload[name]
    return default


def _to_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float without leaking conversion errors."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    """Convert a value to int without leaking conversion errors."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_datetime(value: Any) -> datetime | None:
    """Convert common timestamp inputs to datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value))
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None


def _split_symbols(symbols: str) -> list[str]:
    """Split a comma-separated symbol list into normalized symbols."""
    return [item.strip().upper() for item in symbols.split(",") if item.strip()]


def _resolve_provider(provider: str | None) -> str:
    """Resolve a tool provider from an explicit value or active connection."""
    if provider is not None and provider.strip():
        return provider.strip().lower()
    if _ACTIVE_CONNECTION is not None:
        active_provider = str(_ACTIVE_CONNECTION.get("provider") or "").strip().lower()
        if active_provider:
            return active_provider
    raise ValueError(
        "No active trading connection. Call trading_connect() first or pass provider."
    )


def _is_ctrader_provider(provider: str) -> bool:
    """Return whether a provider value should use cTrader bridge behavior."""
    return provider in {"ctrader", "c_trader", "ctrader_bridge", "c_trader_bridge"}


def _bridge_name(provider: str) -> str:
    """Return the canonical bridge name for a provider."""
    return "ctrader" if _is_ctrader_provider(provider) else provider


def _blocked_action(
    *,
    provider: str,
    action: str,
    reason: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a JSON-safe fail-closed trading action response."""
    return {
        "provider": _bridge_name(provider),
        "bridge": _bridge_name(provider),
        "action": action,
        "status": "blocked",
        "reason": reason,
        "payload": dict(payload),
        "timestamp": datetime.now().isoformat(),
    }


def _execution_bridge(provider: str, *, live_enabled: bool) -> Any:
    """Return an execution bridge for the selected provider."""
    if (
        _ACTIVE_CONNECTION is not None
        and _ACTIVE_CONNECTION.get("provider") == provider
        and _ACTIVE_CONNECTION.get("handle") is not None
    ):
        handle = _ACTIVE_CONNECTION["handle"]
        if hasattr(handle, "place_order"):
            return handle

    if provider == "mt5":
        from app.services.execution.bridges.mt5_bridge import MT5Bridge

        return MT5Bridge(live_enabled=live_enabled)
    if _is_ctrader_provider(provider):
        from app.services.execution.bridges.ctrader_bridge import CTraderBridge

        return CTraderBridge(live_enabled=live_enabled)
    raise ValueError("provider must be 'mt5' or 'ctrader'")


def _get_mt5_client(
    *,
    user_id: int,
    mt5_login: int | None,
) -> tuple[Any, bool]:
    """Return the active MT5 client or create a short-lived one."""
    if (
        _ACTIVE_CONNECTION is not None
        and _ACTIVE_CONNECTION.get("provider") == "mt5"
        and _ACTIVE_CONNECTION.get("handle") is not None
    ):
        return _ACTIVE_CONNECTION["handle"], False

    from app.services.brokers.mt5 import get_connected_mt5_client

    return get_connected_mt5_client(user_id=user_id, mt5_login=mt5_login), True


def _connection_snapshot() -> dict[str, Any]:
    """Return a JSON-safe snapshot of the active connection state."""
    if _ACTIVE_CONNECTION is None:
        return {
            "connected": False,
            "provider": None,
            "bridge": None,
            "connected_at": None,
            "details": {},
        }
    return {
        "connected": bool(_ACTIVE_CONNECTION.get("connected")),
        "provider": _ACTIVE_CONNECTION.get("provider"),
        "bridge": _ACTIVE_CONNECTION.get("bridge"),
        "connected_at": _ACTIVE_CONNECTION.get("connected_at"),
        "details": dict(_ACTIVE_CONNECTION.get("details") or {}),
    }


def _close_active_connection() -> dict[str, Any]:
    """Close and clear the active connection if one exists."""
    global _ACTIVE_CONNECTION  # pylint: disable=global-statement

    if _ACTIVE_CONNECTION is None:
        return {
            "status": "noop",
            "connected": False,
            "provider": None,
            "message": "No active trading connection.",
        }

    previous = _connection_snapshot()
    handle: Any = _ACTIVE_CONNECTION.get("handle")
    close_error: str | None = None
    if hasattr(handle, "shutdown"):
        try:
            handle.shutdown()
        except Exception as exc:  # noqa: BLE001
            close_error = str(exc)
    elif hasattr(handle, "close"):
        try:
            handle.close()
        except Exception as exc:  # noqa: BLE001
            close_error = str(exc)

    _ACTIVE_CONNECTION = None
    payload = {
        "status": "disconnected" if close_error is None else "disconnect_error",
        "connected": False,
        "previous": previous,
    }
    if close_error is not None:
        payload["error"] = close_error
    return payload


def trading_connect(
    provider: str = "mt5",
    user_id: int = 1,
    mt5_login: int | None = None,
    live_enabled: bool = False,
    url: str | None = None,
) -> dict[str, Any]:
    """Connect and hold one active trading/data bridge.

    Args:
        provider: Bridge provider to connect. Supported values are "mt5",
            "ctrader", "ctrader_bridge", and "dukascopy".
        user_id: Application user ID used by the MT5 credential loader.
        mt5_login: Optional MT5 login override.
        live_enabled: Whether execution bridges should allow live mutations.
        url: Optional cTrader MCP endpoint URL.

    Returns:
        A JSON-safe connection status payload. The active bridge remains held in
        this module until `trading_disconnect()` is called.
    """
    global _ACTIVE_CONNECTION  # pylint: disable=global-statement

    normalized_provider = provider.strip().lower()
    if _ACTIVE_CONNECTION is not None:
        current_provider = str(_ACTIVE_CONNECTION.get("provider") or "")
        if current_provider == normalized_provider:
            return {
                "status": "already_connected",
                **_connection_snapshot(),
            }
        _close_active_connection()

    connected_at = datetime.now().isoformat()
    if normalized_provider == "mt5":
        from app.services.brokers.mt5 import get_connected_mt5_client

        client = get_connected_mt5_client(user_id=user_id, mt5_login=mt5_login)
        connected = (
            bool(client.is_connected()) if hasattr(client, "is_connected") else True
        )
        _ACTIVE_CONNECTION = {
            "provider": "mt5",
            "bridge": "mt5_client",
            "connected": connected,
            "connected_at": connected_at,
            "handle": client,
            "details": {"user_id": user_id, "mt5_login": mt5_login},
        }
        return {"status": "connected", **_connection_snapshot()}

    if normalized_provider == "ctrader":
        from app.services.brokers.ctrader import get_ctrader_client

        client = get_ctrader_client(url=url)
        connected = bool(client.is_connected())
        _ACTIVE_CONNECTION = {
            "provider": "ctrader",
            "bridge": "ctrader_mcp",
            "connected": connected,
            "connected_at": connected_at,
            "handle": client,
            "details": {"url": getattr(client, "url", url)},
        }
        return {"status": "connected", **_connection_snapshot()}

    if normalized_provider in {"ctrader_bridge", "c_trader_bridge"}:
        from app.services.execution.bridges.ctrader_bridge import CTraderBridge

        bridge = CTraderBridge(live_enabled=live_enabled)
        _ACTIVE_CONNECTION = {
            "provider": "ctrader_bridge",
            "bridge": "execution_bridge",
            "connected": True,
            "connected_at": connected_at,
            "handle": bridge,
            "details": {"live_enabled": live_enabled},
        }
        return {"status": "connected", **_connection_snapshot()}

    if normalized_provider == "dukascopy":
        _ACTIVE_CONNECTION = {
            "provider": "dukascopy",
            "bridge": "stateless_data_provider",
            "connected": True,
            "connected_at": connected_at,
            "handle": None,
            "details": {
                "message": "Dukascopy is stateless; connection records provider intent."
            },
        }
        return {"status": "connected", **_connection_snapshot()}

    raise ValueError(
        "provider must be 'mt5', 'ctrader', 'ctrader_bridge', or 'dukascopy'"
    )


def trading_disconnect() -> dict[str, Any]:
    """Disconnect and clear the active trading/data bridge."""
    return _close_active_connection()


def trading_is_connected() -> dict[str, Any]:
    """Return the currently active trading/data bridge connection status."""
    if _ACTIVE_CONNECTION is None:
        return _connection_snapshot()

    handle: Any = _ACTIVE_CONNECTION.get("handle")
    connected = bool(_ACTIVE_CONNECTION.get("connected"))
    if hasattr(handle, "is_connected"):
        try:
            connected = bool(handle.is_connected())
        except Exception:  # noqa: BLE001
            connected = False
    elif hasattr(handle, "heartbeat"):
        try:
            heartbeat = handle.heartbeat()
            connected = str(heartbeat.get("status")) == "healthy"
        except Exception:  # noqa: BLE001
            connected = False

    _ACTIVE_CONNECTION["connected"] = connected
    return _connection_snapshot()


def _mt5_client_rows(
    *,
    method_name: str,
    user_id: int,
    mt5_login: int | None,
    shutdown: bool,
    args: tuple[Any, ...] = (),
    kwargs: Mapping[str, Any] | None = None,
) -> Any:
    """Call a read-only MT5 client method and optionally close the client."""
    client, owned_client = _get_mt5_client(user_id=user_id, mt5_login=mt5_login)
    try:
        method = getattr(client, method_name)
        return method(*args, **dict(kwargs or {}))
    finally:
        if shutdown and owned_client:
            client.shutdown()


def _account_summary(account: Mapping[str, Any]) -> dict[str, Any]:
    """Build a normalized summary from an account snapshot."""
    raw_balance = _get_first(account, "balance", "Balance")
    raw_equity = _get_first(account, "equity", "Equity", default=raw_balance)
    equity = _to_float(raw_equity)
    balance = _to_float(raw_balance, equity)
    margin = _to_float(_get_first(account, "margin", "Margin", "margin_used"))
    margin_free = _to_float(
        _get_first(account, "margin_free", "FreeMargin", "free_margin"),
        equity - margin,
    )
    margin_level = _to_float(
        _get_first(account, "margin_level", "MarginLevel"),
        (equity / margin * 100.0) if margin > 0.0 else 0.0,
    )
    return {
        "login": _get_first(account, "login", "account_id", "id"),
        "name": _get_first(account, "name", "Name", default=""),
        "server": _get_first(account, "server", "Server", default=""),
        "company": _get_first(account, "company", "Company", default=""),
        "currency": _get_first(
            account,
            "currency",
            "Currency",
            "currency_code",
            default="",
        ),
        "leverage": _to_int(_get_first(account, "leverage", "Leverage"), 1),
        "trade_mode": _get_first(account, "trade_mode", "TradeMode"),
        "margin_mode": _get_first(account, "margin_mode", "MarginMode"),
        "trade_allowed": bool(
            _get_first(account, "trade_allowed", "TradeAllowed", default=True)
        ),
        "trade_expert": bool(
            _get_first(account, "trade_expert", "TradeExpert", default=True)
        ),
        "limit_orders": _to_int(
            _get_first(account, "limit_orders", "LimitOrders"),
            0,
        ),
        "balance": balance,
        "credit": _to_float(_get_first(account, "credit", "Credit")),
        "profit": _to_float(_get_first(account, "profit", "Profit")),
        "equity": equity,
        "margin": margin,
        "margin_free": margin_free,
        "margin_level": margin_level,
        "margin_so_call": _get_first(account, "margin_so_call", "MarginSOCall"),
        "margin_so_so": _get_first(account, "margin_so_so", "MarginSOSO"),
    }


def _normalize_order(raw_order: Any) -> dict[str, Any]:
    """Normalize one active or historical order row."""
    order = _json_safe(raw_order)
    if not isinstance(order, Mapping):
        order = {"value": order}
    setup_time = _to_datetime(_deal_value(order, "time_setup", "TimeSetup"))
    done_time = _to_datetime(_deal_value(order, "time_done", "TimeDone"))
    return {
        "ticket": _to_int(_deal_value(order, "ticket", "Ticket")),
        "symbol": str(_deal_value(order, "symbol", "Symbol", default="") or ""),
        "type": _deal_value(order, "type", "Type"),
        "state": _deal_value(order, "state", "State"),
        "volume_initial": _to_float(
            _deal_value(order, "volume_initial", "VolumeInitial")
        ),
        "volume_current": _to_float(
            _deal_value(order, "volume_current", "VolumeCurrent")
        ),
        "price_open": _to_float(_deal_value(order, "price_open", "PriceOpen")),
        "sl": _to_float(_deal_value(order, "sl", "StopLoss", "Sl")),
        "tp": _to_float(_deal_value(order, "tp", "Tp")),
        "magic": _to_int(_deal_value(order, "magic", "Magic")),
        "position_id": _to_int(_deal_value(order, "position_id", "PositionId")),
        "time_setup": _deal_value(order, "time_setup", "TimeSetup"),
        "time_setup_iso": setup_time.isoformat() if setup_time else None,
        "time_setup_msc": _deal_value(order, "time_setup_msc", "TimeSetupMsc"),
        "time_done": _deal_value(order, "time_done", "TimeDone"),
        "time_done_iso": done_time.isoformat() if done_time else None,
        "time_done_msc": _deal_value(order, "time_done_msc", "TimeDoneMsc"),
        "comment": str(_deal_value(order, "comment", "Comment", default="") or ""),
        "external_id": str(
            _deal_value(order, "external_id", "ExternalId", default="") or ""
        ),
    }


def _normalize_position(raw_position: Any) -> dict[str, Any]:
    """Normalize one open position row."""
    position = _json_safe(raw_position)
    if not isinstance(position, Mapping):
        position = {"value": position}
    opened_at = _to_datetime(_deal_value(position, "time", "Time"))
    return {
        "ticket": _to_int(_deal_value(position, "ticket", "Ticket")),
        "identifier": _to_int(_deal_value(position, "identifier", "Identifier")),
        "symbol": str(_deal_value(position, "symbol", "Symbol", default="") or ""),
        "type": _deal_value(position, "type", "Type"),
        "volume": _to_float(_deal_value(position, "volume", "Volume")),
        "price_open": _to_float(_deal_value(position, "price_open", "PriceOpen")),
        "price_current": _to_float(
            _deal_value(position, "price_current", "PriceCurrent")
        ),
        "profit": _to_float(_deal_value(position, "profit", "Profit")),
        "swap": _to_float(_deal_value(position, "swap", "Swap")),
        "sl": _to_float(_deal_value(position, "sl", "Sl")),
        "tp": _to_float(_deal_value(position, "tp", "Tp")),
        "time": _deal_value(position, "time", "Time"),
        "time_iso": opened_at.isoformat() if opened_at else None,
        "time_msc": _deal_value(position, "time_msc", "TimeMsc"),
        "comment": str(_deal_value(position, "comment", "Comment", default="") or ""),
    }


def _normalize_symbol(raw_symbol: Any, requested_symbol: str = "") -> dict[str, Any]:
    """Normalize one symbol-info row."""
    symbol = _json_safe(raw_symbol)
    if not isinstance(symbol, Mapping):
        symbol = {"value": symbol}
    bid = _to_float(_deal_value(symbol, "bid", "Bid"))
    ask = _to_float(_deal_value(symbol, "ask", "Ask"))
    return {
        "name": str(
            _deal_value(symbol, "name", "Name", default=requested_symbol) or ""
        ),
        "description": str(
            _deal_value(symbol, "description", "Description", default="") or ""
        ),
        "path": str(_deal_value(symbol, "path", "Path", default="") or ""),
        "digits": _to_int(_deal_value(symbol, "digits", "Digits"), 5),
        "point": _to_float(_deal_value(symbol, "point", "Point")),
        "trade_tick_size": _to_float(
            _deal_value(symbol, "trade_tick_size", "TradeTickSize")
        ),
        "bid": bid,
        "ask": ask,
        "last": _to_float(_deal_value(symbol, "last", "Last"), (bid + ask) / 2),
        "spread": _to_int(_deal_value(symbol, "spread", "Spread")),
        "spread_float": bool(
            _deal_value(symbol, "spread_float", "SpreadFloat", default=False)
        ),
        "trade_mode": _deal_value(symbol, "trade_mode", "TradeMode"),
        "trade_exemode": _deal_value(symbol, "trade_exemode", "TradeExemode"),
        "trade_calc_mode": _deal_value(symbol, "trade_calc_mode", "TradeCalcMode"),
        "trade_stops_level": _to_int(
            _deal_value(symbol, "trade_stops_level", "TradeStopsLevel")
        ),
        "trade_freeze_level": _to_int(
            _deal_value(symbol, "trade_freeze_level", "TradeFreezeLevel")
        ),
        "trade_contract_size": _to_float(
            _deal_value(symbol, "trade_contract_size", "TradeContractSize")
        ),
        "volume_min": _to_float(_deal_value(symbol, "volume_min", "VolumeMin")),
        "volume_max": _to_float(_deal_value(symbol, "volume_max", "VolumeMax")),
        "volume_step": _to_float(_deal_value(symbol, "volume_step", "VolumeStep")),
        "swap_mode": _deal_value(symbol, "swap_mode", "SwapMode"),
        "swap_long": _to_float(_deal_value(symbol, "swap_long", "SwapLong")),
        "swap_short": _to_float(_deal_value(symbol, "swap_short", "SwapShort")),
    }


def _normalize_terminal(raw_terminal: Any) -> dict[str, Any]:
    """Normalize one terminal-info row."""
    terminal = _json_safe(raw_terminal)
    if not isinstance(terminal, Mapping):
        terminal = {"value": terminal}
    return {
        "build": _to_int(_deal_value(terminal, "build", "Build")),
        "connected": bool(
            _deal_value(terminal, "connected", "Connected", default=False)
        ),
        "trade_allowed": bool(
            _deal_value(terminal, "trade_allowed", "TradeAllowed", default=False)
        ),
        "dlls_allowed": bool(
            _deal_value(terminal, "dlls_allowed", "DLLsAllowed", default=False)
        ),
        "ping_last": _to_int(_deal_value(terminal, "ping_last", "PingLast")),
        "cpu_cores": _to_int(_deal_value(terminal, "cpu_cores", "CPUCores")),
        "memory_total": _to_int(_deal_value(terminal, "memory_total", "MemoryTotal")),
        "memory_available": _to_int(
            _deal_value(terminal, "memory_available", "MemoryAvailable")
        ),
        "language": str(
            _deal_value(terminal, "language", "Language", default="") or ""
        ),
        "company": str(_deal_value(terminal, "company", "Company", default="") or ""),
        "name": str(_deal_value(terminal, "name", "Name", default="") or ""),
        "path": str(_deal_value(terminal, "path", "Path", default="") or ""),
        "data_path": str(
            _deal_value(terminal, "data_path", "DataPath", default="") or ""
        ),
        "commondata_path": str(
            _deal_value(terminal, "commondata_path", "CommondataPath", default="") or ""
        ),
    }


def _deal_value(deal: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    """Return the first matching deal field."""
    for name in names:
        if name in deal:
            return deal[name]
    return default


def _normalize_deal(raw_deal: Any) -> dict[str, Any]:
    """Normalize one broker deal row into a JSON-safe dictionary."""
    deal = _json_safe(raw_deal)
    if not isinstance(deal, Mapping):
        deal = {"value": deal}

    raw_time = _deal_value(deal, "time", "Time")
    raw_time_msc = _deal_value(deal, "time_msc", "TimeMsc")
    timestamp = _to_datetime(raw_time)

    return {
        "ticket": _to_int(_deal_value(deal, "ticket", "Ticket")),
        "order": _to_int(_deal_value(deal, "order", "Order")),
        "position_id": _to_int(_deal_value(deal, "position_id", "PositionId")),
        "symbol": str(_deal_value(deal, "symbol", "Symbol", default="") or ""),
        "type": _deal_value(deal, "type", "Type"),
        "entry": _deal_value(deal, "entry", "Entry"),
        "time": raw_time,
        "time_iso": timestamp.isoformat() if timestamp is not None else None,
        "time_msc": raw_time_msc,
        "volume": _to_float(_deal_value(deal, "volume", "Volume")),
        "price": _to_float(_deal_value(deal, "price", "Price")),
        "commission": _to_float(_deal_value(deal, "commission", "Commission")),
        "swap": _to_float(_deal_value(deal, "swap", "Swap")),
        "profit": _to_float(_deal_value(deal, "profit", "Profit")),
        "magic": _to_int(_deal_value(deal, "magic", "Magic")),
        "comment": str(_deal_value(deal, "comment", "Comment", default="") or ""),
        "external_id": str(
            _deal_value(deal, "external_id", "ExternalId", default="") or ""
        ),
    }


def _deal_summary(deals: list[dict[str, Any]]) -> dict[str, Any]:
    """Build aggregate deal statistics."""
    total_profit = sum(_to_float(deal.get("profit")) for deal in deals)
    total_commission = sum(_to_float(deal.get("commission")) for deal in deals)
    total_swap = sum(_to_float(deal.get("swap")) for deal in deals)
    symbols = sorted(
        {str(deal.get("symbol") or "") for deal in deals if deal.get("symbol")}
    )
    return {
        "total_deals": len(deals),
        "symbols": symbols,
        "total_profit": total_profit,
        "total_commission": total_commission,
        "total_swap": total_swap,
        "net_result": total_profit + total_commission + total_swap,
    }


def _account_payload(
    *,
    provider: str,
    request: Mapping[str, Any],
    account: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the stable account-info payload returned by public tools."""
    return {
        "provider": provider,
        "request": dict(request),
        "account": dict(account),
        "summary": _account_summary(account),
    }


def _deal_payload(
    *,
    provider: str,
    request: Mapping[str, Any],
    deals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the stable deal-history payload returned by public tools."""
    return {
        "provider": provider,
        "request": dict(request),
        "rows": len(deals),
        "deals": deals,
        "summary": _deal_summary(deals),
    }


def _rows_payload(
    *,
    provider: str,
    request: Mapping[str, Any],
    key: str,
    rows: list[dict[str, Any]],
    summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a stable row-list payload for trading snapshots."""
    return {
        "provider": provider,
        "request": dict(request),
        "rows": len(rows),
        key: rows,
        "summary": dict(summary or {"total": len(rows)}),
    }


def _filtered_limited_rows(
    rows: list[dict[str, Any]],
    *,
    symbol: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Apply an exact symbol filter and most-recent limit."""
    if symbol is not None:
        normalized_symbol = symbol.upper().strip()
        rows = [
            row
            for row in rows
            if str(row.get("symbol") or row.get("name") or "").upper()
            == normalized_symbol
        ]
    if limit > 0:
        rows = rows[-int(limit) :]
    return rows


def _mt5_trading_account_info(
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 account information.

    Args:
        user_id: Application user ID used to load saved MT5 credentials.
        mt5_login: Optional MT5 login override. When omitted, the default saved
            credentials for the user are used.
        shutdown: Whether to close the MT5 client connection after reading the
            account snapshot.

    Returns:
        A JSON-safe payload containing request metadata, provider name, raw
        account fields, and a normalized summary with balance, equity, margin,
        permissions, currency, leverage, and account identity fields.
    """
    client, owned_client = _get_mt5_client(user_id=user_id, mt5_login=mt5_login)
    try:
        account = _json_safe(client.account_info())
    finally:
        if shutdown and owned_client:
            client.shutdown()

    if not isinstance(account, Mapping):
        account = {"value": account}

    return _account_payload(
        provider="mt5",
        request={
            "provider": "mt5",
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        account=account,
    )


def _mt5_trading_position_info(
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 open positions.

    Args:
        symbol: Optional exact symbol filter.
        group: Optional MT5 group filter such as "*USD*".
        ticket: Optional position ticket filter.
        limit: Maximum number of most-recent positions to return. Use 0 for all.
        user_id: Application user ID used to load saved MT5 credentials.
        mt5_login: Optional MT5 login override.
        shutdown: Whether to close the MT5 client connection after reading.

    Returns:
        A JSON-safe payload with request metadata, row count, positions, and
        aggregate position statistics.
    """
    kwargs = {"symbol": symbol, "group": group, "ticket": ticket}
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    raw_rows = _mt5_client_rows(
        method_name="positions_get",
        user_id=user_id,
        mt5_login=mt5_login,
        shutdown=shutdown,
        kwargs=kwargs,
    )
    positions = [_normalize_position(row) for row in list(raw_rows or [])]
    positions = _filtered_limited_rows(positions, symbol=symbol, limit=limit)
    total_profit = sum(_to_float(row.get("profit")) for row in positions)
    return _rows_payload(
        provider="mt5",
        request={
            "provider": "mt5",
            "symbol": symbol,
            "group": group,
            "ticket": ticket,
            "limit": limit,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        key="positions",
        rows=positions,
        summary={
            "total_positions": len(positions),
            "total_volume": sum(_to_float(row.get("volume")) for row in positions),
            "total_profit": total_profit,
            "symbols": sorted(
                {str(row.get("symbol") or "") for row in positions if row.get("symbol")}
            ),
        },
    )


def _mt5_trading_order_info(
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 active/pending orders."""
    kwargs = {"symbol": symbol, "group": group, "ticket": ticket}
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    raw_rows = _mt5_client_rows(
        method_name="orders_get",
        user_id=user_id,
        mt5_login=mt5_login,
        shutdown=shutdown,
        kwargs=kwargs,
    )
    orders = [_normalize_order(row) for row in list(raw_rows or [])]
    orders = _filtered_limited_rows(orders, symbol=symbol, limit=limit)
    return _rows_payload(
        provider="mt5",
        request={
            "provider": "mt5",
            "symbol": symbol,
            "group": group,
            "ticket": ticket,
            "limit": limit,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        key="orders",
        rows=orders,
        summary={
            "total_orders": len(orders),
            "total_volume_initial": sum(
                _to_float(row.get("volume_initial")) for row in orders
            ),
            "total_volume_current": sum(
                _to_float(row.get("volume_current")) for row in orders
            ),
            "symbols": sorted(
                {str(row.get("symbol") or "") for row in orders if row.get("symbol")}
            ),
        },
    )


def _mt5_trading_history_order_info(
    days: int = 30,
    group: str | None = None,
    ticket: int | None = None,
    symbol: str | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 historical orders and summary statistics."""
    end = datetime.now()
    start = end - timedelta(days=max(int(days), 0))
    kwargs: dict[str, Any]
    if ticket is not None and group is None:
        args: tuple[Any, ...] = ()
        kwargs = {"ticket": ticket}
    elif ticket is not None:
        args = (start, end)
        kwargs = {"group": group, "ticket": ticket}
    elif group is not None:
        args = (start, end)
        kwargs = {"group": group}
    else:
        args = (start, end)
        kwargs = {}
    raw_rows = _mt5_client_rows(
        method_name="history_orders_get",
        user_id=user_id,
        mt5_login=mt5_login,
        shutdown=shutdown,
        args=args,
        kwargs=kwargs,
    )
    orders = [_normalize_order(row) for row in list(raw_rows or [])]
    orders = _filtered_limited_rows(orders, symbol=symbol, limit=limit)
    filled_count = sum(1 for row in orders if _to_int(row.get("state")) == 4)
    canceled_count = sum(1 for row in orders if _to_int(row.get("state")) == 2)
    return _rows_payload(
        provider="mt5",
        request={
            "provider": "mt5",
            "days": days,
            "group": group,
            "ticket": ticket,
            "symbol": symbol,
            "limit": limit,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        key="history_orders",
        rows=orders,
        summary={
            "total_history_orders": len(orders),
            "filled_count": filled_count,
            "canceled_count": canceled_count,
            "total_volume_ordered": sum(
                _to_float(row.get("volume_initial")) for row in orders
            ),
            "symbols": sorted(
                {str(row.get("symbol") or "") for row in orders if row.get("symbol")}
            ),
        },
    )


def _mt5_trading_symbol_info(
    symbols: str = "EURUSD",
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 symbol metadata for one or more symbols."""
    requested_symbols = _split_symbols(symbols)
    client, owned_client = _get_mt5_client(user_id=user_id, mt5_login=mt5_login)
    try:
        rows = []
        for symbol in requested_symbols:
            try:
                client.symbol_select(symbol, True)
            except (AttributeError, TypeError, ValueError):
                pass
            rows.append(_normalize_symbol(client.symbol_info(symbol), symbol))
    finally:
        if shutdown and owned_client:
            client.shutdown()

    return _rows_payload(
        provider="mt5",
        request={
            "provider": "mt5",
            "symbols": symbols,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        key="symbols",
        rows=rows,
        summary={"total_symbols": len(rows), "symbols": [row["name"] for row in rows]},
    )


def _mt5_trading_terminal_info(
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 terminal information."""
    terminal = _mt5_client_rows(
        method_name="terminal_info",
        user_id=user_id,
        mt5_login=mt5_login,
        shutdown=shutdown,
    )
    info = _normalize_terminal(terminal)
    return {
        "provider": "mt5",
        "request": {
            "provider": "mt5",
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        "terminal": info,
        "summary": {
            "connected": info["connected"],
            "trade_allowed": info["trade_allowed"],
            "name": info["name"],
            "company": info["company"],
            "build": info["build"],
        },
    }


def _mt5_trading_order_calc_margin(
    order_type: int = 0,
    symbol: str = "EURUSD",
    volume: float = 0.01,
    price: float = 0.0,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Calculate required MT5 margin for an order request."""
    value = _mt5_client_rows(
        method_name="order_calc_margin",
        user_id=user_id,
        mt5_login=mt5_login,
        shutdown=shutdown,
        args=(order_type, symbol, volume, price),
    )
    return {
        "provider": "mt5",
        "request": {
            "provider": "mt5",
            "order_type": order_type,
            "symbol": symbol,
            "volume": volume,
            "price": price,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        "margin": _to_float(value),
    }


def _mt5_trading_order_calc_profit(
    order_type: int = 0,
    symbol: str = "EURUSD",
    volume: float = 0.01,
    price_open: float = 0.0,
    price_close: float = 0.0,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Calculate projected MT5 profit for an order request."""
    value = _mt5_client_rows(
        method_name="order_calc_profit",
        user_id=user_id,
        mt5_login=mt5_login,
        shutdown=shutdown,
        args=(order_type, symbol, volume, price_open, price_close),
    )
    return {
        "provider": "mt5",
        "request": {
            "provider": "mt5",
            "order_type": order_type,
            "symbol": symbol,
            "volume": volume,
            "price_open": price_open,
            "price_close": price_close,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
        },
        "profit": _to_float(value),
    }


def trading_place_order(
    provider: str | None = None,
    symbol: str = "EURUSD",
    order_type: str = "BUY",
    volume: float = 0.01,
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Submit a broker order through a fail-closed execution bridge.

    Args:
        provider: Execution bridge to use. Supported values are "mt5" and
            "ctrader".
        symbol: Symbol to trade.
        order_type: Broker order side/type such as "BUY" or "SELL".
        volume: Order volume in lots.
        price: Requested order price. Use 0.0 for market-style requests.
        sl: Stop-loss price.
        tp: Take-profit price.
        live_enabled: Must be True before the bridge accepts live mutations.

    Returns:
        A JSON-safe execution bridge response. By default the response is
        blocked with reason "live_execution_disabled".
    """
    normalized_provider = _resolve_provider(provider)
    order = {
        "symbol": symbol,
        "order_type": order_type,
        "volume": volume,
        "price": price,
        "sl": sl,
        "tp": tp,
    }
    if normalized_provider == "mt5":
        from app.services.execution.bridges.mt5_bridge import MT5Bridge

        return cast(
            "dict[str, Any]",
            _json_safe(MT5Bridge(live_enabled=live_enabled).place_order(order)),
        )
    if _is_ctrader_provider(normalized_provider):
        from app.services.execution.bridges.ctrader_bridge import CTraderBridge

        return cast(
            "dict[str, Any]",
            _json_safe(CTraderBridge(live_enabled=live_enabled).place_order(order)),
        )
    raise ValueError("provider must be 'mt5' or 'ctrader'")


def place_market_order(
    provider: str | None = None,
    symbol: str = "EURUSD",
    side: str = "BUY",
    volume: float = 0.01,
    sl: float = 0.0,
    tp: float = 0.0,
    comment: str = "",
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Place a market order through the active broker bridge.

    Args:
        provider: Optional provider override. When omitted, the active
            `trading_connect()` provider is used.
        symbol: Symbol to trade.
        side: Market side, usually "BUY" or "SELL".
        volume: Order volume in lots.
        sl: Stop-loss price.
        tp: Take-profit price.
        comment: Optional broker/order comment.
        live_enabled: Must be True before the bridge accepts live mutations.

    Returns:
        A JSON-safe bridge response. By default this is blocked with reason
        "live_execution_disabled".
    """
    normalized_provider = _resolve_provider(provider)
    order = {
        "kind": "market",
        "symbol": symbol,
        "order_type": side.upper(),
        "volume": volume,
        "price": 0.0,
        "sl": sl,
        "tp": tp,
        "comment": comment,
    }
    bridge = _execution_bridge(normalized_provider, live_enabled=live_enabled)
    return cast("dict[str, Any]", _json_safe(bridge.place_order(order)))


def _broker_place_pending_order(
    provider: str | None = None,
    symbol: str = "EURUSD",
    order_type: str = "BUY_LIMIT",
    volume: float = 0.01,
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    expiration: str | None = None,
    comment: str = "",
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Place a pending order through the active broker bridge.

    Args:
        provider: Optional provider override. When omitted, the active
            `trading_connect()` provider is used.
        symbol: Symbol to trade.
        order_type: Pending order type such as "BUY_LIMIT" or "SELL_STOP".
        volume: Order volume in lots.
        price: Requested pending-order price.
        sl: Stop-loss price.
        tp: Take-profit price.
        expiration: Optional ISO timestamp/string expiration.
        comment: Optional broker/order comment.
        live_enabled: Must be True before the bridge accepts live mutations.

    Returns:
        A JSON-safe bridge response. By default this is blocked with reason
        "live_execution_disabled".
    """
    normalized_provider = _resolve_provider(provider)
    order = {
        "kind": "pending",
        "symbol": symbol,
        "order_type": order_type.upper(),
        "volume": volume,
        "price": price,
        "sl": sl,
        "tp": tp,
        "expiration": expiration,
        "comment": comment,
    }
    bridge = _execution_bridge(normalized_provider, live_enabled=live_enabled)
    return cast("dict[str, Any]", _json_safe(bridge.place_order(order)))


def _broker_modify_position(
    provider: str | None = None,
    position_id: str = "",
    symbol: str = "",
    sl: float = 0.0,
    tp: float = 0.0,
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Modify stop-loss/take-profit on an open position.

    The current execution bridge does not yet expose a live modify-position
    primitive, so this tool returns a fail-closed response until that service
    method is implemented.
    """
    normalized_provider = _resolve_provider(provider)
    payload = {
        "position_id": position_id,
        "symbol": symbol,
        "sl": sl,
        "tp": tp,
        "live_enabled": live_enabled,
    }
    reason = (
        "live_execution_disabled"
        if not live_enabled
        else "modify_position_not_supported_by_bridge"
    )
    return _blocked_action(
        provider=normalized_provider,
        action="modify_position",
        reason=reason,
        payload=payload,
    )


def modify_pending_order(
    provider: str | None = None,
    order_id: str = "",
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    expiration: str | None = None,
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Modify price/SL/TP/expiration on a pending order.

    The current execution bridge does not yet expose a live modify-pending-order
    primitive, so this tool returns a fail-closed response until that service
    method is implemented.
    """
    normalized_provider = _resolve_provider(provider)
    payload = {
        "order_id": order_id,
        "price": price,
        "sl": sl,
        "tp": tp,
        "expiration": expiration,
        "live_enabled": live_enabled,
    }
    reason = (
        "live_execution_disabled"
        if not live_enabled
        else "modify_pending_order_not_supported_by_bridge"
    )
    return _blocked_action(
        provider=normalized_provider,
        action="modify_pending_order",
        reason=reason,
        payload=payload,
    )


def _broker_close_position(
    provider: str | None = None,
    position_id: str = "",
    symbol: str = "",
    volume: float | None = None,
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Close an open position fully or partially.

    Args:
        provider: Optional provider override. When omitted, the active
            `trading_connect()` provider is used.
        position_id: Broker position/ticket identifier.
        symbol: Optional symbol fallback for position lookup.
        volume: Optional partial-close volume. When omitted, the request is a
            full close. Partial close is fail-closed until bridge support lands.
        live_enabled: Must be True before the bridge accepts live mutations.

    Returns:
        A JSON-safe bridge response.
    """
    normalized_provider = _resolve_provider(provider)
    payload = {
        "position_id": position_id,
        "symbol": symbol,
        "volume": volume,
        "live_enabled": live_enabled,
    }
    if volume is not None:
        reason = (
            "live_execution_disabled"
            if not live_enabled
            else "partial_close_not_supported_by_bridge"
        )
        return _blocked_action(
            provider=normalized_provider,
            action="close_position",
            reason=reason,
            payload=payload,
        )

    bridge = _execution_bridge(normalized_provider, live_enabled=live_enabled)
    target = position_id or symbol
    return cast("dict[str, Any]", _json_safe(bridge.close_position(str(target))))


def _is_simulator_session_candidate(value: Any) -> bool:
    return hasattr(value, "simulator") and hasattr(value, "config")


def _sim_trade_service():
    from app.api.session import trade_service

    return trade_service


def place_pending_order(
    *args: Any, mode: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    if mode == "sim" or (args and _is_simulator_session_candidate(args[0])):
        return _sim_trade_service().place_pending_order(*args, **kwargs)
    return _broker_place_pending_order(*args, **kwargs)


def modify_position(
    *args: Any, mode: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    if mode == "sim" or (args and _is_simulator_session_candidate(args[0])):
        return _sim_trade_service().modify_position(*args, **kwargs)
    return _broker_modify_position(*args, **kwargs)


def close_position(
    *args: Any, mode: str | None = None, **kwargs: Any
) -> dict[str, Any]:
    if mode == "sim" or (args and _is_simulator_session_candidate(args[0])):
        return _sim_trade_service().close_position(*args, **kwargs)
    return _broker_close_position(*args, **kwargs)


def execute_trade(
    *args: Any, mode: str | None = "sim", **kwargs: Any
) -> dict[str, Any]:
    return _sim_trade_service().execute_trade(*args, **kwargs)


def preview_trade(
    *args: Any, mode: str | None = "sim", **kwargs: Any
) -> dict[str, Any]:
    return _sim_trade_service().preview_trade(*args, **kwargs)


def evaluate_what_if(
    *args: Any, mode: str | None = "sim", **kwargs: Any
) -> dict[str, Any]:
    return _sim_trade_service().evaluate_what_if(*args, **kwargs)


def partial_close_position(
    *args: Any, mode: str | None = "sim", **kwargs: Any
) -> dict[str, Any]:
    return _sim_trade_service().partial_close_position(*args, **kwargs)


def modify_order(*args: Any, mode: str | None = "sim", **kwargs: Any) -> dict[str, Any]:
    return _sim_trade_service().modify_order(*args, **kwargs)


def delete_order(*args: Any, mode: str | None = "sim", **kwargs: Any) -> dict[str, Any]:
    return _sim_trade_service().delete_order(*args, **kwargs)


def cancel_pending_order(
    provider: str | None = None,
    order_id: str = "",
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Cancel a pending order through the active broker bridge.

    Args:
        provider: Optional provider override. When omitted, the active
            `trading_connect()` provider is used.
        order_id: Broker pending-order identifier.
        live_enabled: Must be True before the bridge accepts live mutations.

    Returns:
        A JSON-safe bridge response. By default this is blocked with reason
        "live_execution_disabled".
    """
    normalized_provider = _resolve_provider(provider)
    bridge = _execution_bridge(normalized_provider, live_enabled=live_enabled)
    return cast("dict[str, Any]", _json_safe(bridge.cancel_order(str(order_id))))


def _mt5_trading_deal_history(
    days: int = 30,
    group: str | None = None,
    ticket: int | None = None,
    symbol: str | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe MT5 historical deal rows and aggregate statistics.

    Args:
        days: Number of calendar days to look back from the current local time.
        group: Optional MT5 group filter such as "*USD*".
        ticket: Optional deal ticket filter.
        symbol: Optional exact symbol filter applied after retrieval.
        limit: Maximum number of most-recent deals to return. Use 0 for all.
        user_id: Application user ID used to load saved MT5 credentials.
        mt5_login: Optional MT5 login override.
        shutdown: Whether to close the MT5 client connection after reading the
            deal history.

    Returns:
        A JSON-safe payload containing request metadata, row count, normalized
        deal records, and summary statistics for profit, commission, swap, net
        result, and symbols.
    """
    end = datetime.now()
    start = end - timedelta(days=max(int(days), 0))
    client, owned_client = _get_mt5_client(user_id=user_id, mt5_login=mt5_login)
    try:
        if ticket is not None and group is None:
            rows = client.history_deals_get(ticket=ticket)
        elif ticket is not None:
            rows = client.history_deals_get(start, end, group=group, ticket=ticket)
        elif group is not None:
            rows = client.history_deals_get(start, end, group=group)
        else:
            rows = client.history_deals_get(start, end)
    finally:
        if shutdown and owned_client:
            client.shutdown()

    deals = [_normalize_deal(row) for row in list(rows or [])]
    if symbol is not None:
        normalized_symbol = symbol.upper().strip()
        deals = [
            deal
            for deal in deals
            if str(deal.get("symbol") or "").upper() == normalized_symbol
        ]
    deals = sorted(
        deals,
        key=lambda deal: _to_int(deal.get("time_msc"), _to_int(deal.get("time"))),
    )
    if limit > 0:
        deals = deals[-int(limit) :]

    return _deal_payload(
        provider="mt5",
        request={
            "provider": "mt5",
            "days": days,
            "group": group,
            "ticket": ticket,
            "symbol": symbol,
            "limit": limit,
            "user_id": user_id,
            "mt5_login": mt5_login,
            "shutdown": shutdown,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        deals=deals,
    )


def _ctrader_trading_account_info(
    live_enabled: bool = False,
) -> dict[str, Any]:
    """Retrieve JSON-safe cTrader account information.

    Args:
        live_enabled: Whether to initialize the execution bridge in live-enabled
            mode. The current cTrader bridge returns a normalized account
            snapshot without sending live trade mutations.

    Returns:
        A JSON-safe payload containing request metadata, provider name, raw
        account fields, and a normalized summary with balance/equity/margin
        values when the bridge provides them.
    """
    from app.services.execution.bridges.ctrader_bridge import CTraderBridge

    bridge = CTraderBridge(live_enabled=live_enabled)
    account = _json_safe(bridge.get_account_info())
    if not isinstance(account, Mapping):
        account = {"value": account}

    account = {
        **dict(account),
        "account_id": (
            "paper-ctrader"
            if account.get("account_id") == "paper-mt5"
            else account.get("account_id")
        ),
        "provider": "ctrader",
        "bridge": "ctrader",
    }

    return _account_payload(
        provider="ctrader",
        request={
            "provider": "ctrader",
            "live_enabled": live_enabled,
        },
        account=account,
    )


def trading_position_info(
    provider: str | None = None,
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe open positions for a trading provider."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_position_info(
            symbol=symbol,
            group=group,
            ticket=ticket,
            limit=limit,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    if _is_ctrader_provider(normalized_provider):
        from app.services.execution.bridges.ctrader_bridge import CTraderBridge

        rows = [
            _normalize_position(row)
            for row in CTraderBridge(live_enabled=False).get_open_positions()
        ]
        rows = _filtered_limited_rows(rows, symbol=symbol, limit=limit)
        return _rows_payload(
            provider="ctrader",
            request={
                "provider": "ctrader",
                "symbol": symbol,
                "group": group,
                "ticket": ticket,
                "limit": limit,
            },
            key="positions",
            rows=rows,
            summary={"total_positions": len(rows)},
        )
    raise ValueError("provider must be 'mt5' or 'ctrader'")


def trading_order_info(
    provider: str | None = None,
    symbol: str | None = None,
    group: str | None = None,
    ticket: int | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe active or pending orders for a trading provider."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_order_info(
            symbol=symbol,
            group=group,
            ticket=ticket,
            limit=limit,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    if _is_ctrader_provider(normalized_provider):
        from app.services.execution.bridges.ctrader_bridge import CTraderBridge

        rows = [
            _normalize_order(row)
            for row in CTraderBridge(live_enabled=False).get_pending_orders()
        ]
        rows = _filtered_limited_rows(rows, symbol=symbol, limit=limit)
        return _rows_payload(
            provider="ctrader",
            request={
                "provider": "ctrader",
                "symbol": symbol,
                "group": group,
                "ticket": ticket,
                "limit": limit,
            },
            key="orders",
            rows=rows,
            summary={"total_orders": len(rows)},
        )
    raise ValueError("provider must be 'mt5' or 'ctrader'")


def trading_history_order_info(
    provider: str | None = None,
    days: int = 30,
    group: str | None = None,
    ticket: int | None = None,
    symbol: str | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe historical orders for a trading provider."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_history_order_info(
            days=days,
            group=group,
            ticket=ticket,
            symbol=symbol,
            limit=limit,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    raise ValueError("provider must be 'mt5' for history orders")


def trading_symbol_info(
    provider: str | None = None,
    symbols: str = "EURUSD",
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe symbol metadata for a trading provider."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_symbol_info(
            symbols=symbols,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    if _is_ctrader_provider(normalized_provider):
        from app.services.execution.bridges.ctrader_bridge import CTraderBridge

        bridge = CTraderBridge(live_enabled=False)
        rows = [
            _normalize_symbol(bridge.get_symbol_info(symbol), symbol)
            for symbol in _split_symbols(symbols)
        ]
        return _rows_payload(
            provider="ctrader",
            request={"provider": "ctrader", "symbols": symbols},
            key="symbols",
            rows=rows,
            summary={
                "total_symbols": len(rows),
                "symbols": [row["name"] for row in rows],
            },
        )
    raise ValueError("provider must be 'mt5' or 'ctrader'")


def trading_terminal_info(
    provider: str | None = None,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe terminal information for a trading provider."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_terminal_info(
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    raise ValueError("provider must be 'mt5' for terminal info")


def trading_order_calc_margin(
    provider: str | None = None,
    order_type: int = 0,
    symbol: str = "EURUSD",
    volume: float = 0.01,
    price: float = 0.0,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Calculate required margin for a provider order request."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_order_calc_margin(
            order_type=order_type,
            symbol=symbol,
            volume=volume,
            price=price,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    raise ValueError("provider must be 'mt5' for margin calculation")


def trading_order_calc_profit(
    provider: str | None = None,
    order_type: int = 0,
    symbol: str = "EURUSD",
    volume: float = 0.01,
    price_open: float = 0.0,
    price_close: float = 0.0,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Calculate projected profit for a provider order request."""
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_order_calc_profit(
            order_type=order_type,
            symbol=symbol,
            volume=volume,
            price_open=price_open,
            price_close=price_close,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    raise ValueError("provider must be 'mt5' for profit calculation")


def trading_deal_history(
    provider: str | None = None,
    days: int = 30,
    group: str | None = None,
    ticket: int | None = None,
    symbol: str | None = None,
    limit: int = 100,
    user_id: int = 1,
    mt5_login: int | None = None,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe historical deal rows for a trading provider.

    Args:
        provider: Trading backend to query. Currently supported value is "mt5".
        days: Number of calendar days to look back.
        group: Optional broker group filter.
        ticket: Optional deal ticket filter.
        symbol: Optional exact symbol filter.
        limit: Maximum number of most-recent deals to return. Use 0 for all.
        user_id: Application user ID used by the MT5 credential loader.
        mt5_login: Optional MT5 login override.
        shutdown: Whether the MT5 client should be shut down after reading the
            deal history.

    Returns:
        A JSON-safe deal-history payload suitable for application code and agent
        tool calls.
    """
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_deal_history(
            days=days,
            group=group,
            ticket=ticket,
            symbol=symbol,
            limit=limit,
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    raise ValueError("provider must be 'mt5' for deal history")


def trading_account_info(
    provider: str | None = None,
    user_id: int = 1,
    mt5_login: int | None = None,
    live_enabled: bool = False,
    shutdown: bool = True,
) -> dict[str, Any]:
    """Retrieve JSON-safe trading account information for a broker provider.

    Args:
        provider: Trading backend to query. Supported values are "mt5" and
            "ctrader".
        user_id: Application user ID used by the MT5 credential loader.
        mt5_login: Optional MT5 login override.
        live_enabled: cTrader bridge live-mode flag.
        shutdown: Whether the MT5 client should be shut down after reading the
            account snapshot.

    Returns:
        A JSON-safe account-info payload suitable for application code and agent
        tool calls.
    """
    normalized_provider = _resolve_provider(provider)
    if normalized_provider == "mt5":
        return _mt5_trading_account_info(
            user_id=user_id,
            mt5_login=mt5_login,
            shutdown=shutdown,
        )
    if _is_ctrader_provider(normalized_provider):
        return _ctrader_trading_account_info(live_enabled=live_enabled)
    raise ValueError("provider must be 'mt5' or 'ctrader'")


__all__ = [
    "Trade",
    "TradeResult",
    "cancel_pending_order",
    "close_position",
    "delete_order",
    "evaluate_what_if",
    "execute_trade",
    "modify_order",
    "modify_pending_order",
    "modify_position",
    "partial_close_position",
    "place_market_order",
    "place_pending_order",
    "preview_trade",
    "trading_account_info",
    "trading_connect",
    "trading_deal_history",
    "trading_disconnect",
    "trading_history_order_info",
    "trading_is_connected",
    "trading_order_calc_margin",
    "trading_order_calc_profit",
    "trading_order_info",
    "trading_place_order",
    "trading_position_info",
    "trading_symbol_info",
    "trading_terminal_info",
]
