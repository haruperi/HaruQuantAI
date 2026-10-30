"""Object-scoped MQL-style dispatch over typed broker operations."""

from __future__ import annotations

import fnmatch
import inspect
from copy import deepcopy
from dataclasses import asdict
from typing import Any, ClassVar

from app.core.data.contracts import (
    BridgeError,
    DealInfo,
    OrderInfo,
    PositionInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.core.enums import OrderFilling, OrderType
from app.workspace.trading.base import normalize_request


class TradingDispatcher:
    """Adapt a broker while isolating selection and request state per API object."""

    _COLLECTION_SPECS: ClassVar[
        dict[str, tuple[str, str, type[Any], str, tuple[str, ...], tuple[str, ...]]]
    ] = {
        "PositionInfo": (
            "get_positions",
            "_selected_position",
            PositionInfo,
            "PositionsTotal",
            ("PositionsGet", "positions"),
            ("PositionGetTicket", "PositionSelectByTicket", "SelectByTicket"),
        ),
        "OrderInfo": (
            "get_orders",
            "_selected_order",
            OrderInfo,
            "OrdersTotal",
            ("OrdersGet", "orders"),
            ("OrderGetTicket", "OrderSelect", "Select", "SelectByTicket"),
        ),
        "HistoryOrderInfo": (
            "get_history_orders",
            "_selected_history_order",
            OrderInfo,
            "HistoryOrdersTotal",
            ("HistoryOrdersGet", "orders"),
            (
                "HistoryOrderGetTicket",
                "HistoryOrderSelect",
                "Select",
                "SelectByTicket",
                "Ticket",
            ),
        ),
        "DealInfo": (
            "get_deals",
            "_selected_deal",
            DealInfo,
            "HistoryDealsTotal",
            ("HistoryDealsGet", "deals"),
            (
                "HistoryDealGetTicket",
                "HistoryDealSelect",
                "Select",
                "SelectByTicket",
                "Ticket",
            ),
        ),
    }

    def __init__(self, client: Any) -> None:
        self.client = client
        self.name = client.name
        self._current_symbol = "EURUSD"
        self._selected_position: Any = None
        self._selected_order: Any = None
        self._selected_history_order: Any = None
        self._selected_deal: Any = None
        self._request = TradeRequest()
        self._result = TradeResult()
        self._check_result = TradeCheckResult()
        self._settings: dict[str, Any] = {}

    def __getattr__(self, name: str) -> Any:
        """Delegate typed broker operations to the selected client."""
        return getattr(self.client, name)

    async def _trade_operation(self, method: str, args: list[Any]) -> Any:
        request = self._coerce_trade_request(args[0] if args else None)
        self._request = deepcopy(request)
        operation = (
            self.client.order_send if method == "OrderSend" else self.client.order_check
        )
        result = operation(request)
        if inspect.isawaitable(result):
            result = await result
        if method == "OrderSend":
            self._result = deepcopy(result)
        else:
            self._check_result = deepcopy(result)
        return result

    @staticmethod
    def _lookup_case_insensitive_attr(
        obj: Any, method_name: str, default: Any = None
    ) -> Any:
        """Resolve an attribute on `obj` case-insensitively."""
        target = method_name.lower()
        for attr in dir(obj):
            if attr.lower() == target and not attr.startswith("_"):
                return getattr(obj, attr)
        return getattr(obj, method_name, default)

    async def _dispatch_collection(
        self, class_name: str, method_name: str, args: list[Any]
    ) -> Any:
        """Dispatch collection queries and cursor selections for positions, orders, and deals."""
        getter_name, sel_attr, default_cls, total_m, list_ms, ticket_ms = (
            self._COLLECTION_SPECS[class_name]
        )
        raw = getattr(self, getter_name)()
        if inspect.isawaitable(raw):
            raw = await raw
        items = list(raw)
        filters = args[0] if args and isinstance(args[0], dict) else {}
        unknown = set(filters) - {"symbol", "ticket", "position", "group"}
        if unknown:
            raise BridgeError(
                "Unsupported collection filter", code="UNSUPPORTED_OPERATION"
            )
        for key, value in filters.items():
            if key == "group":
                patterns = [
                    part.strip() for part in str(value).split(",") if part.strip()
                ]
                include = [part for part in patterns if not part.startswith("!")]
                exclude = [part[1:] for part in patterns if part.startswith("!")]
                items = [
                    item
                    for item in items
                    if (
                        not include
                        or any(fnmatch.fnmatch(item.symbol, pat) for pat in include)
                    )
                    and not any(fnmatch.fnmatch(item.symbol, pat) for pat in exclude)
                ]
            else:
                attr = "position_id" if key == "position" else key
                items = [item for item in items if getattr(item, attr, None) == value]

        if method_name == total_m:
            return len(items)
        if method_name in list_ms:
            if (
                class_name == "PositionInfo"
                and args
                and isinstance(args[0], str)
                and args[0]
            ):
                return [p for p in items if getattr(p, "symbol", "") == args[0]]
            return items
        if method_name in (class_name, "info"):
            selected = getattr(self, sel_attr)
            return (
                selected
                if selected is not None
                else (items[0] if items else default_cls())
            )
        if method_name == "SelectByIndex":
            idx = int(args[0]) if args else 0
            if 0 <= idx < len(items):
                setattr(self, sel_attr, items[idx])
                return True
            return False
        if method_name in ticket_ms:
            ticket = int(args[0]) if args else 0
            hit = next((i for i in items if getattr(i, "ticket", 0) == ticket), None)
            if hit is not None:
                setattr(self, sel_attr, hit)
                return True
            return False
        if class_name == "PositionInfo" and method_name in ("Select", "SelectByMagic"):
            sym = str(args[0]) if args else ""
            magic = int(args[1]) if len(args) > 1 else 0
            hit = next(
                (
                    p
                    for p in items
                    if getattr(p, "symbol", "") == sym
                    and (method_name == "Select" or getattr(p, "magic", 0) == magic)
                ),
                None,
            )
            if hit is not None:
                self._selected_position = hit
                return True
            return False
        if class_name in ("PositionInfo", "OrderInfo") and method_name in (
            "StoreState",
            "CheckState",
        ):
            return True
        raise BridgeError(
            f"{self.name} does not support {class_name}.{method_name}",
            code="UNSUPPORTED_OPERATION",
        )

    def dispatch(self, class_name: str, method_name: str, args: list[Any]) -> Any:
        """Route generic calls directly to TradingClient typed methods."""
        if class_name == "TerminalInfo":
            t = self.get_terminal_info()
            if method_name in ("TerminalInfo", "info"):
                return t
            return self._lookup_case_insensitive_attr(t, method_name, default=t)

        if class_name == "AccountInfo":
            acc = self.get_account_info()
            if method_name in ("AccountInfo", "info"):
                return acc
            if method_name in ("OrderProfitCheck", "MarginCheck"):
                sym = str(args[0]) if len(args) > 0 else "EURUSD"
                otype = OrderType(int(args[1])) if len(args) > 1 else OrderType.BUY
                vol = float(args[2]) if len(args) > 2 else 1.0
                p1 = float(args[3]) if len(args) > 3 else 0.0
                if method_name == "MarginCheck":
                    return self.calc_margin(otype, sym, vol, p1)
                p2 = float(args[4]) if len(args) > 4 else 0.0
                return self.calc_profit(otype, sym, vol, p1, p2)
            if method_name == "FreeMarginCheck":
                if inspect.isawaitable(acc):

                    async def _free(awaitable: Any) -> float:
                        return float(getattr(await awaitable, "margin_free", 0.0))

                    return _free(acc)
                return float(getattr(acc, "margin_free", 0.0))
            if method_name == "MaxLotCheck":
                return 100.0
            return self._lookup_case_insensitive_attr(acc, method_name)

        if class_name == "SymbolInfo":
            sym = (
                args[0]
                if args and isinstance(args[0], str)
                else getattr(self, "_current_symbol", "EURUSD")
            )
            if method_name in ("SymbolInfo", "info"):
                return self.get_symbol_info(sym)
            if method_name == "SymbolsTotal":
                return len(self.get_symbols())
            if method_name in ("SymbolsGet", "symbols"):
                all_syms = self.get_symbols()
                if args and isinstance(args[0], str) and args[0]:
                    tokens = [p.strip() for p in args[0].split(",") if p.strip()]
                    inc = [p for p in tokens if not p.startswith("!")]
                    exc = [p[1:] for p in tokens if p.startswith("!")]
                    return [
                        s
                        for s in all_syms
                        if (not inc or any(fnmatch.fnmatch(s, p) for p in inc))
                        and not any(fnmatch.fnmatch(s, p) for p in exc)
                    ]
                return all_syms
            if method_name == "SymbolInfoTick":
                return self.get_tick(sym)
            if method_name == "SymbolSelect":
                return self.select_symbol(sym, bool(args[1]) if len(args) > 1 else True)
            if method_name in ("MarketBookAdd", "subscribe_book"):
                return self.subscribe_book(sym)
            if method_name in ("MarketBookRelease", "release_book"):
                return self.release_book(sym)
            if method_name in ("MarketBookGet", "get_book"):
                return self.get_book(sym)
            if method_name in ("Refresh", "RefreshRates", "IsSynchronized"):
                return True
            if method_name == "NormalizePrice":
                return round(
                    float(args[0]) if args else 0.0,
                    int(args[1]) if len(args) > 1 else 5,
                )
            if method_name in ("Name", "Select"):
                if args and isinstance(args[0], str):
                    self._current_symbol = args[0]
                    return self.get_symbol_info(args[0]) is not None
                return (
                    getattr(self, "_current_symbol", "EURUSD")
                    if method_name == "Name"
                    else True
                )
            return self._lookup_case_insensitive_attr(
                self.get_symbol_info(sym), method_name
            )

        if class_name in self._COLLECTION_SPECS:
            return self._dispatch_collection(class_name, method_name, args)

        if class_name == "Trade":
            if method_name in ("OrderSend", "OrderCheck"):
                return self._trade_operation(method_name, args)
            if method_name in {
                "LogLevel",
                "SetExpertMagicNumber",
                "SetDeviationInPoints",
                "SetTypeFilling",
                "SetMarginMode",
            }:
                self._settings[method_name] = args[0] if args else None
                return True
            if method_name == "SetAsyncMode":
                if args and args[0]:
                    raise BridgeError(
                        "Queued execution is unsupported", code="UNSUPPORTED_OPERATION"
                    )
                return None
            if method_name == "SetTypeFillingBySymbol":
                spec = self.client.get_symbol_info(str(args[0]))
                if spec is None:
                    return False
                filling = spec.trade.filling
                if "Fill or Kill" in filling:
                    mode = OrderFilling.FOK
                elif "Immediate or Cancel" in filling:
                    mode = OrderFilling.IOC
                elif spec.trade.execution != "Market":
                    mode = OrderFilling.RETURN
                else:
                    return False
                self._settings["SetTypeFilling"] = int(mode)
                return True
            snapshots = {
                "Request": self._request,
                "Result": self._result,
                "CheckResult": self._check_result,
            }
            if method_name in snapshots:
                return deepcopy(snapshots[method_name])
            if method_name in ("FormatRequest", "FormatRequestResult"):
                return (
                    str(asdict(self._request))
                    if method_name == "FormatRequest"
                    else str(asdict(self._result))
                )
            if method_name in ("PrintRequest", "PrintResult"):
                self.client.logger.info(
                    "%s: %s",
                    method_name,
                    self._request if method_name == "PrintRequest" else self._result,
                )
                return True

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

    def _coerce_trade_request(self, req: Any) -> TradeRequest:
        """Normalize requests with the same rules used by the public trading API."""
        return normalize_request(TradeRequest() if req is None else req)


__all__ = ["TradingDispatcher"]
