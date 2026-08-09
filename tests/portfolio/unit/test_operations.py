"""Tests for FEAT-PORT-10 through FEAT-PORT-12."""

from decimal import Decimal

from app.services.portfolio import (
    build_lifecycle_postings,
    calculate_margin_view,
    calculate_portfolio_valuation,
    reconcile_portfolio,
)


def test_valuation_requires_current_fx() -> None:
    """Missing Data-owned FX evidence produces unknown valuation."""
    result = calculate_portfolio_valuation(
        (), policy_version="v1", policy={}, lot_method="fifo", fx_evidence=None
    )
    assert result["status"] == "unknown"


def test_margin_view_is_decimal_and_fail_closed() -> None:
    """Reserved funds reduce buying power and expose liquidation risk."""
    result = calculate_margin_view(
        equity=Decimal(10),
        margin_used=Decimal(8),
        reserved=Decimal(2),
        maintenance=Decimal(1),
        policy_version="v1",
    )
    assert result["buying_power"] == "0"
    assert result["liquidation_risk"] is True


def test_reconciliation_unknown_and_postings_balanced() -> None:
    """Unavailable broker truth is unknown and lifecycle postings balance."""
    assert (
        reconcile_portfolio({}, None, tolerance=Decimal(0), incident_id="i")["status"]
        == "unknown"
    )
    postings = build_lifecycle_postings("e", "split", Decimal(2), "USD")["postings"]
    assert postings[0]["amount"] == postings[1]["amount"]
