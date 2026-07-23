"""Executable Simulation accounting usage example.

Demonstrates volume normalization, execution cost calculation, margin computation, and FX conversion.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data.evidence.fx_contracts import (
    FXConversionEvidence,
    FXRateLeg,
)
from app.services.simulator.accounting import (
    ExecutionCostInput,
    ExecutionCostModel,
    SymbolSpecification,
    calculate_execution_costs,
    calculate_margin,
    convert_fx_amount,
    normalize_volume,
    validate_fx_evidence,
)


def _specification() -> SymbolSpecification:
    """Build symbol specification."""
    return SymbolSpecification(
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100_000),
        leverage=Decimal(100),
    )


def _model() -> ExecutionCostModel:
    """Build execution cost model."""
    return ExecutionCostModel(
        commission_per_lot_per_side=Decimal(1),
        long_swap_per_lot_rollover=Decimal(0),
        short_swap_per_lot_rollover=Decimal(0),
    )


def _evidence() -> FXConversionEvidence:
    """Build FX conversion evidence."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    leg = FXRateLeg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="USDEUR",
        as_of=instant,
        provenance={"source": "fixture"},
    )
    return FXConversionEvidence(
        source_currency="USD",
        target_currency="EUR",
        legs=(leg,),
        composite_rate=Decimal("0.9"),
        as_of=instant,
        expires_at=instant + timedelta(hours=1),
        path_policy_id="direct",
        path_policy_version="v1",
        provenance={"source": "fixture"},
        request_id="req-44444444-4444-4444-8444-444444444444",
    )


def example_accounting() -> None:
    """Demonstrate accounting operations."""
    print("=" * 80)
    print("Simulator Example 4: Accounting and Cost Calculations")
    print("=" * 80)

    # 1. Volume normalization
    spec = _specification()
    norm_vol = normalize_volume(Decimal(1), spec)
    print(f"Normalized volume: {norm_vol}")

    # 2. Execution costs
    cost_input = ExecutionCostInput(
        volume=Decimal(1), side="BUY", rollover_multiplier=Decimal(0)
    )
    costs = calculate_execution_costs(cost_input, _model())
    print(f"Execution costs commission: {costs['commission']}")

    # 3. Margin calculation
    margin = calculate_margin(Decimal(1), Decimal(1), Decimal(100_000), Decimal(100))
    print(f"Calculated margin: {margin}")

    # 4. FX conversion
    evidence = _evidence()
    validated = validate_fx_evidence(evidence, as_of=evidence.as_of)
    converted = convert_fx_amount(Decimal(10), validated)
    print(f"Converted 10 USD to EUR: {converted}")


def main() -> None:
    """Run Simulator accounting usage example."""
    example_accounting()


if __name__ == "__main__":
    main()
