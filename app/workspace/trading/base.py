"""Backend-neutral proxy identity, serialization, and snapshot helpers.

Description:
    Provides base proxy class TradingClass and serialization/deserialization
    primitives converting between wire representations and domain contract dataclasses.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and proxy serialization.
Key Capabilities:
    - FR-trading-proxy-call: Serialized asynchronous method invocation with argument
      normalization and logging.
    - FR-trading-snapshot-conversion: Decoding backend dictionaries or dataclasses into
      strongly-typed domain models.
    - FR-trading-request-serialization: Wire format encoding of orders, checks, times.
Python API Usage:
    from app.workspace.trading.base import (
        TradingClass, normalize_request, serialize_request
    )
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any, TypeVar

from app.core.enums import (
    TradeRetcode,
)
from app.core.host.logging import get_logger
from app.core.trading.connection.contracts import (
    PropertyValue,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
    normalize_request,
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
        logger.debug(
            "FR-trading-proxy-call: creating trading class object",
            extra={"class_name": self.CLASS_NAME},
        )
        self.backend = backend
        self.object_id = object_id or f"{self.CLASS_NAME.lower()}-{uuid.uuid4().hex}"
        self._lock = asyncio.Lock()

    @property
    def last_command_id(self) -> str | None:
        """Return the last command in this task context."""
        return self.backend.last_command_id()

    async def _call(self, method: str, *args: Any) -> Any:
        logger.debug(
            "FR-trading-proxy-call: invoking backend method",
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
        logger.debug(
            "FR-trading-snapshot-conversion: querying snapshot",
            extra={"method": method, "model": model_cls.__name__},
        )
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
        logger.debug(
            "FR-trading-snapshot-conversion: querying snapshot dictionary",
            extra={"model": model_cls.__name__},
        )
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
        logger.debug(
            "FR-trading-snapshot-conversion: querying collection",
            extra={"method": method, "model": model_cls.__name__},
        )
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


__all__ = [
    "TradingClass",
    "build_trade_check_result",
    "build_trade_result",
    "normalize_request",
    "serialize_request",
]
