"""Validate metadata replacements without changing identity or records.

Description:
    Validate metadata replacements without changing identity or records.
    Accepts caller-supplied immutable data and returns an explicit result.
    No persistence, network calls, scheduling or import-time work is performed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-METADATA-EDITING: Validate metadata replacements without changing
      identity or records.
      Associated: `edit_metadata()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.metadata_editing import (
        edit_metadata,
        InstrumentFacts,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = edit_metadata(
        Catalog((dataset,)),
        "fx",
        symbol="NEW",
        facts=InstrumentFacts("EURUSD", None, "UTC"),
    )
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_metadata_editing.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Catalog, Dataset


@dataclass(frozen=True, slots=True)
class InstrumentFacts:
    """Caller-resolved instrument and broker timezone authority."""

    instrument: str
    broker_id: str | None
    broker_timezone: str


def edit_metadata(
    catalog: Catalog, dataset_id: str, *, symbol: str, facts: InstrumentFacts
) -> StandardResponse[Dataset]:
    """Validate supplied instrument facts, rename and broker timezone changes."""
    item = next((item for item in catalog.datasets if item.id == dataset_id), None)
    if item is None:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNKNOWN_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNKNOWN_DATASET", "Dataset operation rejected."),
        )
    if item.restricted:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "RESTRICTED_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("RESTRICTED_DATASET", "Dataset operation rejected."),
        )
    if any(
        other.symbol == symbol and other.id != dataset_id for other in catalog.datasets
    ):
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "SYMBOL_CONFLICT"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("SYMBOL_CONFLICT", "Dataset operation rejected."),
        )
    if item.records and facts.broker_timezone != item.timezone:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "BROKER_TIMEZONE_CONFLICT"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError(
                "BROKER_TIMEZONE_CONFLICT", "Dataset operation rejected."
            ),
        )
    try:
        updated = replace(
            item,
            symbol=symbol,
            instrument=facts.instrument,
            broker_id=facts.broker_id,
            timezone=facts.broker_timezone,
        )
    except ValueError:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_METADATA"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_METADATA", "Dataset operation rejected."),
        )
    logger.info(
        "Dataset operation completed",
        extra={"outcome": "success", "count": updated.row_count},
    )
    return StandardResponse.success(data=updated)


logger = get_logger(__name__).bind(requirement="FR-DATASET-METADATA-EDITING")
