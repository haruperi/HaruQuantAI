"""Unit tests for Indicators-owned market projections."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.indicators.volatility import market_projection

from tests.indicators.helpers import DataQualityReport, MarketDataset, OHLCVRecord


class _Series:
    """Minimal positional series fixture."""

    def __init__(self, values: tuple[float, ...]) -> None:
        self._values = values

    @property
    def iloc(self) -> _Series:
        """Return the positional index facade."""
        return self

    def __getitem__(self, index: int) -> float:
        """Return one positional value."""
        return self._values[index]

    def __len__(self) -> int:
        """Return the fixture series length."""
        return len(self._values)


def _response(values: tuple[float, ...]) -> object:
    """Return one successful indicator response fixture."""
    return SimpleNamespace(
        status="success",
        data=SimpleNamespace(
            output_columns=("value",),
            values={"value": _Series(values)},
        ),
    )


def _dataset() -> object:
    """Return a bounded D1 dataset fixture."""
    return SimpleNamespace(
        records=(
            *(SimpleNamespace(open=1.10, high=1.106, low=1.101) for _ in range(11)),
            SimpleNamespace(open=1.105, high=1.108, low=1.105),
        )
    )


def test_projection_owns_volatility_adr_pip_and_change_formulas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Projection uses prior settled values and broker quote precision."""
    monkeypatch.setattr(
        market_projection,
        "rolling_volatility",
        lambda *_args, **_kwargs: _response((0.0,) * 10 + (0.125, 0.25)),
    )
    monkeypatch.setattr(
        market_projection,
        "adr",
        lambda *_args, **_kwargs: _response((0.0,) * 10 + (0.005, 0.006)),
    )

    result = market_projection.project_market_overlay(
        _dataset(), digits=5, point=0.00001, last_price=1.107
    )

    assert result["volatility"] == pytest.approx(0.125)
    assert result["adr"] == pytest.approx(50.0)
    assert result["range_percent_of_adr"] == pytest.approx(60.0)
    assert result["change"] == pytest.approx(0.002)
    assert result["change_pips"] == pytest.approx(20.0)


def test_projection_rejects_invalid_point() -> None:
    """Non-positive quote precision fails explicitly."""
    with pytest.raises(ValueError, match="point must be positive"):
        market_projection.project_market_overlay(
            _dataset(), digits=5, point=0.0, last_price=None
        )


def test_projection_matches_usage_example_with_real_dataset() -> None:
    """A canonical D1 dataset produces all three usage-example values."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    records = tuple(
        OHLCVRecord(
            timestamp=start + timedelta(days=index),
            source="test",
            source_symbol="EURUSD",
            available_at=start + timedelta(days=index, seconds=1),
            open=Decimal(str(1.10 + index * 0.001)),
            high=Decimal(str(1.103 + index * 0.001)),
            low=Decimal(str(1.098 + index * 0.001)),
            close=Decimal(str(1.101 + index * 0.001 + (index % 3) * 0.0005)),
            volume=Decimal(100),
            price_unit="USD",
            volume_unit="units",
        )
        for index in range(15)
    )
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
        timeframe="D1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )

    result = market_projection.project_market_overlay(
        dataset, digits=5, point=0.00001, last_price=float(records[-1].close)
    )

    assert result["volatility"] is not None
    assert result["adr"] == pytest.approx(50.0)
    assert result["range_percent_of_adr"] == pytest.approx(100.0)
