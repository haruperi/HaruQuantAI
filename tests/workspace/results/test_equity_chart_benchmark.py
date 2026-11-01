"""Unit tests for EquityChartBenchmarkService."""

from __future__ import annotations

from app.workspace.results.equity_chart_benchmark import (
    BenchmarkPoint,
    EquityChartBenchmarkService,
)


class TestEquityChartBenchmarkService:
    """Test suite for EquityChartBenchmarkService."""

    def test_benchmark_normalization(self) -> None:
        """Verify normal benchmark calculation with positive bars."""
        bars = [
            (1_000_000, 100.0),
            (1_001_000, 105.0),
            (1_002_000, 95.0),
        ]
        res = EquityChartBenchmarkService.compute(10_000.0, bars, symbol="SPY")
        assert res.symbol == "SPY"
        assert res.initial_capital == 10_000.0
        assert len(res.points) == 3

        p0 = res.points[0]
        assert p0.equity == 10_000.0
        assert p0.return_pct == 0.0

        p1 = res.points[1]
        assert p1.equity == 10_500.0
        assert p1.return_pct == 5.0

        p2 = res.points[2]
        assert p2.equity == 9_500.0
        assert p2.return_pct == -5.0

        d = res.to_dict()
        assert d["symbol"] == "SPY"
        assert len(d["points"]) == 3

    def test_benchmark_window_filtering(self) -> None:
        """Verify window filtering with start_ms and end_ms."""
        bars = [
            (1_000, 100.0),
            (2_000, 110.0),
            (3_000, 120.0),
            (4_000, 130.0),
        ]
        res = EquityChartBenchmarkService.compute(
            1_000.0, bars, start_ms=2_000, end_ms=3_000
        )
        assert len(res.points) == 2
        assert res.points[0].timestamp_ms == 2_000
        assert res.points[0].equity == 1_000.0
        assert res.points[1].timestamp_ms == 3_000
        assert res.points[1].equity == round(1_000.0 * (120.0 / 110.0), 2)

    def test_benchmark_empty_or_zero_price(self) -> None:
        """Verify empty series when bars are empty or initial price is non-positive."""
        res_empty = EquityChartBenchmarkService.compute(10_000.0, ())
        assert len(res_empty.points) == 0

        res_zero = EquityChartBenchmarkService.compute(10_000.0, [(1000, 0.0)])
        assert len(res_zero.points) == 0

    def test_benchmark_point_to_dict(self) -> None:
        """Verify BenchmarkPoint dictionary conversion."""
        pt = BenchmarkPoint(timestamp_ms=1234, equity=10000.0, return_pct=0.0)
        d = pt.to_dict()
        assert d["timestamp_ms"] == 1234
        assert d["equity"] == 10000.0
