# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared SymbolInfo proxy for native broker operations.

Description:
    Forwards the current MQL5 SymbolInfo method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-SYMBOLINFO-FORWARDING: Forward native methods.
      Associated: `SymbolInfo`, `TradingClass._call()`
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

from app.services.brokers.contracts import PropertyValue

from .base import TradingClass


class SymbolInfo(TradingClass):
    """Canonical asynchronous SymbolInfo API."""

    CLASS_NAME = "SymbolInfo"

    async def Refresh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Refresh operation."""
        return await self._call("Refresh", *args)

    async def RefreshRates(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.RefreshRates operation."""
        return await self._call("RefreshRates", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Name operation."""
        return await self._call("Name", *args)

    async def Select(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Select operation."""
        return await self._call("Select", *args)

    async def IsSynchronized(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.IsSynchronized operation."""
        return await self._call("IsSynchronized", *args)

    async def Volume(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Volume operation."""
        return await self._call("Volume", *args)

    async def VolumeHigh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.VolumeHigh operation."""
        return await self._call("VolumeHigh", *args)

    async def VolumeLow(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.VolumeLow operation."""
        return await self._call("VolumeLow", *args)

    async def Time(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Time operation."""
        return await self._call("Time", *args)

    async def Spread(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Spread operation."""
        return await self._call("Spread", *args)

    async def SpreadFloat(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SpreadFloat operation."""
        return await self._call("SpreadFloat", *args)

    async def TicksBookDepth(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TicksBookDepth operation."""
        return await self._call("TicksBookDepth", *args)

    async def StopsLevel(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.StopsLevel operation."""
        return await self._call("StopsLevel", *args)

    async def FreezeLevel(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.FreezeLevel operation."""
        return await self._call("FreezeLevel", *args)

    async def Bid(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Bid operation."""
        return await self._call("Bid", *args)

    async def BidHigh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.BidHigh operation."""
        return await self._call("BidHigh", *args)

    async def BidLow(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.BidLow operation."""
        return await self._call("BidLow", *args)

    async def Ask(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Ask operation."""
        return await self._call("Ask", *args)

    async def AskHigh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.AskHigh operation."""
        return await self._call("AskHigh", *args)

    async def AskLow(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.AskLow operation."""
        return await self._call("AskLow", *args)

    async def Last(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Last operation."""
        return await self._call("Last", *args)

    async def LastHigh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.LastHigh operation."""
        return await self._call("LastHigh", *args)

    async def LastLow(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.LastLow operation."""
        return await self._call("LastLow", *args)

    async def TradeCalcMode(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeCalcMode operation."""
        return await self._call("TradeCalcMode", *args)

    async def TradeCalcModeDescription(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeCalcModeDescription operation."""
        return await self._call("TradeCalcModeDescription", *args)

    async def TradeMode(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeMode operation."""
        return await self._call("TradeMode", *args)

    async def TradeModeDescription(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeModeDescription operation."""
        return await self._call("TradeModeDescription", *args)

    async def TradeExecution(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeExecution operation."""
        return await self._call("TradeExecution", *args)

    async def TradeExecutionDescription(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeExecutionDescription operation."""
        return await self._call("TradeExecutionDescription", *args)

    async def SwapMode(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SwapMode operation."""
        return await self._call("SwapMode", *args)

    async def SwapModeDescription(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SwapModeDescription operation."""
        return await self._call("SwapModeDescription", *args)

    async def SwapRollover3days(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SwapRollover3days operation."""
        return await self._call("SwapRollover3days", *args)

    async def SwapRollover3daysDescription(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SwapRollover3daysDescription operation."""
        return await self._call("SwapRollover3daysDescription", *args)

    async def MarginInitial(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginInitial operation."""
        return await self._call("MarginInitial", *args)

    async def MarginMaintenance(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginMaintenance operation."""
        return await self._call("MarginMaintenance", *args)

    async def MarginLong(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginLong operation."""
        return await self._call("MarginLong", *args)

    async def MarginShort(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginShort operation."""
        return await self._call("MarginShort", *args)

    async def MarginLimit(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginLimit operation."""
        return await self._call("MarginLimit", *args)

    async def MarginStop(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginStop operation."""
        return await self._call("MarginStop", *args)

    async def MarginStopLimit(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.MarginStopLimit operation."""
        return await self._call("MarginStopLimit", *args)

    async def TradeTimeFlags(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeTimeFlags operation."""
        return await self._call("TradeTimeFlags", *args)

    async def TradeFillFlags(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TradeFillFlags operation."""
        return await self._call("TradeFillFlags", *args)

    async def Digits(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Digits operation."""
        return await self._call("Digits", *args)

    async def Point(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Point operation."""
        return await self._call("Point", *args)

    async def TickValue(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TickValue operation."""
        return await self._call("TickValue", *args)

    async def TickValueProfit(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TickValueProfit operation."""
        return await self._call("TickValueProfit", *args)

    async def TickValueLoss(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TickValueLoss operation."""
        return await self._call("TickValueLoss", *args)

    async def TickSize(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.TickSize operation."""
        return await self._call("TickSize", *args)

    async def ContractSize(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.ContractSize operation."""
        return await self._call("ContractSize", *args)

    async def LotsMin(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.LotsMin operation."""
        return await self._call("LotsMin", *args)

    async def LotsMax(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.LotsMax operation."""
        return await self._call("LotsMax", *args)

    async def LotsStep(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.LotsStep operation."""
        return await self._call("LotsStep", *args)

    async def LotsLimit(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.LotsLimit operation."""
        return await self._call("LotsLimit", *args)

    async def SwapLong(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SwapLong operation."""
        return await self._call("SwapLong", *args)

    async def SwapShort(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SwapShort operation."""
        return await self._call("SwapShort", *args)

    async def CurrencyBase(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.CurrencyBase operation."""
        return await self._call("CurrencyBase", *args)

    async def CurrencyProfit(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.CurrencyProfit operation."""
        return await self._call("CurrencyProfit", *args)

    async def CurrencyMargin(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.CurrencyMargin operation."""
        return await self._call("CurrencyMargin", *args)

    async def Bank(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Bank operation."""
        return await self._call("Bank", *args)

    async def Description(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Description operation."""
        return await self._call("Description", *args)

    async def Path(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Path operation."""
        return await self._call("Path", *args)

    async def SessionDeals(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionDeals operation."""
        return await self._call("SessionDeals", *args)

    async def SessionBuyOrders(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionBuyOrders operation."""
        return await self._call("SessionBuyOrders", *args)

    async def SessionSellOrders(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionSellOrders operation."""
        return await self._call("SessionSellOrders", *args)

    async def SessionTurnover(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionTurnover operation."""
        return await self._call("SessionTurnover", *args)

    async def SessionInterest(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionInterest operation."""
        return await self._call("SessionInterest", *args)

    async def SessionBuyOrdersVolume(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionBuyOrdersVolume operation."""
        return await self._call("SessionBuyOrdersVolume", *args)

    async def SessionSellOrdersVolume(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionSellOrdersVolume operation."""
        return await self._call("SessionSellOrdersVolume", *args)

    async def SessionOpen(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionOpen operation."""
        return await self._call("SessionOpen", *args)

    async def SessionClose(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionClose operation."""
        return await self._call("SessionClose", *args)

    async def SessionAW(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionAW operation."""
        return await self._call("SessionAW", *args)

    async def SessionPriceSettlement(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionPriceSettlement operation."""
        return await self._call("SessionPriceSettlement", *args)

    async def SessionPriceLimitMin(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionPriceLimitMin operation."""
        return await self._call("SessionPriceLimitMin", *args)

    async def SessionPriceLimitMax(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SessionPriceLimitMax operation."""
        return await self._call("SessionPriceLimitMax", *args)

    async def InfoInteger(self, prop_id: int | str) -> PropertyValue:
        """Await the backend SymbolInfo.InfoInteger operation."""
        return await self._property("InfoInteger", prop_id)

    async def InfoDouble(self, prop_id: int | str) -> PropertyValue:
        """Await the backend SymbolInfo.InfoDouble operation."""
        return await self._property("InfoDouble", prop_id)

    async def InfoString(self, prop_id: int | str) -> PropertyValue:
        """Await the backend SymbolInfo.InfoString operation."""
        return await self._property("InfoString", prop_id)

    async def NormalizePrice(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.NormalizePrice operation."""
        return await self._call("NormalizePrice", *args)
