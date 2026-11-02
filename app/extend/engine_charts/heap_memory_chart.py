"""Heap Memory engine chart implementation.

Description:
    Implements HeapMemoryChart which tracks process heap memory usage
    and committed heap size over time as an area chart with memory-scaled
    ticks.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-heap-memory: Track heap memory telemetry.

Python API Usage:
    from app.extend.engine_charts.heap_memory_chart import HeapMemoryChart
    chart = HeapMemoryChart()
    chart.add_next_value()
    payload = chart.print()

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

import gc
from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.engine_charts.base import (
    DATA_TYPE_CHART,
    DEFAULT_POINTS_COUNT,
    MEGABYTE,
    TYPE_GLOBAL,
    EngineChart,
    MemoryBean,
    Project,
    TimeSeries,
    TimeSeriesAreaChart,
)

logger = get_logger(__name__)

CHECKS_MODULO_GC: int = 5000


class HeapMemoryChart(EngineChart):
    """Engine chart tracking runtime heap memory usage and committed capacity."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
        max_heap_memory: int = 1024 * 1024 * 1024,
    ) -> None:
        super().__init__(
            name="Heap memory chart",
            chart_type=TYPE_GLOBAL,
            project=project,
            memory_bean=memory_bean,
            max_heap_memory=max_heap_memory,
        )
        self.chart: TimeSeriesAreaChart = TimeSeriesAreaChart()
        self.chart.y_axis_title = "Memory"
        self.chart.x_axis_title = "Time"
        self.chart.y_axis_range_min = 0.0
        self.chart.y_axis_range_max = float(int(self.max_heap_memory * 1.1 / MEGABYTE))
        self.chart.max_x_ticks_limit = 4
        self.chart.max_y_ticks_limit = 6
        self.chart.y_axis_ticks_memory = True

        self.memory_usage_series: TimeSeries = TimeSeries(
            name="Memory Usage",
            points_count=DEFAULT_POINTS_COUNT,
            color="#FF6E66",
        )
        self.heap_size_series: TimeSeries = TimeSeries(
            name="Heap Size",
            points_count=DEFAULT_POINTS_COUNT,
            color="#BFDFBF",
        )

        self.chart.add_series(self.memory_usage_series)
        self.chart.add_series(self.heap_size_series)
        self.checks: int = 0
        logger.info("FR-engine-charts-heap-memory: initialized HeapMemoryChart")

    @override
    def print(self) -> dict[str, Any] | None:
        """Render chart data dictionary and trigger periodic GC maintenance."""
        self.checks += 1
        if self.checks % CHECKS_MODULO_GC == 1:
            gc.collect()

        return {
            "type": DATA_TYPE_CHART,
            "chart": self.chart.to_json(),
        }

    @override
    def add_next_value(self) -> None:
        """Sample heap usage and committed size from memory bean in megabytes."""
        try:
            heap_usage = self.memory_bean.get_heap_memory_usage()
            used_mb = heap_usage.get_used() / MEGABYTE
            heap_size_mb = heap_usage.get_committed() / MEGABYTE

            now = self.current_time_millis()
            self.memory_usage_series.add_value(now, used_mb)
            self.heap_size_series.add_value(now, heap_size_mb)
            logger.info(
                "FR-engine-charts-heap-memory: used_mb=%f, committed_mb=%f",
                used_mb,
                heap_size_mb,
            )
        except Exception:
            logger.exception("FR-engine-charts-heap-memory: error")
