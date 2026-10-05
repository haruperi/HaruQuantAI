"""Return bounded pages of stored records without resampling.

Description:
    Return bounded pages of stored records without resampling.
    Inputs are caller-supplied immutable data. Output is an explicit result,
    with no storage, network calls, scheduling or import-time work.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-RECORD-REVIEW: Owns this operation's validation and output.
      Associated: `review_records()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.record_review import (
        review_records,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = review_records(dataset)
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_record_review.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import dataclass

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Dataset, Record

MAX_PAGE_SIZE = 10_000


@dataclass(frozen=True, slots=True)
class RecordPage:
    """Stored rows, requested position and total observation count."""

    rows: tuple[Record, ...]
    offset: int
    total_count: int


def review_records(
    dataset: Dataset, *, offset: int = 0, count: int = 100, timeframe: str | None = None
) -> StandardResponse[RecordPage]:
    """Read an explicit page; reject derived-timeframe and invalid requests."""
    if timeframe is not None and timeframe != dataset.timeframe:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNSUPPORTED_TIMEFRAME"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNSUPPORTED_TIMEFRAME", "Dataset operation rejected."),
        )
    if type(offset) is not int or type(count) is not int:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_BOUNDS"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_BOUNDS", "Dataset operation rejected."),
        )
    if offset < 0 or not 0 <= count <= MAX_PAGE_SIZE:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_BOUNDS"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_BOUNDS", "Dataset operation rejected."),
        )
    rows = dataset.records[offset : offset + count]
    logger.info(
        "Dataset operation completed", extra={"outcome": "success", "count": len(rows)}
    )
    return StandardResponse.success(data=RecordPage(rows, offset, dataset.row_count))


logger = get_logger(__name__).bind(requirement="FR-DATASET-RECORD-REVIEW")
