"""Shared deterministic fixtures for Indicators tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, TypeVar

import pandas as pd
from app.services.data import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.results import IndicatorResult, build_indicator_result
from app.utils import StandardResponse

if TYPE_CHECKING:
    from collections.abc import Sequence

_START = datetime(2026, 1, 1, tzinfo=UTC)
_REQUEST_ID = "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
_ResponseT = TypeVar("_ResponseT")


def unwrap_response(response: StandardResponse[_ResponseT]) -> _ResponseT:
    """Return a successful raw Indicators result from a standard response.

    Args:
        response: Indicators operation response.

    Returns:
        The exact successful raw result stored in ``data``.

    Raises:
        AssertionError: If the operation returned an error response.
    """
    if response.status != "success" or response.error is not None:
        message = f"expected success response, got {response.status}"
        raise AssertionError(message)
    if response.data is None:
        raise AssertionError("successful response did not contain data")
    return response.data


def assert_error(response: StandardResponse[object], code: str) -> None:
    """Assert one safe Indicators error response code.

    Args:
        response: Indicators operation response.
        code: Expected symbolic error code.

    Raises:
        AssertionError: If the response is not the expected error.
    """
    if response.status != "error" or response.data is not None:
        message = f"expected error response, got {response.status}"
        raise AssertionError(message)
    if response.error is None or response.error.code != code:
        actual = response.error.code if response.error is not None else None
        message = f"expected error {code}, got {actual}"
        raise AssertionError(message)


def build_dataset(
    bars: list[tuple[float, float, float, float, float]],
    *,
    timeframe: str = "M5",
) -> MarketDataset:
    """Build one normalized OHLCV dataset from numeric bar tuples.

    Args:
        bars: Row-ordered ``(open, high, low, close, volume)`` tuples.
        timeframe: Exact source timeframe.

    Returns:
        One normalized immutable ``MarketDataset v1``.
    """
    records = tuple(
        OHLCVRecord(
            timestamp=_START + timedelta(minutes=5 * position),
            source="indicator-test",
            source_symbol="TEST",
            available_at=_START
            + timedelta(minutes=5 * position)
            + timedelta(seconds=1),
            open=Decimal(str(open_price)),
            high=Decimal(str(high)),
            low=Decimal(str(low)),
            close=Decimal(str(close)),
            volume=Decimal(str(volume)),
            price_unit="USD",
            volume_unit="units",
        )
        for position, (open_price, high, low, close, volume) in enumerate(bars)
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal("1.0"),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="TEST",
        timeframe=timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "indicator-test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )


def close_dataset(prices: list[float]) -> MarketDataset:
    """Build bars centered on the supplied close prices.

    Args:
        prices: Row-ordered close prices.

    Returns:
        One normalized immutable ``MarketDataset v1``.
    """
    return build_dataset(
        [(price, price + 0.5, price - 0.5, price, 100.0) for price in prices]
    )


def build_indicator_evidence(
    market: MarketDataset,
    *,
    indicator_id: str,
    output_column: str,
    values: Sequence[float],
) -> IndicatorResult:
    """Build checksum-bound indicator evidence for cross-domain test fixtures.

    Args:
        market: Exact source market dataset.
        indicator_id: Official indicator identity.
        output_column: Exact output column name.
        values: Ordered ready indicator values.

    Returns:
        A deterministic ``IndicatorResult`` for consumer-domain unit tests.
    """
    index = pd.DatetimeIndex(
        [record.timestamp for record in market.records],
        name="timestamp",
        tz="UTC",
    )
    output_values = pd.DataFrame({output_column: values}, index=index)
    available_at = pd.Series(
        [record.available_at for record in market.records],
        index=index,
    )
    computed_from = pd.Series(
        [record.timestamp for record in market.records],
        index=index,
    )
    unavailable_reason = pd.Series([pd.NA] * len(index), index=index)
    config = IndicatorConfig(
        indicator_id=indicator_id,
        parameters=(),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    return build_indicator_result(
        data=market,
        config=config,
        indicator_version="1.0.0",
        output_columns=(output_column,),
        output_values=output_values,
        available_at=available_at,
        computed_from_start=computed_from,
        computed_from_end=computed_from,
        unavailable_reason=unavailable_reason,
    )


__all__ = [
    "assert_error",
    "build_dataset",
    "build_indicator_evidence",
    "close_dataset",
    "unwrap_response",
]
