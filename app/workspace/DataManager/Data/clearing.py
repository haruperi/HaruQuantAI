"""Clear records while retaining identity and metadata.

Description:
    Clear records while retaining identity and metadata.
    Inputs are caller-supplied immutable data. Output is an explicit result,
    with no storage, network calls, scheduling or import-time work.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-CLEARING: Owns this operation's validation and output.
      Associated: `clear_datasets()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.clearing import (
        clear_datasets,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = clear_datasets(Catalog((dataset,)), ("fx",))
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_clearing.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Catalog


@dataclass(frozen=True, slots=True)
class ClearResult:
    """Updated complete catalog and explicitly cleared IDs."""

    catalog: Catalog
    cleared_ids: tuple[str, ...]


def clear_datasets(
    catalog: Catalog, ids: tuple[str, ...], *, confirm_sources: bool = False
) -> StandardResponse[ClearResult]:
    """Validate an entire clear request before constructing an empty series."""
    by_id = {item.id: item for item in catalog.datasets}
    if len(set(ids)) != len(ids):
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "DUPLICATE_SELECTION"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("DUPLICATE_SELECTION", "Dataset operation rejected."),
        )
    if any(item_id not in by_id for item_id in ids):
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNKNOWN_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNKNOWN_DATASET", "Dataset operation rejected."),
        )
    if any(by_id[item_id].restricted for item_id in ids):
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "RESTRICTED_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("RESTRICTED_DATASET", "Dataset operation rejected."),
        )
    if (
        any(item.parent_id in ids for item in catalog.datasets)
        and confirm_sources is not True
    ):
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "SOURCE_CONFIRMATION_REQUIRED"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError(
                "SOURCE_CONFIRMATION_REQUIRED", "Dataset operation rejected."
            ),
        )
    updated = Catalog(
        tuple(
            replace(item, records=()) if item.id in ids else item
            for item in catalog.datasets
        )
    )
    logger.info(
        "Dataset operation completed", extra={"outcome": "success", "count": len(ids)}
    )
    return StandardResponse.success(data=ClearResult(updated, ids))


logger = get_logger(__name__).bind(requirement="FR-DATASET-CLEARING")
