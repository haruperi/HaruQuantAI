"""Drawdown underwater curve subchart series generator service.

Description:
    Implements EquityChartDrawdownService computing non-positive underwater
    drawdown curves in money and percentage synchronized with Equity Chart.

Purpose:
    FEAT-RESULTS-DRAWDOWN: Underwater drawdown subchart series.

Key Capabilities:
    - FR-results-drawdown-underwater: Compute peak-to-trough drawdown series.

Python API Usage:
    from app.workspace.results.equity_chart_drawdown import (
        EquityChartDrawdownService,
    )
    service = EquityChartDrawdownService()
    series = service.compute(10000.0, [(1, 10200.0), (2, 9996.0)])

CLI Usage:
    python -m app.cli results drawdown --strategy-id Strat_01
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class DrawdownPoint:
    """Individual underwater drawdown data point."""

    index: int
    timestamp_ms: int
    drawdown_money: float
    drawdown_pct: float
    peak_equity: float

    def to_dict(self) -> dict[str, Any]:
        """Convert drawdown point to dictionary representation."""
        return {
            "index": self.index,
            "timestamp_ms": self.timestamp_ms,
            "drawdown_money": self.drawdown_money,
            "drawdown_pct": self.drawdown_pct,
            "peak_equity": self.peak_equity,
        }


class EquityChartDrawdownService:
    """Drawdown subchart series generator service."""

    @classmethod
    def compute(
        cls,
        initial_capital: float,
        equity_points: Sequence[tuple[int, float]],
    ) -> tuple[DrawdownPoint, ...]:
        """Compute underwater drawdown money and percentage for equity sequence."""
        points: list[DrawdownPoint] = []
        peak_equity = initial_capital

        for idx, (ts, eq) in enumerate(equity_points, start=1):
            peak_equity = max(peak_equity, eq)
            dd_money = round(min(0.0, eq - peak_equity), 2)
            dd_pct = (
                round((dd_money / peak_equity) * 100.0, 4) if peak_equity > 0.0 else 0.0
            )

            points.append(
                DrawdownPoint(
                    index=idx,
                    timestamp_ms=ts,
                    drawdown_money=dd_money,
                    drawdown_pct=dd_pct,
                    peak_equity=round(peak_equity, 2),
                )
            )

        logger.info(
            "FR-results-drawdown-underwater: computed %d drawdown points",
            len(points),
        )
        return tuple(points)
