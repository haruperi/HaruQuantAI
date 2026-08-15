"""Unit tests for account mode and stop-out policy."""

from decimal import Decimal

import pytest
from app.services.simulator.accounting.stop_out import (
    get_margin_state,
    plan_stop_out_liquidation,
    project_account_mode,
)


def test_percent_and_money_thresholds_are_exact() -> None:
    """Both admitted MT5 threshold modes classify boundary equality."""
    assert (
        get_margin_state(
            equity=Decimal(50),
            used_margin=Decimal(100),
            margin_call_level=Decimal(80),
            stop_out_level=Decimal(50),
            mode="PERCENT",
        )
        == "STOP_OUT"
    )
    assert (
        get_margin_state(
            equity=Decimal(75),
            used_margin=Decimal(100),
            margin_call_level=Decimal(80),
            stop_out_level=Decimal(50),
            mode="MONEY",
        )
        == "MARGIN_CALL"
    )


def test_netting_hedging_and_evidenced_liquidation() -> None:
    """Account modes preserve their distinct position identity rules."""
    hedged = project_account_mode(
        (), mode="HEDGING", symbol="EURUSD", side="BUY", volume=Decimal(1)
    )
    assert hedged[0]["position_id"] == "hedge-1"
    netted = project_account_mode(
        (), mode="NETTING", symbol="EURUSD", side="BUY", volume=Decimal(1)
    )
    netted = project_account_mode(
        netted, mode="NETTING", symbol="EURUSD", side="SELL", volume=Decimal("0.5")
    )
    assert netted[0]["volume"] == Decimal("0.5")
    with pytest.raises(ValueError, match="target evidence"):
        plan_stop_out_liquidation(
            (), ordering="WORST_LOSS_FIRST", target_evidence_reference=None
        )
