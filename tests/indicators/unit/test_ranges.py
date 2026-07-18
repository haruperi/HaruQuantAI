"""Unit tests for the official ATR and ADR volatility calculators."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.volatility import adr, atr

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "volatility_golden.json"
)
_START = datetime(2026, 1, 1, tzinfo=UTC)


def _load_fixture() -> dict:
    """Load the committed hand-calculated volatility golden fixture.

    Returns:
        The parsed golden fixture mapping.
    """
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _dataset_from_bars(bars: list[dict], *, timeframe: str) -> MarketDataset:
    """Build one ``MarketDataset v1`` from fixture-style OHLCV bar rows.

    Args:
        bars: Fixture bar rows with timestamp/open/high/low/close/volume.
        timeframe: The dataset's source timeframe.

    Returns:
        One normalized bar ``MarketDataset v1``.
    """
    records = tuple(
        OHLCVRecord(
            timestamp=datetime.fromisoformat(bar["timestamp"]),
            source="test",
            source_symbol="EURUSD",
            available_at=datetime.fromisoformat(bar["timestamp"])
            + timedelta(seconds=1),
            open=Decimal(str(bar["open"])),
            high=Decimal(str(bar["high"])),
            low=Decimal(str(bar["low"])),
            close=Decimal(str(bar["close"])),
            volume=Decimal(str(bar["volume"])),
            price_unit="USD",
            volume_unit="units",
        )
        for bar in bars
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
        symbol="EURUSD",
        timeframe=timeframe,
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


def _flat_daily_dataset(bar_count: int, price: float) -> MarketDataset:
    """Build one D1 dataset of constant OHLC daily bars for zero-range tests.

    Args:
        bar_count: Number of identical daily bars to generate.
        price: The constant open/high/low/close price.

    Returns:
        One normalized D1 ``MarketDataset v1`` with zero daily range.
    """
    records = []
    for index in range(bar_count):
        t = _START + timedelta(days=index)
        value = Decimal(str(price))
        records.append(
            OHLCVRecord(
                timestamp=t,
                source="test",
                source_symbol="EURUSD",
                available_at=t + timedelta(seconds=1),
                open=value,
                high=value,
                low=value,
                close=value,
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
        timeframe="D1",
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


def test_atr_matches_approved_gap_fixture() -> None:
    """FR-INDI-018: ATR matches the hand-calculated golden gap fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["atr_bars"], timeframe="M5")
    spec = fixture["atr"]
    result = atr(data, period=spec["period"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_adr_matches_approved_golden_fixture() -> None:
    """FR-INDI-019: ADR matches the hand-calculated golden D1 fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["adr_bars"], timeframe="D1")
    spec = fixture["adr"]
    result = adr(data, period=spec["period"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_atr_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["atr_bars"], timeframe="M5")
    bad_config = IndicatorConfig(
        indicator_id="atr",
        parameters=(("period", 5),),
        source=None,
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    with pytest.raises(IndicatorError) as excinfo:
        atr(data, period=2, config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_adr_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["adr_bars"], timeframe="D1")
    bad_config = IndicatorConfig(
        indicator_id="adr",
        parameters=(("period", 5),),
        source=None,
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    with pytest.raises(IndicatorError) as excinfo:
        adr(data, period=2, config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_adr_rejects_non_d1_timeframe() -> None:
    """ADR against a non-D1 dataset raises IND_UNSUPPORTED_TIMEFRAME."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["atr_bars"], timeframe="M5")
    with pytest.raises(IndicatorError) as excinfo:
        adr(data, period=2)
    assert excinfo.value.code == IndicatorErrorCode.IND_UNSUPPORTED_TIMEFRAME


def test_adr_zero_range_is_valid() -> None:
    """A constant flat D1 dataset produces a valid zero ADR, not an error."""
    data = _flat_daily_dataset(4, 1.5)
    result = adr(data, period=2)
    valid = result.values["unavailable_reason"].isna()
    assert valid.any()
    assert (result.values.loc[valid, "adr_2"] == 0.0).all()


def test_atr_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["atr_bars"][:1], timeframe="M5")
    result = atr(data, period=2)
    assert result.values["atr_2"].isna().all()
    assert (result.values["unavailable_reason"] == "warmup").all()


def test_atr_manifest_row_count_matches_input() -> None:
    """ATR's manifest row count matches the input dataset row count."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["atr_bars"], timeframe="M5")
    result = atr(data, period=2)
    assert result.manifest.row_count == len(fixture["atr_bars"])
