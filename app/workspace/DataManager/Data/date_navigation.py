"""Find the first stored record at or after a UTC millisecond instant.

Description:
    Find the first stored record at or after a UTC millisecond instant.
    Inputs are caller-supplied immutable data. Output is an explicit result,
    with no storage, network calls, scheduling or import-time work.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-DATE-NAVIGATION: Owns this operation's validation and output.
      Associated: `find_date_index()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.date_navigation import (
        find_date_index,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = find_date_index(dataset, 0)
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_date_navigation.py --no-cov
    ```
"""

from __future__ import annotations

from bisect import bisect_left

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Dataset


def find_date_index(dataset: Dataset, time_ms: int) -> StandardResponse[int]:
    """Use lower-bound binary search; count is the end-of-data sentinel."""
    if type(time_ms) is not int:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_TIMESTAMP"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_TIMESTAMP", "Dataset operation rejected."),
        )
    index = bisect_left(dataset.records, time_ms, key=lambda record: record.time_ms)
    logger.info(
        "Dataset operation completed",
        extra={"outcome": "success", "count": dataset.row_count},
    )
    return StandardResponse.success(data=index)


logger = get_logger(__name__).bind(requirement="FR-DATASET-DATE-NAVIGATION")
