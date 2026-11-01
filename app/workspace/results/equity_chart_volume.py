"""Trade size and volume subchart series generator service.

Description:
    Implements EquityChartVolumeService generating trade volume and lot
    size bar series synchronized with the strategy trade sequence.

Purpose:
    FEAT-RESULTS-VOLUME: Trade lot volume subchart series.

Key Capabilities:
    - FR-results-volume-series: Map closed trade lot sizes and directions.

Python API Usage:
    from app.workspace.results.equity_chart_volume import (
        EquityChartVolumeService,
    )
    service = EquityChartVolumeService()
    series = service.compute(trades)

CLI Usage:
    python -m app.cli results volume --strategy-id Strat_01
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.workspace.results.app_results import to_float, to_int

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class VolumePoint:
    """Individual trade size volume data point."""

    index: int
    timestamp_ms: int
    size: float
    direction: Literal["LONG", "SHORT"]

    def to_dict(self) -> dict[str, Any]:
        """Convert volume point to dictionary representation."""
        return {
            "index": self.index,
            "timestamp_ms": self.timestamp_ms,
            "size": self.size,
            "direction": self.direction,
        }


class EquityChartVolumeService:
    """Trade volume subchart series generator service."""

    @classmethod
    def compute(
        cls,
        trades: Sequence[dict[str, Any]],
    ) -> tuple[VolumePoint, ...]:
        """Map trades to chronological VolumePoint entries."""
        points: list[VolumePoint] = []
        for idx, t in enumerate(trades, start=1):
            ts = to_int(
                t.get(
                    "close_time_ms",
                    t.get("close_time", t.get("open_time_ms", 0)),
                )
            )
            raw_size = to_float(t.get("size", 1.0))
            raw_dir = str(t.get("type", t.get("direction", "BUY"))).upper()
            dir_str: Literal["LONG", "SHORT"] = (
                "SHORT" if raw_dir in ("SELL", "SHORT") else "LONG"
            )

            points.append(
                VolumePoint(
                    index=idx,
                    timestamp_ms=ts,
                    size=round(abs(raw_size), 4),
                    direction=dir_str,
                )
            )

        logger.info(
            "FR-results-volume-series: generated %d volume points",
            len(points),
        )
        return tuple(points)
