"""Unit tests for the Indicators Core fail-fast request validation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.indicators import (
    build_indicator_config,
    get_warmup_requirement,
    validate_indicator,
)

from tests.indicators.helpers import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    assert_error,
    unwrap_response,
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


def _dataset(
    bar_count: int = 20,
    timeframe: str = "M5",
    quality_decision: str = "accepted",
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
        quality_status=("critical" if quality_decision == "rejected" else "perfect"),
        quality_decision=quality_decision,  # type: ignore[arg-type]
        quality_score=(
            Decimal("0.00") if quality_decision == "rejected" else Decimal("100.00")
        ),
        issues=(
            ()
            if quality_decision != "rejected"
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
) -> object:
    """Build one canonical ``IndicatorConfig`` for validation tests."""
    return build_indicator_config(
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
    spec = unwrap_response(validate_indicator("sma", _dataset(), _config()))
    assert spec.indicator_id == "sma"


def test_validate_indicator_rejects_unknown_indicator() -> None:
    """Precedence 1: an unknown indicator ID is rejected first."""
    assert_error(
        validate_indicator(
            "unknown_indicator", _dataset(), _config(indicator_id="unknown_indicator")
        ),
        "IND_UNSUPPORTED_INDICATOR",
    )


def test_validate_indicator_rejects_mismatched_config_identity() -> None:
    """Precedence 2: a mismatched config indicator_id is rejected."""
    assert_error(
        validate_indicator("sma", _dataset(), _config(indicator_id="ema")),
        "IND_INVALID_CONFIG",
    )


def test_validate_indicator_rejects_invalid_output_mode() -> None:
    """Precedence 3: a non-values output_mode is rejected."""
    bad_config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values_and_errors",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    assert_error(
        validate_indicator("sma", _dataset(), bad_config), "IND_INVALID_OUTPUT_MODE"
    )


def test_validate_indicator_rejects_unsupported_dtype() -> None:
    """Precedence 4: a non-float64 precision_dtype is rejected."""
    bad_config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 14),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float32",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    assert_error(
        validate_indicator("sma", _dataset(), bad_config), "IND_UNSUPPORTED_DTYPE"
    )


def test_validate_indicator_rejects_formula_version_mismatch() -> None:
    """Precedence 5: a mismatched formula_version is rejected."""
    assert_error(
        validate_indicator("sma", _dataset(), _config(formula_version="2.0.0")),
        "IND_FORMULA_VERSION_MISMATCH",
    )


def test_validate_indicator_rejects_out_of_range_period() -> None:
    """Precedence 6: a period below the minimum is rejected."""
    assert_error(
        validate_indicator("sma", _dataset(), _config(period=1)),
        "IND_INVALID_PARAMETER",
    )


def test_validate_indicator_rejects_invalid_source() -> None:
    """Precedence 6: an invalid source for a source-selectable indicator."""
    assert_error(
        validate_indicator("sma", _dataset(), _config(source="volume")),
        "IND_INVALID_PARAMETER",
    )


def test_validate_indicator_rejects_unsupported_timeframe_for_adr() -> None:
    """Precedence 9: ADR against a non-D1 dataset is rejected."""
    assert_error(
        validate_indicator(
            "adr",
            _dataset(timeframe="M5"),
            _config(indicator_id="adr", source=None),
        ),
        "IND_UNSUPPORTED_TIMEFRAME",
    )


def test_validate_indicator_rejects_empty_dataset() -> None:
    """Precedence 10: an empty dataset raises IND_INSUFFICIENT_DATA."""
    assert_error(
        validate_indicator("sma", _dataset(bar_count=0), _config()),
        "IND_INSUFFICIENT_DATA",
    )


def test_validate_indicator_accepts_short_non_empty_dataset() -> None:
    """A non-empty dataset shorter than the warmup window remains valid."""
    spec = unwrap_response(
        validate_indicator("sma", _dataset(bar_count=2), _config(period=14))
    )
    assert spec.indicator_id == "sma"


def test_validate_indicator_rejects_rejected_quality() -> None:
    """Precedence 8: a rejected Data quality decision is rejected."""
    assert_error(
        validate_indicator("sma", _dataset(quality_decision="rejected"), _config()),
        "IND_INVALID_INPUT_SCHEMA",
    )


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
    assert_error(
        validate_indicator(
            "rolling_volatility",
            dataset,
            _config(indicator_id="rolling_volatility", period=2, source="close"),
        ),
        "IND_INVALID_OHLC",
    )


def test_validate_indicator_rejects_non_approved_fixed_policy() -> None:
    """A changed fixed policy is rejected before inspecting input data."""
    config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 2),),
        source="close",
        formula_version="1.0.0",
        quality_policy="ignore",
    )
    assert_error(
        validate_indicator("sma", _dataset(), config),
        "IND_INVALID_CONFIG",
    )


@pytest.mark.parametrize(
    ("parameters", "source"),
    [
        ((), "close"),
        ((("period", True),), "close"),
        ((("unknown", 2),), "close"),
        ((("Period", 2),), "close"),
        ((("period", 2),), None),
    ],
)
def test_validate_indicator_rejects_invalid_parameter_shapes(
    parameters: tuple[tuple[str, int], ...],
    source: str | None,
) -> None:
    """Required, typed, declared, named, and source parameters fail closed."""
    config = build_indicator_config(
        indicator_id="sma",
        parameters=parameters,
        source=source,
        formula_version="1.0.0",
    )
    assert_error(
        validate_indicator("sma", _dataset(), config),
        "IND_INVALID_PARAMETER",
    )


def test_validate_indicator_rejects_fixed_ohlc_indicator_source() -> None:
    """A fixed-OHLC indicator cannot accept a selectable source."""
    config = build_indicator_config(
        indicator_id="obv",
        parameters=(),
        source="close",
        formula_version="1.0.0",
    )
    assert_error(
        validate_indicator("obv", _dataset(), config),
        "IND_INVALID_PARAMETER",
    )


def test_validate_indicator_rejects_dataset_contract_identity() -> None:
    """A non-v1 dataset identity fails before record inspection."""
    dataset = _dataset().model_copy(update={"contract_version": "v2"})
    assert_error(
        validate_indicator("sma", dataset, _config()),
        "IND_INVALID_INPUT_SCHEMA",
    )


def test_validate_indicator_rejects_non_bar_dataset() -> None:
    """Indicators accept normalized bars only."""
    dataset = _dataset().model_copy(update={"data_kind": "ticks"})
    assert_error(
        validate_indicator("sma", dataset, _config()),
        "IND_INVALID_INPUT_SCHEMA",
    )


def test_validate_indicator_rejects_non_utc_timestamp() -> None:
    """Naive timestamps fail the causal UTC contract."""
    dataset = _dataset(bar_count=2)
    first = dataset.records[0].model_copy(
        update={"timestamp": dataset.records[0].timestamp.replace(tzinfo=None)}
    )
    dataset = dataset.model_copy(update={"records": (first, dataset.records[1])})
    assert_error(
        validate_indicator("sma", dataset, _config(period=2)),
        "IND_INVALID_TIMEZONE",
    )


def test_validate_indicator_rejects_duplicate_timestamps() -> None:
    """Duplicate row timestamps fail deterministically."""
    dataset = _dataset(bar_count=2)
    second = dataset.records[1].model_copy(
        update={"timestamp": dataset.records[0].timestamp}
    )
    dataset = dataset.model_copy(update={"records": (dataset.records[0], second)})
    assert_error(
        validate_indicator("sma", dataset, _config(period=2)),
        "IND_DUPLICATE_TIMESTAMP",
    )


def test_validate_indicator_rejects_non_monotonic_timestamps() -> None:
    """Out-of-order rows fail before calculation."""
    dataset = _dataset(bar_count=2)
    dataset = dataset.model_copy(update={"records": tuple(reversed(dataset.records))})
    assert_error(
        validate_indicator("sma", dataset, _config(period=2)),
        "IND_NON_MONOTONIC_TIME",
    )


@pytest.mark.parametrize(
    ("indicator_id", "parameters", "source", "expected"),
    [
        ("obv", (), None, 1),
        ("rsi", (("period", 2),), "close", 3),
        ("adx", (("period", 2),), None, 4),
        ("hull_ma", (("period", 4),), "close", 5),
        ("engulfing", (), None, 2),
    ],
)
def test_warmup_requirement_covers_every_policy(
    indicator_id: str,
    parameters: tuple[tuple[str, int], ...],
    source: str | None,
    expected: int,
) -> None:
    """Every declared warmup policy resolves to an exact observation count."""
    config = build_indicator_config(
        indicator_id=indicator_id,
        parameters=parameters,
        source=source,
        formula_version="1.0.0",
    )
    requirement = unwrap_response(get_warmup_requirement(indicator_id, config))
    assert requirement.minimum_observations == expected
