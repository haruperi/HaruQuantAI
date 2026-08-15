"""Integration tests for incremental Simulation-to-Trading evaluation."""

import pytest
from app.services.simulator.run.contracts import SimulationBacktestRequestV2
from app.services.simulator.run.orchestrator import advance_trading_timeline
from app.services.simulator.timeline import build_tick_timeline

from tests.simulator.unit.test_timeline import _dataset


@pytest.mark.anyio
async def test_each_tick_invokes_one_point_in_time_cycle_after_execution() -> None:
    """Prior tick effects are visible before the next decision is evaluated."""
    calls: list[tuple[int, int]] = []

    class Engine:
        """Count authority ticks."""

        count = 0

        def execute_tick(self, _tick):
            self.count += 1
            return ()

    class Dependencies:
        """Capture bounded dataset size and already-applied tick count."""

        async def evaluate_point_in_time_cycle(
            self, dataset, _decision_at, engine, _request
        ):
            calls.append((dataset.record_count, engine.count))
            return {"decision": dataset.record_count}

        async def execute_trading_action(self, *_args):
            raise AssertionError("no prebuilt request expected")

    dataset = _dataset()
    receipts: list[object] = []
    await advance_trading_timeline(
        Dependencies(),
        SimulationBacktestRequestV2.model_construct(),
        Engine(),
        build_tick_timeline(dataset),
        [],
        receipts,
        dataset,
    )
    assert calls == [(1, 1), (2, 2)]
    assert receipts == [{"decision": 1}, {"decision": 2}]
