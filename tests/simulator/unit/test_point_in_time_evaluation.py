"""Unit tests for point-in-time Simulation evidence assembly."""

from datetime import timedelta

import pytest
from app.services.simulator.run.evaluation import build_point_in_time_dataset

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
