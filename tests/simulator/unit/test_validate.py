"""Unit tests for Simulation boundary validation."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    OHLCVRecord,
    TickRecord,
)
from app.services.simulator.errors import SimulationError
from app.services.simulator.validation.contracts import MarketDataValidationContext
from app.services.simulator.validation.validate import (
    validate_market_data,
    validate_phase_one_scope,
    validate_run_inputs,
)
from app.utils import canonical_json


def _dataset() -> MarketDataset:
    """Build one valid Data-owned tick dataset."""
    instant = datetime(2025, 1, 2, 12, tzinfo=UTC)
    record = TickRecord(
        timestamp=instant,
        source="fixture",
        source_symbol="EURUSD",
        available_at=instant,
        bid=Decimal("1.10000"),
        ask=Decimal("1.10002"),
        last=Decimal("1.10001"),
        volume=Decimal(2),
        price_unit="quote",
        volume_unit="lot",
        source_bar_time=instant,
        tick_index_in_bar=0,
        bar_phase=1,
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=1,
        schema_version="v1",
        generated_at=instant,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=(record,),
        start=instant,
        end=instant,
        available_at=instant,
        record_count=1,
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-11111111-1111-4111-8111-111111111111",
    )


def _context(dataset: MarketDataset) -> MarketDataValidationContext:
    """Build matching explicit validation evidence."""
    digest = sha256(
        canonical_json(dataset.model_dump(mode="python", warnings=False)).encode(
            "utf-8"
        )
    ).hexdigest()
    return MarketDataValidationContext(
        expected_data_hash=digest,
        requested_start=dataset.start,
        requested_end=dataset.end,
        evaluated_at=dataset.available_at,
        maximum_staleness=timedelta(0),
        allowed_tick_models=("real",),
    )


def _valid_payload() -> dict[str, object]:
    """Build the required reference-only request projection."""
    return {
        "request_id": "req-simulator-validation",
        "workflow_id": "wf-simulator-validation",
        "correlation_id": "cor-simulator-validation",
        "strategy_id": "strategy",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "dataset",
        "data_version": "v1",
        "data_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "risk-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": "EURUSD",
        "config_hash": "e" * 64,
    }


def test_validate_run_inputs_rejects_raw_code() -> None:
    """Reject executable source before any import or execution."""
    payload = _valid_payload() | {"source_code": "raise SystemExit"}
    with pytest.raises(SimulationError, match="Raw code") as captured:
        validate_run_inputs(payload)
    assert captured.value.code == "SIM_ARBITRARY_CODE_REJECTED"


def test_validate_market_data_blocks_invalid_ohlc() -> None:
    """Reject a tampered dataset before execution."""
    dataset = _dataset()
    invalid_record = OHLCVRecord.model_construct(
        timestamp=dataset.start,
        source="fixture",
        source_symbol="EURUSD",
        available_at=dataset.start,
        open=Decimal(2),
        high=Decimal(1),
        low=Decimal(0),
        close=Decimal("0.5"),
        volume=Decimal(1),
        price_unit="quote",
        volume_unit="lot",
    )
    tampered = dataset.model_copy(update={"records": (invalid_record,)})
    context = _context(tampered)
    with pytest.raises(SimulationError) as captured:
        validate_market_data(tampered, context)
    assert captured.value.code == "SIM_DATA_OHLC_INVALID"


def test_validate_market_data_returns_evidence() -> None:
    """Return immutable proof for matching market evidence."""
    dataset = _dataset()
    evidence = validate_market_data(dataset, _context(dataset))
    assert evidence.record_count == 1
    assert evidence.tick_model == "real"


def test_validate_phase_one_scope_rejects_unsupported_asset() -> None:
    """Reject non-FX official scope."""
    with pytest.raises(SimulationError) as captured:
        validate_phase_one_scope(
            {
                "asset_class": "EQUITY",
                "runtime_profile": "simulation",
                "execution_route": "sim",
            }
        )
    assert captured.value.code == "SIM_UNSUPPORTED_ASSET_CLASS"


def test_validate_run_inputs_accepts_reference_material() -> None:
    """Accept deterministic reference-only material."""
    validate_run_inputs(_valid_payload())


def test_validate_run_inputs_requires_symbol() -> None:
    """Return the exact missing-symbol code before execution."""
    payload = _valid_payload()
    del payload["symbol"]
    with pytest.raises(SimulationError) as captured:
        validate_run_inputs(payload)
    assert captured.value.code == "SIM_MISSING_SYMBOL"


def test_validate_run_inputs_rejects_reversed_date_range() -> None:
    """Return the exact invalid-range code before execution."""
    payload = _valid_payload() | {
        "start": datetime(2025, 1, 2, tzinfo=UTC),
        "end": datetime(2025, 1, 1, tzinfo=UTC),
    }
    with pytest.raises(SimulationError) as captured:
        validate_run_inputs(payload)
    assert captured.value.code == "SIM_INVALID_DATE_RANGE"


def test_validate_market_data_rejects_future_availability() -> None:
    """Return the general lookahead code for unavailable Data evidence."""
    dataset = _dataset()
    context = _context(dataset).model_copy(
        update={"evaluated_at": dataset.available_at - timedelta(seconds=1)}
    )
    with pytest.raises(SimulationError) as captured:
        validate_market_data(dataset, context)
    assert captured.value.code == "SIM_LOOKAHEAD_DETECTED"
