"""Canonical Simulation-to-Trading cutover integration evidence."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from app.services.simulator.run.contracts import SimulationBacktestRequest
from app.services.simulator.run.orchestrator import advance_trading_timeline

NOW = datetime(2026, 8, 16, tzinfo=UTC)


class _Engine:
    """Record scheduler-owned tick advancement without constructing an intent."""

    def __init__(self) -> None:
        self.ticks: list[object] = []

    def execute_tick(self, tick: object) -> tuple[object, ...]:
        """Record and accept one deterministic tick."""
        self.ticks.append(tick)
        return ()


@pytest.mark.anyio
async def test_v2_requests_enter_only_through_async_trading_action() -> None:
    """A canonical request is awaited through Trading after its due tick."""
    calls: list[object] = []

    class Dependencies:
        """Expose only the public Trading-action seam under test."""

        async def execute_trading_action(
            self, approved: object, engine: object, request: object
        ) -> object:
            """Capture unchanged approved material and return authority evidence."""
            calls.append((approved, engine, request))
            return {"status": "accepted"}

    request = SimulationBacktestRequest.model_construct()
    approved = SimpleNamespace(system_time=NOW, request_id="request-1")
    tick = SimpleNamespace(timestamp=NOW)
    engine = _Engine()
    unsent: list[object] = [approved]
    receipts: list[object] = []

    await advance_trading_timeline(
        Dependencies(),
        request,
        engine,
        (tick,),
        unsent,
        receipts,  # type: ignore[arg-type]
    )

    assert calls == [(approved, engine, request)]
    assert not unsent
    assert receipts == [{"status": "accepted"}]


@pytest.mark.anyio
async def test_trading_action_cancellation_propagates_without_duplicate_mutation() -> (
    None
):
    """Cancellation remains visible and the approved request is consumed once."""
    calls = 0

    class Dependencies:
        """Cancel the one asynchronous Trading action."""

        async def execute_trading_action(self, *_args: object) -> object:
            """Raise the scheduler-visible cancellation."""
            nonlocal calls
            calls += 1
            raise TimeoutError("cancelled")

    approved = SimpleNamespace(system_time=NOW, request_id="request-1")
    with pytest.raises(TimeoutError, match="cancelled"):
        await advance_trading_timeline(
            Dependencies(),  # type: ignore[arg-type]
            SimulationBacktestRequest.model_construct(),
            _Engine(),
            (SimpleNamespace(timestamp=NOW),),
            [approved],
            [],
        )
    assert calls == 1
