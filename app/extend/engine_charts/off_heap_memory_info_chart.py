"""Off-Heap Memory Info engine chart implementation.

Description:
    Implements OffHeapMemoryInfoChart which outputs a key-value grid with
    native allocated objects count and formatted allocated memory bytes.

Purpose:
    FEAT-EXTEND-ENGINE-CHARTS: Builder runtime telemetry engine charts.

Key Capabilities:
    - FR-engine-charts-off-heap-info: Report off-heap object counts and memory size.

Python API Usage:
    from app.extend.engine_charts.off_heap_memory_info_chart import (
        OffHeapMemoryInfoChart,
    )
    chart = OffHeapMemoryInfoChart()
    payload = chart.print()

CLI Usage:
    python -m app.cli extend engine-charts --list
"""

from __future__ import annotations

from typing import Any, override

from app.core.host.logging import get_logger
from app.extend.engine_charts.base import (
    DATA_TYPE_GRID,
    TYPE_GLOBAL,
    EngineChart,
    MemoryBean,
    MemoryInfo,
    Project,
    format_bytes_to_human_format,
)

logger = get_logger(__name__)


class OffHeapMemoryInfoChart(EngineChart):
    """Engine chart presenting a grid summary of off-heap memory allocations."""

    def __init__(
        self,
        project: Project | None = None,
        memory_bean: MemoryBean | None = None,
        off_heap_info: MemoryInfo | None = None,
    ) -> None:
        super().__init__(
            name="Off-heap memory info",
            chart_type=TYPE_GLOBAL,
            project=project,
            memory_bean=memory_bean,
        )
        self.off_heap_info: MemoryInfo = off_heap_info or MemoryInfo()
        logger.info(
            "FR-engine-charts-off-heap-info: initialized OffHeapMemoryInfoChart"
        )

    @override
    def print(self) -> dict[str, Any] | None:
        """Render grid data dictionary containing allocated objects and memory."""
        items: list[dict[str, Any]] = [
            {
                "name": "Allocated objects",
                "value": self.off_heap_info.allocated_objects,
            },
            {
                "name": "Allocated memory",
                "value": format_bytes_to_human_format(
                    self.off_heap_info.allocated_memory
                ),
            },
        ]
        logger.info(
            "FR-engine-charts-off-heap-info: objects=%d, memory=%s",
            self.off_heap_info.allocated_objects,
            format_bytes_to_human_format(self.off_heap_info.allocated_memory),
        )
        return {
            "type": DATA_TYPE_GRID,
            "items": items,
        }

    @override
    def add_next_value(self) -> None:
        """No-op matching donor implementation."""
