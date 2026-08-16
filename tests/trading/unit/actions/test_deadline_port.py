"""Unit tests for the injected Trading evaluation deadline port."""

from __future__ import annotations

import asyncio
from decimal import Decimal

import pytest
from app.services.trading.actions.deadlines import create_monotonic_deadline_factory


@pytest.mark.anyio
async def test_monotonic_deadline_allows_work_before_bound() -> None:
    """The live adapter owns one absolute monotonic deadline."""
    loop = asyncio.get_running_loop()
    factory = create_monotonic_deadline_factory(loop.time)

    async with factory(Decimal(1), {"route": "demo"}):
        await asyncio.sleep(0)


@pytest.mark.anyio
async def test_monotonic_deadline_raises_timeout_at_bound() -> None:
    """The live adapter converts task cancellation at its bound to TimeoutError."""
    loop = asyncio.get_running_loop()
    factory = create_monotonic_deadline_factory(loop.time)

    with pytest.raises(TimeoutError):
        async with factory(Decimal("0.001"), {"route": "demo"}):
            await asyncio.sleep(0.01)


def test_deadline_module_is_the_single_asyncio_timeout_owner() -> None:
    """Evaluation runtime delegates timeout ownership to the deadline adapter."""
    runtime_source = (
        __import__("pathlib")
        .Path("app/services/trading/actions/runtime.py")
        .read_text(encoding="utf-8")
    )
    assert "asyncio.timeout" not in runtime_source
