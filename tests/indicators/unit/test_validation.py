"""Unit tests for the Indicators Core fail-fast request validation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.core.validation import validate_indicator

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


def _dataset(
    bar_count: int = 20,
    timeframe: str = "M5",
    quality_status: str = "passed",
) -> MarketDataset:
    """Build one normalized bar dataset for validation-layer tests."""
    records = tuple(_bar(i) for i in range(bar_count)) if bar_count else ()
    if bar_count:
        start, end, available_at = (
            records[0].timestamp,
            records[-1].timestamp,
            records[-1].available_at,
        )
    else:
        start = end = available_at = _START
    quality = DataQualityReport(
        quality_status=quality_status,  # type: ignore[arg-type]
        quality_score=Decimal("1.0"),
        issues=(
            ()
            if quality_status != "failed"
            else (
                {
                    "code": "X",
                    "severity": "error",
                    "message": "bad",
                },
            )
        ),
        record_count=bar_count,
        checked_count=bar_count,
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe=timeframe,
        records=records,
        start=start,
        end=end,
        available_at=available_at,
        record_count=bar_count,
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )


def _config(
    indicator_id: str = "sma",
    period: int = 14,
    source: str | None = "close",
    formula_version: str = "1.0.0",
) -> IndicatorConfig:
    """Build one canonical ``IndicatorConfig`` for validation tests."""
    return IndicatorConfig(
        indicator_id=indicator_id,
        parameters=(("period", period),),
        source=source,
        formula_version=formula_version,
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


def test_validate_indicator_fails_before_formula_execution() -> None:
    """FR-INDI-014: validation succeeds and returns the resolved spec."""
    spec = validate_indicator("sma", _dataset(), _config())
    assert spec.indicator_id == "sma"


def test_validate_indicator_rejects_unknown_indicator() -> None:
    """Precedence 1: an unknown indicator ID is rejected first."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("macd", _dataset(), _config(indicator_id="macd"))
    assert excinfo.value.code == IndicatorErrorCode.IND_UNSUPPORTED_INDICATOR


def test_validate_indicator_rejects_mismatched_config_identity() -> None:
    """Precedence 2: a mismatched config indicator_id is rejected."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(), _config(indicator_id="ema"))
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_validate_indicator_rejects_invalid_output_mode() -> None:
    """Precedence 3: a non-values output_mode is rejected."""
    bad_config = IndicatorConfig(
        indicator_id="sma",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values_and_errors",  # type: ignore[arg-type]
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(), bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_OUTPUT_MODE


def test_validate_indicator_rejects_unsupported_dtype() -> None:
    """Precedence 4: a non-float64 precision_dtype is rejected."""
    bad_config = IndicatorConfig(
        indicator_id="sma",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float32",  # type: ignore[arg-type]
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(), bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_UNSUPPORTED_DTYPE


def test_validate_indicator_rejects_formula_version_mismatch() -> None:
    """Precedence 5: a mismatched formula_version is rejected."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(), _config(formula_version="2.0.0"))
    assert excinfo.value.code == IndicatorErrorCode.IND_FORMULA_VERSION_MISMATCH


def test_validate_indicator_rejects_out_of_range_period() -> None:
    """Precedence 6: a period below the minimum is rejected."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(), _config(period=1))
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_PARAMETER


def test_validate_indicator_rejects_invalid_source() -> None:
    """Precedence 6: an invalid source for a source-selectable indicator."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(), _config(source="volume"))
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_PARAMETER


def test_validate_indicator_rejects_unsupported_timeframe_for_adr() -> None:
    """Precedence 9: ADR against a non-D1 dataset is rejected."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator(
            "adr",
            _dataset(timeframe="M5"),
            _config(indicator_id="adr", source=None),
        )
    assert excinfo.value.code == IndicatorErrorCode.IND_UNSUPPORTED_TIMEFRAME


def test_validate_indicator_rejects_empty_dataset() -> None:
    """Precedence 10: an empty dataset raises IND_INSUFFICIENT_DATA."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(bar_count=0), _config())
    assert excinfo.value.code == IndicatorErrorCode.IND_INSUFFICIENT_DATA


def test_validate_indicator_accepts_short_non_empty_dataset() -> None:
    """A non-empty dataset shorter than the warmup window remains valid."""
    spec = validate_indicator("sma", _dataset(bar_count=2), _config(period=14))
    assert spec.indicator_id == "sma"


def test_validate_indicator_rejects_failed_quality() -> None:
    """Precedence 8: a failed Data quality status is rejected."""
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator("sma", _dataset(quality_status="failed"), _config())
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_INPUT_SCHEMA


def test_validate_indicator_rejects_non_positive_rolling_volatility_source() -> None:
    """Precedence 17: rolling_volatility requires strictly positive prices."""
    zero_price_bar = OHLCVRecord(
        timestamp=_START,
        source="test",
        source_symbol="EURUSD",
        available_at=_START + timedelta(seconds=1),
        open=Decimal(0),
        high=Decimal(0),
        low=Decimal(0),
        close=Decimal(0),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="units",
    )
    records = (zero_price_bar, *(_bar(i) for i in range(1, 3)))
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
    dataset = MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M5",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )
    with pytest.raises(IndicatorError) as excinfo:
        validate_indicator(
            "rolling_volatility",
            dataset,
            _config(indicator_id="rolling_volatility", period=2, source="close"),
        )
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_OHLC
