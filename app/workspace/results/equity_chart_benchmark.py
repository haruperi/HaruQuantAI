"""Benchmark overlay series calculation service for Equity Charts.

Description:
    Implements EquityChartBenchmarkService computing buy-and-hold benchmark
    curves normalized to initial capital and date boundaries.

Purpose:
    FEAT-RESULTS-BENCHMARK: Buy-and-hold benchmark overlay series.

Key Capabilities:
    - FR-results-benchmark-normalize: Normalize price bars to initial capital.

Python API Usage:
    from app.workspace.results.equity_chart_benchmark import (
        EquityChartBenchmarkService,
    )
    service = EquityChartBenchmarkService()
    series = service.compute(10000.0, [(1000, 100.0), (2000, 105.0)])

CLI Usage:
    python -m app.cli results benchmark --symbol SPY --capital 10000
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class BenchmarkPoint:
    """Individual normalized benchmark curve data point."""

    timestamp_ms: int
    equity: float
    return_pct: float

    def to_dict(self) -> dict[str, Any]:
        """Convert point to dictionary representation."""
        return {
            "timestamp_ms": self.timestamp_ms,
            "equity": self.equity,
            "return_pct": self.return_pct,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkSeriesResult:
    """Normalized benchmark series outcome."""

    symbol: str
    initial_capital: float
    points: tuple[BenchmarkPoint, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert series result to dictionary representation."""
        return {
            "symbol": self.symbol,
            "initial_capital": self.initial_capital,
            "points": [p.to_dict() for p in self.points],
        }


class EquityChartBenchmarkService:
    """Benchmark series generator service."""

    @classmethod
    def compute(
        cls,
        initial_capital: float,
        bars: Sequence[tuple[int, float]],
        *,
        start_ms: int | None = None,
        end_ms: int | None = None,
        symbol: str = "",
    ) -> BenchmarkSeriesResult:
        """Compute normalized benchmark points over optional time window."""
        filtered_bars = [
            (ts, close)
            for ts, close in bars
            if (start_ms is None or ts >= start_ms) and (end_ms is None or ts <= end_ms)
        ]

        if not filtered_bars or filtered_bars[0][1] <= 0.0:
            logger.info(
                "FR-results-benchmark-normalize: no valid bars for symbol=%s",
                symbol,
            )
            return BenchmarkSeriesResult(
                symbol=symbol,
                initial_capital=initial_capital,
                points=(),
            )

        close_0 = filtered_bars[0][1]
        points: list[BenchmarkPoint] = []
        for ts, close in filtered_bars:
            ratio = close / close_0
            equity = round(initial_capital * ratio, 2)
            ret_pct = round((ratio - 1.0) * 100.0, 4)
            points.append(
                BenchmarkPoint(
                    timestamp_ms=ts,
                    equity=equity,
                    return_pct=ret_pct,
                )
            )

        logger.info(
            "FR-results-benchmark-normalize: computed %d benchmark points for %s",
            len(points),
            symbol,
        )
        return BenchmarkSeriesResult(
            symbol=symbol,
            initial_capital=initial_capital,
            points=tuple(points),
        )
