"""Verify one async eight-class API and backend-neutral serialization.

Description:
    Inspect the canonical API and exercise locking without live broker calls.

Purpose:
    FEAT-TRADING-API: Preserve the full compatibility method surface.

Key Capabilities:
    - FR-TRADING-API-SURFACE: Verify eight async classes and complete dispatch.
      Associated: `Trading`, `TradingClass`
      Logging: Tests inspect structural invariants without secret-bearing output.

Python API Usage:
    Execute through pytest with a local simulator and bounded async test calls.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_api.py --no-cov
"""

import asyncio
import inspect
from unittest.mock import AsyncMock

import pytest
from app.services import trading
from app.services.brokers._simulation_api import HANDLERS
from app.services.brokers.contracts import TradingBackend
from app.services.brokers.simulator import SimulationBackend


@pytest.mark.parametrize(
    ("name", "count"),
    [
        ("Trade", 67),
        ("AccountInfo", 38),
        ("SymbolInfo", 118),
        ("OrderInfo", 32),
        ("HistoryOrderInfo", 29),
        ("PositionInfo", 27),
        ("DealInfo", 22),
        ("TerminalInfo", 32),
    ],
)
def test_one_complete_async_class(name: str, count: int) -> None:
    """Every retained method has a backend-local implementation."""
    cls = getattr(trading, name)
    methods = {
        method
        for method, value in cls.__dict__.items()
        if not method.startswith("_") and inspect.iscoroutinefunction(value)
    }
    assert len(methods) == count
    assert methods == set(HANDLERS[name])
    assert cls.__module__.startswith("app.services.trading.")


def test_per_object_serialization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two calls on one object cannot overwrite its selection concurrently."""

    async def scenario() -> None:
        backend: TradingBackend = SimulationBackend()
        facade = trading.Trading(backend)
        active = 0
        maximum = 0

        async def execute(**kwargs: object) -> bool:
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            await asyncio.sleep(0)
            active -= 1
            return True

        call = AsyncMock(side_effect=execute)
        monkeypatch.setattr(backend, "call", call)
        await asyncio.gather(facade.symbol.Name("EURUSD"), facade.symbol.Name("GBPUSD"))
        assert maximum == 1
        assert call.call_count == 2
        assert (
            call.call_args_list[0].kwargs["object_id"]
            == call.call_args_list[1].kwargs["object_id"]
        )
        assert facade.symbol.object_id != facade.order.object_id
        await facade.close()

    asyncio.run(scenario())
