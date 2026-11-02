"""Engine charts definitions and telemetry series projection catalog (14 charts).

Description:
    Implements EngineChartsCatalog and registers all 14 donor engine charts
    covering engine throughput, databank fitness progression (IS/IST/ISV/OOS),
    genetic evolution fitness, and runtime memory consumption telemetry.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-catalog: Catalog and registry for all 14 engine charts.
    - FR-engine-charts-project: Project runtime telemetry onto engine chart series.

Python API Usage:
    from app.extend.engine_charts.catalog import EngineChartsCatalog
    chart = EngineChartsCatalog.create_chart("AcceptedStrategiesPerHour")
    points = EngineChartsCatalog.project("AcceptedStrategiesPerHour", telemetry)

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.extend.engine_charts.accepted_strategies_per_hour import (
    AcceptedStrategiesPerHour,
)
from app.extend.engine_charts.average_strategies_per_hour_chart import (
    AverageStrategiesPerHourChart,
)
from app.extend.engine_charts.base import EngineChart, MemoryBean, Project
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

logger = get_logger(__name__)

ChartCategory = Literal[
    "THROUGHPUT",
    "DATABANK_FITNESS",
    "GENETIC_FITNESS",
    "MEMORY",
]


@dataclass(frozen=True, slots=True)
class EngineChartSeriesPoint:
    """Individual data point along an engine chart progression curve."""

    step: int
    timestamp_ms: int
    value: float
    secondary_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert point to dictionary representation."""
        return {
            "step": self.step,
            "timestamp_ms": self.timestamp_ms,
            "value": self.value,
            "secondary_value": self.secondary_value,
        }


@dataclass(frozen=True, slots=True)
class EngineChartDescriptor:
    """Descriptor defining identity and telemetry key for an engine chart."""

    chart_id: str
    label: str
    category: ChartCategory
    sample_key: str | None
    unit: str
    source_ref: str

    def to_dict(self) -> dict[str, Any]:
        """Convert descriptor to dictionary representation."""
        return {
            "chart_id": self.chart_id,
            "label": self.label,
            "category": self.category,
            "sample_key": self.sample_key,
            "unit": self.unit,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True, slots=True)
class JobRuntimeTelemetrySnapshot:
    """Builder job runtime telemetry snapshot containing metric series."""

    steps: tuple[int, ...] = ()
    timestamps_ms: tuple[int, ...] = ()
    metrics: dict[str, tuple[float, ...]] = field(default_factory=dict)


# Register all 14 donor EngineCharts metadata descriptors
ENGINE_CHARTS: dict[str, EngineChartDescriptor] = {
    # Throughput (2)
    "AcceptedStrategiesPerHour": EngineChartDescriptor(
        "AcceptedStrategiesPerHour",
        "Accepted Strategies / Hour",
        "THROUGHPUT",
        None,
        "strats/hr",
        "AcceptedStrategiesPerHour.java",
    ),
    "AverageStrategiesPerHourChart": EngineChartDescriptor(
        "AverageStrategiesPerHourChart",
        "Average Strategies / Hour",
        "THROUGHPUT",
        None,
        "strats/hr",
        "AverageStrategiesPerHourChart.java",
    ),
    # Databank Fitness (4)
    "DatabankFitnessIS": EngineChartDescriptor(
        "DatabankFitnessIS",
        "Databank Fitness (In-Sample)",
        "DATABANK_FITNESS",
        "IS",
        "score",
        "DatabankFitnessIS.java",
    ),
    "DatabankFitnessIST": EngineChartDescriptor(
        "DatabankFitnessIST",
        "Databank Fitness (IS Training)",
        "DATABANK_FITNESS",
        "IST",
        "score",
        "DatabankFitnessIST.java",
    ),
    "DatabankFitnessISV": EngineChartDescriptor(
        "DatabankFitnessISV",
        "Databank Fitness (IS Validation)",
        "DATABANK_FITNESS",
        "ISV",
        "score",
        "DatabankFitnessISV.java",
    ),
    "DatabankFitnessOOS": EngineChartDescriptor(
        "DatabankFitnessOOS",
        "Databank Fitness (Out-of-Sample)",
        "DATABANK_FITNESS",
        "OOS",
        "score",
        "DatabankFitnessOOS.java",
    ),
    # Genetic Fitness (5)
    "GenEvoFitnessIS": EngineChartDescriptor(
        "GenEvoFitnessIS",
        "Genetic Evolution Fitness (IS)",
        "GENETIC_FITNESS",
        "IS",
        "score",
        "GenEvoFitnessIS.java",
    ),
    "GenEvoFitnessIST": EngineChartDescriptor(
        "GenEvoFitnessIST",
        "Genetic Evolution Fitness (IST)",
        "GENETIC_FITNESS",
        "IST",
        "score",
        "GenEvoFitnessIST.java",
    ),
    "GenEvoFitnessISV": EngineChartDescriptor(
        "GenEvoFitnessISV",
        "Genetic Evolution Fitness (ISV)",
        "GENETIC_FITNESS",
        "ISV",
        "score",
        "GenEvoFitnessISV.java",
    ),
    "GenEvoFitnessOOS": EngineChartDescriptor(
        "GenEvoFitnessOOS",
        "Genetic Evolution Fitness (OOS)",
        "GENETIC_FITNESS",
        "OOS",
        "score",
        "GenEvoFitnessOOS.java",
    ),
    "GeneticEvolutionInfo": EngineChartDescriptor(
        "GeneticEvolutionInfo",
        "Genetic Evolution Population Summary",
        "GENETIC_FITNESS",
        None,
        "score",
        "GeneticEvolutionInfo.java",
    ),
    # Memory (3)
    "HeapMemoryChart": EngineChartDescriptor(
        "HeapMemoryChart",
        "Heap Memory Used",
        "MEMORY",
        None,
        "MB",
        "HeapMemoryChart.java",
    ),
    "OffHeapMemoryChart": EngineChartDescriptor(
        "OffHeapMemoryChart",
        "Off-Heap Memory Used",
        "MEMORY",
        None,
        "MB",
        "OffHeapMemoryChart.java",
    ),
    "OffHeapMemoryInfoChart": EngineChartDescriptor(
        "OffHeapMemoryInfoChart",
        "Off-Heap Memory Direct vs Non-Direct",
        "MEMORY",
        None,
        "MB",
        "OffHeapMemoryInfoChart.java",
    ),
}

# Mapping of chart ID to concrete implementation class
CHART_CLASSES: dict[str, type[EngineChart]] = {
    "AcceptedStrategiesPerHour": AcceptedStrategiesPerHour,
    "AverageStrategiesPerHourChart": AverageStrategiesPerHourChart,
    "DatabankFitnessIS": DatabankFitnessIS,
    "DatabankFitnessIST": DatabankFitnessIST,
    "DatabankFitnessISV": DatabankFitnessISV,
    "DatabankFitnessOOS": DatabankFitnessOOS,
    "GenEvoFitnessIS": GenEvoFitnessIS,
    "GenEvoFitnessIST": GenEvoFitnessIST,
    "GenEvoFitnessISV": GenEvoFitnessISV,
    "GenEvoFitnessOOS": GenEvoFitnessOOS,
    "GeneticEvolutionInfo": GeneticEvolutionInfo,
    "HeapMemoryChart": HeapMemoryChart,
    "OffHeapMemoryChart": OffHeapMemoryChart,
    "OffHeapMemoryInfoChart": OffHeapMemoryInfoChart,
}


class EngineChartsCatalog:
    """Catalog of runtime telemetry engine charts, series projector, and factory."""

    @classmethod
    def list_descriptors(cls) -> tuple[EngineChartDescriptor, ...]:
        """List all 14 registered EngineChart descriptors."""
        return tuple(ENGINE_CHARTS.values())

    @classmethod
    def list_classes(cls) -> dict[str, type[EngineChart]]:
        """List all registered chart classes."""
        return dict(CHART_CLASSES)

    @classmethod
    def get(cls, chart_id: str) -> EngineChartDescriptor:
        """Get EngineChart descriptor by ID."""
        if chart_id not in ENGINE_CHARTS:
            raise DomainError(
                code="ENGINE_CHART_NOT_FOUND",
                message=f"Engine chart '{chart_id}' not found",
                details={"chart_id": chart_id},
            )
        return ENGINE_CHARTS[chart_id]

    @classmethod
    def get_class(cls, chart_id: str) -> type[EngineChart]:
        """Get EngineChart class by ID."""
        if chart_id not in CHART_CLASSES:
            raise DomainError(
                code="ENGINE_CHART_NOT_FOUND",
                message=f"Engine chart class '{chart_id}' not found",
                details={"chart_id": chart_id},
            )
        return CHART_CLASSES[chart_id]

    @classmethod
    def create_chart(
        cls,
        chart_id: str,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
    ) -> EngineChart:
        """Instantiate EngineChart by ID."""
        chart_cls = cls.get_class(chart_id)
        logger.info(
            "FR-engine-charts-catalog: creating chart instance for '%s'", chart_id
        )
        return chart_cls(project=project, memory_bean=memory_bean)

    @classmethod
    def project(
        cls, chart_id: str, telemetry: JobRuntimeTelemetrySnapshot
    ) -> tuple[EngineChartSeriesPoint, ...]:
        """Project telemetry snapshot metric series to EngineChartSeriesPoint tuple."""
        desc = cls.get(chart_id)
        logger.info(
            "FR-engine-charts-project: projecting %s (%s)",
            chart_id,
            desc.category,
        )

        steps = telemetry.steps
        ts_list = telemetry.timestamps_ms
        series = telemetry.metrics.get(chart_id, ())
        secondary_series = telemetry.metrics.get(f"{chart_id}_secondary", ())

        points: list[EngineChartSeriesPoint] = []
        n = min(len(steps), len(series))

        for i in range(n):
            step = steps[i]
            ts = ts_list[i] if i < len(ts_list) else step
            val = series[i]
            sec_val = secondary_series[i] if i < len(secondary_series) else None

            points.append(
                EngineChartSeriesPoint(
                    step=step,
                    timestamp_ms=ts,
                    value=round(val, 2),
                    secondary_value=round(sec_val, 2) if sec_val is not None else None,
                )
            )

        return tuple(points)
