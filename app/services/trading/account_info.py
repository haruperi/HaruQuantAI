# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared AccountInfo proxy for native broker operations.

Description:
    Forwards the current MQL5 AccountInfo method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-ACCOUNTINFO-FORWARDING: Forward native methods.
      Associated: `AccountInfo`, `TradingClass._call()`
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


class AccountInfo(TradingClass):
    """Canonical asynchronous AccountInfo API."""

    CLASS_NAME = "AccountInfo"

    async def Login(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Login operation."""
        return await self._call("Login", *args)

    async def TradeMode(self, *args: Any) -> Any:
        """Await the backend AccountInfo.TradeMode operation."""
        return await self._call("TradeMode", *args)

    async def TradeModeDescription(self, *args: Any) -> Any:
        """Await the backend AccountInfo.TradeModeDescription operation."""
        return await self._call("TradeModeDescription", *args)

    async def Leverage(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Leverage operation."""
        return await self._call("Leverage", *args)

    async def StopoutMode(self, *args: Any) -> Any:
        """Await the backend AccountInfo.StopoutMode operation."""
        return await self._call("StopoutMode", *args)

    async def StopoutModeDescription(self, *args: Any) -> Any:
        """Await the backend AccountInfo.StopoutModeDescription operation."""
        return await self._call("StopoutModeDescription", *args)

    async def MarginMode(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginMode operation."""
        return await self._call("MarginMode", *args)

    async def MarginModeDescription(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginModeDescription operation."""
        return await self._call("MarginModeDescription", *args)

    async def TradeAllowed(self, *args: Any) -> Any:
        """Await the backend AccountInfo.TradeAllowed operation."""
        return await self._call("TradeAllowed", *args)

    async def TradeExpert(self, *args: Any) -> Any:
        """Await the backend AccountInfo.TradeExpert operation."""
        return await self._call("TradeExpert", *args)

    async def LimitOrders(self, *args: Any) -> Any:
        """Await the backend AccountInfo.LimitOrders operation."""
        return await self._call("LimitOrders", *args)

    async def Balance(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Balance operation."""
        return await self._call("Balance", *args)

    async def Credit(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Credit operation."""
        return await self._call("Credit", *args)

    async def Profit(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Profit operation."""
        return await self._call("Profit", *args)

    async def Equity(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Equity operation."""
        return await self._call("Equity", *args)

    async def Margin(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Margin operation."""
        return await self._call("Margin", *args)

    async def FreeMargin(self, *args: Any) -> Any:
        """Await the backend AccountInfo.FreeMargin operation."""
        return await self._call("FreeMargin", *args)

    async def MarginLevel(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginLevel operation."""
        return await self._call("MarginLevel", *args)

    async def MarginCall(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginCall operation."""
        return await self._call("MarginCall", *args)

    async def MarginStopOut(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginStopOut operation."""
        return await self._call("MarginStopOut", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Name operation."""
        return await self._call("Name", *args)

    async def Server(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Server operation."""
        return await self._call("Server", *args)

    async def Currency(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Currency operation."""
        return await self._call("Currency", *args)

    async def Company(self, *args: Any) -> Any:
        """Await the backend AccountInfo.Company operation."""
        return await self._call("Company", *args)

    async def InfoInteger(self, *args: Any) -> Any:
        """Await the backend AccountInfo.InfoInteger operation."""
        return await self._call("InfoInteger", *args)

    async def InfoDouble(self, *args: Any) -> Any:
        """Await the backend AccountInfo.InfoDouble operation."""
        return await self._call("InfoDouble", *args)

    async def InfoString(self, *args: Any) -> Any:
        """Await the backend AccountInfo.InfoString operation."""
        return await self._call("InfoString", *args)

    async def OrderProfitCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.OrderProfitCheck operation."""
        return await self._call("OrderProfitCheck", *args)

    async def MarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginCheck operation."""
        return await self._call("MarginCheck", *args)

    async def FreeMarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.FreeMarginCheck operation."""
        return await self._call("FreeMarginCheck", *args)

    async def MaxLotCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MaxLotCheck operation."""
        return await self._call("MaxLotCheck", *args)
