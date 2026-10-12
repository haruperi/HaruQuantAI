# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared HistoryOrderInfo proxy for native broker operations.

Description:
    Forwards the current MQL5 HistoryOrderInfo method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-HISTORYORDERINFO-FORWARDING: Forward native methods.
      Associated: `HistoryOrderInfo`, `TradingClass._call()`
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


class HistoryOrderInfo(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API."""

    CLASS_NAME = "HistoryOrderInfo"

    async def TimeSetup(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TimeSetup operation."""
        return await self._call("TimeSetup", *args)

    async def TimeSetupMsc(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TimeSetupMsc operation."""
        return await self._call("TimeSetupMsc", *args)

    async def OrderType(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.OrderType operation."""
        return await self._call("OrderType", *args)

    async def TypeDescription(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TypeDescription operation."""
        return await self._call("TypeDescription", *args)

    async def State(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.State operation."""
        return await self._call("State", *args)

    async def StateDescription(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.StateDescription operation."""
        return await self._call("StateDescription", *args)

    async def TimeExpiration(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TimeExpiration operation."""
        return await self._call("TimeExpiration", *args)

    async def TimeDone(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TimeDone operation."""
        return await self._call("TimeDone", *args)

    async def TimeDoneMsc(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TimeDoneMsc operation."""
        return await self._call("TimeDoneMsc", *args)

    async def TypeFilling(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TypeFilling operation."""
        return await self._call("TypeFilling", *args)

    async def TypeFillingDescription(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TypeFillingDescription operation."""
        return await self._call("TypeFillingDescription", *args)

    async def TypeTime(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TypeTime operation."""
        return await self._call("TypeTime", *args)

    async def TypeTimeDescription(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TypeTimeDescription operation."""
        return await self._call("TypeTimeDescription", *args)

    async def Magic(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Magic operation."""
        return await self._call("Magic", *args)

    async def PositionId(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.PositionId operation."""
        return await self._call("PositionId", *args)

    async def VolumeInitial(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.VolumeInitial operation."""
        return await self._call("VolumeInitial", *args)

    async def VolumeCurrent(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.VolumeCurrent operation."""
        return await self._call("VolumeCurrent", *args)

    async def PriceOpen(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.PriceOpen operation."""
        return await self._call("PriceOpen", *args)

    async def StopLoss(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.StopLoss operation."""
        return await self._call("StopLoss", *args)

    async def TakeProfit(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.TakeProfit operation."""
        return await self._call("TakeProfit", *args)

    async def PriceCurrent(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.PriceCurrent operation."""
        return await self._call("PriceCurrent", *args)

    async def PriceStopLimit(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.PriceStopLimit operation."""
        return await self._call("PriceStopLimit", *args)

    async def Symbol(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Symbol operation."""
        return await self._call("Symbol", *args)

    async def Comment(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Comment operation."""
        return await self._call("Comment", *args)

    async def InfoInteger(self, prop_id: int | str) -> PropertyValue:
        """Await the backend HistoryOrderInfo.InfoInteger operation."""
        return await self._property("InfoInteger", prop_id)

    async def InfoDouble(self, prop_id: int | str) -> PropertyValue:
        """Await the backend HistoryOrderInfo.InfoDouble operation."""
        return await self._property("InfoDouble", prop_id)

    async def InfoString(self, prop_id: int | str) -> PropertyValue:
        """Await the backend HistoryOrderInfo.InfoString operation."""
        return await self._property("InfoString", prop_id)

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)
