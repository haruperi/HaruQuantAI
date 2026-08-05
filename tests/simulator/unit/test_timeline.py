"""Unit tests for Simulation timeline construction and timing."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_tick_record,
)
from app.services.simulator.errors import SimulationError
from app.services.simulator.timeline import build_tick_timeline, validate_intent_timing


def _dataset() -> object:
    """Build a valid two-tick dataset."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    records = tuple(
        build_tick_record(
            timestamp=start + timedelta(seconds=index),
            source="fixture",
            source_symbol="EURUSD",
            available_at=start + timedelta(seconds=index),
            bid=Decimal("1.10000") + Decimal(index) / Decimal(100_000),
            ask=Decimal("1.10002") + Decimal(index) / Decimal(100_000),
            last=None,
            volume=Decimal(2),
            price_unit="quote",
            volume_unit="lot",
        )
        for index in range(2)
    )
    quality = build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=2,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=2,
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-22222222-2222-4222-8222-222222222222",
    )


def test_build_tick_timeline_is_deterministic() -> None:
    """Build byte-equivalent immutable clocks from identical input."""
    first = build_tick_timeline(_dataset())
    second = build_tick_timeline(_dataset())
    assert first == second
    assert tuple(tick.sequence for tick in first) == (0, 1)


def test_validate_intent_timing_blocks_lookahead() -> None:
    """Reject evidence from after the execution tick."""
    execution = datetime(2025, 1, 1, tzinfo=UTC)
    with pytest.raises(SimulationError) as captured:
        validate_intent_timing(execution + timedelta(microseconds=1), execution)
    assert captured.value.code == "SIM_FEATURE_LOOKAHEAD_DETECTED"


def test_validate_intent_timing_accepts_visible_evidence() -> None:
    """Accept evidence already visible at the execution tick."""
    execution = datetime(2025, 1, 1, tzinfo=UTC)
    validate_intent_timing(execution, execution)


def test_timeline_rejects_unsupported_and_malformed_datasets() -> None:
    """Reject unsupported models, non-ticks, missing spread, and incomplete bars."""
    dataset = _dataset()
    unsupported = dataset.model_copy(
        update={"source_metadata": {"tick_generation_model": "invented"}}
    )
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(unsupported)
    assert captured.value.code == "SIM_UNSUPPORTED_TICK_MODEL"
    malformed = dataset.model_copy(update={"records": (object(),)})
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(malformed)
    assert captured.value.code == "SIM_DATA_SCHEMA_INVALID"
    no_spread = dataset.records[0].model_copy(update={"bid": None, "ask": None})
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(dataset.model_copy(update={"records": (no_spread,)}))
    assert captured.value.code == "SIM_SPREAD_MISSING"
    derived = dataset.model_copy(
        update={"source_metadata": {"tick_generation_model": "trading_bar"}}
    )
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(derived)
    assert captured.value.code == "SIM_DATA_SCHEMA_INVALID"


def test_timeline_rejects_invalid_price_and_timestamp_order() -> None:
    """Reject invalid tick contracts, non-monotonic order, and duplicates."""
    dataset = _dataset()
    invalid = dataset.records[0].model_copy(
        update={"bid": Decimal("1.2"), "ask": Decimal("1.1")}
    )
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(dataset.model_copy(update={"records": (invalid,)}))
    assert captured.value.code == "SIM_INVALID_PRICE"
    reversed_records = tuple(reversed(dataset.records))
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(dataset.model_copy(update={"records": reversed_records}))
    assert captured.value.code == "SIM_DATA_NON_MONOTONIC"
    duplicate = dataset.records[1].model_copy(
        update={"timestamp": dataset.records[0].timestamp}
    )
    with pytest.raises(SimulationError) as captured:
        build_tick_timeline(
            dataset.model_copy(update={"records": (dataset.records[0], duplicate)})
        )
    assert captured.value.code == "SIM_DATA_DUPLICATE_TIMESTAMP"


def test_validate_intent_timing_rejects_naive_time() -> None:
    """Reject timing evidence without an aware UTC offset."""
    with pytest.raises(SimulationError) as captured:
        validate_intent_timing(
            datetime(2025, 1, 1),  # noqa: DTZ001 - deliberately invalid evidence.
            datetime(2025, 1, 1, tzinfo=UTC),
        )
    assert captured.value.code == "SIM_INVALID_CONFIG"
