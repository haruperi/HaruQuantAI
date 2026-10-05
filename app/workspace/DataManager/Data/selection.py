"""Resolve stable IDs and report busy items without silent selection changes.

Description:
    Resolve stable IDs and report busy items without silent selection changes.
    Accepts caller-supplied immutable data and returns an explicit result.
    No persistence, network calls, scheduling or import-time work is performed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-SELECTION: Resolve stable IDs and report busy items without silent
      selection changes.
      Associated: `select_datasets()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.selection import (
        select_datasets,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = select_datasets(Catalog((dataset,)), ("fx",))
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_selection.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Catalog, Dataset


@dataclass(frozen=True, slots=True)
class SelectionResult:
    """Eligible datasets and IDs explicitly excluded as busy."""

    datasets: tuple[Dataset, ...]
    excluded_ids: tuple[str, ...]


def select_datasets(
    catalog: Catalog, ids: tuple[str, ...], *, busy_ids: Collection[str] = ()
) -> StandardResponse[SelectionResult]:
    """Resolve the whole selection before excluding caller-reported busy items."""
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
    if any(item_id not in by_id for item_id in busy_ids):
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNKNOWN_BUSY_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNKNOWN_BUSY_DATASET", "Dataset operation rejected."),
        )
    excluded = tuple(item_id for item_id in ids if item_id in busy_ids)
    items = tuple(by_id[item_id] for item_id in ids if item_id not in busy_ids)
    logger.info(
        "Dataset operation completed", extra={"outcome": "success", "count": len(items)}
    )
    return StandardResponse.success(data=SelectionResult(items, excluded))


logger = get_logger(__name__).bind(requirement="FR-DATASET-SELECTION")
