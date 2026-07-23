"""Unit tests for Simulation timeline construction and timing."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    TickRecord,
)
from app.services.simulator.errors import SimulationError
from app.services.simulator.timeline import build_tick_timeline, validate_intent_timing


def _dataset() -> MarketDataset:
    """Build a valid two-tick dataset."""
    start = datetime(2025, 1, 1, tzinfo=UTC)
    records = tuple(
        TickRecord(
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
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=2,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
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
