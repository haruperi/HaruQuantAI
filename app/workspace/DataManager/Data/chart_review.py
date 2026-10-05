"""Project a bounded stored-record slice into chart-ready values.

Description:
    Project a bounded stored-record slice into chart-ready values.
    Inputs are caller-supplied immutable data. Output is an explicit result,
    with no storage, network calls, scheduling or import-time work.
Purpose:
    FEAT-DATASET-MANAGEMENT: Historical Dataset Management.
Key Capabilities:
    - FR-DATASET-CHART-REVIEW: Owns this operation's validation and output.
      Associated: `review_chart()`.
      Logging: INFO completion with requirement, outcome and bounded count;
      WARNING rejection with requirement, outcome and safe error code.
Python API Usage:
    ```python
    from app.workspace.DataManager.Data.contracts import (
        BarRecord,
        Catalog,
        Dataset,
    )
    from app.workspace.DataManager.Data.chart_review import (
        review_chart,
    )

    dataset = Dataset(
        "fx",
        "EURUSD",
        "EURUSD",
        records=(BarRecord(0, 1, 2, 0, 1),),
    )
    result = review_chart(dataset)
    if result.is_success:
        data = result.unwrap()
    else:
        error_code = result.error_code
    ```
CLI Usage:
    ```bash
    uv run pytest tests/workspace/DataManager/Data/test_chart_review.py --no-cov
    ```
"""

from __future__ import annotations

from dataclasses import dataclass

from app.host.logging import get_logger
from app.host.response import StandardError, StandardResponse
from app.workspace.DataManager.Data.contracts import BarRecord, Dataset

MAX_CHART_POINTS = 10_000


@dataclass(frozen=True, slots=True)
class ChartPoint:
    """Timestamp and values in the result's explicit column order."""

    time_ms: int
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ChartData:
    """Chart projection without rendering, sampling or derived bars."""

    columns: tuple[str, ...]
    points: tuple[ChartPoint, ...]
    offset: int
    total_count: int


def review_chart(
    dataset: Dataset, *, offset: int = 0, count: int = 100, timeframe: str | None = None
) -> StandardResponse[ChartData]:
    """Project stored OHLC bars or bid/ask ticks without smoothing."""
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
    if offset < 0 or not 0 <= count <= MAX_CHART_POINTS:
        logger.warning(
            "Dataset operation rejected",
            extra={"outcome": "error", "code": "INVALID_BOUNDS"},
        )
        return StandardResponse.failure(
            message="Dataset operation rejected.",
            error=StandardError("INVALID_BOUNDS", "Dataset operation rejected."),
        )
    columns = (
        ("open", "high", "low", "close")
        if dataset.timeframe != "TICK"
        else ("bid", "ask")
    )
    points = tuple(
        ChartPoint(
            record.time_ms,
            (record.open, record.high, record.low, record.close)
            if isinstance(record, BarRecord)
            else (record.bid, record.ask),
        )
        for record in dataset.records[offset : offset + count]
    )
    logger.info(
        "Dataset operation completed",
        extra={"outcome": "success", "count": len(points)},
    )
    return StandardResponse.success(
        data=ChartData(columns, points, offset, dataset.row_count)
    )


logger = get_logger(__name__).bind(requirement="FR-DATASET-CHART-REVIEW")
