"""Unit tests for deterministic Simulation accounting calculations."""
# ruff: noqa: INP001

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
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
from app.services.simulator.errors import SimulationError


def _specification() -> SymbolSpecification:
    """Build one approved symbol specification."""
    return SymbolSpecification(
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100_000),
        leverage=Decimal(100),
    )


def _fx_evidence() -> FXConversionEvidence:
    """Build fresh Data-owned FX evidence."""
    instant = datetime(2025, 1, 1, tzinfo=UTC)
    leg = FXRateLeg(
        source_currency="USD",
        target_currency="EUR",
        rate=Decimal("0.9"),
        source_id="fixture",
        provider_symbol="USDEUR",
        as_of=instant,
        provenance={"provider": "fixture"},
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
        provenance={"provider": "fixture"},
        request_id="req-33333333-3333-4333-8333-333333333333",
    )


def test_normalize_volume_preserves_approved_size() -> None:
    """Return the exact valid Risk-approved volume."""
    approved = Decimal("1.23")
    assert normalize_volume(approved, _specification()) is approved


def test_calculate_execution_costs_is_exact() -> None:
    """Calculate exact signed commission and swap."""
    costs = calculate_execution_costs(
        ExecutionCostInput(
            volume=Decimal(2), side="BUY", rollover_multiplier=Decimal(3)
        ),
        ExecutionCostModel(
            commission_per_lot_per_side=Decimal("1.5"),
            long_swap_per_lot_rollover=Decimal("0.2"),
            short_swap_per_lot_rollover=Decimal("0.3"),
        ),
    )
    assert costs == {
        "commission": Decimal("-3.0"),
        "swap": Decimal("-1.2"),
        "total": Decimal("-4.2"),
    }


def test_calculate_execution_costs_rejects_invalid_commission() -> None:
    """Map a non-finite commission calculation to its exact code."""
    fill = ExecutionCostInput(
        volume=Decimal(1), side="BUY", rollover_multiplier=Decimal(0)
    )
    model = ExecutionCostModel.model_construct(
        commission_per_lot_per_side=Decimal("NaN"),
        long_swap_per_lot_rollover=Decimal(0),
        short_swap_per_lot_rollover=Decimal(0),
    )
    with pytest.raises(SimulationError) as captured:
        calculate_execution_costs(fill, model)
    assert captured.value.code == "SIM_COMMISSION_CALCULATION_FAILED"


def test_calculate_execution_costs_rejects_invalid_swap() -> None:
    """Map a non-finite swap calculation to its exact code."""
    fill = ExecutionCostInput(
        volume=Decimal(1), side="BUY", rollover_multiplier=Decimal(1)
    )
    model = ExecutionCostModel.model_construct(
        commission_per_lot_per_side=Decimal(0),
        long_swap_per_lot_rollover=Decimal("NaN"),
        short_swap_per_lot_rollover=Decimal(0),
    )
    with pytest.raises(SimulationError) as captured:
        calculate_execution_costs(fill, model)
    assert captured.value.code == "SIM_SWAP_CALCULATION_FAILED"


def test_calculate_margin_rejects_zero_leverage() -> None:
    """Reject an invalid leverage divisor."""
    with pytest.raises(SimulationError) as captured:
        calculate_margin(Decimal(1), Decimal(1), Decimal(100_000), Decimal(0))
    assert captured.value.code == "SIM_INVALID_CONFIG"


def test_fx_evidence_must_be_fresh() -> None:
    """Reject expired conversion evidence."""
    evidence = _fx_evidence()
    with pytest.raises(SimulationError) as captured:
        validate_fx_evidence(evidence, as_of=evidence.expires_at)
    assert captured.value.code == "SIM_FX_EVIDENCE_UNAVAILABLE"


def test_convert_fx_amount_uses_supplied_rate_only() -> None:
    """Multiply only by the supplied validated composite rate."""
    evidence = _fx_evidence()
    validated = validate_fx_evidence(evidence, as_of=evidence.as_of)
    assert convert_fx_amount(Decimal(10), validated) == Decimal(9)
