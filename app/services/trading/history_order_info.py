# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared HistoryOrderInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous historical order snapshot queries, index selection, and
    interval totals through TradingClass. Historical order property reads are
    consolidated into a single atomic HistoryOrderInfo() call returning a strongly
    typed HistoryOrderSnapshot dataclass to eliminate IPC round-trips and temporal
    skew. HistoryOrdersGet() returns a strongly typed list of HistoryOrderSnapshot
    dataclasses.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-HISTORYORDERINFO-SNAPSHOT: Query historical order
      specification and completion snapshot.
      Associated: `HistoryOrderInfo.HistoryOrderInfo()`,
        `HistoryOrderInfo.__call__()`, `HistoryOrderInfo.as_dict()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.
    - FR-BROKER-PROXIES-HISTORYORDERINFO-OPERATIONS: Select historical orders
      and inspect totals.
      Associated: `HistoryOrderInfo.Ticket()`, `HistoryOrderInfo.SelectByIndex()`,
        `HistoryOrderInfo.HistoryOrdersTotal()`, `HistoryOrderInfo.HistoryOrdersGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        history = await trading.history_order.HistoryOrdersGet()
        for ord_item in history:
            print(f"Ticket: {ord_item.ticket}, Done: {ord_item.time_done}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.brokers.contracts import HistoryOrderSnapshot

from .base import TradingClass


class HistoryOrderInfo(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API."""

    CLASS_NAME = "HistoryOrderInfo"

    async def HistoryOrderInfo(self, *args: Any) -> HistoryOrderSnapshot:
        """Await the backend HistoryOrderInfo snapshot."""
        data = await self._call("HistoryOrderInfo", *args)
        if isinstance(data, HistoryOrderSnapshot):
            return data
        if isinstance(data, dict):
            return HistoryOrderSnapshot(**data)
        raise TypeError(
            f"unexpected history order snapshot type: {type(data).__name__}"
        )

    async def __call__(self, *args: Any) -> HistoryOrderSnapshot:
        """Await the backend HistoryOrderInfo snapshot directly via call syntax."""
        return await self.HistoryOrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, HistoryOrderSnapshot):
            return asdict(data)
        raise TypeError(
            f"unexpected history order dictionary type: {type(data).__name__}"
        )

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryOrdersTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend HistoryOrderInfo.HistoryOrdersTotal operation."""
        if kwargs:
            return await self._call("HistoryOrdersTotal", kwargs)
        return await self._call("HistoryOrdersTotal", *args)

    async def HistoryOrdersGet(
        self, *args: Any, **kwargs: Any
    ) -> list[HistoryOrderSnapshot]:
        """Await the backend HistoryOrderInfo.HistoryOrdersGet operation."""
        data = (
            await self._call("HistoryOrdersGet", kwargs)
            if kwargs
            else await self._call("HistoryOrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, HistoryOrderSnapshot)
                else HistoryOrderSnapshot(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryOrdersGet return type: {type(data).__name__}"
        )
