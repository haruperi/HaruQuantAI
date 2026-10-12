# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared DealInfo proxy for native broker operations.

Description:
    Forwards the current MQL5 DealInfo method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-DEALINFO-FORWARDING: Forward native methods.
      Associated: `DealInfo`, `TradingClass._call()`
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


class DealInfo(TradingClass):
    """Canonical asynchronous DealInfo API."""

    CLASS_NAME = "DealInfo"

    async def Order(self, *args: Any) -> Any:
        """Await the backend DealInfo.Order operation."""
        return await self._call("Order", *args)

    async def Time(self, *args: Any) -> Any:
        """Await the backend DealInfo.Time operation."""
        return await self._call("Time", *args)

    async def TimeMsc(self, *args: Any) -> Any:
        """Await the backend DealInfo.TimeMsc operation."""
        return await self._call("TimeMsc", *args)

    async def DealType(self, *args: Any) -> Any:
        """Await the backend DealInfo.DealType operation."""
        return await self._call("DealType", *args)

    async def TypeDescription(self, *args: Any) -> Any:
        """Await the backend DealInfo.TypeDescription operation."""
        return await self._call("TypeDescription", *args)

    async def Entry(self, *args: Any) -> Any:
        """Await the backend DealInfo.Entry operation."""
        return await self._call("Entry", *args)

    async def EntryDescription(self, *args: Any) -> Any:
        """Await the backend DealInfo.EntryDescription operation."""
        return await self._call("EntryDescription", *args)

    async def Magic(self, *args: Any) -> Any:
        """Await the backend DealInfo.Magic operation."""
        return await self._call("Magic", *args)

    async def PositionId(self, *args: Any) -> Any:
        """Await the backend DealInfo.PositionId operation."""
        return await self._call("PositionId", *args)

    async def Volume(self, *args: Any) -> Any:
        """Await the backend DealInfo.Volume operation."""
        return await self._call("Volume", *args)

    async def Price(self, *args: Any) -> Any:
        """Await the backend DealInfo.Price operation."""
        return await self._call("Price", *args)

    async def Commision(self, *args: Any) -> Any:
        """Await the backend DealInfo.Commision operation."""
        return await self._call("Commision", *args)

    async def Swap(self, *args: Any) -> Any:
        """Await the backend DealInfo.Swap operation."""
        return await self._call("Swap", *args)

    async def Profit(self, *args: Any) -> Any:
        """Await the backend DealInfo.Profit operation."""
        return await self._call("Profit", *args)

    async def Symbol(self, *args: Any) -> Any:
        """Await the backend DealInfo.Symbol operation."""
        return await self._call("Symbol", *args)

    async def Comment(self, *args: Any) -> Any:
        """Await the backend DealInfo.Comment operation."""
        return await self._call("Comment", *args)

    async def InfoInteger(self, prop_id: int | str) -> PropertyValue:
        """Await the backend DealInfo.InfoInteger operation."""
        return await self._property("InfoInteger", prop_id)

    async def InfoDouble(self, prop_id: int | str) -> PropertyValue:
        """Await the backend DealInfo.InfoDouble operation."""
        return await self._property("InfoDouble", prop_id)

    async def InfoString(self, prop_id: int | str) -> PropertyValue:
        """Await the backend DealInfo.InfoString operation."""
        return await self._property("InfoString", prop_id)

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend DealInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend DealInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def Commission(self, *args: Any) -> Any:
        """Compatibility alias for the correctly-spelled method page."""
        return await self._call("Commision", *args)
