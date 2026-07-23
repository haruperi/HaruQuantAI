"""Executable Simulation validation usage example.

Demonstrates run input validation, phase-one scope validation, and market data validation.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    TickRecord,
)
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
    """Build matching validation context."""
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


def example_validation() -> None:
    """Demonstrate simulation validation operations."""
    print("=" * 80)
    print("Simulator Example 1: Boundary Validation")
    print("=" * 80)

    # 1. Run inputs validation
    payload = {
        "request_id": "req-simulator-usage",
        "workflow_id": "wf-simulator-usage",
        "correlation_id": "cor-simulator-usage",
        "strategy_id": "registered-strategy",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "market-data",
        "data_version": "v1",
        "data_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "sim-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": "EURUSD",
        "config_hash": "e" * 64,
    }
    validate_run_inputs(payload)
    print("Run inputs successfully validated")

    # 2. Phase one scope validation
    validate_phase_one_scope(
        {
            "asset_class": "FX",
            "runtime_profile": "simulation",
            "execution_route": "sim",
        }
    )
    print("Phase one scope successfully validated")

    # 3. Market data validation
    dataset = _dataset()
    evidence = validate_market_data(dataset, _context(dataset))
    print(f"Validated market data records: {evidence.record_count}")


def main() -> None:
    """Run Simulator validation usage example."""
    example_validation()


if __name__ == "__main__":
    main()
