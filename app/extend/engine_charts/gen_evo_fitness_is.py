"""Genetic Evolution Island #1 Fitness (IS) engine chart implementation.

Description:
    Implements GenEvoFitnessIS which monitors Island #1 genetic evolution
    in-sample (IS) fitness progression per generation across Top Strategy,
    Top Ten Average, and All Average series.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-gen-evo-fitness-is: Track Island #1 IS evolution fitness.

Python API Usage:
    from app.extend.engine_charts.gen_evo_fitness_is import GenEvoFitnessIS
    chart = GenEvoFitnessIS()
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
    GeneticInfo,
    MemoryBean,
    Project,
    TimeSeries,
    TimeSeriesLineChart,
)

logger = get_logger(__name__)


class GenEvoFitnessIS(EngineChart):
    """Engine chart tracking Island #1 in-sample genetic evolution fitness."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
    ) -> None:
        super().__init__(
            name="Island #1 - Fitness IS",
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
        self.best5_avg_series: TimeSeries = TimeSeries(
            name="Top Ten Avg",
            points_count=DEFAULT_POINTS_COUNT,
            color=COLOR_BLUE,
        )
        self.avg_series: TimeSeries = TimeSeries(
            name="All Avg",
            points_count=DEFAULT_POINTS_COUNT,
            color=COLOR_RED,
        )

        self.chart.add_series(self.best_series)
        self.chart.add_series(self.best5_avg_series)
        self.chart.add_series(self.avg_series)
        logger.info("FR-engine-charts-gen-evo-fitness-is: initialized GenEvoFitnessIS")

    @override
    def print(self) -> dict[str, Any] | None:
        """Render chart data dictionary."""
        return {
            "type": DATA_TYPE_CHART,
            "chart": self.chart.to_json(),
        }

    @override
    def add_next_value(self) -> None:
        """Sample fitness metrics from island genetic evolution tracking."""
        try:
            databank: Databank | None = self.project.get_results_databank()
            if databank is None or not self.project.is_running():
                return
            self._add_value_from_gen_evo()
        except Exception:
            logger.exception("FR-engine-charts-gen-evo-fitness-is: error")

    def _add_value_from_gen_evo(self) -> None:
        genetic_info: GeneticInfo = self.project.get_genetic_info()
        best_fitness: float = 0.0
        best5_fitness: float = 0.0
        avg_fitness: float = 0.0

        if genetic_info.is_genetic_build():
            islands = genetic_info.get_islands_evo_data()
            if islands:
                island = islands[0]
                if (
                    island.generation < len(island.generation_data)
                    and island.generation_data[island.generation] is not None
                ):
                    gen_data = island.generation_data[island.generation]
                    if gen_data is not None:
                        best_fitness = gen_data.best_fitness_is
                        best5_fitness = gen_data.top_avg_fitness_is
                        avg_fitness = gen_data.avg_fitness_is

        now = self.current_time_millis()
        self.best_series.add_value(now, best_fitness)
        self.best5_avg_series.add_value(now, best5_fitness)
        self.avg_series.add_value(now, avg_fitness)
        logger.info(
            "FR-engine-charts-gen-evo-fitness-is: best=%f, best5=%f, avg=%f",
            best_fitness,
            best5_fitness,
            avg_fitness,
        )

    def reset(self) -> None:
        """Clear all series data points."""
        self.best_series.clear()
        self.best5_avg_series.clear()
        self.avg_series.clear()
