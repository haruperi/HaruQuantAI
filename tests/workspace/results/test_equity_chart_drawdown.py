"""Unit tests for EquityChartDrawdownService."""

from __future__ import annotations

import pytest
from app.workspace.results.equity_chart_drawdown import (
    DrawdownPoint,
    EquityChartDrawdownService,
)


class TestEquityChartDrawdownService:
    """Test suite for EquityChartDrawdownService."""

    def test_drawdown_underwater_progression(self) -> None:
        """Verify underwater drawdown calculation in money and percentage."""
        points = [
            (1000, 10_500.0),  # New peak 10500, dd=0
            (2000, 10_200.0),  # dd = -300 (-2.8571%)
            (3000, 9_900.0),  # dd = -600 (-5.7143%)
            (4000, 10_600.0),  # New peak 10600, dd=0
        ]
        dd_series = EquityChartDrawdownService.compute(10_000.0, points)
        assert len(dd_series) == 4

        p1 = dd_series[0]
        assert p1.index == 1
        assert p1.peak_equity == 10_500.0
        assert p1.drawdown_money == 0.0
        assert p1.drawdown_pct == 0.0

        p2 = dd_series[1]
        assert p2.index == 2
        assert p2.peak_equity == 10_500.0
        assert p2.drawdown_money == -300.0
        assert p2.drawdown_pct == pytest.approx(-2.8571, abs=1e-3)

        p3 = dd_series[2]
        assert p3.drawdown_money == -600.0

        p4 = dd_series[3]
        assert p4.peak_equity == 10_600.0
        assert p4.drawdown_money == 0.0

        d = p2.to_dict()
        assert d["drawdown_money"] == -300.0

    def test_drawdown_empty(self) -> None:
        """Verify empty points input."""
        res = EquityChartDrawdownService.compute(10_000.0, ())
        assert len(res) == 0

    def test_drawdown_point_to_dict(self) -> None:
        """Verify DrawdownPoint to_dict."""
        pt = DrawdownPoint(
            index=1,
            timestamp_ms=1000,
            drawdown_money=-50.0,
            drawdown_pct=-0.5,
            peak_equity=10000.0,
        )
        d = pt.to_dict()
        assert d["index"] == 1
        assert d["drawdown_money"] == -50.0
