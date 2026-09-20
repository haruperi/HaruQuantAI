"""Tests for FEAT-BROKERS-FENCING (app/services/brokers/isolation_fencing.py)."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.brokers import (
    BROKER_FENCING,
    BrokerFencedError,
)
from app.kernel.bootstrapper import Runtime
from app.services.brokers.isolation_fencing import (
    BrokerFencingConfig,
    BrokerFencingService,
    feature,
)


def test_fencing_trip_and_reset() -> None:
    """Verify FR-BROKERS-CIRCUIT_FENCING: manual trip and reset of isolation fence."""
    fencing = BrokerFencingService(BrokerFencingConfig(max_consecutive_errors=2))

    assert fencing.is_fenced("mt5") is False
    fencing.assert_safe_to_submit("mt5")

    fencing.trip_fence("mt5", "Socket disconnected abruptly")
    assert fencing.is_fenced("mt5") is True

    with pytest.raises(BrokerFencedError, match="locked in fail-closed fence"):
        fencing.assert_safe_to_submit("mt5")

    fencing.reset_fence("mt5")
    assert fencing.is_fenced("mt5") is False
    fencing.assert_safe_to_submit("mt5")


def test_consecutive_errors_threshold() -> None:
    """Verify automatic fence engagement when consecutive errors exceed limit."""
    fencing = BrokerFencingService(BrokerFencingConfig(max_consecutive_errors=3))

    fencing.record_error("ctrader", "Timeout 1")
    assert fencing.is_fenced("ctrader") is False

    fencing.record_success("ctrader")  # Resets counter
    fencing.record_error("ctrader", "Timeout 1 again")
    fencing.record_error("ctrader", "Timeout 2")
    assert fencing.is_fenced("ctrader") is False

    fencing.record_error("ctrader", "Timeout 3")  # Hits 3
    assert fencing.is_fenced("ctrader") is True


def test_fencing_runtime_wiring() -> None:
    """Verify runtime publication of BROKER_FENCING capability."""

    async def _test() -> None:
        runtime = Runtime((feature,))
        async with runtime:
            svc = runtime.get(BROKER_FENCING)
            assert svc is not None
            assert svc.is_fenced("binance") is False

    asyncio.run(_test())
