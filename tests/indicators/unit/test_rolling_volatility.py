"""Unit tests for the official rolling volatility calculator."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.volatility.rolling_volatility import rolling_volatility

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


def test_rolling_volatility_matches_approved_return_fixture() -> None:
    """FR-INDI-020: rolling volatility matches the hand-calculated fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["rolling_bars"])
    spec = fixture["rolling_volatility"]
    result = rolling_volatility(data, period=spec["period"], source=spec["source"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_rolling_volatility_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    bad_config = IndicatorConfig(
        indicator_id="rolling_volatility",
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
        rolling_volatility(data, period=2, source="close", config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_rolling_volatility_rejects_non_positive_source() -> None:
    """A non-positive selected price raises IND_INVALID_OHLC."""
    data = _dataset([1.0, 2.0, 0.0, 3.0])
    with pytest.raises(IndicatorError) as excinfo:
        rolling_volatility(data, period=2)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_OHLC


def test_rolling_volatility_constant_prices_are_zero() -> None:
    """Constant prices produce exactly zero rolling volatility."""
    data = _dataset([2.0, 2.0, 2.0, 2.0, 2.0])
    result = rolling_volatility(data, period=2)
    valid = result.values["unavailable_reason"].isna()
    assert valid.any()
    assert (result.values.loc[valid, "rolling_volatility_2"] == 0.0).all()


def test_rolling_volatility_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than period+1 prices stays entirely unavailable."""
    data = _dataset([1.0, 2.0])
    result = rolling_volatility(data, period=2)
    assert result.values["rolling_volatility_2"].isna().all()
    assert (result.values["unavailable_reason"] == "warmup").all()


def test_rolling_volatility_non_default_source_uses_qualified_output_name() -> None:
    """A non-close source produces the exact source-qualified output name."""
    data = _dataset([1.0, 2.0, 3.0, 4.0, 5.0])
    result = rolling_volatility(data, period=2, source="high")
    assert "rolling_volatility_high_2" in result.output_columns
