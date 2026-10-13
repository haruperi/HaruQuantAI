# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared AccountInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous account snapshot queries and trade margin/profit
    pre-calculations through TradingClass. Account property reads are consolidated
    into a single atomic AccountInfo() call returning a strongly typed
    AccountSnapshot dataclass to eliminate IPC latency and temporal skew.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-ACCOUNTINFO-SNAPSHOT: Query full account snapshot.
      Associated: `AccountInfo.AccountInfo()`, `AccountInfo.__call__()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.
    - FR-BROKER-PROXIES-ACCOUNTINFO-CHECKS: Execute pre-trade margin and profit checks.
      Associated: `AccountInfo.OrderProfitCheck()`, `AccountInfo.MarginCheck()`,
        `AccountInfo.FreeMarginCheck()`, `AccountInfo.MaxLotCheck()`
      Logging: DEBUG invocation metadata emitted via TradingClass._call().

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        info = await trading.account.AccountInfo()
        print(f"Balance: {info.balance}, Equity: {info.equity}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from typing import Any

from app.services.brokers.contracts import AccountSnapshot

from .base import TradingClass


class AccountInfo(TradingClass):
    """Canonical asynchronous AccountInfo API."""

    CLASS_NAME = "AccountInfo"

    async def AccountInfo(self, *args: Any) -> AccountSnapshot:
        """Await the backend AccountInfo snapshot."""
        data = await self._call("AccountInfo", *args)
        if isinstance(data, AccountSnapshot):
            return data
        if isinstance(data, dict):
            return AccountSnapshot(**data)
        raise TypeError(f"unexpected account snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> AccountSnapshot:
        """Await the backend AccountInfo snapshot directly via call syntax."""
        return await self.AccountInfo(*args)

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
