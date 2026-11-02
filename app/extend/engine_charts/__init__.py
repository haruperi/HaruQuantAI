"""EngineCharts extension cohort package.

Description:
    Exposes all 14 builder runtime telemetry engine charts matching SQX donor
    snippets, along with chart base classes, telemetry models, and catalog.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-catalog: Expose all 14 engine chart classes and models.

Python API Usage:
    from app.extend.engine_charts import (
        AcceptedStrategiesPerHour,
        AverageStrategiesPerHourChart,
        DatabankFitnessIS,
        DatabankFitnessIST,
        DatabankFitnessISV,
        DatabankFitnessOOS,
        GenEvoFitnessIS,
        GenEvoFitnessIST,
        GenEvoFitnessISV,
        GenEvoFitnessOOS,
        GeneticEvolutionInfo,
        HeapMemoryChart,
        OffHeapMemoryChart,
        OffHeapMemoryInfoChart,
        EngineChartsCatalog,
    )

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from app.extend.engine_charts.accepted_strategies_per_hour import (
    AcceptedStrategiesPerHour,
)
from app.extend.engine_charts.average_strategies_per_hour_chart import (
    AverageStrategiesPerHourChart,
)
from app.extend.engine_charts.base import (
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_RED,
    DATA_TYPE_CHART,
    DATA_TYPE_GRID,
    DATA_TYPE_ROWS,
    DEFAULT_POINTS_COUNT,
    MEGABYTE,
    TYPE_GLOBAL,
    TYPE_PROJECT_BASED,
    Databank,
    EngineChart,
    FitnessCollectionData,
    GeneticInfo,
    GPFitnessEvolutionData,
    HeapMemoryUsage,
    MemoryBean,
    MemoryInfo,
    Project,
    ProjectRunInfo,
    TimeSeries,
    TimeSeriesAreaChart,
    TimeSeriesChart,
    TimeSeriesDataPoint,
    TimeSeriesLineChart,
    format_bytes_to_human_format,
)
from app.extend.engine_charts.catalog import (
    CHART_CLASSES,
    ENGINE_CHARTS,
    ChartCategory,
    EngineChartDescriptor,
    EngineChartsCatalog,
    EngineChartSeriesPoint,
    JobRuntimeTelemetrySnapshot,
)
from app.extend.engine_charts.databank_fitness_is import DatabankFitnessIS
from app.extend.engine_charts.databank_fitness_ist import DatabankFitnessIST
from app.extend.engine_charts.databank_fitness_isv import DatabankFitnessISV
from app.extend.engine_charts.databank_fitness_oos import DatabankFitnessOOS
from app.extend.engine_charts.gen_evo_fitness_is import GenEvoFitnessIS
from app.extend.engine_charts.gen_evo_fitness_ist import GenEvoFitnessIST
from app.extend.engine_charts.gen_evo_fitness_isv import GenEvoFitnessISV
from app.extend.engine_charts.gen_evo_fitness_oos import GenEvoFitnessOOS
from app.extend.engine_charts.genetic_evolution_info import GeneticEvolutionInfo
from app.extend.engine_charts.heap_memory_chart import HeapMemoryChart
from app.extend.engine_charts.off_heap_memory_chart import OffHeapMemoryChart
from app.extend.engine_charts.off_heap_memory_info_chart import (
    OffHeapMemoryInfoChart,
)

__all__ = [
    "CHART_CLASSES",
    "COLOR_BLUE",
    "COLOR_GREEN",
    "COLOR_RED",
    "DATA_TYPE_CHART",
    "DATA_TYPE_GRID",
    "DATA_TYPE_ROWS",
    "DEFAULT_POINTS_COUNT",
    "ENGINE_CHARTS",
    "MEGABYTE",
    "TYPE_GLOBAL",
    "TYPE_PROJECT_BASED",
    "AcceptedStrategiesPerHour",
    "AverageStrategiesPerHourChart",
    "ChartCategory",
    "Databank",
    "DatabankFitnessIS",
    "DatabankFitnessIST",
    "DatabankFitnessISV",
    "DatabankFitnessOOS",
    "EngineChart",
    "EngineChartDescriptor",
    "EngineChartSeriesPoint",
    "EngineChartsCatalog",
    "FitnessCollectionData",
    "GPFitnessEvolutionData",
    "GenEvoFitnessIS",
    "GenEvoFitnessIST",
    "GenEvoFitnessISV",
    "GenEvoFitnessOOS",
    "GeneticEvolutionInfo",
    "GeneticInfo",
    "HeapMemoryChart",
    "HeapMemoryUsage",
    "JobRuntimeTelemetrySnapshot",
    "MemoryBean",
    "MemoryInfo",
    "OffHeapMemoryChart",
    "OffHeapMemoryInfoChart",
    "Project",
    "ProjectRunInfo",
    "TimeSeries",
    "TimeSeriesAreaChart",
    "TimeSeriesChart",
    "TimeSeriesDataPoint",
    "TimeSeriesLineChart",
    "format_bytes_to_human_format",
]
