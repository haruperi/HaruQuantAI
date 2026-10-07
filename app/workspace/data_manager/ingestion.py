"""Data ingestion re-exports for the Data Manager workspace.

Description:
    Exposes `BarRecord`, `DataIngestionService`, `IngestionConfig`, `IngestionResult`
    from `data`.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Data ingestion pipeline re-exports.

Key Capabilities:
    FR-DATA-INGESTION-STREAMING: Stream and chunk file parsing with delimiter sniffing.

Python API Usage:
    ```python
    from app.workspace.data_manager.ingestion import (
        BarRecord,
        DataIngestionService,
        IngestionConfig,
    )
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.data --help
    ```
"""

from __future__ import annotations

from app.workspace.data_manager.data import (
    BarRecord,
    DataIngestionService,
    IngestionConfig,
    IngestionResult,
)

__all__ = [
    "BarRecord",
    "DataIngestionService",
    "IngestionConfig",
    "IngestionResult",
]
