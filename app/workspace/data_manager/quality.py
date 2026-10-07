"""Data quality inspection re-exports for the Data Manager workspace.

Description:
    Exposes `DataQualityInspector` and `DataQualityReport` from
    `actions.review.quality`.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Data quality inspection re-exports.

Key Capabilities:
    FR-DATA-QUALITY-METRICS: Quality inspection and scoring.

Python API Usage:
    ```python
    from app.workspace.data_manager.quality import DataQualityInspector
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.actions.review.quality --help
    ```
"""

from __future__ import annotations

from app.workspace.data_manager.actions.review.quality import (
    DataQualityInspector,
    DataQualityReport,
)

__all__ = ["DataQualityInspector", "DataQualityReport"]
