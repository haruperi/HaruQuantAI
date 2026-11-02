"""Off-Heap Memory engine chart implementation.

Description:
    Implements OffHeapMemoryChart which tracks native/off-heap memory
    allocation in megabytes over time using an area chart.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-off-heap-memory: Track off-heap memory consumption.

Python API Usage:
    from app.extend.engine_charts.off_heap_memory_chart import OffHeapMemoryChart
    chart = OffHeapMemoryChart()
    chart.add_next_value()
    payload = chart.print()

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.engine_charts.base import (
    DATA_TYPE_CHART,
    DEFAULT_POINTS_COUNT,
    MEGABYTE,
    TYPE_GLOBAL,
    EngineChart,
    MemoryBean,
    MemoryInfo,
    Project,
    TimeSeries,
    TimeSeriesAreaChart,
)

logger = get_logger(__name__)


class OffHeapMemoryChart(EngineChart):
    """Engine chart tracking off-heap/native allocated memory in megabytes."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
        off_heap_info: MemoryInfo | None = None,
    ) -> None:
        super().__init__(
            name="Off-heap memory chart",
            chart_type=TYPE_GLOBAL,
            project=project,
            memory_bean=memory_bean,
        )
        self.off_heap_info: MemoryInfo = off_heap_info or MemoryInfo()
        self.chart: TimeSeriesAreaChart = TimeSeriesAreaChart()
        self.chart.y_axis_title = "Memory"
        self.chart.x_axis_title = "Time"
        self.chart.max_x_ticks_limit = 4
        self.chart.y_axis_range_min = 0.0
        self.chart.max_y_ticks_limit = 6
        self.chart.y_axis_ticks_memory = True

        self.series: TimeSeries = TimeSeries(
            name="Off-Heap Size",
            points_count=DEFAULT_POINTS_COUNT,
            color="#FF6E66",
        )
        self.chart.add_series(self.series)
        logger.info("FR-engine-charts-off-heap-memory: initialized OffHeapMemoryChart")

    @override
    def print(self) -> dict[str, Any] | None:
        """Render chart data dictionary."""
        return {
            "type": DATA_TYPE_CHART,
            "chart": self.chart.to_json(),
        }

    @override
    def add_next_value(self) -> None:
        """Sample off-heap allocated memory clamped to non-negative megabytes."""
        try:
            used_mb = max(0.0, self.off_heap_info.allocated_memory / MEGABYTE)
            self.series.add_value(self.current_time_millis(), used_mb)
            logger.info("FR-engine-charts-off-heap-memory: used_mb=%f", used_mb)
        except Exception:
            logger.exception("FR-engine-charts-off-heap-memory: error")
