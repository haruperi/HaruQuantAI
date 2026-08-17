"""Unit tests for Portfolio margin, reconciliation, and valuation modules."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.services.portfolio.margin import contracts as margin_contracts
from app.services.portfolio.margin import providers as margin_providers
from app.services.portfolio.margin.risk_health import build_portfolio_risk_health
from app.services.portfolio.reconciliation import contracts as recon_contracts
from app.services.portfolio.reconciliation.comparison import reconcile_portfolio
from app.services.portfolio.valuation import contracts as val_contracts
from app.services.portfolio.valuation import providers as val_providers
from app.services.portfolio.valuation.lots import cost_basis
from app.services.portfolio.valuation.pnl import calculate_portfolio_valuation
from app.services.portfolio.valuation.policies import select_price


def test_margin_recon_and_valuation_contracts_metadata() -> None:
    """Verify version metadata and provider exports in margin, recon, and valuation."""
    assert margin_contracts.PORTFOLIO_MARGIN_VIEW_VERSION == "v1"
    assert margin_contracts.PORTFOLIO_RISK_HEALTH_VERSION == "v1"
    assert margin_providers.calculate_margin_view is not None

    assert recon_contracts.RECONCILIATION_CONTRACT_VERSION == "v1"

    assert val_contracts.VALUATION_CONTRACT_VERSION == "v1"
    assert val_providers.calculate_portfolio_valuation is not None


def test_build_portfolio_risk_health_empty_and_valid() -> None:
    """Verify build_portfolio_risk_health handles empty and populated inputs."""
    res_empty = build_portfolio_risk_health(
        [],
        confidence=Decimal("0.95"),
        model="historical",
        window=100,
        stress_losses={},
        high_water_mark=Decimal(1000),
    )
    assert res_empty["status"] == "unknown"
    assert res_empty["reason"] == "NO_OBSERVATIONS"

    values = [Decimal(100), Decimal(105), Decimal(95), Decimal(110)]
    res_valid = build_portfolio_risk_health(
        values,
        confidence=Decimal("0.95"),
        model="historical",
        window=4,
        stress_losses={"crisis": Decimal(500)},
        high_water_mark=Decimal(120),
    )
    assert res_valid["status"] == "known"
    assert res_valid["observations"] == 4
    assert res_valid["drawdown"] == "-10"
    assert "var" in res_valid
    assert "cvar" in res_valid
    assert res_valid["stress"] == {"crisis": "500"}


def test_cost_basis_branches() -> None:
    """Verify cost_basis method check and quantity zero check."""
    with pytest.raises(ValueError, match="unsupported lot matching method"):
        cost_basis([], "invalid_method")

    assert cost_basis([], "fifo") == Decimal(0)
    assert cost_basis([(Decimal(10), Decimal(100))], "fifo") == Decimal(100)


def test_select_price_policy() -> None:
    """Verify select_price policy lookups for long and short sides."""
    long_pos = {"side": "long", "mark": 105, "bid": 104}
    short_pos = {"side": "short", "mark": 105, "ask": 106}
    policy = {"long_source": "bid", "short_source": "ask"}

    price, src = select_price(long_pos, policy)
    assert price == 104
    assert src == "bid"

    price_s, src_s = select_price(short_pos, policy)
    assert price_s == 106
    assert src_s == "ask"


def test_reconcile_portfolio_branches() -> None:
    """Verify reconcile_portfolio handling missing broker and difference matching."""
    res_none = reconcile_portfolio(
        {}, None, tolerance=Decimal("0.01"), incident_id="inc-1"
    )
    assert res_none["status"] == "unknown"
    assert res_none["reason"] == "BROKER_TRUTH_UNAVAILABLE"

    rebuilt = {"cash": Decimal(1000), "pnl": Decimal(50)}
    broker_clean = {"cash": Decimal(1000), "pnl": Decimal(50)}
    res_clean = reconcile_portfolio(
        rebuilt, broker_clean, tolerance=Decimal("0.01"), incident_id="inc-2"
    )
    assert res_clean["status"] == "reconciled"
    assert res_clean["differences"] == {}

    broker_mismatch = {"cash": Decimal(990), "pnl": Decimal(50)}
    res_mismatch = reconcile_portfolio(
        rebuilt, broker_mismatch, tolerance=Decimal("0.01"), incident_id="inc-3"
    )
    assert res_mismatch["status"] == "mismatch"
    assert "cash" in res_mismatch["differences"]


def test_calculate_portfolio_valuation_branches() -> None:
    """Verify calculate_portfolio_valuation branch handling."""
    res_no_fx = calculate_portfolio_valuation(
        [], policy_version="v1", policy={}, lot_method="fifo", fx_evidence=None
    )
    assert res_no_fx["status"] == "unknown"
    assert res_no_fx["reason"] == "FX_EVIDENCE_UNAVAILABLE"

    fx = {"status": "current", "evidence_id": "fx-123"}
    policy = {"long_source": "mark"}

    stale_pos = [{"side": "long", "mark": None, "stale": True}]
    res_stale = calculate_portfolio_valuation(
        stale_pos, policy_version="v1", policy=policy, lot_method="fifo", fx_evidence=fx
    )
    assert res_stale["status"] == "unknown"
    assert res_stale["reason"] == "PRICE_UNAVAILABLE"

    bad_lots_pos = [
        {"side": "long", "mark": 100, "stale": False, "lots": "not_a_tuple"}
    ]
    res_bad_lots = calculate_portfolio_valuation(
        bad_lots_pos,
        policy_version="v1",
        policy=policy,
        lot_method="fifo",
        fx_evidence=fx,
    )
    assert res_bad_lots["status"] == "unknown"
    assert res_bad_lots["reason"] == "LOTS_UNAVAILABLE"

    valid_pos = [
        {
            "position_id": "pos-1",
            "side": "long",
            "mark": 110,
            "stale": False,
            "lots": [("10", "100")],
            "costs": "5",
        }
    ]
    res_valid = calculate_portfolio_valuation(
        valid_pos, policy_version="v1", policy=policy, lot_method="fifo", fx_evidence=fx
    )
    assert res_valid["status"] == "known"
    assert res_valid["net_pnl"] == "95"
