"""Stream generic stored records to an explicit caller-owned text writer.

Description:
    Stream generic stored records to an explicit caller-owned text writer.
    The caller supplies records and options explicitly; no provider, database,
    persistent preset, background worker or host-local timezone is assumed.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-CSV-EXPORT: Owns this operation's validation and output.
      Associated: `export_csv()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with a safe code; CSV writer failures emit ERROR with
      written-row count and never include writer exceptions or record values.
Python API Usage:
    ```python
    from io import StringIO
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.csv_export import (
        export_csv,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    writer = StringIO()  # Caller owns the output resource.
    result = export_csv(dataset, writer)
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    writer.close()
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_csv_export.py --no-cov
    ```
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import TextIO

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import BarRecord, Dataset, Record

MAX_PRECISION = 15


@dataclass(frozen=True, slots=True)
class CsvResult:
    """Number of successfully written historical data rows."""

    rows_written: int


def export_csv(
    dataset: Dataset,
    writer: TextIO,
    *,
    columns: tuple[str, ...] | None = None,
    separator: str = ",",
    include_header: bool = True,
    precision: int = 5,
    date_from_ms: int | None = None,
    date_to_ms: int | None = None,
    timeframe: str | None = None,
) -> StandardResponse[CsvResult]:
    """Validate options before output; preserve UTC times and actual volume."""
    if timeframe is not None and timeframe != dataset.timeframe:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "UNSUPPORTED_TIMEFRAME"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("UNSUPPORTED_TIMEFRAME", "Dataset operation rejected."),
        )
    defaults = (
        ("time_ms", "open", "high", "low", "close", "volume")
        if dataset.timeframe != "TICK"
        else ("time_ms", "bid", "ask", "volume")
    )
    fields = defaults if columns is None else columns
    error = _format_error(
        fields,
        defaults,
        precision=precision,
        separator=separator,
        include_header=include_header,
        date_from_ms=date_from_ms,
        date_to_ms=date_to_ms,
    )
    if error is not None:
        logger.warning(
            "Dataset operation rejected", extra={"outcome": "error", "code": error}
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError(error, "Dataset operation rejected."),
        )
    count = 0
    writer_failed = False
    try:
        csv_writer = csv.writer(writer, delimiter=separator, lineterminator="\n")
        if include_header:
            csv_writer.writerow(fields)
        for record in dataset.records:
            if date_from_ms is not None and record.time_ms < date_from_ms:
                continue
            if date_to_ms is not None and record.time_ms > date_to_ms:
                continue
            row = _row(record, dataset.symbol, precision)
            csv_writer.writerow(tuple(row[field] for field in fields))
            count += 1
    except OSError, ValueError, csv.Error:
        writer_failed = True
    if writer_failed:
        logger.error(
            "Dataset operation failed",
            extra={"outcome": "error", "code": "CSV_WRITE_FAILED", "count": count},
        )
        return StandardResponse.failure(
            message="CSV writer failed; output may be partial.",
            error=StandardError(
                "CSV_WRITE_FAILED", "CSV writer failed; output may be partial."
            ),
            side_effects=True,
            extensions={"rows_written": count},
        )
    logger.info(
        "Dataset operation completed", extra={"outcome": "success", "count": count}
    )
    return StandardResponse.success(data=CsvResult(count), side_effects=True)


def _format_error(
    fields: tuple[str, ...],
    defaults: tuple[str, ...],
    *,
    precision: int,
    separator: str,
    include_header: object,
    date_from_ms: int | None,
    date_to_ms: int | None,
) -> str | None:
    if type(precision) is not int or not 0 <= precision <= MAX_PRECISION:
        return "INVALID_PRECISION"
    if len(separator) != 1 or separator in "\r\n\0" or type(include_header) is not bool:
        return "INVALID_FORMAT"
    if not _dates_valid(date_from_ms, date_to_ms):
        return "INVALID_DATES"
    if (
        not fields
        or len(set(fields)) != len(fields)
        or any(field not in (*defaults, "symbol") for field in fields)
    ):
        return "INVALID_COLUMNS"
    return None


def _dates_valid(begin: int | None, end: int | None) -> bool:
    if any(value is not None and type(value) is not int for value in (begin, end)):
        return False
    return begin is None or end is None or begin <= end


def _row(record: Record, symbol: str, precision: int) -> dict[str, str]:
    values = (
        {
            "open": record.open,
            "high": record.high,
            "low": record.low,
            "close": record.close,
        }
        if isinstance(record, BarRecord)
        else {"bid": record.bid, "ask": record.ask}
    )
    values["volume"] = record.volume
    result = {field: f"{value:.{precision}f}" for field, value in values.items()}
    result.update(time_ms=str(record.time_ms), symbol=symbol)
    return result


logger = get_logger(__name__).bind(requirement="FR-DATASET-CSV-EXPORT")
