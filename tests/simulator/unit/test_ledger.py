"""Unit tests for the authoritative Simulation account ledger."""
# ruff: noqa: INP001

from decimal import Decimal

import pytest
from app.services.simulator.accounting import (
    AccountLedger,
    ExecutionCostModel,
    LedgerFill,
    SymbolSpecification,
)
from app.services.simulator.errors import SimulationError


def _ledger() -> AccountLedger:
    """Build one isolated account ledger."""
    return AccountLedger(
        initial_balance=Decimal(10_000),
        account_currency="USD",
        symbol_specification=SymbolSpecification(
            minimum_volume=Decimal("0.01"),
            maximum_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            contract_size=Decimal(100_000),
            leverage=Decimal(100),
        ),
        cost_model=ExecutionCostModel(
            commission_per_lot_per_side=Decimal(1),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        ),
    )


def test_apply_fill_preserves_account_invariants() -> None:
    """Reserve margin and debit commission atomically."""
    ledger = _ledger()
    ledger.apply_fill(
        LedgerFill(
            action="OPEN",
            side="BUY",
            volume=Decimal(1),
            price=Decimal("1.1"),
        )
    )
    snapshot = ledger.snapshot()
    assert snapshot["balance"] == Decimal(9_999)
    assert snapshot["used_margin"] == Decimal(1_100)
    assert snapshot["free_margin"] == Decimal(8_899)


def test_snapshot_is_immutable() -> None:
    """Prevent callers from mutating ledger state through a snapshot."""
    snapshot = _ledger().snapshot()
    with pytest.raises(TypeError, match="does not support item assignment"):
        snapshot["balance"] = Decimal(0)  # type: ignore[index]


def _open_one_lot(ledger: AccountLedger) -> None:
    """Open one standard lot on the supplied ledger.

    Args:
        ledger: Ledger receiving the fill.
    """
    ledger.apply_fill(
        LedgerFill(
            action="OPEN",
            side="BUY",
            volume=Decimal(1),
            price=Decimal("1.1"),
        )
    )


def test_apply_fill_returns_itemized_costs() -> None:
    """Return the exact costs charged so callers can attribute them."""
    costs = _ledger().apply_fill(
        LedgerFill(
            action="OPEN",
            side="BUY",
            volume=Decimal(1),
            price=Decimal("1.1"),
        )
    )
    assert costs["commission"] == Decimal(-1)
    assert costs["total"] == costs["commission"] + costs["swap"]


def test_snapshot_reports_accumulated_costs() -> None:
    """Accumulate commission, swap, and gross profit across fills."""
    ledger = _ledger()
    _open_one_lot(ledger)
    _open_one_lot(ledger)
    snapshot = ledger.snapshot()
    assert snapshot["commission"] == Decimal(-2)
    assert snapshot["swap"] == Decimal(0)
    assert snapshot["gross_profit"] == Decimal(0)


def test_equity_includes_unrealized_pnl() -> None:
    """Reflect open-position floating loss in equity and free margin."""
    ledger = _ledger()
    _open_one_lot(ledger)
    before = ledger.snapshot()
    ledger.mark_to_market(Decimal(-500))
    after = ledger.snapshot()
    assert after["balance"] == before["balance"]
    assert after["equity"] == before["balance"] - Decimal(500)
    assert after["free_margin"] == before["free_margin"] - Decimal(500)


def test_mark_to_market_rejects_non_finite_value() -> None:
    """Fail closed when the supplied unrealized value is not finite."""
    with pytest.raises(SimulationError) as captured:
        _ledger().mark_to_market(Decimal("NaN"))
    assert captured.value.code == "SIM_ACCOUNT_INVARIANT_BROKEN"


def test_insufficient_free_margin_accounts_for_open_loss() -> None:
    """Refuse a fill the account could not support once open losses count."""
    ledger = _ledger()
    _open_one_lot(ledger)
    ledger.mark_to_market(Decimal(-9_000))
    with pytest.raises(SimulationError) as captured:
        ledger.apply_fill(
            LedgerFill(
                action="OPEN",
                side="BUY",
                volume=Decimal(5),
                price=Decimal("1.1"),
            )
        )
    assert captured.value.code == "SIM_INSUFFICIENT_MARGIN"
