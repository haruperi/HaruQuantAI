"""WF-INDI-001 integration test: core batch indicator calculation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.indicators import IndicatorConfig, sma, validate_indicator

_START = datetime(2026, 1, 1, tzinfo=UTC)


def _dataset(closes: list[float]) -> MarketDataset:
    """Build one normalized bar ``MarketDataset v1`` from close prices.

    Args:
        closes: Row-ordered close prices.

    Returns:
        One normalized bar ``MarketDataset v1``.
    """
    records = []
    for index, close in enumerate(closes):
        t = _START + timedelta(minutes=5 * index)
        price = Decimal(str(close))
        records.append(
            OHLCVRecord(
                timestamp=t,
                source="test",
                source_symbol="EURUSD",
                available_at=t + timedelta(seconds=1),
                open=price,
                high=price + Decimal("0.5"),
                low=price - Decimal("0.5"),
                close=price,
                volume=Decimal(100),
                price_unit="USD",
                volume_unit="units",
            )
        )
    records_tuple = tuple(records)
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal("1.0"),
        record_count=len(records_tuple),
        checked_count=len(records_tuple),
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=records_tuple[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M5",
        records=records_tuple,
        start=records_tuple[0].timestamp,
        end=records_tuple[-1].timestamp,
        available_at=records_tuple[-1].available_at,
        record_count=len(records_tuple),
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )


def _config() -> IndicatorConfig:
    """Build one canonical two-period close-source SMA config.

    Returns:
        The immutable calculation configuration.
    """
    return IndicatorConfig(
        indicator_id="sma",
        parameters=(("period", 2),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


def test_batch_calculation_returns_atomic_available_result() -> None:
    """WF-INDI-001: validate, calculate, and assemble one atomic result.

    Exercises the full internal workflow in order: ``validate_indicator``
    resolves and validates the request before any formula work; the
    official ``sma`` function executes its vectorized formula in canonical
    row order; warmup rows are retained and marked unavailable; Data-owned
    provenance and quality are propagated unchanged; and the returned
    result is deterministic and atomic (one row per input row).
    """
    data = _dataset([1.0, 2.0, 3.0, 4.0, 5.0])
    config = _config()

    spec = validate_indicator("sma", data, config)
    assert spec.indicator_id == "sma"

    result_first = sma(data, period=2, source="close", config=config)
    result_second = sma(data, period=2, source="close", config=config)

    assert (
        result_first.manifest.output_checksum == result_second.manifest.output_checksum
    )
    assert result_first.manifest.input_checksum == result_second.manifest.input_checksum
    assert result_first.manifest.parameter_hash == result_second.manifest.parameter_hash

    result_values = result_first.values_only
    assert len(result_values) == data.record_count
    assert result_values["unavailable_reason"].iloc[0] == "warmup"
    assert pd.isna(result_values["sma_2"].iloc[0])
    assert not pd.isna(result_values["sma_2"].iloc[-1])
    assert result_values["unavailable_reason"].iloc[1:].isna().all()

    assert result_first.manifest.quality_status == data.quality_report.quality_status
    assert result_first.manifest.source_metadata == dict(data.source_metadata)
    assert len(result_first.manifest.output_checksum) == 64
    assert result_first.output_columns == ("sma_2",)
