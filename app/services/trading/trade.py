# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared Trade proxy for native broker operations.

Description:
    Forwards the current MQL5 Trade method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-TRADE-FORWARDING: Forward native methods.
      Associated: `Trade`, `TradingClass._call()`
      Logging: Transport emits DEBUG encoding-attempt metadata for remote calls;
        no payload logging or proxy logging configuration is introduced here.

Python API Usage:
    Access this proxy through a configured MetaTrader facade or bind it to the
    async backend capability. Remote calls are asynchronous.

CLI Usage:
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
"""

from __future__ import annotations

from typing import Any

from .base import TradingClass


class Trade(TradingClass):
    """Canonical asynchronous Trade API."""

    CLASS_NAME = "Trade"
    TRADING_METHODS = frozenset(
        [
            "Buy",
            "BuyLimit",
            "BuyStop",
            "OrderDelete",
            "OrderModify",
            "OrderOpen",
            "PositionClose",
            "PositionCloseBy",
            "PositionClosePartial",
            "PositionModify",
            "PositionOpen",
            "Sell",
            "SellLimit",
            "SellStop",
        ]
    )

    async def __call__(
        self, action: str, symbol: str, volume: float, /, **kwargs: Any
    ) -> Any:
        """Await a market or pending operation through the canonical methods."""
        key = action.strip().lower().replace("-", "_").replace(" ", "_")
        routes = {
            "buy": self.Buy,
            "sell": self.Sell,
            "buy_limit": self.BuyLimit,
            "buy_stop": self.BuyStop,
            "sell_limit": self.SellLimit,
            "sell_stop": self.SellStop,
        }
        fn = routes.get(key)
        if fn is None:
            raise ValueError("unsupported convenience trade action")
        if key in {"buy", "sell"}:
            return await fn(
                volume,
                symbol,
                kwargs.get("price", 0.0),
                kwargs.get("sl", 0.0),
                kwargs.get("tp", 0.0),
                kwargs.get("comment", ""),
            )
        if "price" not in kwargs:
            raise ValueError("pending convenience trades require price")
        return await fn(
            volume,
            kwargs["price"],
            symbol,
            kwargs.get("sl", 0.0),
            kwargs.get("tp", 0.0),
            kwargs.get("type_time", 0),
            kwargs.get("expiration"),
            kwargs.get("comment", ""),
        )

    async def LogLevel(self, *args: Any) -> Any:
        """Await the backend Trade.LogLevel operation."""
        return await self._call("LogLevel", *args)

    async def SetExpertMagicNumber(self, *args: Any) -> Any:
        """Await the backend Trade.SetExpertMagicNumber operation."""
        return await self._call("SetExpertMagicNumber", *args)

    async def SetDeviationInPoints(self, *args: Any) -> Any:
        """Await the backend Trade.SetDeviationInPoints operation."""
        return await self._call("SetDeviationInPoints", *args)

    async def SetTypeFilling(self, *args: Any) -> Any:
        """Await the backend Trade.SetTypeFilling operation."""
        return await self._call("SetTypeFilling", *args)

    async def SetTypeFillingBySymbol(self, *args: Any) -> Any:
        """Await the backend Trade.SetTypeFillingBySymbol operation."""
        return await self._call("SetTypeFillingBySymbol", *args)

    async def SetAsyncMode(self, *args: Any) -> Any:
        """Await the backend Trade.SetAsyncMode operation."""
        return await self._call("SetAsyncMode", *args)

    async def SetMarginMode(self, *args: Any) -> Any:
        """Await the backend Trade.SetMarginMode operation."""
        return await self._call("SetMarginMode", *args)

    async def OrderOpen(self, *args: Any) -> Any:
        """Await the backend Trade.OrderOpen operation."""
        return await self._call("OrderOpen", *args)

    async def OrderModify(self, *args: Any) -> Any:
        """Await the backend Trade.OrderModify operation."""
        return await self._call("OrderModify", *args)

    async def OrderDelete(self, *args: Any) -> Any:
        """Await the backend Trade.OrderDelete operation."""
        return await self._call("OrderDelete", *args)

    async def PositionOpen(self, *args: Any) -> Any:
        """Await the backend Trade.PositionOpen operation."""
        return await self._call("PositionOpen", *args)

    async def PositionModify(self, *args: Any) -> Any:
        """Await the backend Trade.PositionModify operation."""
        return await self._call("PositionModify", *args)

    async def PositionClose(self, *args: Any) -> Any:
        """Await the backend Trade.PositionClose operation."""
        return await self._call("PositionClose", *args)

    async def PositionClosePartial(self, *args: Any) -> Any:
        """Await the backend Trade.PositionClosePartial operation."""
        return await self._call("PositionClosePartial", *args)

    async def PositionCloseBy(self, *args: Any) -> Any:
        """Await the backend Trade.PositionCloseBy operation."""
        return await self._call("PositionCloseBy", *args)

    async def Buy(self, *args: Any) -> Any:
        """Await the backend Trade.Buy operation."""
        return await self._call("Buy", *args)

    async def Sell(self, *args: Any) -> Any:
        """Await the backend Trade.Sell operation."""
        return await self._call("Sell", *args)

    async def BuyLimit(self, *args: Any) -> Any:
        """Await the backend Trade.BuyLimit operation."""
        return await self._call("BuyLimit", *args)

    async def BuyStop(self, *args: Any) -> Any:
        """Await the backend Trade.BuyStop operation."""
        return await self._call("BuyStop", *args)

    async def SellLimit(self, *args: Any) -> Any:
        """Await the backend Trade.SellLimit operation."""
        return await self._call("SellLimit", *args)

    async def SellStop(self, *args: Any) -> Any:
        """Await the backend Trade.SellStop operation."""
        return await self._call("SellStop", *args)

    async def Request(self, *args: Any) -> Any:
        """Await the backend Trade.Request operation."""
        return await self._call("Request", *args)

    async def RequestAction(self, *args: Any) -> Any:
        """Await the backend Trade.RequestAction operation."""
        return await self._call("RequestAction", *args)

    async def RequestActionDescription(self, *args: Any) -> Any:
        """Await the backend Trade.RequestActionDescription operation."""
        return await self._call("RequestActionDescription", *args)

    async def RequestMagic(self, *args: Any) -> Any:
        """Await the backend Trade.RequestMagic operation."""
        return await self._call("RequestMagic", *args)

    async def RequestOrder(self, *args: Any) -> Any:
        """Await the backend Trade.RequestOrder operation."""
        return await self._call("RequestOrder", *args)

    async def RequestSymbol(self, *args: Any) -> Any:
        """Await the backend Trade.RequestSymbol operation."""
        return await self._call("RequestSymbol", *args)

    async def RequestVolume(self, *args: Any) -> Any:
        """Await the backend Trade.RequestVolume operation."""
        return await self._call("RequestVolume", *args)

    async def RequestPrice(self, *args: Any) -> Any:
        """Await the backend Trade.RequestPrice operation."""
        return await self._call("RequestPrice", *args)

    async def RequestStopLimit(self, *args: Any) -> Any:
        """Await the backend Trade.RequestStopLimit operation."""
        return await self._call("RequestStopLimit", *args)

    async def RequestSL(self, *args: Any) -> Any:
        """Await the backend Trade.RequestSL operation."""
        return await self._call("RequestSL", *args)

    async def RequestTP(self, *args: Any) -> Any:
        """Await the backend Trade.RequestTP operation."""
        return await self._call("RequestTP", *args)

    async def RequestDeviation(self, *args: Any) -> Any:
        """Await the backend Trade.RequestDeviation operation."""
        return await self._call("RequestDeviation", *args)

    async def RequestType(self, *args: Any) -> Any:
        """Await the backend Trade.RequestType operation."""
        return await self._call("RequestType", *args)

    async def RequestTypeDescription(self, *args: Any) -> Any:
        """Await the backend Trade.RequestTypeDescription operation."""
        return await self._call("RequestTypeDescription", *args)

    async def RequestTypeFilling(self, *args: Any) -> Any:
        """Await the backend Trade.RequestTypeFilling operation."""
        return await self._call("RequestTypeFilling", *args)

    async def RequestTypeFillingDescription(self, *args: Any) -> Any:
        """Await the backend Trade.RequestTypeFillingDescription operation."""
        return await self._call("RequestTypeFillingDescription", *args)

    async def RequestTypeTime(self, *args: Any) -> Any:
        """Await the backend Trade.RequestTypeTime operation."""
        return await self._call("RequestTypeTime", *args)

    async def RequestTypeTimeDescription(self, *args: Any) -> Any:
        """Await the backend Trade.RequestTypeTimeDescription operation."""
        return await self._call("RequestTypeTimeDescription", *args)

    async def RequestExpiration(self, *args: Any) -> Any:
        """Await the backend Trade.RequestExpiration operation."""
        return await self._call("RequestExpiration", *args)

    async def RequestComment(self, *args: Any) -> Any:
        """Await the backend Trade.RequestComment operation."""
        return await self._call("RequestComment", *args)

    async def RequestPosition(self, *args: Any) -> Any:
        """Await the backend Trade.RequestPosition operation."""
        return await self._call("RequestPosition", *args)

    async def RequestPositionBy(self, *args: Any) -> Any:
        """Await the backend Trade.RequestPositionBy operation."""
        return await self._call("RequestPositionBy", *args)

    async def Result(self, *args: Any) -> Any:
        """Await the backend Trade.Result operation."""
        return await self._call("Result", *args)

    async def ResultRetcode(self, *args: Any) -> Any:
        """Await the backend Trade.ResultRetcode operation."""
        return await self._call("ResultRetcode", *args)

    async def ResultRetcodeDescription(self, *args: Any) -> Any:
        """Await the backend Trade.ResultRetcodeDescription operation."""
        return await self._call("ResultRetcodeDescription", *args)

    async def ResultDeal(self, *args: Any) -> Any:
        """Await the backend Trade.ResultDeal operation."""
        return await self._call("ResultDeal", *args)

    async def ResultOrder(self, *args: Any) -> Any:
        """Await the backend Trade.ResultOrder operation."""
        return await self._call("ResultOrder", *args)

    async def ResultVolume(self, *args: Any) -> Any:
        """Await the backend Trade.ResultVolume operation."""
        return await self._call("ResultVolume", *args)

    async def ResultPrice(self, *args: Any) -> Any:
        """Await the backend Trade.ResultPrice operation."""
        return await self._call("ResultPrice", *args)

    async def ResultBid(self, *args: Any) -> Any:
        """Await the backend Trade.ResultBid operation."""
        return await self._call("ResultBid", *args)

    async def ResultAsk(self, *args: Any) -> Any:
        """Await the backend Trade.ResultAsk operation."""
        return await self._call("ResultAsk", *args)

    async def ResultComment(self, *args: Any) -> Any:
        """Await the backend Trade.ResultComment operation."""
        return await self._call("ResultComment", *args)

    async def CheckResult(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResult operation."""
        return await self._call("CheckResult", *args)

    async def CheckResultRetcode(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultRetcode operation."""
        return await self._call("CheckResultRetcode", *args)

    async def CheckResultRetcodeDescription(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultRetcodeDescription operation."""
        return await self._call("CheckResultRetcodeDescription", *args)

    async def CheckResultBalance(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultBalance operation."""
        return await self._call("CheckResultBalance", *args)

    async def CheckResultEquity(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultEquity operation."""
        return await self._call("CheckResultEquity", *args)

    async def CheckResultProfit(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultProfit operation."""
        return await self._call("CheckResultProfit", *args)

    async def CheckResultMargin(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultMargin operation."""
        return await self._call("CheckResultMargin", *args)

    async def CheckResultMarginFree(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultMarginFree operation."""
        return await self._call("CheckResultMarginFree", *args)

    async def CheckResultMarginLevel(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultMarginLevel operation."""
        return await self._call("CheckResultMarginLevel", *args)

    async def CheckResultComment(self, *args: Any) -> Any:
        """Await the backend Trade.CheckResultComment operation."""
        return await self._call("CheckResultComment", *args)

    async def PrintRequest(self, *args: Any) -> Any:
        """Await the backend Trade.PrintRequest operation."""
        return await self._call("PrintRequest", *args)

    async def PrintResult(self, *args: Any) -> Any:
        """Await the backend Trade.PrintResult operation."""
        return await self._call("PrintResult", *args)

    async def FormatRequest(self, *args: Any) -> Any:
        """Await the backend Trade.FormatRequest operation."""
        return await self._call("FormatRequest", *args)

    async def FormatRequestResult(self, *args: Any) -> Any:
        """Await the backend Trade.FormatRequestResult operation."""
        return await self._call("FormatRequestResult", *args)
