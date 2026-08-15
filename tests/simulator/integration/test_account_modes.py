"""Integration matrix for netting and hedging account modes."""

from decimal import Decimal

from app.services.simulator.accounting.stop_out import project_account_mode


def test_netting_reverses_while_hedging_retains_both_sides() -> None:
    """Opposite fills reverse one net position but create a hedge position."""
    net = project_account_mode(
        (), mode="NETTING", symbol="USDJPY", side="BUY", volume=Decimal(1)
    )
    net = project_account_mode(
        net, mode="NETTING", symbol="USDJPY", side="SELL", volume=Decimal(2)
    )
    assert net[0]["side"] == "SELL"
    assert net[0]["volume"] == Decimal(1)
    hedge = project_account_mode(
        (), mode="HEDGING", symbol="USDJPY", side="BUY", volume=Decimal(1)
    )
    hedge = project_account_mode(
        hedge, mode="HEDGING", symbol="USDJPY", side="SELL", volume=Decimal(2)
    )
    assert len(hedge) == 2
