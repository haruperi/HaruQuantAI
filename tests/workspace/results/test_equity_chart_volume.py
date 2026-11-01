"""Unit tests for EquityChartVolumeService."""

from __future__ import annotations

from app.workspace.results.equity_chart_volume import (
    EquityChartVolumeService,
    VolumePoint,
)


class TestEquityChartVolumeService:
    """Test suite for EquityChartVolumeService."""

    def test_volume_computation(self) -> None:
        """Verify volume series mapping trade size and direction."""
        trades = [
            {"close_time_ms": 1000, "size": 1.5, "direction": "BUY"},
            {"close_time_ms": 2000, "size": -2.0, "direction": "SELL"},
        ]
        points = EquityChartVolumeService.compute(trades)
        assert len(points) == 2

        p1 = points[0]
        assert p1.index == 1
        assert p1.timestamp_ms == 1000
        assert p1.size == 1.5
        assert p1.direction == "LONG"

        p2 = points[1]
        assert p2.index == 2
        assert p2.timestamp_ms == 2000
        assert p2.size == 2.0
        assert p2.direction == "SHORT"

        d = p1.to_dict()
        assert d["direction"] == "LONG"
        assert d["size"] == 1.5

    def test_volume_empty(self) -> None:
        """Verify empty trades list produces empty tuple."""
        points = EquityChartVolumeService.compute([])
        assert len(points) == 0

    def test_volume_point_to_dict(self) -> None:
        """Verify VolumePoint to_dict serialization."""
        pt = VolumePoint(index=1, timestamp_ms=5000, size=0.5, direction="LONG")
        d = pt.to_dict()
        assert d["index"] == 1
        assert d["size"] == 0.5
