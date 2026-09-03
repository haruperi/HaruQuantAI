"""Unit, contract, and scenario tests for Bar Aggregation service."""

from decimal import Decimal

import pytest
from app.contracts.common.models import Timeframe
from app.contracts.data.errors import DataFailure
from app.contracts.data.models import (
    AggregateBarsRequest,
    AggregateBarsSuccess,
    AggregationSpec,
    Bar,
)
from app.services.data.bar_aggregation.bar_aggregation import (
    BarAggregationService,
    _format_decimal,
    _generate_uuid7,
    _get_bucket_start,
    _parse_timeframe_dict,
    _parse_timeframe_str,
    _validate_multiple_bounds,
    data_aggregate_timeframes,
    data_define_custom_timeframes,
    data_record_aggregation_lineage,
    main,
)


def _sample_m1_bars(count: int = 10, start_minute: int = 0) -> tuple[Bar, ...]:
    """Generate deterministic M1 sample bars."""
    bars = []
    for i in range(count):
        m = start_minute + i
        bars.append(
            Bar(
                timestamp=f"2026-08-28T10:{m:02d}:00.000000Z",
                open=_format_decimal(Decimal(100) + Decimal(i) * Decimal("0.1")),
                high=_format_decimal(Decimal("100.5") + Decimal(i) * Decimal("0.1")),
                low=_format_decimal(
                    Decimal(100)
                    if i == 0
                    else Decimal("99.9") + Decimal(i) * Decimal("0.1")
                ),
                close=_format_decimal(Decimal("100.2") + Decimal(i) * Decimal("0.1")),
                volume="100",
                spread_ticks="1",
                source_sequence=i,
                flags=0,
            )
        )
    return tuple(bars)


def test_define_custom_timeframes_presets() -> None:
    """Verify FR-DATA-DEFINE_CUSTOM_TIMEFRAMES: preset parsing."""
    for preset, (unit, mult) in [
        ("M1", ("MINUTE", 1)),
        ("M5", ("MINUTE", 5)),
        ("M15", ("MINUTE", 15)),
        ("M30", ("MINUTE", 30)),
        ("H1", ("MINUTE", 60)),
        ("H4", ("MINUTE", 240)),
        ("D1", ("DAY", 1)),
        ("W1", ("WEEK", 1)),
        ("MN", ("MONTH", 1)),
    ]:
        tf = data_define_custom_timeframes(preset)
        assert tf.unit == unit
        assert tf.multiple == mult


def test_define_custom_timeframes_custom_positive_intervals() -> None:
    """Verify FR-DATA-DEFINE_CUSTOM_TIMEFRAMES: positive custom intervals."""
    tf_m10 = data_define_custom_timeframes("M10")
    assert tf_m10.unit == "MINUTE"
    assert tf_m10.multiple == 10

    tf_h2 = data_define_custom_timeframes("H2")
    assert tf_h2.unit == "MINUTE"
    assert tf_h2.multiple == 120

    tf_d3 = data_define_custom_timeframes("D3")
    assert tf_d3.unit == "DAY"
    assert tf_d3.multiple == 3

    tf_dict = data_define_custom_timeframes({"unit": "MINUTE", "multiple": 45})
    assert tf_dict.unit == "MINUTE"
    assert tf_dict.multiple == 45


def test_define_custom_timeframes_invalid_rejections() -> None:
    """Verify FR-DATA-DEFINE_CUSTOM_TIMEFRAMES: zero, negative, and invalid rejections."""
    with pytest.raises(ValueError, match="multiple must be >= 1"):
        data_define_custom_timeframes("M0")

    with pytest.raises(ValueError, match="Invalid timeframe representation"):
        data_define_custom_timeframes("M-5")

    with pytest.raises(ValueError, match="Invalid timeframe representation"):
        data_define_custom_timeframes("INVALID")

    with pytest.raises(ValueError, match="multiple must be >= 1"):
        data_define_custom_timeframes(
            Timeframe.model_construct(unit="MINUTE", multiple=0)
        )

    with pytest.raises(ValueError, match="Unsupported timeframe unit"):
        data_define_custom_timeframes({"unit": "INVALID_UNIT", "multiple": 5})


def test_data_aggregate_timeframes_m1_to_m5() -> None:
    """Verify FR-DATA-AGGREGATE_TIMEFRAMES: M1 to M5 OHLCV reconciliation."""
    bars = _sample_m1_bars(count=10, start_minute=0)
    m5_bars = data_aggregate_timeframes(bars, target_timeframe="M5")

    assert len(m5_bars) == 2

    # First bucket (10:00 - 10:04)
    b0 = m5_bars[0]
    assert b0.timestamp == "2026-08-28T10:00:00.000000Z"
    assert b0.open == bars[0].open
    assert b0.close == bars[4].close
    assert Decimal(b0.high) == max(Decimal(b.high) for b in bars[:5])
    assert Decimal(b0.low) == min(Decimal(b.low) for b in bars[:5])
    assert Decimal(b0.volume) == Decimal(500)

    # Second bucket (10:05 - 10:09)
    b1 = m5_bars[1]
    assert b1.timestamp == "2026-08-28T10:05:00.000000Z"
    assert b1.open == bars[5].open
    assert b1.close == bars[9].close
    assert Decimal(b1.volume) == Decimal(500)


def test_data_aggregate_timeframes_m1_to_h1() -> None:
    """Verify FR-DATA-AGGREGATE_TIMEFRAMES: M1 to H1 OHLCV reconciliation."""
    bars = _sample_m1_bars(count=60, start_minute=0)
    h1_bars = data_aggregate_timeframes(bars, target_timeframe="H1")

    assert len(h1_bars) == 1
    b0 = h1_bars[0]
    assert b0.timestamp == "2026-08-28T10:00:00.000000Z"
    assert b0.open == bars[0].open
    assert b0.close == bars[59].close
    assert Decimal(b0.volume) == Decimal(6000)


def test_data_aggregate_timeframes_empty() -> None:
    """Verify aggregation of empty sequence returns empty tuple."""
    assert data_aggregate_timeframes((), target_timeframe="M5") == ()


def test_data_aggregate_timeframes_session_boundaries() -> None:
    """Verify aggregation respects session boundaries without crossing."""
    # Create bars in session 1 (08:00 - 10:00) and session 2 (14:00 - 16:00)
    bars_s1 = [
        Bar(
            timestamp=f"2026-08-28T09:{m:02d}:00.000000Z",
            open="100",
            high="101",
            low="99",
            close="100.5",
            volume="100",
            source_sequence=m,
            flags=0,
        )
        for m in range(5)
    ]
    bars_s2 = [
        Bar(
            timestamp=f"2026-08-28T14:{m:02d}:00.000000Z",
            open="105",
            high="106",
            low="104",
            close="105.5",
            volume="100",
            source_sequence=m + 10,
            flags=0,
        )
        for m in range(5)
    ]
    all_bars = tuple(bars_s1 + bars_s2)
    aggregated = data_aggregate_timeframes(
        all_bars,
        target_timeframe="M5",
        alignment_origin="SESSION_BOUNDARY",
        session_start_hour=8,
        session_end_hour=16,
    )
    # Aggregated bars should be partitioned cleanly into two separate session buckets
    assert len(aggregated) == 2
    assert aggregated[0].timestamp == "2026-08-28T09:00:00.000000Z"
    assert aggregated[1].timestamp == "2026-08-28T14:00:00.000000Z"
    assert Decimal(aggregated[0].volume) == Decimal(500)
    assert Decimal(aggregated[1].volume) == Decimal(500)


def test_data_record_aggregation_lineage_hash() -> None:
    """Verify FR-DATA-RECORD_AGGREGATION_LINEAGE: deterministic hash and policy sensitivity."""
    tf = Timeframe(unit="MINUTE", multiple=5)
    spec = AggregationSpec(
        spec_id=_generate_uuid7(),
        source_version_id=_generate_uuid7(),
        target_timeframe=tf,
        session_version_id=_generate_uuid7(),
        calendar_version_id=_generate_uuid7(),
        timezone="UTC",
        alignment_origin="UTC_MIDNIGHT",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="1.0.0",
    )
    derived_id_1, hash_1 = data_record_aggregation_lineage(spec)
    derived_id_1_repeat, hash_1_repeat = data_record_aggregation_lineage(spec)

    assert derived_id_1 == derived_id_1_repeat
    assert hash_1 == hash_1_repeat

    # Change algorithm version
    spec_mod_algo = AggregationSpec(
        spec_id=spec.spec_id,
        source_version_id=spec.source_version_id,
        target_timeframe=tf,
        session_version_id=spec.session_version_id,
        calendar_version_id=spec.calendar_version_id,
        timezone="UTC",
        alignment_origin="UTC_MIDNIGHT",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="2.0.0",
    )
    _, hash_mod_algo = data_record_aggregation_lineage(spec_mod_algo)
    assert hash_1 != hash_mod_algo

    # Change timezone
    spec_mod_tz = AggregationSpec(
        spec_id=spec.spec_id,
        source_version_id=spec.source_version_id,
        target_timeframe=tf,
        session_version_id=spec.session_version_id,
        calendar_version_id=spec.calendar_version_id,
        timezone="America/New_York",
        alignment_origin="UTC_MIDNIGHT",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="1.0.0",
    )
    _, hash_mod_tz = data_record_aggregation_lineage(spec_mod_tz)
    assert hash_1 != hash_mod_tz


@pytest.mark.asyncio
async def test_service_aggregate_bars_success() -> None:
    """Verify successful bar aggregation request handling by service."""
    service = BarAggregationService()
    spec = AggregationSpec(
        spec_id=_generate_uuid7(),
        source_version_id=_generate_uuid7(),
        target_timeframe=Timeframe(unit="MINUTE", multiple=5),
        session_version_id=None,
        calendar_version_id=None,
        timezone="UTC",
        alignment_origin="UTC_MIDNIGHT",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="1.0.0",
    )
    req = AggregateBarsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="AGGREGATE",
        spec=spec,
    )
    result = await service.aggregate_bars(req)
    assert isinstance(result, AggregateBarsSuccess)
    assert result.outcome == "SUCCESS"
    assert result.derived_version_id is not None
    assert result.spec == spec


@pytest.mark.asyncio
async def test_service_validate_timeframe_success() -> None:
    """Verify timeframe validation operation through service."""
    service = BarAggregationService()
    req = AggregateBarsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="VALIDATE_TIMEFRAME",
        target_timeframe=Timeframe(unit="MINUTE", multiple=10),
    )
    result = await service.aggregate_bars(req)
    assert isinstance(result, AggregateBarsSuccess)
    assert result.outcome == "SUCCESS"


@pytest.mark.asyncio
async def test_service_validate_timeframe_failure() -> None:
    """Verify DataFailure on invalid timeframe through service."""
    service = BarAggregationService()
    req = AggregateBarsRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="VALIDATE_TIMEFRAME",
        target_timeframe=Timeframe.model_construct(unit="MINUTE", multiple=0),
    )
    result = await service.aggregate_bars(req)
    assert isinstance(result, DataFailure)
    assert result.code == "DATA_VALIDATION_FAILED"
    assert "multiple must be >= 1" in result.problem.detail


@pytest.mark.asyncio
async def test_service_unsupported_operation() -> None:
    """Verify DataFailure on unsupported operation."""
    service = BarAggregationService()
    req = AggregateBarsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="UNKNOWN_OP",
        schema_version=1,
    )
    result = await service.aggregate_bars(req)
    assert isinstance(result, DataFailure)
    assert result.code == "DATA_VALIDATION_FAILED"
    assert "not supported" in result.problem.detail


def test_format_decimal_zero() -> None:
    """Verify _format_decimal handles zero correctly."""
    assert _format_decimal(0) == "0"
    assert _format_decimal("0") == "0"


def test_validate_multiple_bounds_max() -> None:
    """Verify _validate_multiple_bounds rejects multiples exceeding maximum."""
    with pytest.raises(ValueError, match="exceeds maximum limit"):
        _validate_multiple_bounds(1_000_001)


def test_parse_timeframe_dict_errors() -> None:
    """Verify _parse_timeframe_dict raises ValueError on invalid input."""
    with pytest.raises(ValueError, match="Unsupported timeframe unit"):
        _parse_timeframe_dict({"unit": "YEAR", "multiple": 1})
    with pytest.raises(ValueError, match="Invalid timeframe multiple"):
        _parse_timeframe_dict({"unit": "MINUTE", "multiple": "invalid"})


def test_parse_timeframe_str_errors() -> None:
    """Verify _parse_timeframe_str raises ValueError on empty or unknown string."""
    with pytest.raises(ValueError, match="Timeframe string cannot be empty"):
        _parse_timeframe_str("   ")
    with pytest.raises(ValueError, match="Invalid timeframe representation"):
        _parse_timeframe_str("UNKNOWN123")


def test_define_custom_timeframes_type_error() -> None:
    """Verify data_define_custom_timeframes raises TypeError on invalid types."""
    with pytest.raises(TypeError, match="Expected str, dict, or Timeframe"):
        data_define_custom_timeframes(12345)  # type: ignore[arg-type]


def test_get_bucket_start_calculations() -> None:
    """Verify _get_bucket_start for multiple units and session boundaries."""
    from datetime import UTC, datetime

    dt = datetime(2026, 8, 28, 10, 30, 0, tzinfo=UTC)

    # Session boundary with anchor > dt (anchor at 14:00, so previous day 14:00)
    b_session = _get_bucket_start(
        dt,
        Timeframe(unit="MINUTE", multiple=60),
        alignment_origin="SESSION_BOUNDARY",
        session_start_hour=14,
    )
    assert b_session.hour == 10

    # DAY multiple=1 and multiple=2
    b_day1 = _get_bucket_start(dt, Timeframe(unit="DAY", multiple=1))
    assert b_day1 == datetime(2026, 8, 28, 0, 0, 0, tzinfo=UTC)
    b_day2 = _get_bucket_start(dt, Timeframe(unit="DAY", multiple=2))
    assert b_day2 <= dt

    # WEEK multiple=1 and multiple=2
    b_week1 = _get_bucket_start(dt, Timeframe(unit="WEEK", multiple=1))
    assert b_week1.weekday() == 0
    b_week2 = _get_bucket_start(dt, Timeframe(unit="WEEK", multiple=2))
    assert b_week2 <= dt

    # MONTH multiple=1 and multiple=3
    b_month1 = _get_bucket_start(dt, Timeframe(unit="MONTH", multiple=1))
    assert b_month1 == datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
    b_month3 = _get_bucket_start(dt, Timeframe(unit="MONTH", multiple=3))
    assert b_month3 <= dt


@pytest.mark.asyncio
async def test_service_missing_field_failures() -> None:
    """Verify DataFailure when required fields are missing in service operations."""
    service = BarAggregationService()

    # VALIDATE_TIMEFRAME without target_timeframe
    req_val = AggregateBarsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="VALIDATE_TIMEFRAME",
        target_timeframe=None,
        schema_version=1,
    )
    res_val = await service.aggregate_bars(req_val)
    assert isinstance(res_val, DataFailure)
    assert res_val.code == "DATA_VALIDATION_FAILED"
    assert "requires target_timeframe" in res_val.problem.detail

    # AGGREGATE without spec
    req_agg = AggregateBarsRequest.model_construct(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="AGGREGATE",
        spec=None,
        schema_version=1,
    )
    res_agg = await service.aggregate_bars(req_agg)
    assert isinstance(res_agg, DataFailure)
    assert res_agg.code == "DATA_VALIDATION_FAILED"
    assert "requires spec" in res_agg.problem.detail


@pytest.mark.asyncio
async def test_main_scenario_harness() -> None:
    """Verify execution of the main scenario harness."""
    await main()


def test_bar_aggregation_persistence() -> None:
    """Verify BarAggregationPersistence methods."""
    from app.services.data.bar_aggregation._persistence import (
        BarAggregationPersistence,
    )
    from app.services.data.bar_aggregation.bar_aggregation import AggregationSpec

    store = BarAggregationPersistence()
    tf = Timeframe(unit="MINUTE", multiple=5)
    store.register_timeframe("M5", tf)
    assert store.get_timeframe("M5") == tf
    assert store.get_timeframe("unknown") is None

    spec = AggregationSpec(
        spec_id=_generate_uuid7(),
        source_version_id=_generate_uuid7(),
        target_timeframe=tf,
        session_version_id=None,
        calendar_version_id=None,
        timezone="UTC",
        alignment_origin="UTC_MIDNIGHT",
        gap_policy="ABSENT_EMPTY",
        algorithm_version="1.0.0",
    )
    derived_id = _generate_uuid7()
    store.record_lineage(spec, derived_id, "0" * 64)
    assert store.get_lineage(spec.spec_id) == (derived_id, "0" * 64)

    store.clear()
    assert store.get_timeframe("M5") is None
