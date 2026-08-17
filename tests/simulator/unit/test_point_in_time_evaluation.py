"""Unit tests for point-in-time Simulation evidence assembly."""

from datetime import timedelta
from unittest.mock import Mock

import pytest
from app.services.simulator.run.evaluation import (
    _PointInTimeDatasetCursor,
    build_point_in_time_dataset,
    run_point_in_time_evaluation,
)

from tests.simulator.unit.test_timeline import _dataset


def test_decision_sees_only_records_available_at_its_instant() -> None:
    """A decision excludes every future timestamp and availability edge."""
    dataset = _dataset()
    visible = build_point_in_time_dataset(dataset, dataset.records[0].available_at)
    assert visible.records == (dataset.records[0],)
    assert visible.record_count == 1


def test_decision_without_available_evidence_fails_closed() -> None:
    """The evaluator never invents an empty or future market state."""
    dataset = _dataset()
    with pytest.raises(ValueError, match="no market evidence"):
        build_point_in_time_dataset(
            dataset, dataset.records[0].available_at - timedelta(microseconds=1)
        )


def test_cursor_matches_canonical_builder_at_every_decision_instant() -> None:
    """The optimized cursor returns the canonical visible dataset exactly."""
    dataset = _dataset()
    cursor = _PointInTimeDatasetCursor(dataset)
    decisions = (
        dataset.records[0].available_at,
        dataset.records[0].available_at + timedelta(microseconds=1),
        dataset.records[1].available_at,
    )

    for decision_at in decisions:
        assert cursor.build(decision_at) == build_point_in_time_dataset(
            dataset, decision_at
        )


def test_cursor_falls_back_when_availability_is_not_monotonic() -> None:
    """An invalid fast-path ordering assumption preserves canonical behavior."""
    dataset = _dataset()
    delayed_first = dataset.records[0].model_copy(
        update={"available_at": dataset.records[1].available_at + timedelta(seconds=1)}
    )
    early_second = dataset.records[1].model_copy(
        update={"available_at": dataset.records[1].timestamp}
    )
    unordered = dataset.model_copy(update={"records": (delayed_first, early_second)})
    cursor = _PointInTimeDatasetCursor(unordered)

    decision_at = dataset.records[1].timestamp
    assert cursor.build(decision_at) == build_point_in_time_dataset(
        unordered, decision_at
    )


@pytest.mark.anyio
async def test_repeated_visible_prefix_reuses_one_materialized_dataset() -> None:
    """Derived ticks sharing a source prefix avoid duplicate reconstruction."""
    dataset = _dataset()
    cursor = _PointInTimeDatasetCursor(dataset)
    cycle = Mock(return_value="evaluated")
    decision_at = dataset.records[0].available_at

    first = await run_point_in_time_evaluation(
        dataset, decision_at, cycle, point_in_time_cursor=cursor
    )
    second = await run_point_in_time_evaluation(
        dataset,
        decision_at + timedelta(microseconds=1),
        cycle,
        point_in_time_cursor=cursor,
    )

    assert first == second == "evaluated"
    assert cycle.call_count == 2
    assert cycle.call_args_list[0].args[0] is cycle.call_args_list[1].args[0]
