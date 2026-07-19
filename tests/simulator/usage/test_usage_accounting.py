"""Runnable usage examples for Simulation accounting."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.data.contracts import FXConversionEvidence, FXRateLeg
from app.services.simulator.accounting import (
    AccountLedger,
    ExecutionCostInput,
    ExecutionCostModel,
    LedgerFill,
    SymbolSpecification,
    calculate_execution_costs,
    calculate_margin,
    convert_fx_amount,
    normalize_volume,
    validate_fx_evidence,
)


def _specification() -> SymbolSpecification:
    """Build an explicit usage symbol specification."""
    return SymbolSpecification(
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100_000),
        leverage=Decimal(100),
    )


def _model() -> ExecutionCostModel:
    """Build an explicit usage execution-cost model."""
    return ExecutionCostModel(
        commission_per_lot_per_side=Decimal(1),
        long_swap_per_lot_rollover=Decimal(0),
        short_swap_per_lot_rollover=Decimal(0),
    )


def _evidence() -> FXConversionEvidence:
    """Build fresh usage conversion evidence."""
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
        request_id=f"req-{'4' * 64}",
    )


def test_usage_normalize_volume() -> None:
    """Validate an unchanged approved volume."""
    assert normalize_volume(Decimal(1), _specification()) == Decimal(1)


def test_usage_calculate_execution_costs() -> None:
    """Calculate itemized signed costs."""
    costs = calculate_execution_costs(
        ExecutionCostInput(
            volume=Decimal(1), side="BUY", rollover_multiplier=Decimal(0)
        ),
        _model(),
    )
    assert costs["commission"] == Decimal(-1)


def test_usage_calculate_margin() -> None:
    """Calculate required FX margin."""
    assert calculate_margin(
        Decimal(1), Decimal(1), Decimal(100_000), Decimal(100)
    ) == Decimal(1_000)


def test_usage_validate_fx_evidence() -> None:
    """Validate Data-owned evidence before conversion."""
    evidence = _evidence()
    assert validate_fx_evidence(evidence, as_of=evidence.as_of).evidence is evidence


def test_usage_convert_fx_amount() -> None:
    """Convert with validated evidence only."""
    evidence = _evidence()
    validated = validate_fx_evidence(evidence, as_of=evidence.as_of)
    assert convert_fx_amount(Decimal(10), validated) == Decimal(9)


def test_usage_ledger_apply_fill() -> None:
    """Apply one fill to the authoritative ledger."""
    ledger = AccountLedger(Decimal(10_000), "USD", _specification(), _model())
    ledger.apply_fill(
        LedgerFill(action="OPEN", side="BUY", volume=Decimal(1), price=Decimal(1))
    )
    assert ledger.snapshot()["used_margin"] == Decimal(1_000)


def test_usage_ledger_snapshot() -> None:
    """Read immutable account state."""
    ledger = AccountLedger(Decimal(10_000), "USD", _specification(), _model())
    assert ledger.snapshot()["account_currency"] == "USD"


def test_usage_ledger_mark_to_market() -> None:
    """Reflect open-position profit and loss in equity and free margin."""
    ledger = AccountLedger(Decimal(10_000), "USD", _specification(), _model())
    ledger.mark_to_market(Decimal(-250))
    snapshot = ledger.snapshot()
    assert snapshot["equity"] == Decimal(9_750)
    assert snapshot["free_margin"] == Decimal(9_750)
