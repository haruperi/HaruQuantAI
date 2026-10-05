"""Apply atomic index-based corrections without merging equal-time observations.

Description:
    Apply atomic index-based corrections without merging equal-time observations.
    Inputs are caller-supplied immutable data. Output is an explicit result,
    with no storage, network calls, scheduling or import-time work.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-RECORD-CORRECTION: Owns this operation's validation and output.
      Associated: `correct_records()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.record_correction import (
        correct_records,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = correct_records(dataset, deleted=(0,))
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_record_correction.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import (
    BarRecord,
    Dataset,
    Record,
    TickRecord,
)


def correct_records(
    dataset: Dataset,
    *,
    replacements: Mapping[int, Record] | None = None,
    deleted: tuple[int, ...] = (),
) -> StandardResponse[Dataset]:
    """Validate replacements and deletions before returning a corrected series."""
    changes = {} if replacements is None else dict(replacements)
    indexes = (*changes, *deleted)
    if not indexes:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "NO_CHANGES"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("NO_CHANGES", "Dataset operation rejected."),
        )
    if dataset.restricted:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "RESTRICTED_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("RESTRICTED_DATASET", "Dataset operation rejected."),
        )
    error = _change_error(dataset, changes, deleted)
    if error is not None:
        logger.warning(
            "Dataset operation rejected", extra={"outcome": "error", "code": error}
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError(error, "Dataset operation rejected."),
        )
    records = tuple(
        changes.get(index, record)
        for index, record in enumerate(dataset.records)
        if index not in deleted
    )
    try:
        updated = replace(dataset, records=records)
    except ValueError:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNORDERED_RECORDS"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNORDERED_RECORDS", "Dataset operation rejected."),
        )
    logger.info(
        "Dataset operation completed",
        extra={"outcome": "success", "count": len(indexes)},
    )
    return StandardResponse.success(data=updated)


def _change_error(
    dataset: Dataset, changes: Mapping[int, Record], deleted: tuple[int, ...]
) -> str | None:
    indexes = (*changes, *deleted)
    if any(
        type(index) is not int or not 0 <= index < dataset.row_count
        for index in indexes
    ):
        return "INVALID_INDEX"
    if len(set(deleted)) != len(deleted) or set(changes).intersection(deleted):
        return "CONFLICTING_CHANGES"
    expected = TickRecord if dataset.timeframe == "TICK" else BarRecord
    if any(not isinstance(record, expected) for record in changes.values()):
        return "RECORD_KIND_MISMATCH"
    for record in changes.values():
        if isinstance(record, BarRecord) and not (
            record.low
            <= min(record.open, record.close)
            <= max(record.open, record.close)
            <= record.high
        ):
            return "INVALID_OHLC"
    return None


logger = get_logger(__name__).bind(requirement="FR-DATASET-RECORD-CORRECTION")
