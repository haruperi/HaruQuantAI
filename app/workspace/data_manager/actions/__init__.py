"""Actions package for Data Manager workspace operations.

Description:
    Provides sub-action implementations mirroring SQX DataManagerActions:
    review/quality inspection and transform/export operations.

Purpose:
    FEAT-WORKSPACE-DATAMGR: Workspace actions, data review, and transforms.

Key Capabilities:
    FR-WORKSPACE-DATAMGR-ACTIONS: Data Manager action modules and dispatch.

Python API Usage:
    ```python
    from app.workspace.data_manager.actions.review.quality import (
        DataQualityInspector,
    )
    from app.workspace.data_manager.actions.transform.transforms import (
        SeriesTransformer,
    )
    ```

CLI Usage:
    ```bash
    python -m app.workspace.data_manager.actions.review.quality --help
    ```
"""

from __future__ import annotations
