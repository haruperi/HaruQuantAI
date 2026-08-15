"""Integration tests for Simulation evaluation clock-edge evidence."""

from datetime import UTC, datetime, timedelta

import pytest
from app.services.simulator.run.evaluation import build_evaluation_latency

NOW = datetime(2026, 8, 16, tzinfo=UTC)


def test_missing_clock_edge_excludes_latency_metric() -> None:
    """Incomplete evidence is omitted instead of reported as false zero."""
    assert build_evaluation_latency(NOW, None) is None
    assert build_evaluation_latency(None, NOW) is None


def test_scheduler_clock_edges_produce_non_negative_latency() -> None:
    """Complete ordered scheduler edges yield their exact elapsed seconds."""
    assert build_evaluation_latency(NOW, NOW + timedelta(seconds=2)) == 2.0
    with pytest.raises(ValueError, match="reversed"):
        build_evaluation_latency(NOW, NOW - timedelta(microseconds=1))
