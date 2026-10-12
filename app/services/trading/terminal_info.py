# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared TerminalInfo proxy for native broker operations.

Description:
    Forwards the current MQL5 TerminalInfo method surface through TradingClass.
    Stateful selection and request/result objects retain per-proxy serialization.
    Placement is shared; current method semantics remain those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-TERMINALINFO-FORWARDING: Forward native methods.
      Associated: `TerminalInfo`, `TradingClass._call()`
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


class TerminalInfo(TradingClass):
    """Canonical asynchronous TerminalInfo API."""

    CLASS_NAME = "TerminalInfo"

    async def Build(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.Build operation."""
        return await self._call("Build", *args)

    async def IsConnected(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.IsConnected operation."""
        return await self._call("IsConnected", *args)

    async def IsDLLsAllowed(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.IsDLLsAllowed operation."""
        return await self._call("IsDLLsAllowed", *args)

    async def IsTradeAllowed(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.IsTradeAllowed operation."""
        return await self._call("IsTradeAllowed", *args)

    async def IsEmailEnabled(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.IsEmailEnabled operation."""
        return await self._call("IsEmailEnabled", *args)

    async def IsFtpEnabled(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.IsFtpEnabled operation."""
        return await self._call("IsFtpEnabled", *args)

    async def MaxBars(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.MaxBars operation."""
        return await self._call("MaxBars", *args)

    async def CodePage(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.CodePage operation."""
        return await self._call("CodePage", *args)

    async def CPUCores(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.CPUCores operation."""
        return await self._call("CPUCores", *args)

    async def MemoryPhysical(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.MemoryPhysical operation."""
        return await self._call("MemoryPhysical", *args)

    async def MemoryTotal(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.MemoryTotal operation."""
        return await self._call("MemoryTotal", *args)

    async def MemoryAvailable(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.MemoryAvailable operation."""
        return await self._call("MemoryAvailable", *args)

    async def MemoryUsed(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.MemoryUsed operation."""
        return await self._call("MemoryUsed", *args)

    async def IsX64(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.IsX64 operation."""
        return await self._call("IsX64", *args)

    async def OpenCLSupport(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.OpenCLSupport operation."""
        return await self._call("OpenCLSupport", *args)

    async def DiskSpace(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.DiskSpace operation."""
        return await self._call("DiskSpace", *args)

    async def Language(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.Language operation."""
        return await self._call("Language", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.Name operation."""
        return await self._call("Name", *args)

    async def Company(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.Company operation."""
        return await self._call("Company", *args)

    async def Path(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.Path operation."""
        return await self._call("Path", *args)

    async def DataPath(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.DataPath operation."""
        return await self._call("DataPath", *args)

    async def CommonDataPath(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.CommonDataPath operation."""
        return await self._call("CommonDataPath", *args)

    async def InfoInteger(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.InfoInteger operation."""
        return await self._call("InfoInteger", *args)

    async def InfoString(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.InfoString operation."""
        return await self._call("InfoString", *args)

    async def CommunityAccount(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.CommunityAccount operation."""
        return await self._call("CommunityAccount", *args)

    async def CommunityConnection(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.CommunityConnection operation."""
        return await self._call("CommunityConnection", *args)

    async def TradeAPIDisabled(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.TradeAPIDisabled operation."""
        return await self._call("TradeAPIDisabled", *args)

    async def NotificationsEnabled(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.NotificationsEnabled operation."""
        return await self._call("NotificationsEnabled", *args)

    async def MQID(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.MQID operation."""
        return await self._call("MQID", *args)

    async def PingLast(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.PingLast operation."""
        return await self._call("PingLast", *args)

    async def CommunityBalance(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.CommunityBalance operation."""
        return await self._call("CommunityBalance", *args)

    async def Retransmission(self, *args: Any) -> Any:
        """Await the backend TerminalInfo.Retransmission operation."""
        return await self._call("Retransmission", *args)
