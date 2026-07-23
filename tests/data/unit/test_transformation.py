"""Behavioral coverage for canonical DATA transformation operations."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from app.services.data.contracts import (
    DataError,
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    SpreadRecord,
    TickRecord,
)
from app.services.data.transformation.alignment import align_datasets
from app.services.data.transformation.resampling import resample_dataset
from app.services.data.transformation.tabular import (
    align_dataframe_datetime,
    bars_to_records,
    compare_dataframes,
    compare_ohlc,
    compare_ohlcv,
    serialize_dataframe_records,
    to_ohlcv_dataframe,
    to_tick_dataframe,
)
from app.services.data.transformation.tick_aggregation import aggregate_ticks
from app.utils import generate_id

_START = datetime(2026, 1, 1, tzinfo=UTC)


def _quality(count: int) -> DataQualityReport:
    """Return passing quality evidence for a bounded fixture."""
    return DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=_START + timedelta(hours=1),
    )


def _dataset(
    records: tuple[OHLCVRecord | TickRecord | SpreadRecord, ...],
    kind: str,
    timeframe: str | None,
) -> MarketDataset:
    """Build one canonical dataset from the supplied records."""
    return MarketDataset(
        normalization_version="v1",
        data_kind=kind,  # type: ignore[arg-type]
        symbol="EURUSD",
        timeframe=timeframe,
        records=records,
        start=records[0].timestamp if records else _START,
        end=records[-1].timestamp if records else _START,
        available_at=max((item.available_at for item in records), default=_START),
        record_count=len(records),
        quality_report=_quality(len(records)),
        source_metadata={"source_id": "fixture"},
        license_metadata={"status": "approved"},
        cache_status="not_used",
        workflow_context="validation",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )


def _bars() -> tuple[OHLCVRecord, ...]:
    """Return homogeneous ordered M1 bars."""
    return tuple(
        OHLCVRecord(
            timestamp=_START + timedelta(minutes=index),
            open=Decimal(10 + index),
            high=Decimal(11 + index),
            low=Decimal(9 + index),
            close=Decimal("10.5") + index,
            volume=Decimal(100 + index),
            spread=Decimal("0.2"),
            price_unit="USD",
            volume_unit="units",
            spread_unit="USD",
            source="fixture",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=_START + timedelta(minutes=index, seconds=1),
        )
        for index in range(5)
    )


def _ticks() -> tuple[TickRecord, ...]:
    """Return homogeneous ordered ticks."""
    return tuple(
        TickRecord(
            timestamp=_START + timedelta(seconds=index * 10),
            bid=Decimal(10 + index),
            ask=Decimal("10.2") + index,
            last=Decimal("10.1") + index,
            volume=Decimal(1),
            price_unit="USD",
            volume_unit="units",
            source="fixture",
            source_symbol="EURUSD",
            source_revision="v1",
            available_at=_START + timedelta(seconds=index * 10 + 1),
        )
        for index in range(4)
    )


def test_transformations_produce_canonical_datasets() -> None:
    """Exercise successful resampling, alignment, and tick aggregation."""
    bars = _dataset(_bars(), "bars", "M1")
    ticks = _dataset(_ticks(), "ticks", None)

    assert resample_dataset(bars, "M5").record_count == 1
    aligned = align_datasets({"bars": bars}, (bars.available_at,))
    assert aligned["bars"].record_count == 1
    assert aggregate_ticks(ticks, "M1", "mid").record_count == 1


def test_alignment_supports_all_record_types_and_rejects_bad_targets() -> None:
    """Cover tick/spread projection and fail-closed target validation."""
    ticks = _dataset(_ticks(), "ticks", None)
    spread = SpreadRecord(
        timestamp=_START,
        spread=Decimal("0.2"),
        unit="USD",
        scale=5,
        source="fixture",
        source_symbol="EURUSD",
        source_revision="v1",
        available_at=_START + timedelta(seconds=1),
    )
    spreads = _dataset((spread,), "spreads", None)
    target = (_START + timedelta(seconds=2),)

    assert align_datasets({"ticks": ticks, "spreads": spreads}, target)
    assert align_datasets({}, ()) == {}
    naive = datetime(2026, 1, 1)  # noqa: DTZ001 - ambiguity is under test.
    for invalid in ((), (naive,), (target[0], _START)):
        with pytest.raises(DataError):
            align_datasets({"ticks": ticks}, invalid)
    with pytest.raises(DataError):
        align_datasets({"ticks": ticks}, (_START,))


@pytest.mark.parametrize("policy", ["bid", "ask", "last"])
def test_tick_aggregation_price_policies(policy: str) -> None:
    """Exercise each supported exact price-selection policy."""
    assert aggregate_ticks(_dataset(_ticks(), "ticks", None), "M1", policy).records


def test_transformations_reject_invalid_evidence() -> None:
    """Reject wrong kinds, empty ticks, unsupported policies, and identities."""
    bars = _dataset(_bars(), "bars", "M1")
    ticks = _dataset(_ticks(), "ticks", None)
    with pytest.raises(DataError):
        resample_dataset(ticks, "M5")
    with pytest.raises(DataError):
        aggregate_ticks(bars, "M1", "last")
    with pytest.raises(DataError):
        aggregate_ticks(_dataset((), "ticks", None), "M1", "last")
    with pytest.raises(DataError):
        aggregate_ticks(ticks, "M1", "unsupported")


def test_tabular_projection_and_serialization() -> None:
    """Project detached frames and serialize supported exact values."""
    bars = _dataset(_bars(), "bars", "M1")
    ticks = _dataset(_ticks(), "ticks", None)
    bar_frame = to_ohlcv_dataframe(bars)
    tick_frame = to_tick_dataframe(ticks)

    assert bar_frame.attrs["spread_unit"] == "USD"
    assert tick_frame.attrs["price_unit"] == "USD"
    assert bars_to_records(_bars())[0]["source"] == "fixture"
    serialized = serialize_dataframe_records(bar_frame.head(1))
    assert serialized[0]["timestamp"].endswith("Z")
    assert compare_dataframes(bar_frame, bar_frame.copy())
    assert compare_ohlc(bar_frame, bar_frame.copy())
    assert compare_ohlcv(bar_frame, bar_frame.copy())


def test_dataframe_alignment_uses_aware_utc_copy() -> None:
    """Align either an aware index or named datetime column without mutation."""
    source = pd.DataFrame(
        {
            "when": [
                datetime(2026, 1, 2, tzinfo=UTC),
                datetime(2026, 1, 1, tzinfo=UTC),
            ],
            "value": [2, 1],
        }
    )
    aligned = align_dataframe_datetime(source, "when")
    assert aligned.index.is_monotonic_increasing
    assert not isinstance(source.index, pd.DatetimeIndex)


@pytest.mark.parametrize(
    ("left", "right", "tolerance"),
    [
        (pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [1, 2]}), None),
        (pd.DataFrame({"x": [1]}), pd.DataFrame({"y": [1]}), None),
        (pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]}), Decimal(0)),
        (pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [1]}), Decimal(-1)),
    ],
)
def test_dataframe_comparison_rejects_mismatch(
    left: pd.DataFrame,
    right: pd.DataFrame,
    tolerance: Decimal | None,
) -> None:
    """Fail closed for incompatible frames and invalid tolerances."""
    with pytest.raises(DataError):
        compare_dataframes(left, right, tolerance)


def test_tabular_operations_reject_ambiguous_inputs() -> None:
    """Reject missing datetime columns, naive time, and wrong dataset kinds."""
    with pytest.raises(DataError):
        align_dataframe_datetime(pd.DataFrame({"x": [1]}), "missing")
    naive = datetime(2026, 1, 1)  # noqa: DTZ001 - ambiguity is under test.
    with pytest.raises(DataError):
        align_dataframe_datetime(pd.DataFrame({"x": [1]}, index=[naive]))
    with pytest.raises(DataError):
        serialize_dataframe_records(
            pd.DataFrame({"x": [object()]}, index=[datetime(2026, 1, 1, tzinfo=UTC)])
        )
    bars = _dataset(_bars(), "bars", "M1")
    ticks = _dataset(_ticks(), "ticks", None)
    with pytest.raises(DataError):
        to_ohlcv_dataframe(ticks)
    with pytest.raises(DataError):
        to_tick_dataframe(bars)
    with pytest.raises(DataError):
        compare_ohlc(pd.DataFrame({"open": [1]}), pd.DataFrame({"open": [1]}))
    with pytest.raises(DataError):
        compare_ohlcv(pd.DataFrame({"open": [1]}), pd.DataFrame({"open": [1]}))
