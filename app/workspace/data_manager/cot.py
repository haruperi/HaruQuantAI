"""Commitments of Traders (COT) report re-exports for the Data Manager workspace.

Description:
    Exposes `CotService`, `CotSymbolMapping`, `CotObservation` from `custom_data`
    for modular access within the Data Manager workspace.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Commitments of Traders (COT) modular re-exports.

Key Capabilities:
    FR-DATA-COT-MAPPING: COT service and models.

Python API Usage:
    ```python
    from app.workspace.data_manager.cot import CotService
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.custom_data --list
    ```
"""

from __future__ import annotations

from app.workspace.data_manager.custom_data import (
    DEFAULT_COT_CATALOG,
    CotObservation,
    CotService,
    CotSymbolMapping,
)

__all__ = [
    "DEFAULT_COT_CATALOG",
    "CotObservation",
    "CotService",
    "CotSymbolMapping",
]
