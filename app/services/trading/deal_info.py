# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared DealInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous historical deal snapshot queries, index selection, and
    interval totals through TradingClass. Historical deal property reads are
    consolidated into a single atomic DealInfo() call returning a strongly
    typed DealSnapshot dataclass to eliminate IPC round-trips and temporal skew.
    HistoryDealsGet() returns a strongly typed list of DealSnapshot dataclasses.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-DEALINFO-SNAPSHOT: Query historical deal
      specification and execution snapshot.
      Associated: `DealInfo.DealInfo()`, `DealInfo.__call__()`, `DealInfo.as_dict()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.
    - FR-BROKER-PROXIES-DEALINFO-OPERATIONS: Select historical deals
      and inspect totals.
      Associated: `DealInfo.Ticket()`, `DealInfo.SelectByIndex()`,
        `DealInfo.HistoryDealsTotal()`, `DealInfo.HistoryDealsGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        deals = await trading.deal.HistoryDealsGet()
        for deal in deals:
            print(f"Ticket: {deal.ticket}, Profit: {deal.profit}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.brokers.contracts import DealSnapshot

from .base import TradingClass


class DealInfo(TradingClass):
    """Canonical asynchronous DealInfo API."""

    CLASS_NAME = "DealInfo"

    async def DealInfo(self, *args: Any) -> DealSnapshot:
        """Await the backend DealInfo snapshot."""
        data = await self._call("DealInfo", *args)
        if isinstance(data, DealSnapshot):
            return data
        if isinstance(data, dict):
            return DealSnapshot(**data)
        raise TypeError(f"unexpected deal snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> DealSnapshot:
        """Await the backend DealInfo snapshot directly via call syntax."""
        return await self.DealInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical deal snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, DealSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected deal dictionary type: {type(data).__name__}")

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend DealInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend DealInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryDealsTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend DealInfo.HistoryDealsTotal operation."""
        if kwargs:
            return await self._call("HistoryDealsTotal", kwargs)
        return await self._call("HistoryDealsTotal", *args)

    async def HistoryDealsGet(self, *args: Any, **kwargs: Any) -> list[DealSnapshot]:
        """Await the backend DealInfo.HistoryDealsGet operation."""
        data = (
            await self._call("HistoryDealsGet", kwargs)
            if kwargs
            else await self._call("HistoryDealsGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, DealSnapshot) else DealSnapshot(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryDealsGet return type: {type(data).__name__}"
        )
