# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared PositionInfo proxy for native broker operations.

Description:
    Forwards the current MQL5 PositionInfo method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-POSITIONINFO-FORWARDING: Forward native methods.
      Associated: `PositionInfo`, `TradingClass._call()`
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


class PositionInfo(TradingClass):
    """Canonical asynchronous PositionInfo API."""

    CLASS_NAME = "PositionInfo"

    async def Time(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Time operation."""
        return await self._call("Time", *args)

    async def TimeMsc(self, *args: Any) -> Any:
        """Await the backend PositionInfo.TimeMsc operation."""
        return await self._call("TimeMsc", *args)

    async def TimeUpdate(self, *args: Any) -> Any:
        """Await the backend PositionInfo.TimeUpdate operation."""
        return await self._call("TimeUpdate", *args)

    async def TimeUpdateMsc(self, *args: Any) -> Any:
        """Await the backend PositionInfo.TimeUpdateMsc operation."""
        return await self._call("TimeUpdateMsc", *args)

    async def PositionType(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PositionType operation."""
        return await self._call("PositionType", *args)

    async def TypeDescription(self, *args: Any) -> Any:
        """Await the backend PositionInfo.TypeDescription operation."""
        return await self._call("TypeDescription", *args)

    async def Magic(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Magic operation."""
        return await self._call("Magic", *args)

    async def Identifier(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Identifier operation."""
        return await self._call("Identifier", *args)

    async def Volume(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Volume operation."""
        return await self._call("Volume", *args)

    async def PriceOpen(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PriceOpen operation."""
        return await self._call("PriceOpen", *args)

    async def StopLoss(self, *args: Any) -> Any:
        """Await the backend PositionInfo.StopLoss operation."""
        return await self._call("StopLoss", *args)

    async def TakeProfit(self, *args: Any) -> Any:
        """Await the backend PositionInfo.TakeProfit operation."""
        return await self._call("TakeProfit", *args)

    async def PriceCurrent(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PriceCurrent operation."""
        return await self._call("PriceCurrent", *args)

    async def Commission(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Commission operation."""
        return await self._call("Commission", *args)

    async def Swap(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Swap operation."""
        return await self._call("Swap", *args)

    async def Profit(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Profit operation."""
        return await self._call("Profit", *args)

    async def Symbol(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Symbol operation."""
        return await self._call("Symbol", *args)

    async def Comment(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Comment operation."""
        return await self._call("Comment", *args)

    async def InfoInteger(self, prop_id: int | str) -> PropertyValue:
        """Await the backend PositionInfo.InfoInteger operation."""
        return await self._property("InfoInteger", prop_id)

    async def InfoDouble(self, prop_id: int | str) -> PropertyValue:
        """Await the backend PositionInfo.InfoDouble operation."""
        return await self._property("InfoDouble", prop_id)

    async def InfoString(self, prop_id: int | str) -> PropertyValue:
        """Await the backend PositionInfo.InfoString operation."""
        return await self._property("InfoString", prop_id)

    async def Select(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def SelectByMagic(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByMagic operation."""
        return await self._call("SelectByMagic", *args)

    async def SelectByTicket(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByTicket operation."""
        return await self._call("SelectByTicket", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.CheckState operation."""
        return await self._call("CheckState", *args)
