"""Integration evidence that scheduler decisions cannot observe future data."""

import pytest
from app.services.simulator.run.evaluation import run_point_in_time_evaluation

from tests.simulator.unit.test_timeline import _dataset


@pytest.mark.anyio
async def test_no_dependency_returns_future_available_evidence() -> None:
    """The owner composition receives a physically bounded Data contract."""
    dataset = _dataset()

    async def cycle(visible, decision_at):
        assert all(row.timestamp <= decision_at for row in visible.records)
        assert all(row.available_at <= decision_at for row in visible.records)
        return visible.record_count

    result = await run_point_in_time_evaluation(
        dataset, dataset.records[0].available_at, cycle
    )
    assert result == 1
