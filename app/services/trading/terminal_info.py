# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared TerminalInfo proxy for native and simulated broker operations.

Description:
    Forwards asynchronous terminal snapshot queries through TradingClass.
    Terminal property reads are consolidated into a single atomic TerminalInfo()
    call returning a strongly typed TerminalSnapshot dataclass to eliminate IPC
    latency and temporal skew.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-TERMINALINFO-SNAPSHOT: Query full terminal snapshot.
      Associated: `TerminalInfo.TerminalInfo()`, `TerminalInfo.__call__()`
      Logging: DEBUG transport invocation metadata emitted via TradingClass;
        no secret or payload logging occurs here.

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        info = await trading.terminal.TerminalInfo()
        print(f"Connected: {info.connected}, Build: {info.build}")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_metatrader_bridge_protocol.py --no-cov
    ```
"""

from __future__ import annotations

from typing import Any

from app.services.brokers.contracts import TerminalSnapshot

from .base import TradingClass


class TerminalInfo(TradingClass):
    """Canonical asynchronous TerminalInfo API."""

    CLASS_NAME = "TerminalInfo"

    async def TerminalInfo(self, *args: Any) -> TerminalSnapshot:
        """Await the backend TerminalInfo snapshot."""
        data = await self._call("TerminalInfo", *args)
        if isinstance(data, TerminalSnapshot):
            return data
        if isinstance(data, dict):
            return TerminalSnapshot(**data)
        raise TypeError(f"unexpected terminal snapshot type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> TerminalSnapshot:
        """Await the backend TerminalInfo snapshot directly via call syntax."""
        return await self.TerminalInfo(*args)
