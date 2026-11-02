"""Accepted strategies per hour engine chart implementation.

Description:
    Implements the AcceptedStrategiesPerHour engine chart which monitors
    the rate of strategies accepted into results databanks per hour over
    time, refreshing UI telemetry with threshold throttling.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-accepted-per-hour: Track accepted strategies rate.

Python API Usage:
    from app.extend.engine_charts.accepted_strategies_per_hour import (
        AcceptedStrategiesPerHour,
    )
    chart = AcceptedStrategiesPerHour()
    chart.add_next_value()
    payload = chart.print()

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.engine_charts.base import (
    COLOR_GREEN,
    DATA_TYPE_CHART,
    DEFAULT_POINTS_COUNT,
    TYPE_PROJECT_BASED,
    EngineChart,
    MemoryBean,
    Project,
    ProjectRunInfo,
    TimeSeries,
    TimeSeriesLineChart,
)

logger = get_logger(__name__)

MAX_CHECKS_WITHOUT_CHANGE: int = 10


class AcceptedStrategiesPerHour(EngineChart):
    """Engine chart tracking accepted strategies produced per hour."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
    ) -> None:
        super().__init__(
            name="Accepted strategies per hour",
            chart_type=TYPE_PROJECT_BASED,
            project=project,
            memory_bean=memory_bean,
        )
        self.chart: TimeSeriesLineChart = TimeSeriesLineChart()
        self.chart.y_axis_title = "Strategies"
        self.chart.x_axis_title = "Time"
        self.chart.max_x_ticks_limit = 4
        self.chart.y_axis_range_min = 0.0

        self.series: TimeSeries = TimeSeries(
            name="Accepted str. per hour",
            points_count=DEFAULT_POINTS_COUNT,
            color=COLOR_GREEN,
        )
        self.chart.add_series(self.series)

        self.project_run_info: ProjectRunInfo = ProjectRunInfo()
        self.old_project_run_info: ProjectRunInfo = ProjectRunInfo()
        self.old_project_run_info.total_jobs_done = -1
        self.checks_since_last_change: int = 0
        logger.info(
            "FR-engine-charts-accepted-per-hour: initialized AcceptedStrategiesPerHour"
        )

    @override
    def print(self) -> dict[str, Any] | None:
        """Render chart JSON data if status changed or throttling limit exceeded."""
        self.project.load_tracking_info(self.project_run_info, force=False)
        self.checks_since_last_change += 1

        if (
            self.old_project_run_info.total_jobs_done == -1
            or self.project_run_info.total_jobs_done
            != self.old_project_run_info.total_jobs_done
            or self.checks_since_last_change > MAX_CHECKS_WITHOUT_CHANGE
        ):
            self.old_project_run_info.total_jobs_done = (
                self.project_run_info.total_jobs_done
            )
            self.checks_since_last_change = 0

            return {
                "type": DATA_TYPE_CHART,
                "chart": self.chart.to_json(),
            }
        return None

    @override
    def add_next_value(self) -> None:
        """Sample accepted strategies per hour from project runtime tracking."""
        try:
            if not self.project.is_running():
                return
            self.project.load_tracking_info(self.project_run_info, force=False)
            self.series.add_value(
                self.current_time_millis(),
                self.project_run_info.accepted_strategies_per_hour,
            )
            logger.info(
                "FR-engine-charts-accepted-per-hour: sampled value %f",
                self.project_run_info.accepted_strategies_per_hour,
            )
        except Exception:
            logger.exception("FR-engine-charts-accepted-per-hour: error adding value")
