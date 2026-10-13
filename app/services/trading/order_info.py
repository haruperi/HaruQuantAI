# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared OrderInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous order snapshot queries, order selection, and state
    checks through TradingClass. Order property reads are consolidated into a
    single atomic OrderInfo() call returning a strongly typed OrderSnapshot
    dataclass to eliminate IPC round-trips and temporal skew across properties.
    OrdersGet() returns a strongly typed list of OrderSnapshot dataclasses.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-ORDERINFO-SNAPSHOT: Query full order specification
      and state snapshot.
      Associated: `OrderInfo.OrderInfo()`, `OrderInfo.__call__()`,
        `OrderInfo.as_dict()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.
    - FR-BROKER-PROXIES-ORDERINFO-OPERATIONS: Select orders and inspect totals.
      Associated: `OrderInfo.Select()`, `OrderInfo.SelectByIndex()`,
        `OrderInfo.StoreState()`, `OrderInfo.CheckState()`,
        `OrderInfo.OrdersTotal()`, `OrderInfo.OrdersGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        orders = await trading.order.OrdersGet()
        for ord_item in orders:
            print(f"Ticket: {ord_item.ticket}, Price: {ord_item.price_open}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.brokers.contracts import OrderSnapshot

from .base import TradingClass


class OrderInfo(TradingClass):
    """Canonical asynchronous OrderInfo API."""

    CLASS_NAME = "OrderInfo"

    async def OrderInfo(self, *args: Any) -> OrderSnapshot:
        """Await the backend OrderInfo snapshot."""
        data = await self._call("OrderInfo", *args)
        if isinstance(data, OrderSnapshot):
            return data
        if isinstance(data, dict):
            return OrderSnapshot(**data)
        raise TypeError(f"unexpected order snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> OrderSnapshot:
        """Await the backend OrderInfo snapshot directly via call syntax."""
        return await self.OrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, OrderSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected order dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend OrderInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend OrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def OrdersTotal(self, *args: Any) -> Any:
        """Await the backend OrderInfo.OrdersTotal operation."""
        return await self._call("OrdersTotal", *args)

    async def OrdersGet(self, *args: Any, **kwargs: Any) -> list[OrderSnapshot]:
        """Await the backend OrderInfo.OrdersGet operation."""
        data = (
            await self._call("OrdersGet", kwargs)
            if kwargs
            else await self._call("OrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, OrderSnapshot) else OrderSnapshot(**item)
                for item in data
            ]
        raise TypeError(f"unexpected OrdersGet return type: {type(data).__name__}")
