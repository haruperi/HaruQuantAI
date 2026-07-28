"""Executable Simulation accounting usage example.

Demonstrates volume normalization, execution cost calculation, margin
computation, and FX conversion.
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
from app.services.simulator import (
    AccountLedger,
    ExecutionCostInput,
    ExecutionCostModel,
    LedgerFill,
    SymbolSpecification,
    calculate_execution_costs,
    calculate_margin,
    convert_fx_amount,
    normalize_volume,
    unwrap_simulation_response,
    validate_fx_evidence,
)


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.accounting")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def _ledger() -> AccountLedger:
    """Build one isolated fixed-precision account ledger."""
    return AccountLedger(Decimal(10_000), "USD", _specification(), _model())


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


def fr_sim_007() -> None:
    """Demonstrate FR-SIM-007.

    Responsibility:
        The system shall verify that the final approved volume is finite, positive, and
        within symbol min/max/step constraints without increasing, decreasing, or
        otherwise re-sizing it.
    """
    _header(
        "Demonstrate FR-SIM-007. Responsibility: The system shall verify that the final approved volume is finite, positive, and within symbol min/max/step constraints without increasing, decreasing, or otherwise re-sizing it."
    )
    spec = _specification()
    norm_vol = _value(normalize_volume(Decimal(1), spec))
    print(f"Normalized volume: {norm_vol}")


def fr_sim_008() -> None:
    """Demonstrate FR-SIM-008.

    Responsibility:
        The system shall calculate configured Phase 1 commission and swap
        deterministically and return an itemized fixed-precision cost mapping.
    """
    _header(
        "Demonstrate FR-SIM-008. Responsibility: The system shall calculate configured Phase 1 commission and swap deterministically and return an itemized fixed-precision cost mapping."
    )
    cost_input = ExecutionCostInput(
        volume=Decimal(1), side="BUY", rollover_multiplier=Decimal(0)
    )
    costs = _value(calculate_execution_costs(cost_input, _model()))
    print(f"Execution costs commission: {costs['commission']}")


def fr_sim_009() -> None:
    """Demonstrate FR-SIM-009.

    Responsibility:
        The system shall calculate required FX margin from approved symbol evidence,
        price, volume, and leverage, rejecting insufficient free margin before a fill.
    """
    _header(
        "Demonstrate FR-SIM-009. Responsibility: The system shall calculate required FX margin from approved symbol evidence, price, volume, and leverage, rejecting insufficient free margin before a fill."
    )
    margin = _value(
        calculate_margin(Decimal(1), Decimal(1), Decimal(100_000), Decimal(100))
    )
    print(f"Calculated margin: {margin}")


def fr_sim_010() -> None:
    """Demonstrate FR-SIM-010.

    Responsibility:
        The system shall accept only fresh, schema-compatible Data-owned
        `FXConversionEvidence v1` for conversion-dependent accounting, and shall never
        choose, synthesize, refresh, or fetch a rate path.
    """
    _header(
        "Demonstrate FR-SIM-010. Responsibility: The system shall accept only fresh, schema-compatible Data-owned `FXConversionEvidence v1` for conversion-dependent accounting, and shall never choose, synthesize, refresh, or fetch a rate path."
    )
    evidence = _evidence()
    validated = _value(validate_fx_evidence(evidence, as_of=evidence.as_of))
    print(f"Validated FX evidence hash: {validated.evidence_hash}")


def fr_sim_039() -> None:
    """Demonstrate FR-SIM-039.

    Responsibility:
        The system shall convert one monetary amount using only the composite rate
        carried by validated `FXConversionEvidence v1`, preserving fixed precision and
        rejecting any conversion whose evidence was not first validated.
    """
    _header(
        "Demonstrate FR-SIM-039. Responsibility: The system shall convert one monetary amount using only the composite rate carried by validated `FXConversionEvidence v1`, preserving fixed precision and rejecting any conversion whose evidence was not first validated."
    )
    evidence = _evidence()
    validated = _value(validate_fx_evidence(evidence, as_of=evidence.as_of))
    converted = _value(convert_fx_amount(Decimal(10), validated))
    print(f"Converted 10 USD to EUR: {converted}")


def fr_sim_011() -> None:
    """Demonstrate FR-SIM-011.

    Responsibility:
        The system shall atomically apply a simulated fill, realized PnL, commission,
        swap, and margin effect while preserving balance/equity/free-margin invariants,
        accumulating commission, swap, and gross-profit totals, and returning the
        itemized costs charged by that fill so the caller can attribute them to the
        exact position. The engine journals the resulting evidence; the ledger itself
        publishes no event.
    """
    _header(
        "Demonstrate FR-SIM-011. Responsibility: The system shall atomically apply a simulated fill, realized PnL, commission, swap, and margin effect while preserving balance/equity/free-margin invariants, accumulating commission, swap, and gross-profit totals, and returning the itemized costs charged by that fill so the caller can attribute them to the exact position. The engine journals the resulting evidence; the ledger itself publishes no event."
    )
    costs = _value(
        _ledger().apply_fill(
            LedgerFill(
                action="OPEN",
                side="BUY",
                volume=Decimal(1),
                price=Decimal("1.1"),
            )
        )
    )
    print(f"Applied fill total costs: {costs['total']}")


def fr_sim_012() -> None:
    """Demonstrate FR-SIM-012.

    Responsibility:
        The system shall return an immutable read-only fixed-precision account snapshot
        without exposing mutable engine state. The snapshot exposes `balance`, `equity`,
        `used_margin`, `free_margin`, `unrealized`, `commission`, `swap`,
        `gross_profit`, and `account_currency`. `equity` is `balance + unrealized` and
        `free_margin` is `equity - used_margin`, so open-position risk is reflected
        before the next fill is admitted.
    """
    _header(
        "Demonstrate FR-SIM-012. Responsibility: The system shall return an immutable read-only fixed-precision account snapshot without exposing mutable engine state. The snapshot exposes `balance`, `equity`, `used_margin`, `free_margin`, `unrealized`, `commission`, `swap`, `gross_profit`, and `account_currency`. `equity` is `balance + unrealized` and `free_margin` is `equity - used_margin`, so open-position risk is reflected before the next fill is admitted."
    )
    snapshot = _value(_ledger().snapshot())
    print(f"Account equity: {snapshot['equity']}")


def fr_sim_042() -> None:
    """Demonstrate FR-SIM-042.

    Responsibility:
        The system shall accept the current aggregate unrealized profit and loss of all
        open positions, so that equity, free margin, and margin admission reflect open
        exposure at the current tick. The engine supplies it once per tick from observed
        excursions; Simulation computes no price of its own.
    """
    _header(
        "Demonstrate FR-SIM-042. Responsibility: The system shall accept the current aggregate unrealized profit and loss of all open positions, so that equity, free margin, and margin admission reflect open exposure at the current tick. The engine supplies it once per tick from observed excursions; Simulation computes no price of its own."
    )
    ledger = _ledger()
    _value(ledger.mark_to_market(Decimal(-25)))
    print(f"Marked equity: {_value(ledger.snapshot())['equity']}")


def main() -> None:
    """Run Simulator accounting usage example."""
    fr_sim_007()
    fr_sim_008()
    fr_sim_009()
    fr_sim_010()
    fr_sim_011()
    fr_sim_012()
    fr_sim_039()
    fr_sim_042()


if __name__ == "__main__":
    main()
