"""Genetic Evolution Info engine chart implementation.

Description:
    Implements GeneticEvolutionInfo which renders a row-based status summary
    table displaying generation count and population size for up to seven
    genetic evolution islands.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-genetic-evolution-info: Report genetic evolution islands status.

Python API Usage:
    from app.extend.engine_charts.genetic_evolution_info import GeneticEvolutionInfo
    chart = GeneticEvolutionInfo()
    payload = chart.print()

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.engine_charts.base import (
    DATA_TYPE_ROWS,
    TYPE_PROJECT_BASED,
    EngineChart,
    GeneticInfo,
    MemoryBean,
    Project,
)

logger = get_logger(__name__)


class GeneticEvolutionInfo(EngineChart):
    """Engine chart presenting a tabular summary of active genetic islands."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
    ) -> None:
        super().__init__(
            name="Genetic Evolution info",
            chart_type=TYPE_PROJECT_BASED,
            project=project,
            memory_bean=memory_bean,
        )
        logger.info(
            "FR-engine-charts-genetic-evolution-info: initialized GeneticEvolutionInfo"
        )

    @override
    def print(self) -> dict[str, Any] | None:
        """Render rows payload containing island status or no data indicator."""
        genetic_info: GeneticInfo = self.project.get_genetic_info()
        items: list[dict[str, str]] = []

        if not genetic_info.is_genetic_build():
            items.append({"name": "No data", "value": "No genetic evolution running"})
        else:
            islands = genetic_info.get_islands_evo_data()
            limit = min(7, len(islands))
            for i in range(limit):
                island = islands[i]
                items.append(
                    {
                        "name": f"Island #{i + 1}",
                        "value": (
                            f"Generation: {island.generation}, "
                            f"Population: {island.population_size}"
                        ),
                    }
                )

        logger.info(
            "FR-engine-charts-genetic-evolution-info: rendered %d items",
            len(items),
        )
        return {
            "type": DATA_TYPE_ROWS,
            "items": items,
        }

    @override
    def add_next_value(self) -> None:
        """No-op matching donor implementation."""
