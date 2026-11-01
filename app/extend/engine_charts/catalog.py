"""Engine charts definitions and telemetry series projection catalog (14 charts).

Description:
    Implements EngineChartsCatalog and registers all 14 donor engine charts
    covering engine throughput, databank fitness progression (IS/IST/ISV/OOS),
    genetic evolution fitness, and runtime memory consumption telemetry.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-project: Project runtime telemetry onto engine chart series.

Python API Usage:
    from app.extend.engine_charts.catalog import EngineChartsCatalog
    points = EngineChartsCatalog.project("AcceptedStrategiesPerHour", telemetry)

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

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


# Register all 14 donor EngineCharts
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


class EngineChartsCatalog:
    """Catalog of runtime telemetry engine charts and series projector."""

    @classmethod
    def list_descriptors(cls) -> tuple[EngineChartDescriptor, ...]:
        """List all 14 registered EngineChart descriptors."""
        return tuple(ENGINE_CHARTS.values())

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
