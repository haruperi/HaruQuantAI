"""WF-INDI-002 integration test: decision-time consumption."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import DataQualityReport, MarketDataset, OHLCVRecord
from app.services.indicators import ema

_START = datetime(2026, 1, 1, tzinfo=UTC)


def _dataset(closes: list[float]) -> MarketDataset:
    """Build one normalized bar ``MarketDataset v1`` from close prices.

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


def test_strategy_receives_only_availability_qualified_series() -> None:
    """WF-INDI-002: Strategy consumes only rows qualified by decision time.

    Simulates Trading/Simulation supplying a normalized dataset, calling
    the official ``ema`` calculation, and returning the resulting
    ``IndicatorSeries v1`` to Strategy. Strategy (not Indicators) enforces
    the decision-time filter: it consumes only rows whose ``available_at``
    is at or before its current decision time, so no row exposes
    current/future data as already available.
    """
    data = _dataset([1.0, 2.0, 3.0, 4.0, 5.0])
    result = ema(data, period=2)
    values = result.values

    decision_time = values["available_at"].iloc[2]

    qualified = values.loc[values["available_at"] <= decision_time]
    disqualified = values.loc[values["available_at"] > decision_time]

    assert len(qualified) + len(disqualified) == len(values)
    assert len(disqualified) > 0
    assert (qualified["available_at"] <= decision_time).all()
    assert (qualified["computed_from_end"].dropna() <= decision_time).all()
