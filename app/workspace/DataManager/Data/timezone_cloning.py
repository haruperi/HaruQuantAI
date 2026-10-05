"""Clone supplied records with explicit UTC semantics and parent identity.

Description:
    Clone supplied records with explicit UTC semantics and parent identity.
    The caller supplies records and options explicitly; no provider, database,
    persistent preset, background worker or host-local timezone is assumed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-TIMEZONE-CLONING: Owns this operation's validation and output.
      Associated: `clone_timezone()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with a safe code and no record payloads.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.timezone_cloning import (
        clone_timezone,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = clone_timezone(
        Catalog((dataset,)),
        "fx",
        clone_id="clone",
        symbol="CLONE",
        target_timezone="America/New_York",
    )
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_timezone_cloning.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import Catalog, Dataset, Record

MAX_SHIFT_HOURS = 23
SATURDAY = 6
MILLIS_PER_HOUR = 3_600_000
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def clone_timezone(
    catalog: Catalog,
    dataset_id: str,
    *,
    clone_id: str,
    symbol: str,
    target_timezone: str | None = None,
    shift_hours: int | None = None,
    remove_weekends: bool = False,
) -> StandardResponse[Dataset]:
    """Use either a named zone or a fixed timestamp shift, never both."""
    source = next((item for item in catalog.datasets if item.id == dataset_id), None)
    if source is None:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNKNOWN_DATASET"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNKNOWN_DATASET", "Dataset operation rejected."),
        )
    if source.restricted or source.parent_id is not None:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "CLONE_NOT_ALLOWED"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("CLONE_NOT_ALLOWED", "Dataset operation rejected."),
        )
    error = _option_error(target_timezone, shift_hours, remove_weekends)
    if error is not None:
        logger.warning(
            "Dataset operation rejected", extra={"outcome": "error", "code": error}
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError(error, "Dataset operation rejected."),
        )
    zone_name = source.timezone if target_timezone is None else target_timezone
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError, ValueError:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNSUPPORTED_TIMEZONE"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNSUPPORTED_TIMEZONE", "Dataset operation rejected."),
        )
    shift = 0 if shift_hours is None else shift_hours * MILLIS_PER_HOUR
    try:
        records = _records(source.records, shift, zone, remove_weekends)
        clone = replace(
            source,
            id=clone_id,
            symbol=symbol,
            timezone=zone_name,
            parent_id=source.id,
            records=records,
        )
        Catalog((*catalog.datasets, clone))
    except ValueError, OverflowError:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_CLONE"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_CLONE", "Dataset operation rejected."),
        )
    logger.info(
        "Dataset operation completed",
        extra={"outcome": "success", "count": clone.row_count},
    )
    return StandardResponse.success(data=clone)


def _option_error(
    target_timezone: str | None, shift_hours: int | None, remove_weekends: object
) -> str | None:
    if (target_timezone is None) == (shift_hours is None):
        return "AMBIGUOUS_TIMEZONE_OPTIONS"
    if type(remove_weekends) is not bool:
        return "INVALID_WEEKEND_OPTION"
    if shift_hours is not None and (
        type(shift_hours) is not int or abs(shift_hours) > MAX_SHIFT_HOURS
    ):
        return "INVALID_SHIFT"
    return None


def _records(
    records: tuple[Record, ...], shift: int, zone: ZoneInfo, remove_weekends: bool
) -> tuple[Record, ...]:
    result: list[Record] = []
    for record in records:
        shifted = replace(record, time_ms=record.time_ms + shift)
        local = (EPOCH + timedelta(milliseconds=shifted.time_ms)).astimezone(zone)
        if not remove_weekends or local.isoweekday() < SATURDAY:
            result.append(shifted)
    return tuple(result)


logger = get_logger(__name__).bind(requirement="FR-DATASET-TIMEZONE-CLONING")
