"""Shared deterministic fixtures for Indicators tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord

_START = datetime(2026, 1, 1, tzinfo=UTC)
_REQUEST_ID = "req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def build_dataset(
    bars: list[tuple[float, float, float, float, float]],
    *,
    timeframe: str = "M5",
) -> MarketDataset:
    """Build one normalized OHLCV dataset from numeric bar tuples.

    Args:
        bars: Row-ordered ``(open, high, low, close, volume)`` tuples.
        timeframe: Exact source timeframe.

    Returns:
        One normalized immutable ``MarketDataset v1``.
    """
    records = tuple(
        OHLCVRecord(
            timestamp=_START + timedelta(minutes=5 * position),
            source="indicator-test",
            source_symbol="TEST",
            available_at=_START
            + timedelta(minutes=5 * position)
            + timedelta(seconds=1),
            open=Decimal(str(open_price)),
            high=Decimal(str(high)),
            low=Decimal(str(low)),
            close=Decimal(str(close)),
            volume=Decimal(str(volume)),
            price_unit="USD",
            volume_unit="units",
        )
        for position, (open_price, high, low, close, volume) in enumerate(bars)
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
        symbol="TEST",
        timeframe=timeframe,
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=quality,
        source_metadata={"provider": "indicator-test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id=_REQUEST_ID,
    )


def close_dataset(prices: list[float]) -> MarketDataset:
    """Build bars centered on the supplied close prices.

    Args:
        prices: Row-ordered close prices.

    Returns:
        One normalized immutable ``MarketDataset v1``.
    """
    return build_dataset(
        [(price, price + 0.5, price - 0.5, price, 100.0) for price in prices]
    )


__all__ = ["build_dataset", "close_dataset"]
