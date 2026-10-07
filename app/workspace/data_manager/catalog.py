"""Dataset catalog re-exports for the Data Manager workspace.

Description:
    Exposes `CatalogService` and `DatasetRecord` from `data`.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Dataset catalog re-exports.

Key Capabilities:
    FR-DATA-CATALOG-DATASET-REGISTRY: Authoritative dataset metadata tracking.

Python API Usage:
    ```python
    from app.workspace.data_manager.catalog import CatalogService, DatasetRecord
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.data --list
    ```
"""

from __future__ import annotations

from app.workspace.data_manager.data import CatalogService, DatasetRecord

__all__ = ["CatalogService", "DatasetRecord"]
