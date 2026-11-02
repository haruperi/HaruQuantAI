"""Databank Fitness (IS Training) engine chart implementation.

Description:
    Implements DatabankFitnessIST which charts in-sample training (IST)
    fitness progression over time across Top Strategy, Top 10 Average,
    and All Average series.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-databank-fitness-ist: Track in-sample training databank fitness.

Python API Usage:
    from app.extend.engine_charts.databank_fitness_ist import DatabankFitnessIST
    chart = DatabankFitnessIST()
    chart.add_next_value()
    payload = chart.print()

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.engine_charts.base import (
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_RED,
    DATA_TYPE_CHART,
    DEFAULT_POINTS_COUNT,
    TYPE_PROJECT_BASED,
    Databank,
    EngineChart,
    MemoryBean,
    Project,
    TimeSeries,
    TimeSeriesLineChart,
)

logger = get_logger(__name__)


class DatabankFitnessIST(EngineChart):
    """Engine chart tracking in-sample training databank fitness curve."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
    ) -> None:
        super().__init__(
            name="Databank Fitness - IS Training",
            chart_type=TYPE_PROJECT_BASED,
            project=project,
            memory_bean=memory_bean,
        )
        self.chart: TimeSeriesLineChart = TimeSeriesLineChart()
        self.chart.y_axis_range_min = 0.0
        self.chart.y_axis_range_max = 1.0
        self.chart.max_x_ticks_limit = 4
        self.chart.show_legend = True

        self.best_series: TimeSeries = TimeSeries(
            name="Top Strategy",
            points_count=DEFAULT_POINTS_COUNT,
            color=COLOR_GREEN,
        )
        self.top_avg_series: TimeSeries = TimeSeries(
            name="Top 10 Avg",
            points_count=DEFAULT_POINTS_COUNT,
            color=COLOR_BLUE,
        )
        self.avg_series: TimeSeries = TimeSeries(
            name="All Avg",
            points_count=DEFAULT_POINTS_COUNT,
            color=COLOR_RED,
        )

        self.chart.add_series(self.best_series)
        self.chart.add_series(self.top_avg_series)
        self.chart.add_series(self.avg_series)
        logger.info(
            "FR-engine-charts-databank-fitness-ist: initialized DatabankFitnessIST"
        )

    @override
    def print(self) -> dict[str, Any] | None:
        """Render chart data dictionary."""
        return {
            "type": DATA_TYPE_CHART,
            "chart": self.chart.to_json(),
        }

    @override
    def add_next_value(self) -> None:
        """Sample fitness metrics from project results databank."""
        try:
            databank: Databank | None = self.project.get_results_databank()
            if databank is None or not self.project.is_running():
                return
            self._add_value_from_databank(databank)
        except Exception:
            logger.exception("FR-engine-charts-databank-fitness-ist: error")

    def _add_value_from_databank(self, databank: Databank) -> None:
        data = databank.get_fitness_data()
        now = self.current_time_millis()
        self.best_series.add_value(now, data.best_fitness_ist)
        self.top_avg_series.add_value(now, data.top_avg_fitness_ist)
        self.avg_series.add_value(now, data.avg_fitness_ist)
        logger.info(
            "FR-engine-charts-databank-fitness-ist: best=%f, top10=%f, avg=%f",
            data.best_fitness_ist,
            data.top_avg_fitness_ist,
            data.avg_fitness_ist,
        )

    def reset(self) -> None:
        """Clear all series data points."""
        self.best_series.clear()
        self.top_avg_series.clear()
        self.avg_series.clear()
