"""WF-INDI-004 integration test: availability-aware multi-timeframe calculation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
)
from app.services.indicators import sma

_START = datetime(2026, 1, 1, tzinfo=UTC)


def _dataset(
    closes: list[float], *, timeframe: str, minutes_per_bar: int
) -> MarketDataset:
    """Build one normalized bar ``MarketDataset v1`` on a given timeframe.

    Args:
        closes: Row-ordered close prices.
        timeframe: The dataset's source timeframe.
        minutes_per_bar: Minutes between consecutive bar timestamps.

    Returns:
        One normalized bar ``MarketDataset v1``.
    """
    records = []
    for index, close in enumerate(closes):
        t = _START + timedelta(minutes=minutes_per_bar * index)
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
        timeframe=timeframe,
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


def test_separate_timeframe_results_preserve_source_availability() -> None:
    """WF-INDI-004: separate per-timeframe results stay independent.

    Data supplies an already-aligned primary (M5) and higher-timeframe
    (H1) dataset. The orchestrator submits each to the same official
    ``sma`` calculation independently; Indicators neither combines nor
    realigns the two results. Each result preserves its own source
    timeframe and record availability, and the orchestrator alone performs
    any decision-time-qualified join across the two independent series.
    """
    primary = _dataset([1.0, 2.0, 3.0, 4.0, 5.0], timeframe="M5", minutes_per_bar=5)
    higher = _dataset([10.0, 12.0, 14.0], timeframe="H1", minutes_per_bar=60)

    primary_result = sma(primary, period=2, source="close")
    higher_result = sma(higher, period=2, source="close")

    assert primary_result.manifest.source_timeframe == "M5"
    assert higher_result.manifest.source_timeframe == "H1"
    assert primary_result.manifest.row_count == len(primary.records)
    assert higher_result.manifest.row_count == len(higher.records)
    assert (
        primary_result.manifest.input_checksum != higher_result.manifest.input_checksum
    )

    decision_time = primary_result.values["available_at"].iloc[2]
    qualified_higher = higher_result.values.loc[
        higher_result.values["available_at"] <= decision_time
    ]
    assert (qualified_higher["available_at"] <= decision_time).all()
    assert len(qualified_higher) < len(higher_result.values)
