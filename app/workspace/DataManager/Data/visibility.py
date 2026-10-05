"""Set explicit visibility without UI checkbox inversion.

Description:
    Set explicit visibility without UI checkbox inversion.
    Accepts caller-supplied immutable data and returns an explicit result.
    No persistence, network calls, scheduling or import-time work is performed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-VISIBILITY: Set explicit visibility without UI checkbox inversion.
      Associated: `set_visibility()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.visibility import (
        set_visibility,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = set_visibility(dataset, False)
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_visibility.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import replace

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Dataset


def set_visibility(dataset: Dataset, visible: bool) -> StandardResponse[Dataset]:
    """Return new metadata with an explicitly validated visibility value."""
    try:
        updated = replace(dataset, visible=visible)
    except ValueError, TypeError:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_VISIBILITY"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_VISIBILITY", "Dataset operation rejected."),
        )
    logger.info(
        "Dataset operation completed",
        extra={"outcome": "success", "count": dataset.row_count},
    )
    return StandardResponse.success(data=updated)


logger = get_logger(__name__).bind(requirement="FR-DATASET-VISIBILITY")
