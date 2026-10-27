"""Backend-neutral proxy identity, serialization, and snapshot helpers."""

from __future__ import annotations

import asyncio
import math
import uuid
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any, TypeVar

from app.host.logging import get_logger
from app.include.contracts import (
    OrderInfo,
    PositionInfo,
    PropertyValue,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)
from app.include.enums import (
    OrderFilling,
    OrderTime,
    OrderType,
    TradeAction,
    TradeRetcode,
)

_T = TypeVar("_T")


logger = get_logger(__name__)


class TradingClass:
    """Backend-neutral object identity and serialized async forwarding."""

    CLASS_NAME = "Base"
    TRADING_METHODS: frozenset[str] = frozenset()

    def __init__(
        self, backend: TradingBackend, *, object_id: str | None = None
    ) -> None:
        logger.debug("FR-TRADING-COMPOSITION: creating object")
        self.backend = backend
        self.object_id = object_id or f"{self.CLASS_NAME.lower()}-{uuid.uuid4().hex}"
        self._lock = asyncio.Lock()

    @property
    def last_command_id(self) -> str | None:
        """Return the last command in this task context."""
        return self.backend.last_command_id()

    async def _call(self, method: str, *args: Any) -> Any:
        logger.debug(
            "FR-TRADING-COMPOSITION: invoking backend",
            extra={"class_name": self.CLASS_NAME, "method_name": method},
        )
        wire_args: list[Any] = []
        for value in args:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    raise ValueError("trading datetimes must include a timezone")
                wire_args.append(int(value.timestamp()))
            else:
                wire_args.append(value)
        async with self._lock:
            return await self.backend.call(
                object_id=self.object_id,
                class_name=self.CLASS_NAME,
                method_name=method,
                args=wire_args,
                requires_arm=method in self.TRADING_METHODS,
            )

    async def _property(self, method: str, *args: Any) -> PropertyValue:
        value = await self._call(method, *args)
        if isinstance(value, dict) and {"ok", "value"} <= value.keys():
            return PropertyValue(
                ok=bool(value["ok"]),
                value=value.get("value"),
                error=value.get("error"),
            )
        return PropertyValue(ok=True, value=value)

    async def _snapshot(
        self, method: str, model_cls: type[_T], label: str, *args: Any
    ) -> _T:
        """Execute backend snapshot call and coerce dict into model_cls."""
        data = await self._call(method, *args)
        if isinstance(data, model_cls):
            return data
        if isinstance(data, dict):
            return model_cls(**data)
        raise TypeError(f"unexpected {label} type: {type(data).__name__}")

    async def _snapshot_dict(
        self, model_cls: type[Any], label: str, *args: Any
    ) -> dict[str, Any]:
        """Execute backend as_dict call and coerce model_cls into dict."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, model_cls):
            return asdict(data)
        raise TypeError(f"unexpected {label} dictionary type: {type(data).__name__}")

    async def _collection(
        self, method: str, model_cls: type[_T], *args: Any, **kwargs: Any
    ) -> list[_T]:
        """Execute backend collection call and coerce items into model_cls."""
        if args and kwargs:
            raise TypeError("use positional arguments or keyword filters, not both")
        data = (
            await self._call(method, kwargs)
            if kwargs
            else await self._call(method, *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, model_cls) else model_cls(**item)
                for item in data
            ]
        raise TypeError(f"unexpected {method} return type: {type(data).__name__}")


def serialize_request(req: TradeRequest | dict[str, Any]) -> dict[str, Any]:
    """Serialize a TradeRequest or dictionary to wire-compatible dictionary."""
    if isinstance(req, TradeRequest):
        data: dict[str, Any] = {
            "action": int(req.action),
            "symbol": req.symbol,
            "volume": float(req.volume),
            "order_type": int(req.order_type),
            "price": float(req.price),
            "stoplimit": float(req.stoplimit),
            "sl": float(req.sl),
            "tp": float(req.tp),
            "deviation": req.deviation,
            "magic": req.magic,
            "order": req.order,
            "position": req.position,
            "position_by": req.position_by,
            "type_filling": int(req.type_filling),
            "type_time": int(req.type_time),
            "comment": req.comment,
        }
        if req.expiration is not None:
            if req.expiration.tzinfo is None:
                raise ValueError("trading datetimes must include a timezone")
            data["expiration"] = int(req.expiration.timestamp())
        return data
    return serialize_request(normalize_request(req))


def normalize_request(data: TradeRequest | dict[str, Any]) -> TradeRequest:
    """Normalize request mappings, native aliases, and UTC expiration times."""
    if isinstance(data, TradeRequest):
        if data.expiration is not None and data.expiration.tzinfo is None:
            raise ValueError("trading datetimes must include a timezone")
        return data
    action_val = data.get("action", TradeAction.DEAL)
    action = (
        action_val
        if isinstance(action_val, TradeAction)
        else TradeAction(int(action_val))
    )
    order_type_val = data.get("type", data.get("order_type", OrderType.BUY))
    order_type = (
        order_type_val
        if isinstance(order_type_val, OrderType)
        else OrderType(int(order_type_val))
    )
    filling_val = data.get("type_filling", OrderFilling.FOK)
    filling = (
        filling_val
        if isinstance(filling_val, OrderFilling)
        else OrderFilling(int(filling_val))
    )
    time_val = data.get("type_time", OrderTime.GTC)
    type_time = (
        time_val if isinstance(time_val, OrderTime) else OrderTime(int(time_val))
    )

    exp_val = data.get("expiration")
    expiration: datetime | None = None
    if isinstance(exp_val, datetime):
        if exp_val.tzinfo is None:
            raise ValueError("trading datetimes must include a timezone")
        expiration = exp_val
    elif isinstance(exp_val, (int, float)) and exp_val > 0:
        expiration = datetime.fromtimestamp(exp_val, tz=UTC)

    return TradeRequest(
        action=action,
        magic=int(data.get("magic", 0)),
        order=int(data.get("order", 0)),
        symbol=str(data.get("symbol", "")),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        stoplimit=float(data.get("stoplimit", 0.0)),
        sl=float(data.get("sl", 0.0)),
        tp=float(data.get("tp", 0.0)),
        deviation=int(data.get("deviation", 0)),
        order_type=order_type,
        type_filling=filling,
        type_time=type_time,
        expiration=expiration,
        comment=str(data.get("comment", "")),
        position=int(data.get("position", 0)),
        position_by=int(data.get("position_by", 0)),
    )


def build_trade_result(data: dict[str, Any]) -> TradeResult:
    """Decode a backend execution result."""
    return TradeResult(
        retcode=int(data.get("retcode", int(TradeRetcode.ERROR))),
        deal=int(data.get("deal", 0)),
        order=int(data.get("order", 0)),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        bid=float(data.get("bid", 0.0)),
        ask=float(data.get("ask", 0.0)),
        comment=str(data.get("comment", "")),
        request_id=int(data.get("request_id", 0)),
        retcode_external=int(data.get("retcode_external", 0)),
        retcode_description=str(data.get("retcode_description", "")),
        raw=data.get("raw", data),
    )


def build_trade_check_result(data: dict[str, Any]) -> TradeCheckResult:
    """Decode a backend validation result."""
    return TradeCheckResult(
        retcode=int(data.get("retcode", int(TradeRetcode.ERROR))),
        balance=float(data.get("balance", 0.0)),
        equity=float(data.get("equity", 0.0)),
        profit=float(data.get("profit", 0.0)),
        margin=float(data.get("margin", 0.0)),
        margin_free=float(data.get("margin_free", 0.0)),
        margin_level=float(data.get("margin_level", 0.0)),
        comment=str(data.get("comment", "")),
        raw=data.get("raw", data),
    )


@dataclass(frozen=True, slots=True)
class TradeFilter:
    """Explicit trading scope; None means any symbol/magic, direction 0 means either.

    Comments match by substring. A magic of zero matches zero exactly.
    Resolve strategy aliases such as Current before constructing this filter.
    """

    symbol: str | None
    direction: int = 0
    magic: int | None = None
    comment: str = ""
    ticket: int | None = None

    def __post_init__(self) -> None:
        """Validate the direction selector."""
        if type(self.direction) is not int or self.direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0, or 1")

    def matches(self, item: PositionInfo | OrderInfo) -> bool:
        """Match one canonical position or working order without backend filtering."""
        kind = item.position_type if isinstance(item, PositionInfo) else item.order_type
        direction = 1 if kind in (0, 2, 4, 6) else -1
        return (
            (self.symbol is None or item.symbol == self.symbol)
            and (self.direction in (0, direction))
            and (self.magic is None or item.magic == self.magic)
            and (not self.comment or self.comment in item.comment)
            and (self.ticket is None or item.ticket == self.ticket)
        )


def aware_timestamp(value: datetime) -> float:
    """Validate an explicit evaluation timestamp and return epoch seconds."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("evaluation timestamps must include a timezone")
    return value.timestamp()


def bars_since(timestamp: float, bar_times: Sequence[datetime], as_of: datetime) -> int:
    """Count actual bar starts strictly after an event, bounded by evaluation time.

    Bars must be oldest first and cover the event. Missing history is an error.
    """
    end = aware_timestamp(as_of)
    starts = [aware_timestamp(value) for value in bar_times]
    if not starts or any(a >= b for a, b in pairwise(starts)):
        raise ValueError("bar times must be nonempty and strictly oldest first")
    if starts[-1] > end:
        raise ValueError("bar times must not extend past evaluation time")
    if timestamp > end:
        return -1
    if timestamp < starts[0]:
        raise ValueError("bar history does not cover the trade timestamp")
    return sum(timestamp < start <= end for start in starts)


def pip_size(price: float | None, tick_size: float) -> float:
    """Use an explicit pip size, falling back to the instrument tick size."""
    value = tick_size if price is None else price
    if not math.isfinite(value) or value <= 0:
        raise ValueError("pip size must be finite and positive")
    return value
