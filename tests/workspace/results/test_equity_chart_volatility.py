"""Unit tests for EquityChartVolatilityService."""

from __future__ import annotations

import pytest
from app.core.lib.errors import DomainError
from app.workspace.results.equity_chart_volatility import (
    EquityChartVolatilityService,
    VolatilityPoint,
)


class TestEquityChartVolatilityService:
    """Test suite for EquityChartVolatilityService."""

    def test_volatility_computation(self) -> None:
        """Verify rolling standard deviation calculation."""
        points = [
            (1000, 10_000.0),
            (2000, 10_100.0),
            (3000, 10_050.0),
            (4000, 10_200.0),
        ]
        series = EquityChartVolatilityService.compute(points, window=2)
        assert len(series) == 4

        p0 = series[0]
        assert p0.index == 0
        assert p0.rolling_stddev_money == 0.0

        p1 = series[1]
        assert p1.index == 1
        assert p1.rolling_stddev_money >= 0.0

        p3 = series[3]
        assert p3.rolling_stddev_money >= 0.0

        d = p1.to_dict()
        assert d["index"] == 1
        assert "rolling_stddev_pct" in d

    def test_volatility_invalid_window(self) -> None:
        """Verify DomainError when window < 2."""
        with pytest.raises(DomainError) as exc_info:
            EquityChartVolatilityService.compute([(1000, 100.0)], window=1)
        assert exc_info.value.code == "RESULTS_INVALID_VOLATILITY_WINDOW"

    def test_volatility_empty_points(self) -> None:
        """Verify empty series for empty input points."""
        res = EquityChartVolatilityService.compute((), window=5)
        assert len(res) == 0

    def test_volatility_point_to_dict(self) -> None:
        """Verify VolatilityPoint to_dict."""
        pt = VolatilityPoint(
            index=2,
            timestamp_ms=2000,
            rolling_stddev_money=12.5,
            rolling_stddev_pct=0.125,
        )
        d = pt.to_dict()
        assert d["rolling_stddev_money"] == 12.5
