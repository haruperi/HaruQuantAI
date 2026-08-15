"""Unit evidence for independent source and tick market lineage."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    build_tick_record,
)
from app.services.simulator import validate_market_evidence_lineage

NOW = datetime(2026, 8, 15, 10, tzinfo=UTC)


def _quality(count: int) -> object:
    """Build accepted deterministic data quality evidence."""
    return build_data_quality_report(
        quality_status="perfect",
        quality_decision="accepted",
        quality_score=Decimal(100),
        record_count=count,
        checked_count=count,
        truncated=False,
        sample_limit=count,
        schema_version="v1",
        generated_at=NOW,
    )


def source_dataset(*, close: Decimal = Decimal("1.101")) -> object:
    """Build one Data-owned source-bar dataset."""
    record = build_ohlcv_record(
        timestamp=NOW,
        source="fixture",
        source_symbol="EURUSD",
        available_at=NOW + timedelta(minutes=1),
        open=Decimal("1.100"),
        high=Decimal("1.102"),
        low=Decimal("1.099"),
        close=close,
        volume=Decimal(10),
        price_unit="quote",
        volume_unit="ticks",
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="bars",
        symbol="EURUSD",
        timeframe="M1",
        records=(record,),
        start=NOW,
        end=NOW,
        available_at=record.available_at,
        record_count=1,
        quality_report=_quality(1),
        source_metadata={"source": "fixture"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-11111111-1111-4111-8111-111111111111",
    )


def tick_dataset(
    *, model: str = "real", available_at: datetime | None = None
) -> object:
    """Build one Data-owned tick dataset."""
    available = available_at or NOW + timedelta(minutes=1)
    record = build_tick_record(
        timestamp=NOW,
        source="fixture",
        source_symbol="EURUSD",
        available_at=available,
        bid=Decimal("1.1000"),
        ask=Decimal("1.1002"),
        last=Decimal("1.1001"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="lot",
        source_bar_time=None if model == "real" else NOW,
        tick_index_in_bar=None if model == "real" else 0,
        bar_phase=None if model == "real" else 1,
    )
    return build_market_dataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=(record,),
        start=NOW,
        end=NOW,
        available_at=available,
        record_count=1,
        quality_report=_quality(1),
        source_metadata={"tick_generation_model": model},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-22222222-2222-4222-8222-222222222222",
    )


def _validate(source: object, ticks: object, **overrides: object) -> object:
    """Call the public lineage validator with a complete clock fixture."""
    fields = {
        "decision_instant": NOW + timedelta(minutes=2),
        "runtime_profile": "simulation",
        "path_sensitive": True,
        "required_clock_edges": ("availability", "decision", "provider_event"),
        "clock_edges": {
            "provider_event": NOW,
            "availability": NOW + timedelta(minutes=1),
            "decision": NOW + timedelta(minutes=2),
        },
    }
    fields.update(overrides)
    return validate_market_evidence_lineage(source, ticks, **fields)


def test_fr_sim_136_hashes_source_and_ticks_independently() -> None:
    """FR-SIM-136: independent canonical identities are stable and sensitive."""
    first = _validate(source_dataset(), tick_dataset()).data
    changed = _validate(source_dataset(close=Decimal("1.1015")), tick_dataset()).data
    assert first.source_lineage_hash != changed.source_lineage_hash
    assert first.tick_lineage_hash == changed.tick_lineage_hash
    assert first.market_evidence_class == "genuine_bid_ask_ticks"


def test_derived_bar_path_is_rejected_for_path_sensitive_parity() -> None:
    """Derived OHLC paths cannot certify path-dependent execution behavior."""
    result = _validate(source_dataset(), tick_dataset(model="ohlc_m1"))
    assert result.status == "error"
    assert result.error.code == "SIM_UNSUPPORTED_TICK_MODEL"


def test_tick_model_change_changes_tick_identity() -> None:
    """A named tick-model change changes the tick lineage hash."""
    real = _validate(source_dataset(), tick_dataset()).data
    derived = _validate(
        source_dataset(),
        tick_dataset(model="ohlc_m1"),
        runtime_profile="fast_research",
        path_sensitive=False,
    ).data
    assert real.tick_lineage_hash != derived.tick_lineage_hash
    assert derived.market_evidence_class == "derived_bar_model"


@pytest.mark.parametrize(
    "defect", ["duplicate", "reordered", "missing", "naive", "nan", "ohlc"]
)
def test_source_record_integrity_defects_fail_closed(defect: str) -> None:
    """Reordering, duplication, gaps, timezone, numeric, and OHLC defects fail."""
    source = source_dataset()
    first = source.records[0]
    if defect == "duplicate":
        source = source.model_copy(
            update={"records": (first, first), "record_count": 2}
        )
    elif defect == "reordered":
        later = first.model_copy(
            update={
                "timestamp": NOW + timedelta(minutes=1),
                "available_at": NOW + timedelta(minutes=1),
            }
        )
        source = source.model_copy(
            update={"records": (later, first), "record_count": 2}
        )
    elif defect == "missing":
        source = source.model_copy(update={"record_count": 2})
    elif defect == "naive":
        source = source.model_copy(
            update={
                "records": (
                    first.model_copy(update={"timestamp": NOW.replace(tzinfo=None)}),
                )
            }
        )
    elif defect == "nan":
        source = source.model_copy(
            update={"records": (first.model_copy(update={"close": Decimal("NaN")}),)}
        )
    else:
        source = source.model_copy(
            update={"records": (first.model_copy(update={"close": Decimal("1.2")}),)}
        )
    assert _validate(source, tick_dataset()).status == "error"


def test_explicit_depth_class_is_preserved() -> None:
    """Depth-supported evidence remains a distinct declared class."""
    ticks = tick_dataset().model_copy(
        update={
            "source_metadata": {
                "tick_generation_model": "real",
                "market_evidence_class": "depth_supported_ticks",
            }
        }
    )
    evidence = _validate(source_dataset(), ticks).data
    assert evidence.market_evidence_class == "depth_supported_ticks"
