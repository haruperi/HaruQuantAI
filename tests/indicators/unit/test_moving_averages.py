"""Unit tests for the official EMA and SMA trend calculators."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.indicators.core.contracts import IndicatorConfig
from app.services.indicators.core.errors import IndicatorError, IndicatorErrorCode
from app.services.indicators.trend import ema, sma

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent / "fixtures" / "trend_golden.json"
)
_START = datetime(2026, 1, 1, tzinfo=UTC)


def _load_fixture() -> dict:
    """Load the committed hand-calculated trend golden fixture.

    Returns:
        The parsed golden fixture mapping.
    """
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _dataset_from_bars(bars: list[dict], *, timeframe: str = "M5") -> MarketDataset:
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


def _bar(index: int, close: float) -> OHLCVRecord:
    """Build one deterministic OHLCV bar for the given row index and close.

    Args:
        index: Zero-based row position.
        close: The bar's close price.

    Returns:
        One ``OHLCVRecord`` five minutes after the previous index.
    """
    t = _START + timedelta(minutes=5 * index)
    price = Decimal(str(close))
    return OHLCVRecord(
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


def _dataset(closes: list[float]) -> MarketDataset:
    """Build one normalized dataset from a list of close prices.

    Args:
        closes: Row-ordered close prices.

    Returns:
        One normalized bar ``MarketDataset v1``.
    """
    records = tuple(_bar(i, close) for i, close in enumerate(closes))
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


def test_sma_matches_approved_golden_fixture() -> None:
    """FR-INDI-016: SMA matches the hand-calculated golden fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["bars"])
    spec = fixture["sma"]
    result = sma(data, period=spec["period"], source=spec["source"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_ema_matches_approved_golden_fixture() -> None:
    """FR-INDI-015: EMA matches the hand-calculated golden fixture."""
    fixture = _load_fixture()
    data = _dataset_from_bars(fixture["bars"])
    spec = fixture["ema"]
    result = ema(data, period=spec["period"], source=spec["source"])
    actual = result.values[spec["output_column"]].tolist()
    for actual_value, expected_value in zip(actual, spec["expected"], strict=True):
        if expected_value is None:
            assert actual_value != actual_value  # noqa: PLR0124 (NaN self-check)
        else:
            assert actual_value == pytest.approx(expected_value, abs=1e-9)


def test_sma_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    bad_config = IndicatorConfig(
        indicator_id="sma",
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
        sma(data, period=3, source="close", config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_ema_rejects_config_disagreement() -> None:
    """A supplied config disagreeing with wrapper args raises IND_INVALID_CONFIG."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    bad_config = IndicatorConfig(
        indicator_id="ema",
        parameters=(("period", 3),),
        source="high",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    with pytest.raises(IndicatorError) as excinfo:
        ema(data, period=3, source="close", config=bad_config)
    assert excinfo.value.code == IndicatorErrorCode.IND_INVALID_CONFIG


def test_sma_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = _dataset([1.0, 2.0])
    result = sma(data, period=5)
    assert result.values["sma_5"].isna().all()
    assert (result.values["unavailable_reason"] == "warmup").all()


def test_ema_short_history_is_entirely_warmup() -> None:
    """A dataset shorter than the period stays entirely unavailable."""
    data = _dataset([1.0, 2.0])
    result = ema(data, period=5)
    assert result.values["ema_5"].isna().all()
    assert (result.values["unavailable_reason"] == "warmup").all()


def test_sma_non_default_source_uses_qualified_output_name() -> None:
    """A non-close source produces the exact source-qualified output name."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    result = sma(data, period=2, source="high")
    assert "sma_high_2" in result.output_columns
    assert result.values["sma_high_2"].notna().sum() == 3


def test_ema_non_default_source_uses_qualified_output_name() -> None:
    """A non-close source produces the exact source-qualified output name."""
    data = _dataset([1.0, 2.0, 3.0, 4.0])
    result = ema(data, period=2, source="low")
    assert "ema_low_2" in result.output_columns
    assert result.values["ema_low_2"].notna().sum() == 3


def test_sma_manifest_matches_join_to_input_checksum() -> None:
    """SMA's manifest input checksum agrees with join_to for the same dataset."""
    data = _dataset([1.0, 2.0, 3.0, 4.0, 5.0])
    result = sma(data, period=3)
    joined = result.join_to(data)
    assert "sma_3" in joined.columns
    assert result.manifest.row_count == 5
