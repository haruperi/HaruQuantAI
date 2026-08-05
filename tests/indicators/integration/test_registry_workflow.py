"""WF-INDI-005 integration test: static registry discovery and validation."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.indicators import (
    build_indicator_config,
    get_capability_matrix,
    get_indicator,
    list_indicators,
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
_OFFICIAL_INDICATOR_IDS = frozenset(
    {
        "adx",
        "adr",
        "atr",
        "bollinger_bands",
        "cmf",
        "doji",
        "ema",
        "engulfing",
        "hull_ma",
        "inside_bar",
        "mfi",
        "obv",
        "pinbar",
        "price_volume_distribution",
        "rolling_volatility",
        "rsi",
        "sma",
        "standard_deviation",
        "williams_r",
        "wma",
        "zigzag",
    }
)


def _dataset() -> MarketDataset:
    """Build one normalized bar ``MarketDataset v1`` of four bars.

    Returns:
        One normalized bar ``MarketDataset v1``.
    """
    records = []
    for index in range(4):
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
    quality = DataQualityReport(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
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


def test_registry_discovers_and_validates_only_official_batch_indicators() -> None:
    """WF-INDI-005: the registry exposes exactly the official built-ins.

    ``get_indicator`` resolves a candidate ID to its immutable spec or
    raises a deterministic refusal for anything outside the eight reviewed
    built-ins; ``list_indicators``/``get_capability_matrix`` describe
    exactly that fixed set; and ``validate_indicator`` either returns the
    resolved spec for a valid request or raises a deterministic
    ``IND_*`` error, never a partial or silent result.
    """
    specs = unwrap_response(list_indicators())
    assert {spec.indicator_id for spec in specs} == set(_OFFICIAL_INDICATOR_IDS)

    matrix = unwrap_response(get_capability_matrix())
    assert {record["indicator_id"] for record in matrix} == set(_OFFICIAL_INDICATOR_IDS)

    for indicator_id in _OFFICIAL_INDICATOR_IDS:
        spec = unwrap_response(get_indicator(indicator_id))
        assert spec.indicator_id == indicator_id

    assert_error(get_indicator("macd"), "IND_UNSUPPORTED_INDICATOR")

    data = _dataset()
    config = build_indicator_config(
        indicator_id="sma",
        parameters=(("period", 2),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )
    resolved = unwrap_response(validate_indicator("sma", data, config))
    assert resolved.indicator_id == "sma"

    assert_error(validate_indicator("ema", data, config), "IND_INVALID_CONFIG")
