"""Grid Test workspace service and plugin registration.

Description:
    Implements the GridTest application plugin service, delivering plugin
    registration metadata, deterministic row generation parity, and timer
    interval specifications for UI grid testing.

Purpose:
    FEAT-GRID-TEST: Provide backend plugin descriptor and deterministic
    test row generation parity for the Grid Test workspace.

Key Capabilities:
    FR-GRID-TEST-PLUGIN-REGISTRATION: Export GridTest application metadata.
    FR-GRID-TEST-INTERVALS: Provide donor timer interval configuration.
    FR-GRID-TEST-ROW-PARITY: Python generator parity for test rows.

Python API Usage:
    from app.workspace.grid_test.app_grid_test import GridTestService

    service = GridTestService()
    descriptor = service.get_plugin_descriptor()
    batch = service.generate_manual_batch()

CLI Usage:
    uv run python -c "from app.workspace.grid_test import GridTestService"
"""

import logging
from typing import Final

from app.workspace.grid_test.app_grid_test_models import (
    GridTestBatchResponse,
    GridTestIntervalsModel,
    GridTestPluginDescriptor,
    GridTestRowModel,
)

logger: Final[logging.Logger] = logging.getLogger(__name__)


class GridTestService:
    """Service providing GridTest plugin registration and row generation."""

    def __init__(self) -> None:
        """Initialize GridTestService with descriptor and interval settings."""
        self._descriptor = GridTestPluginDescriptor()
        self._intervals = GridTestIntervalsModel()
        logger.info(
            "Initialized GridTestService app_code=%s "
            "[FR-GRID-TEST-PLUGIN-REGISTRATION]",
            self._descriptor.app_code,
        )

    def get_plugin_descriptor(self) -> GridTestPluginDescriptor:
        """Retrieve the plugin registration metadata descriptor.

        Returns:
            GridTestPluginDescriptor with name, app_code, and context path.
        """
        logger.info(
            "Retrieved plugin descriptor for %s [FR-GRID-TEST-PLUGIN-REGISTRATION]",
            self._descriptor.app_code,
        )
        return self._descriptor

    def get_intervals(self) -> GridTestIntervalsModel:
        """Retrieve timer intervals for add, remove, change, and count operations.

        Returns:
            GridTestIntervalsModel containing period values in milliseconds.
        """
        logger.info(
            "Retrieved grid test timer intervals: add=%dms, remove=%dms, "
            "change=%dms, count=%dms [FR-GRID-TEST-INTERVALS]",
            self._intervals.add,
            self._intervals.remove,
            self._intervals.change,
            self._intervals.count,
        )
        return self._intervals

    def generate_manual_batch(self) -> GridTestBatchResponse:
        """Generate a deterministic batch of 100 test rows (indices 0..99).

        Returns:
            GridTestBatchResponse containing 100 GridTestRowModel objects.
        """
        rows: list[GridTestRowModel] = [
            GridTestRowModel(index=i, value=i * 2, text=f"{i}-text") for i in range(100)
        ]
        logger.info(
            "Generated manual batch of %d grid test rows [FR-GRID-TEST-ROW-PARITY]",
            len(rows),
        )
        return GridTestBatchResponse(rows=rows, total_count=len(rows))

    def generate_timed_row(self, counter: int) -> GridTestRowModel:
        """Generate a single deterministic timed row for the specified counter.

        Args:
            counter: The sequential counter value.

        Returns:
            GridTestRowModel for the given counter.
        """
        row = GridTestRowModel(index=counter, value=counter * 2, text=f"{counter}-text")
        logger.info(
            "Generated timed row index=%d value=%d [FR-GRID-TEST-ROW-PARITY]",
            row.index,
            row.value,
        )
        return row
