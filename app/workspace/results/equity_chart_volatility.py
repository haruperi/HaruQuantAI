"""Rolling return volatility subchart series generator service.

Description:
    Implements EquityChartVolatilityService computing rolling standard
    deviation of equity return deltas and percentages over trailing windows.

Purpose:
    FEAT-RESULTS-VOLATILITY: Rolling return volatility subchart series.

Key Capabilities:
    - FR-results-volatility-rolling: Trailing standard deviation of returns.

Python API Usage:
    from app.workspace.results.equity_chart_volatility import (
        EquityChartVolatilityService,
    )
    service = EquityChartVolatilityService()
    series = service.compute([(1, 10000.0), (2, 10100.0)], window=2)

CLI Usage:
    python -m app.cli results volatility --strategy-id Strat_01 --window 20
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)

MIN_VOLATILITY_WINDOW = 2


@dataclass(frozen=True, slots=True)
class VolatilityPoint:
    """Individual rolling volatility data point."""

    index: int
    timestamp_ms: int
    rolling_stddev_money: float
    rolling_stddev_pct: float

    def to_dict(self) -> dict[str, Any]:
        """Convert volatility point to dictionary representation."""
        return {
            "index": self.index,
            "timestamp_ms": self.timestamp_ms,
            "rolling_stddev_money": self.rolling_stddev_money,
            "rolling_stddev_pct": self.rolling_stddev_pct,
        }


class EquityChartVolatilityService:
    """Rolling volatility subchart series generator service."""

    @classmethod
    def compute(
        cls,
        points: Sequence[tuple[int, float]],
        *,
        window: int = 20,
    ) -> tuple[VolatilityPoint, ...]:
        """Compute rolling population standard deviation of step returns."""
        if window < MIN_VOLATILITY_WINDOW:
            raise DomainError(
                code="RESULTS_INVALID_VOLATILITY_WINDOW",
                message=f"Volatility window must be >= 2, got {window}",
                details={"window": window},
            )

        if not points:
            return ()

        # Compute deltas
        deltas_money: list[float] = [0.0]
        deltas_pct: list[float] = [0.0]

        for i in range(1, len(points)):
            prev_eq = points[i - 1][1]
            curr_eq = points[i][1]
            d_m = curr_eq - prev_eq
            d_p = (d_m / prev_eq) * 100.0 if prev_eq > 0.0 else 0.0
            deltas_money.append(d_m)
            deltas_pct.append(d_p)

        vol_points: list[VolatilityPoint] = []
        for i, (ts, _) in enumerate(points):
            if i == 0:
                vol_points.append(
                    VolatilityPoint(
                        index=i,
                        timestamp_ms=ts,
                        rolling_stddev_money=0.0,
                        rolling_stddev_pct=0.0,
                    )
                )
                continue

            start_idx = max(1, i - window + 1)
            win_m = deltas_money[start_idx : i + 1]
            win_p = deltas_pct[start_idx : i + 1]

            std_m = cls._calc_stddev(win_m)
            std_p = cls._calc_stddev(win_p)

            vol_points.append(
                VolatilityPoint(
                    index=i,
                    timestamp_ms=ts,
                    rolling_stddev_money=round(std_m, 4),
                    rolling_stddev_pct=round(std_p, 4),
                )
            )

        logger.info(
            "FR-results-volatility-rolling: computed %d volatility points (window=%d)",
            len(vol_points),
            window,
        )
        return tuple(vol_points)

    @staticmethod
    def _calc_stddev(values: list[float]) -> float:
        if len(values) < MIN_VOLATILITY_WINDOW:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
