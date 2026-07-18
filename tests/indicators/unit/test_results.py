"""Unit tests for the Indicators Core manifest and result behavior."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError
from app.services.indicators.core.results import (
    IndicatorManifest,
    IndicatorResult,
    build_indicator_result,
)

_START = datetime(2026, 1, 1, tzinfo=UTC)


def _bar(index: int) -> OHLCVRecord:
    """Build one deterministic OHLCV bar for the given row index."""
    t = _START + timedelta(minutes=5 * index)
    price = Decimal("1.1000") + Decimal(index) * Decimal("0.0010")
    return OHLCVRecord(
        timestamp=t,
        source="test",
        source_symbol="EURUSD",
        available_at=t + timedelta(seconds=1),
        open=price,
        high=price + Decimal("0.0005"),
        low=price - Decimal("0.0005"),
        close=price,
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="units",
    )


def _dataset(bar_count: int = 3) -> MarketDataset:
    """Build one small normalized bar dataset for results-layer tests."""
    records = tuple(_bar(i) for i in range(bar_count))
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal("1.0"),
        record_count=bar_count,
        checked_count=bar_count,
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M5",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=bar_count,
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )


def _config() -> IndicatorConfig:
    """Build one canonical ``IndicatorConfig`` for a two-period SMA stand-in."""
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


def _build_result(data: MarketDataset) -> IndicatorResult:
    """Build one ``IndicatorResult`` using a hand-computed two-period mean."""
    closes = [float(record.close) for record in data.records]
    index = pd.DatetimeIndex(
        [record.timestamp for record in data.records], name="timestamp", tz="UTC"
    )
    means = [(closes[i - 1] + closes[i]) / 2 for i in range(1, len(closes))]
    sma = pd.Series([float("nan"), *means], index=index)
    output_values = pd.DataFrame({"sma_2": sma}, index=index)
    available_at = pd.Series(
        [record.available_at for record in data.records], index=index
    )
    computed_from_start = pd.Series(
        [pd.NaT, *[data.records[i - 1].timestamp for i in range(1, len(closes))]],
        index=index,
    )
    computed_from_end = pd.Series(
        [pd.NaT, *[data.records[i].timestamp for i in range(1, len(closes))]],
        index=index,
    )
    unavailable_reason = pd.Series(
        ["warmup", *[pd.NA for _ in range(1, len(closes))]], index=index
    )
    return build_indicator_result(
        data=data,
        config=_config(),
        indicator_version="1.0.0",
        output_columns=("sma_2",),
        output_values=output_values,
        available_at=available_at,
        computed_from_start=computed_from_start,
        computed_from_end=computed_from_end,
        unavailable_reason=unavailable_reason,
    )


def test_manifest_is_stable_for_equivalent_inputs() -> None:
    """FR-INDI-007: equivalent inputs produce byte-identical manifest hashes."""
    result_one = _build_result(_dataset())
    result_two = _build_result(_dataset())
    assert result_one.manifest == result_two.manifest
    assert isinstance(result_one.manifest, IndicatorManifest)
    assert len(result_one.manifest.parameter_hash) == 64
    assert len(result_one.manifest.input_checksum) == 64
    assert len(result_one.manifest.output_checksum) == 64
    assert result_one.manifest.quality_status == "passed"


def test_indicator_result_matches_v1_contract() -> None:
    """FR-INDI-008: the result preserves warmup rows and the v1 schema shape."""
    result = _build_result(_dataset())
    assert result.contract_version == "v1"
    assert result.schema_id == "indicators.indicator_series.v1"
    assert result.output_columns == ("sma_2",)
    frame = result.values  # noqa: PD011 -- IndicatorResult.values is a contract field
    assert list(frame.columns) == [
        "symbol",
        "sma_2",
        "available_at",
        "computed_from_start",
        "computed_from_end",
        "source_timeframe",
        "data_quality_status",
        "data_quality_score",
        "unavailable_reason",
    ]
    assert pd.isna(frame["sma_2"].iloc[0])
    assert frame["unavailable_reason"].iloc[0] == "warmup"
    assert pd.isna(frame["unavailable_reason"].iloc[1])
    assert result.errors == ()


def test_values_only_excludes_source_columns() -> None:
    """FR-INDI-009: values_only carries no original OHLCV columns."""
    result = _build_result(_dataset())
    projection = result.values_only
    for column in ("open", "high", "low", "close", "volume"):
        assert column not in projection.columns
    assert "sma_2" in projection.columns
    projection.loc[projection.index[0], "sma_2"] = 999.0
    stored = result.values  # noqa: PD011 -- IndicatorResult.values is a contract field
    assert stored["sma_2"].iloc[0] != 999.0  # copy-safe, no aliasing


def test_join_to_preserves_input_and_alignment() -> None:
    """FR-INDI-010: join_to appends generated columns onto a copied projection."""
    data = _dataset()
    result = _build_result(data)
    joined = result.join_to(data)
    assert len(joined) == data.record_count
    assert "close" in joined.columns
    assert "sma_2" in joined.columns
    assert joined["close"].iloc[0] == float(data.records[0].close)
    assert pd.isna(joined["sma_2"].iloc[0])


def test_join_to_rejects_mismatched_dataset() -> None:
    """FR-INDI-010: join_to fails when the dataset checksum does not match."""
    result = _build_result(_dataset())
    other = _dataset(bar_count=4)
    with pytest.raises(IndicatorError):
        result.join_to(other)


def test_join_to_rejects_unsupported_mode() -> None:
    """FR-INDI-010: join_to fails for any mode other than copy."""
    data = _dataset()
    result = _build_result(data)
    with pytest.raises(IndicatorError):
        result.join_to(data, mode="overwrite")  # type: ignore[arg-type]
