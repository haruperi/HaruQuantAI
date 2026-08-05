"""Shared deterministic fixtures for Indicators tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, TypeVar

import pandas as pd
from app.services.data import build_ohlcv_record
from app.services.indicators import (
    get_indicator_result_metadata,
    get_indicator_result_values,
    join_indicator_result,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


_START = datetime(2026, 1, 1, tzinfo=UTC)
_REQUEST_ID = "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
_ResponseT = TypeVar("_ResponseT")
MarketDataset = Any
StandardResponse = Any


class _FixtureModel(SimpleNamespace):
    """Minimal model-shaped fixture accepted by Indicators validation."""

    def __init__(self, **kwargs: object) -> None:
        """Initialize one bounded fixture contract."""
        kwargs.setdefault("contract_version", "v1")
        kwargs.setdefault("schema_id", "data.market_dataset.v1")
        super().__init__(**kwargs)

    def model_dump(self, *, mode: str = "python") -> dict[str, object]:
        """Return a deterministic mapping for checksum construction."""
        del mode
        payload: dict[str, object] = {}
        for name, value in vars(self).items():
            if hasattr(value, "model_dump"):
                payload[name] = value.model_dump(mode="json")
            elif isinstance(value, tuple):
                payload[name] = tuple(
                    item.model_dump(mode="json")
                    if hasattr(item, "model_dump")
                    else item
                    for item in value
                )
            else:
                payload[name] = value
        return payload

    def model_copy(self, *, update: dict[str, object] | None = None) -> _FixtureModel:
        """Return a detached fixture copy with optional field updates."""
        values = dict(vars(self))
        if update:
            values.update(update)
        return type(self)(**values)


DataQualityReport = _FixtureModel
MarketDataset = _FixtureModel
OHLCVRecord = build_ohlcv_record


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


def result_values(result: object) -> pd.DataFrame:
    """Read opaque IndicatorResult values through the public Indicators API.

    Returns:
        A defensive copy of the result values.
    """
    return get_indicator_result_values(result)


def result_metadata(result: object) -> dict[str, object]:
    """Read opaque IndicatorResult metadata through the public API.

    Returns:
        Public result metadata as a detached dictionary.
    """
    return dict(get_indicator_result_metadata(result))


def join_result(result: object, data: object) -> pd.DataFrame:
    """Join an opaque IndicatorResult through the public Indicators API.

    Returns:
        A copied source frame with the indicator columns joined.

    Raises:
        AssertionError: If the join operation returns an error response.
    """
    return unwrap_response(join_indicator_result(result, data))


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
        build_ohlcv_record(
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
    quality = _FixtureModel(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=len(records),
        checked_count=len(records),
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return _FixtureModel(
        contract_version="v1",
        schema_id="data.market_dataset.v1",
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
) -> object:
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
    output_values = pd.DataFrame(
        {
            "symbol": market.symbol,
            output_column: values,
            "available_at": [record.available_at for record in market.records],
            "computed_from_start": [record.timestamp for record in market.records],
            "computed_from_end": [record.timestamp for record in market.records],
            "source_timeframe": market.timeframe,
            "data_quality_status": market.quality_report.quality_status,
            "data_quality_decision": market.quality_report.quality_decision,
            "data_quality_score": float(market.quality_report.quality_score),
            "unavailable_reason": [pd.NA] * len(index),
        },
        index=index,
    )
    manifest = SimpleNamespace(
        indicator_id=indicator_id,
        indicator_version="1.0.0",
        formula_version="1.0.0",
        parameter_hash="a" * 64,
        input_checksum="b" * 64,
        output_checksum="c" * 64,
        output_columns=(output_column,),
        row_count=market.record_count,
        symbol=market.symbol,
        source_timeframe=market.timeframe,
    )
    return SimpleNamespace(
        contract_version="v1",
        schema_id="indicators.indicator_series.v1",
        indicator_id=indicator_id,
        indicator_version="1.0.0",
        formula_version="1.0.0",
        parameter_hash="a" * 64,
        values=output_values,
        output_columns=(output_column,),
        manifest=manifest,
    )


__all__ = [
    "assert_error",
    "build_dataset",
    "build_indicator_evidence",
    "close_dataset",
    "join_result",
    "result_metadata",
    "result_values",
    "unwrap_response",
]
