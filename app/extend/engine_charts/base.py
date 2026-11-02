"""EngineCharts core base classes, time series chart structures, and telemetry models.

Description:
    Provides the foundational EngineChart abstract base class, time series
    primitives (TimeSeries, TimeSeriesLineChart, TimeSeriesAreaChart),
    runtime context models (ProjectRunInfo, FitnessCollectionData,
    GeneticInfo, MemoryInfo, MemoryBean), and human byte formatting utilities.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Core engine charts framework and data structures.

Key Capabilities:
    - FR-engine-charts-core: Core time series, line/area charts, and telemetry models.

Python API Usage:
    from app.extend.engine_charts.base import (
        EngineChart,
        TimeSeriesLineChart,
        TimeSeries,
        ProjectRunInfo,
    )

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

# Output types matching Angular directives
DATA_TYPE_CHART: str = "chart"
DATA_TYPE_ROWS: str = "rows"
DATA_TYPE_GRID: str = "grid"

# Scope types
TYPE_PROJECT_BASED: int = 1
TYPE_GLOBAL: int = 2

# Memory constants
MEGABYTE: int = 1024 * 1024
BYTES_PER_KB: float = 1024.0

# Standard UI palette colors matching donor ChartsConst
COLOR_GREEN: str = "#5cb85c"
COLOR_BLUE: str = "#337ab7"
COLOR_RED: str = "#d9534f"

DEFAULT_POINTS_COUNT: int = 100


def format_bytes_to_human_format(bytes_count: int) -> str:
    """Format a byte count into a human-readable string (e.g. '12.5 MB').

    Args:
        bytes_count: Raw number of bytes.

    Returns:
        Formatted human-readable string.
    """
    if bytes_count < 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    val = float(bytes_count)
    unit_idx = 0
    while val >= BYTES_PER_KB and unit_idx < len(units) - 1:
        val /= BYTES_PER_KB
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(val)} B"
    return f"{val:.1f} {units[unit_idx]}"


@dataclass
class ProjectRunInfo:
    """Snapshot of builder project execution tracking information."""

    total_jobs_done: int = 0
    accepted_strategies_per_hour: float = 0.0
    strategies_per_hour: float = 0.0

    @property
    def totalJobsDone(self) -> int:  # noqa: N802
        """Donor compatibility getter for total jobs completed."""
        return self.total_jobs_done

    @totalJobsDone.setter
    def totalJobsDone(self, val: int) -> None:  # noqa: N802
        """Donor compatibility setter for total jobs completed."""
        self.total_jobs_done = val

    @property
    def acceptedStrategiesPerHour(self) -> float:  # noqa: N802
        """Donor compatibility getter for accepted strategies rate."""
        return self.accepted_strategies_per_hour

    @acceptedStrategiesPerHour.setter
    def acceptedStrategiesPerHour(self, val: float) -> None:  # noqa: N802
        """Donor compatibility setter for accepted strategies rate."""
        self.accepted_strategies_per_hour = val

    @property
    def strategiesPerHour(self) -> float:  # noqa: N802
        """Donor compatibility getter for generated strategies rate."""
        return self.strategies_per_hour

    @strategiesPerHour.setter
    def strategiesPerHour(self, val: float) -> None:  # noqa: N802
        """Donor compatibility setter for generated strategies rate."""
        self.strategies_per_hour = val


@dataclass
class FitnessCollectionData:
    """Collection of best, top-average, and average fitness scores per sample."""

    best_fitness_is: float = 0.0
    top_avg_fitness_is: float = 0.0
    avg_fitness_is: float = 0.0

    best_fitness_ist: float = 0.0
    top_avg_fitness_ist: float = 0.0
    avg_fitness_ist: float = 0.0

    best_fitness_isv: float = 0.0
    top_avg_fitness_isv: float = 0.0
    avg_fitness_isv: float = 0.0

    best_fitness_oos: float = 0.0
    top_avg_fitness_oos: float = 0.0
    avg_fitness_oos: float = 0.0

    @property
    def bestFitnessIS(self) -> float:  # noqa: N802
        """Donor compatibility getter for best fitness in-sample."""
        return self.best_fitness_is

    @property
    def topAvgFitnessIS(self) -> float:  # noqa: N802
        """Donor compatibility getter for top-average fitness in-sample."""
        return self.top_avg_fitness_is

    @property
    def avgFitnessIS(self) -> float:  # noqa: N802
        """Donor compatibility getter for average fitness in-sample."""
        return self.avg_fitness_is

    @property
    def bestFitnessIST(self) -> float:  # noqa: N802
        """Donor compatibility getter for best fitness IS training."""
        return self.best_fitness_ist

    @property
    def topAvgFitnessIST(self) -> float:  # noqa: N802
        """Donor compatibility getter for top-average fitness IS training."""
        return self.top_avg_fitness_ist

    @property
    def avgFitnessIST(self) -> float:  # noqa: N802
        """Donor compatibility getter for average fitness IS training."""
        return self.avg_fitness_ist

    @property
    def bestFitnessISV(self) -> float:  # noqa: N802
        """Donor compatibility getter for best fitness IS validation."""
        return self.best_fitness_isv

    @property
    def topAvgFitnessISV(self) -> float:  # noqa: N802
        """Donor compatibility getter for top-average fitness IS validation."""
        return self.top_avg_fitness_isv

    @property
    def avgFitnessISV(self) -> float:  # noqa: N802
        """Donor compatibility getter for average fitness IS validation."""
        return self.avg_fitness_isv

    @property
    def bestFitnessOOS(self) -> float:  # noqa: N802
        """Donor compatibility getter for best fitness out-of-sample."""
        return self.best_fitness_oos

    @property
    def topAvgFitnessOOS(self) -> float:  # noqa: N802
        """Donor compatibility getter for top-average fitness out-of-sample."""
        return self.top_avg_fitness_oos

    @property
    def avgFitnessOOS(self) -> float:  # noqa: N802
        """Donor compatibility getter for average fitness out-of-sample."""
        return self.avg_fitness_oos


@dataclass
class GPFitnessEvolutionData:
    """Evolution telemetry data for a single genetic programming island."""

    generation: int = 0
    population_size: int = 0
    generation_data: list[FitnessCollectionData | None] = field(default_factory=list)

    @property
    def populationSize(self) -> int:  # noqa: N802
        """Donor compatibility getter for island population size."""
        return self.population_size

    @property
    def generationData(self) -> list[FitnessCollectionData | None]:  # noqa: N802
        """Donor compatibility getter for generations data list."""
        return self.generation_data


@dataclass
class GeneticInfo:
    """Container for genetic evolution status and island progress."""

    is_genetic: bool = False
    islands_evo_data: list[GPFitnessEvolutionData] = field(default_factory=list)

    def is_genetic_build(self) -> bool:
        """Check if genetic build is running."""
        return self.is_genetic

    def isGeneticBuild(self) -> bool:  # noqa: N802
        """Donor compatibility alias for is_genetic_build."""
        return self.is_genetic_build()

    def get_islands_evo_data(self) -> list[GPFitnessEvolutionData]:
        """Get list of island evolution data structures."""
        return self.islands_evo_data

    def getIslandsEvoData(self) -> list[GPFitnessEvolutionData]:  # noqa: N802
        """Donor compatibility alias for get_islands_evo_data."""
        return self.get_islands_evo_data()


@dataclass
class MemoryInfo:
    """Off-heap / native memory accounting snapshot."""

    allocated_objects: int = 0
    allocated_memory: int = 0
    total_allocated_objects: int = 0
    total_allocated_memory: int = 0
    reallocations: int = 0

    @property
    def allocatedObjects(self) -> int:  # noqa: N802
        """Donor compatibility getter for allocated objects count."""
        return self.allocated_objects

    @property
    def allocatedMemory(self) -> int:  # noqa: N802
        """Donor compatibility getter for allocated memory bytes."""
        return self.allocated_memory

    @property
    def totalAllocatedObjects(self) -> int:  # noqa: N802
        """Donor compatibility getter for total allocated objects."""
        return self.total_allocated_objects

    @property
    def totalAllocatedMemory(self) -> int:  # noqa: N802
        """Donor compatibility getter for total allocated memory."""
        return self.total_allocated_memory


@dataclass
class HeapMemoryUsage:
    """Heap memory usage metrics in bytes."""

    used: int = 0
    committed: int = 0
    max_bytes: int = 0

    def get_used(self) -> int:
        """Get used bytes."""
        return self.used

    def getUsed(self) -> int:  # noqa: N802
        """Donor compatibility getter for used bytes."""
        return self.used

    def get_committed(self) -> int:
        """Get committed bytes."""
        return self.committed

    def getCommitted(self) -> int:  # noqa: N802
        """Donor compatibility getter for committed bytes."""
        return self.committed

    def get_max(self) -> int:
        """Get maximum bytes."""
        return self.max_bytes

    def getMax(self) -> int:  # noqa: N802
        """Donor compatibility getter for maximum bytes."""
        return self.max_bytes


class MemoryBean:
    """Bean providing heap memory telemetry metrics."""

    def __init__(self, heap_usage: HeapMemoryUsage | None = None) -> None:
        self.heap_usage = heap_usage or HeapMemoryUsage()

    def get_heap_memory_usage(self) -> HeapMemoryUsage:
        """Get heap memory usage."""
        return self.heap_usage

    def getHeapMemoryUsage(self) -> HeapMemoryUsage:  # noqa: N802
        """Donor compatibility getter for heap memory usage."""
        return self.get_heap_memory_usage()


class Databank:
    """Databank container holding generated strategies and fitness aggregates."""

    def __init__(self, fitness_data: FitnessCollectionData | None = None) -> None:
        self._fitness_data = fitness_data or FitnessCollectionData()

    def get_fitness_data(self) -> FitnessCollectionData:
        """Return fitness metrics aggregate across databank strategies."""
        return self._fitness_data

    def getFitnessData(self) -> FitnessCollectionData:  # noqa: N802
        """Donor compatibility getter for fitness collection data."""
        return self.get_fitness_data()


class Project:
    """Runtime project context orchestrating builder engines and tracking info."""

    def __init__(
        self,
        is_running: bool = True,
        databank: Databank | None = None,
        genetic_info: GeneticInfo | None = None,
        run_info: ProjectRunInfo | None = None,
    ) -> None:
        self._is_running = is_running
        self._databank = databank or Databank()
        self._genetic_info = genetic_info or GeneticInfo()
        self._run_info = run_info or ProjectRunInfo()

    def is_running(self) -> bool:
        """Return whether project builder execution is currently active."""
        return self._is_running

    def isRunning(self) -> bool:  # noqa: N802
        """Donor compatibility getter for project execution state."""
        return self.is_running()

    def load_tracking_info(self, target: ProjectRunInfo, force: bool = False) -> None:
        """Load latest tracking metrics into target ProjectRunInfo."""
        del force
        target.total_jobs_done = self._run_info.total_jobs_done
        target.accepted_strategies_per_hour = (
            self._run_info.accepted_strategies_per_hour
        )
        target.strategies_per_hour = self._run_info.strategies_per_hour

    def loadTrackingInfo(  # noqa: N802
        self, target: ProjectRunInfo, force: bool = False
    ) -> None:
        """Donor compatibility alias for load_tracking_info."""
        self.load_tracking_info(target, force)

    def get_results_databank(self) -> Databank | None:
        """Get results databank."""
        return self._databank

    def getResultsDatabank(self) -> Databank | None:  # noqa: N802
        """Donor compatibility getter for results databank."""
        return self.get_results_databank()

    def get_genetic_info(self) -> GeneticInfo:
        """Get genetic evolution tracking info."""
        return self._genetic_info

    def getGeneticInfo(self) -> GeneticInfo:  # noqa: N802
        """Donor compatibility getter for genetic evolution info."""
        return self.get_genetic_info()


@dataclass(frozen=True, slots=True)
class TimeSeriesDataPoint:
    """Individual data point on a time series line."""

    timestamp_ms: int
    value: float

    def to_dict(self) -> dict[str, Any]:
        """Convert point to dictionary representation."""
        return {"timestamp_ms": self.timestamp_ms, "value": self.value}


class TimeSeries:
    """Named sequence of time-series data points with capacity constraint."""

    def __init__(
        self,
        name: str,
        points_count: int = DEFAULT_POINTS_COUNT,
        color: str | None = None,
    ) -> None:
        self.name: str = name
        self.points_count: int = points_count
        self.color: str | None = color
        self.points: list[TimeSeriesDataPoint] = []

    def add_value(self, timestamp_ms: int, value: float) -> None:
        """Add new timestamped value and trim old points beyond capacity."""
        self.points.append(TimeSeriesDataPoint(timestamp_ms=timestamp_ms, value=value))
        if len(self.points) > self.points_count:
            self.points = self.points[-self.points_count :]

    def addValue(self, timestamp_ms: int, value: float) -> None:  # noqa: N802
        """Donor compatibility alias."""
        self.add_value(timestamp_ms, value)

    def clear(self) -> None:
        """Clear all recorded data points."""
        self.points.clear()

    def to_json(self) -> dict[str, Any]:
        """Serialize series for UI chart rendering."""
        return {
            "name": self.name,
            "color": self.color,
            "points": [p.to_dict() for p in self.points],
        }

    def toJSON(self) -> dict[str, Any]:  # noqa: N802
        """Donor compatibility alias."""
        return self.to_json()


class TimeSeriesChart:
    """Base chart container managing axes, ticks, and series collections."""

    PointsCount: int = DEFAULT_POINTS_COUNT

    def __init__(self, chart_type: str = "line") -> None:
        self.chart_type: str = chart_type
        self.x_axis_title: str = ""
        self.y_axis_title: str = ""
        self.y_axis_range_min: float | None = None
        self.y_axis_range_max: float | None = None
        self.max_x_ticks_limit: int = 4
        self.max_y_ticks_limit: int = 6
        self.show_legend: bool = False
        self.y_axis_ticks_memory: bool = False
        self.series: list[TimeSeries] = []

    # Donor compatibility property aliases
    @property
    def xAxisTitle(self) -> str:  # noqa: N802
        """Donor compatibility getter for X axis title."""
        return self.x_axis_title

    @xAxisTitle.setter
    def xAxisTitle(self, val: str) -> None:  # noqa: N802
        """Donor compatibility setter for X axis title."""
        self.x_axis_title = val

    @property
    def yAxisTitle(self) -> str:  # noqa: N802
        """Donor compatibility getter for Y axis title."""
        return self.y_axis_title

    @yAxisTitle.setter
    def yAxisTitle(self, val: str) -> None:  # noqa: N802
        """Donor compatibility setter for Y axis title."""
        self.y_axis_title = val

    @property
    def yAxisRangeMin(self) -> float | None:  # noqa: N802
        """Donor compatibility getter for Y axis minimum range."""
        return self.y_axis_range_min

    @yAxisRangeMin.setter
    def yAxisRangeMin(self, val: float | None) -> None:  # noqa: N802
        """Donor compatibility setter for Y axis minimum range."""
        self.y_axis_range_min = val

    @property
    def yAxisRangeMax(self) -> float | None:  # noqa: N802
        """Donor compatibility getter for Y axis maximum range."""
        return self.y_axis_range_max

    @yAxisRangeMax.setter
    def yAxisRangeMax(self, val: float | None) -> None:  # noqa: N802
        """Donor compatibility setter for Y axis maximum range."""
        self.y_axis_range_max = val

    @property
    def maxXTicksLimit(self) -> int:  # noqa: N802
        """Donor compatibility getter for max X ticks limit."""
        return self.max_x_ticks_limit

    @maxXTicksLimit.setter
    def maxXTicksLimit(self, val: int) -> None:  # noqa: N802
        """Donor compatibility setter for max X ticks limit."""
        self.max_x_ticks_limit = val

    @property
    def maxYTicksLimit(self) -> int:  # noqa: N802
        """Donor compatibility getter for max Y ticks limit."""
        return self.max_y_ticks_limit

    @maxYTicksLimit.setter
    def maxYTicksLimit(self, val: int) -> None:  # noqa: N802
        """Donor compatibility setter for max Y ticks limit."""
        self.max_y_ticks_limit = val

    @property
    def showLegend(self) -> bool:  # noqa: N802
        """Donor compatibility getter for show legend flag."""
        return self.show_legend

    @showLegend.setter
    def showLegend(self, val: bool) -> None:  # noqa: N802
        """Donor compatibility setter for show legend flag."""
        self.show_legend = val

    @property
    def yAxisTicksMemory(self) -> bool:  # noqa: N802
        """Donor compatibility getter for memory ticks mode."""
        return self.y_axis_ticks_memory

    @yAxisTicksMemory.setter
    def yAxisTicksMemory(self, val: bool) -> None:  # noqa: N802
        """Donor compatibility setter for memory ticks mode."""
        self.y_axis_ticks_memory = val

    def add_series(self, series: TimeSeries) -> None:
        """Add time series to chart collection."""
        self.series.append(series)

    def addSeries(self, series: TimeSeries) -> None:  # noqa: N802
        """Donor compatibility alias for add_series."""
        self.add_series(series)

    def to_json(self) -> dict[str, Any]:
        """Serialize chart configuration and series payload."""
        return {
            "chartType": self.chart_type,
            "xAxisTitle": self.x_axis_title,
            "yAxisTitle": self.y_axis_title,
            "yAxisRangeMin": self.y_axis_range_min,
            "yAxisRangeMax": self.y_axis_range_max,
            "maxXTicksLimit": self.max_x_ticks_limit,
            "maxYTicksLimit": self.max_y_ticks_limit,
            "showLegend": self.show_legend,
            "yAxisTicksMemory": self.y_axis_ticks_memory,
            "series": [s.to_json() for s in self.series],
        }

    def toJSON(self) -> dict[str, Any]:  # noqa: N802
        """Donor compatibility alias for to_json."""
        return self.to_json()


class TimeSeriesLineChart(TimeSeriesChart):
    """Line chart representation for engine metric series."""

    def __init__(self) -> None:
        super().__init__(chart_type="line")


class TimeSeriesAreaChart(TimeSeriesChart):
    """Area chart representation for memory and engine capacity metrics."""

    def __init__(self) -> None:
        super().__init__(chart_type="area")


class EngineChart(ABC):
    """Abstract base class for all engine charts matching SQX EngineChart."""

    def __init__(
        self,
        name: str = "EngineChart",
        chart_type: int = TYPE_PROJECT_BASED,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
        max_heap_memory: int = 1024 * 1024 * 1024,
    ) -> None:
        self.name: str = name
        self.chart_type: int = chart_type
        self.project: Project = project or Project()
        self.memory_bean: MemoryBean = memory_bean or MemoryBean()
        self.max_heap_memory: int = max_heap_memory
        logger.info(
            "FR-engine-charts-core: initialized EngineChart '%s' (type=%d)",
            self.name,
            self.chart_type,
        )

    # Donor compatibility property aliases
    @property
    def maxHeapMemory(self) -> int:  # noqa: N802
        """Donor compatibility getter for max heap memory bytes."""
        return self.max_heap_memory

    @property
    def memoryBean(self) -> MemoryBean:  # noqa: N802
        """Donor compatibility getter for memory bean instance."""
        return self.memory_bean

    @abstractmethod
    def print(self) -> dict[str, Any] | None:
        """Render chart data dictionary for UI consumption or None if unchanged."""

    @abstractmethod
    def add_next_value(self) -> None:
        """Sample current state from project/runtime and append to series."""

    def addNextValue(self) -> None:  # noqa: N802
        """Donor compatibility alias for add_next_value."""
        self.add_next_value()

    def current_time_millis(self) -> int:
        """Return current epoch timestamp in milliseconds."""
        return int(time.time() * 1000)
