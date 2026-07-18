"""Unit tests for the official RSI and Williams %R momentum oscillators."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.momentum import rsi, williams_r

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "momentum_golden.json"
)
_START = datetime(2026, 1, 1, tzinfo=UTC)


def _load_fixture() -> dict:
    """Load the committed hand-calculated momentum golden fixture.

    Returns:
        The parsed golden fixture mapping.
    """
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _dataset_from_bars(bars: list[dict]) -> MarketDataset:
    """Build one ``MarketDataset v1`` from fixture-style OHLCV bar rows.

    Args:
        bars: Fixture bar rows with timestamp/open/high/low/close/volume.

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


def _dataset(closes: list[float]) -> MarketDataset:
    """Build one normalized dataset from a list of close prices.

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


def _flat_dataset(bar_count: int, price: float) -> MarketDataset:
    """Build one dataset of constant OHLC bars for zero-range tests.

    Args:
        bar_count: Number of identical bars to generate.
        price: The constant open/high/low/close price.

    Returns:
        One normalized bar ``MarketDataset v1`` with zero true range.
    """
    records = []
    for index in range(bar_count):
        t = _START + timedelta(minutes=5 * index)
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


def test_rsi_matches_approved_flat_and_golden_fixtures() -> None:
    """FR-INDI-021: RSI matches the hand-calculated golden fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["rsi_bars"])
    spec = fixture["rsi"]
    result = rsi(data, period=spec["period"], source=spec["source"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_rsi_flat_prices_yield_flat_fifty() -> None:
    """Zero gain and zero loss together yield the flat RSI value of 50."""
    data = _dataset([2.0, 2.0, 2.0, 2.0, 2.0])
    result = rsi(data, period=2)
    valid = result.values["unavailable_reason"].isna()
    assert valid.any()
    assert (result.values.loc[valid, "rsi_2"] == 50.0).all()


def test_williams_r_matches_approved_zero_range_fixture() -> None:
    """FR-INDI-022: Williams %R matches the hand-calculated golden fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["williams_r_bars"])
    spec = fixture["williams_r"]
    result = williams_r(data, period=spec["period"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_williams_r_zero_range_raises_invalid_ohlc() -> None:
    """A flat OHLC window raises IND_INVALID_OHLC for Williams %R."""
    data = _flat_dataset(4, 1.5)
    with pytest.raises(IndicatorError) as excinfo:
        williams_r(data, period=2)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_OHLC


def test_rsi_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    bad_config = IndicatorConfig(
        indicator_id="rsi",
        parameters=(("period", 5),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    with pytest.raises(IndicatorError) as excinfo:
        rsi(data, period=2, source="close", config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_williams_r_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["williams_r_bars"])
    bad_config = IndicatorConfig(
        indicator_id="williams_r",
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
        williams_r(data, period=3, config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_rsi_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than period+1 prices stays entirely unavailable."""
    data = _dataset([1.0, 2.0])
    result = rsi(data, period=3)
    assert result.values["rsi_3"].isna().all()
    assert (result.values["unavailable_reason"] == "warmup").all()


def test_rsi_non_default_source_uses_qualified_output_name() -> None:
    """A non-close source produces the exact source-qualified output name."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    result = rsi(data, period=2, source="high")
    assert "rsi_high_2" in result.output_columns
