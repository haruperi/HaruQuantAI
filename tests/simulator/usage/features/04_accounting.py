"""Executable Simulation accounting usage example.

Demonstrates FEAT-SIM-04 volume normalization, cost calculation, margin requirement calculation, FX evidence validation, rate conversion, ledger fill execution, snapshot generation, and mark-to-market updating.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_fx_conversion_evidence, build_fx_rate_leg
from app.services.simulator import (
    build_transaction_posting,
    calculate_execution_costs,
    calculate_margin,
    convert_fx_amount,
    create_simulation_handle,
    create_simulation_value,
    create_transaction_ledger,
    execute_simulation_handle_operation,
    normalize_volume,
    post_transaction,
    restore_transaction_ledger,
    serialize_transaction_ledger,
    unwrap_simulation_response,
    validate_fx_evidence,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"SUCCESS: Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"SUCCESS: Output Result -> {type_name}({keys}) : {type_name}"
    return f"SUCCESS: Output Result -> {type_name} : {type_name}"


def _value(response: object) -> object:
    """Unwrap one public Simulation response for display."""
    return unwrap_simulation_response(response, operation="usage.accounting")


def _spec() -> object:
    """Build symbol specification."""
    return create_simulation_value(
        "SymbolSpecification",
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100_000),
        leverage=Decimal(100),
    )


def _cost_model() -> object:
    """Build execution cost model."""
    return create_simulation_value(
        "ExecutionCostModel",
        commission_per_lot_per_side=Decimal(1),
        long_swap_per_lot_rollover=Decimal(0),
        short_swap_per_lot_rollover=Decimal(0),
    )


def _ledger() -> object:
    """Build account ledger."""
    return create_simulation_handle(
        "AccountLedger", Decimal(10_000), "USD", _spec(), _cost_model()
    )


def fr_sim_007() -> None:
    """
    FR-SIM-007: Stage 1 — Normalize and validate volume against symbol specification.

    The system shall verify that the final approved volume is finite, positive, and within symbol min/max/step constraints without increasing, decreasing, or otherwise re-sizing it.
    """
    _header("Stage 1: Volume Verification - Normalize Volume (FR-SIM-007)")
    resp = normalize_volume(Decimal(1), _spec())
    vol = _value(resp)
    print(_format_result(resp))
    print(f"Data -> normalized_volume={vol}")


def fr_sim_008() -> None:
    """
    FR-SIM-008: Stage 2 — Calculate execution costs deterministically.

    The system shall calculate configured Phase 1 commission and swap deterministically and return an itemized fixed-precision cost mapping.
    """
    _header("Stage 2: Cost Calculation - Calculate Execution Costs (FR-SIM-008)")
    cost_input = create_simulation_value(
        "ExecutionCostInput",
        volume=Decimal(1),
        side="BUY",
        rollover_multiplier=Decimal(0),
    )
    resp = calculate_execution_costs(cost_input, _cost_model())
    costs = _value(resp)
    print(_format_result(resp))
    print(
        f"Data -> commission={getattr(costs, 'commission', None)}, swap={getattr(costs, 'swap', None)}"
    )


def fr_sim_009() -> None:
    """
    FR-SIM-009: Stage 2 — Calculate required margin from symbol specifications.

    The system shall calculate required FX margin from approved symbol evidence, price, volume, and leverage, rejecting insufficient free margin before a fill.
    """
    _header("Stage 2: Margin Calculation - Calculate Margin (FR-SIM-009)")
    resp = calculate_margin(Decimal(1), Decimal(1), Decimal(100_000), Decimal(100))
    margin = _value(resp)
    print(_format_result(resp))
    print(f"Data -> required_margin={margin}")


def fr_sim_010() -> None:
    """
    FR-SIM-010: Stage 2 — Validate schema-compatible FX conversion evidence.

    The system shall accept only fresh, schema-compatible Data-owned `FXConversionEvidence v1` for conversion-dependent accounting, and shall never choose, synthesize, refresh, or fetch a rate path.
    """
    _header("Stage 2: FX Validation - Validate FX Conversion Evidence (FR-SIM-010)")
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    leg = build_fx_rate_leg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="USDEUR",
        as_of=instant,
        provenance={"source": "fixture"},
    )
    evidence = build_fx_conversion_evidence(
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
    resp = validate_fx_evidence(evidence, as_of=instant)
    _value(resp)
    print(_format_result(resp))
    print(f"Data -> fx_validation_status='{resp.status}'")


def fr_sim_039() -> None:
    """
    FR-SIM-039: Stage 2 — Convert monetary amount using validated FX rate.

    The system shall convert one monetary amount using only the composite rate carried by validated `FXConversionEvidence v1`, preserving fixed precision and rejecting any conversion whose evidence was not first validated.
    """
    _header("Stage 2: Rate Conversion - Convert FX Amount (FR-SIM-039)")
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    leg = build_fx_rate_leg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="USDEUR",
        as_of=instant,
        provenance={"source": "fixture"},
    )
    evidence = build_fx_conversion_evidence(
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
    validated = _value(validate_fx_evidence(evidence, as_of=instant))
    resp = convert_fx_amount(Decimal(10), validated)
    converted = _value(resp)
    print(_format_result(resp))
    print(f"Data -> converted_amount={converted}")


def fr_sim_011() -> None:
    """
    FR-SIM-011: Stage 3 — Atomically apply fill to account ledger.

    The system shall atomically apply a simulated fill, realized PnL, commission, swap, and margin effect while preserving balance/equity/free-margin invariants, accumulating commission, swap, and gross-profit totals, and returning the itemized costs charged by that fill so the caller can attribute them to the exact position. The engine journals the resulting evidence; the ledger itself publishes no event.
    """
    _header("Stage 3: Fill Application - Apply Fill to AccountLedger (FR-SIM-011)")
    fill = create_simulation_value(
        "LedgerFill",
        action="OPEN",
        side="BUY",
        volume=Decimal(1),
        price=Decimal("1.1"),
    )
    resp = execute_simulation_handle_operation(_ledger(), "apply_fill", fill)
    costs = _value(resp)
    print(_format_result(resp))
    print(
        f"Data -> fill_costs_commission={costs.get('commission') if isinstance(costs, dict) else costs}"
    )


def fr_sim_012() -> None:
    """
    FR-SIM-012: Stage 3 — Expose read-only fixed-precision account snapshot.

    The system shall return an immutable read-only fixed-precision account snapshot without exposing mutable engine state. The snapshot exposes `balance`, `equity`, `used_margin`, `free_margin`, `unrealized`, `commission`, `swap`, `gross_profit`, and `account_currency`. `equity` is `balance + unrealized` and `free_margin` is `equity - used_margin`, so open-position risk is reflected before the next fill is admitted.
    """
    _header("Stage 3: Account Snapshot - AccountLedger Snapshot (FR-SIM-012)")
    resp = execute_simulation_handle_operation(_ledger(), "snapshot")
    snapshot = _value(resp)
    print(_format_result(resp))
    print(
        f"Data -> balance={snapshot['balance'] if isinstance(snapshot, dict) else None}"
    )


def fr_sim_042() -> None:
    """
    FR-SIM-042: Stage 3 — Update aggregate unrealized PnL and mark to market.

    The system shall accept the current aggregate unrealized profit and loss of all open positions, so that equity, free margin, and margin admission reflect open exposure at the current tick. The engine supplies it once per tick from observed excursions; Simulation computes no price of its own.
    """
    _header("Stage 3: Mark to Market - Update Unrealized PnL (FR-SIM-042)")
    ledger = _ledger()
    resp = execute_simulation_handle_operation(ledger, "mark_to_market", Decimal(-25))
    snap = _value(execute_simulation_handle_operation(ledger, "snapshot"))
    print(_format_result(resp))
    print(
        f"Data -> updated_equity={snap['equity'] if isinstance(snap, dict) else None}"
    )


def _posting(kind: str, amount: Decimal, sequence: int) -> object:
    """Build one fixed evidence-backed transaction posting."""
    instant = datetime(2026, 8, 12, sequence, tzinfo=UTC)
    return build_transaction_posting(
        economic_at=instant,
        source_at=instant,
        account_currency="USD",
        amount=amount,
        kind=kind,
        source_sequence=sequence,
        evidence_reference=f"provider-ledger-fixture:{sequence}",
        causal_deal_id=f"deal-{sequence}",
    )


def fr_sim_179() -> None:
    """FR-SIM-179: Post named account transactions to the signed ledger."""
    ledger = create_transaction_ledger(Decimal(1000), "USD")
    snapshot = post_transaction(ledger, _posting("profit", Decimal(25), 1))
    print(f"Data -> named_transaction_balance={snapshot['balance']}")


def fr_sim_180() -> None:
    """FR-SIM-180: Bind dynamic costs to explicit provider evidence."""
    ledger = create_transaction_ledger(Decimal(1000), "USD")
    posting = _posting("commission", Decimal("-2.50"), 1)
    snapshot = post_transaction(ledger, posting)
    evidence = snapshot["postings"][0]["evidence_reference"]
    print(f"Data -> provider_cost_evidence='{evidence}'")


def fr_sim_240() -> None:
    """FR-SIM-240: Preserve signs and conservation through cold restore."""
    ledger = create_transaction_ledger(Decimal(1000), "USD")
    post_transaction(ledger, _posting("withdrawal", Decimal(-10), 1))
    restored = restore_transaction_ledger(serialize_transaction_ledger(ledger))
    snapshot = serialize_transaction_ledger(restored)
    print(
        f"Data -> signed_balance={snapshot['balance']}, conservation={snapshot['conservation']}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-04 — accounting/ — Fixed-Precision Account Math\n\n"
        "Purpose: Normalize trade volume, calculate execution costs and margin requirements, validate FX evidence, convert rates, apply ledger fills, generate snapshots, and update mark to market.\n\n"
        "Module flow:\n"
        "-> Stage 1: Volume normalization and specification validation\n"
        "-> Stage 2: Cost, margin, and FX rate calculations with evidence validation\n"
        "-> Stage 3: AccountLedger fill application, snapshot generation, and mark-to-market updates"
    )

    # Stage 1: Volume normalization
    fr_sim_007()

    # Stage 2: Cost/Margin & FX
    fr_sim_008()
    fr_sim_009()
    fr_sim_010()
    fr_sim_039()

    # Stage 3: Ledger fills, snapshots & Mark to market
    fr_sim_011()
    fr_sim_012()
    fr_sim_042()

    # Stage 4: Evidence-backed signed transaction ledger
    fr_sim_179()
    fr_sim_180()
    fr_sim_240()


if __name__ == "__main__":
    main()
