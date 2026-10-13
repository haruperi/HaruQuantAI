# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared PositionInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous position snapshot queries, position selection, and state
    checks through TradingClass. Position property reads are consolidated into a
    single atomic PositionInfo() call returning a strongly typed PositionSnapshot
    dataclass to eliminate IPC round-trips and temporal skew across properties.
    PositionsGet() returns a strongly typed list of PositionSnapshot dataclasses.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-POSITIONINFO-SNAPSHOT: Query full position specification
      and state snapshot.
      Associated: `PositionInfo.PositionInfo()`, `PositionInfo.__call__()`,
        `PositionInfo.as_dict()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.
    - FR-BROKER-PROXIES-POSITIONINFO-OPERATIONS: Select positions and inspect totals.
      Associated: `PositionInfo.Select()`, `PositionInfo.SelectByIndex()`,
        `PositionInfo.SelectByMagic()`, `PositionInfo.SelectByTicket()`,
        `PositionInfo.StoreState()`, `PositionInfo.CheckState()`,
        `PositionInfo.PositionsTotal()`, `PositionInfo.PositionsGet()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass._call().

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        positions = await trading.position.PositionsGet()
        for pos in positions:
            print(f"Ticket: {pos.ticket}, Profit: {pos.profit}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.services.brokers.contracts import PositionSnapshot

from .base import TradingClass


class PositionInfo(TradingClass):
    """Canonical asynchronous PositionInfo API."""

    CLASS_NAME = "PositionInfo"

    async def PositionInfo(self, *args: Any) -> PositionSnapshot:
        """Await the backend PositionInfo snapshot."""
        data = await self._call("PositionInfo", *args)
        if isinstance(data, PositionSnapshot):
            return data
        if isinstance(data, dict):
            return PositionSnapshot(**data)
        raise TypeError(f"unexpected position snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> PositionSnapshot:
        """Await the backend PositionInfo snapshot directly via call syntax."""
        return await self.PositionInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend position snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, PositionSnapshot):
            return asdict(data)
        raise TypeError(f"unexpected position dictionary type: {type(data).__name__}")

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

    async def PositionsTotal(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PositionsTotal operation."""
        return await self._call("PositionsTotal", *args)

    async def PositionsGet(self, *args: Any, **kwargs: Any) -> list[PositionSnapshot]:
        """Await the backend PositionInfo.PositionsGet operation."""
        data = (
            await self._call("PositionsGet", kwargs)
            if kwargs
            else await self._call("PositionsGet", *args)
        )
        if isinstance(data, list):
            return [
                item if isinstance(item, PositionSnapshot) else PositionSnapshot(**item)
                for item in data
            ]
        raise TypeError(f"unexpected PositionsGet return type: {type(data).__name__}")
