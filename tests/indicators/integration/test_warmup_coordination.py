"""WF-INDI-003 integration test: warmup coordination."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.indicators import (
    build_indicator_config,
    get_indicator,
    get_indicator_result_values,
    get_warmup_requirement,
    sma,
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


def _dataset(bar_count: int) -> MarketDataset:
    """Build one normalized bar ``MarketDataset v1`` of the given length.

    Args:
        bar_count: Number of bars to generate; ``0`` builds an empty
            dataset.

    Returns:
        One normalized bar ``MarketDataset v1``.
    """
    records = []
    for index in range(bar_count):
        t = _START + timedelta(minutes=5 * index)
        price = Decimal("1.1000") + Decimal(index) * Decimal("0.0010")
        records.append(
            OHLCVRecord(
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
        )
    records_tuple = tuple(records)
    if records_tuple:
        start, end, available_at = (
            records_tuple[0].timestamp,
            records_tuple[-1].timestamp,
            records_tuple[-1].available_at,
        )
    else:
        start = end = available_at = _START
    quality = DataQualityReport(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=len(records_tuple),
        checked_count=len(records_tuple),
        truncated=False,
        sample_limit=1000,
        schema_version="v1",
        generated_at=available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M5",
        records=records_tuple,
        start=start,
        end=end,
        available_at=available_at,
        record_count=len(records_tuple),
        quality_report=quality,
        source_metadata={"provider": "test"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    )


def test_warmup_requirement_preserves_unavailable_rows() -> None:
    """WF-INDI-003: warmup rows are retained and explicitly unavailable.

    The caller first resolves ``WarmupRequirement`` from the official spec
    without fetching data. It then supplies exactly-sufficient normalized
    history: warmup rows remain in the result, marked
    ``unavailable_reason="warmup"``, rather than being dropped or fetched
    further. A non-empty but too-short dataset stays entirely warmup, and
    an empty dataset fails closed with ``IND_INSUFFICIENT_DATA``.
    """
    spec = unwrap_response(get_indicator("sma"))
    period = 3
    config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", period),),
        source="close",
        formula_version=spec.formula_version,
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    requirement = unwrap_response(get_warmup_requirement("sma", config))
    assert requirement.minimum_observations == period

    sufficient_data = _dataset(bar_count=4)
    result = unwrap_response(sma(sufficient_data, period=period, source="close"))
    values = get_indicator_result_values(result)
    assert values["unavailable_reason"].iloc[: period - 1].eq("warmup").all()
    assert values["unavailable_reason"].iloc[period - 1 :].isna().all()

    short_data = _dataset(bar_count=2)
    short_result = unwrap_response(sma(short_data, period=period, source="close"))
    assert (
        get_indicator_result_values(short_result)["unavailable_reason"]
        .eq("warmup")
        .all()
    )

    empty_data = _dataset(bar_count=0)
    assert_error(validate_indicator("sma", empty_data, config), "IND_INSUFFICIENT_DATA")
