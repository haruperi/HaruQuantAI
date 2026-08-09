"""Decimal valuation and P&L calculation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from app.services.portfolio.valuation.lots import cost_basis
from app.services.portfolio.valuation.policies import select_price


def calculate_portfolio_valuation(
    positions: Sequence[Mapping[str, object]],
    *,
    policy_version: str,
    policy: Mapping[str, object],
    lot_method: str,
    fx_evidence: Mapping[str, object] | None,
) -> Mapping[str, object]:
    """Calculate side-aware Decimal P&L or return explicit unknown status.

    Returns:
        Valuation evidence with source lineage.
    """
    if fx_evidence is None or fx_evidence.get("status") != "current":
        return {
            "status": "unknown",
            "reason": "FX_EVIDENCE_UNAVAILABLE",
            "policy_version": policy_version,
        }
    total = Decimal(0)
    lineage: list[dict[str, object]] = []
    for position in positions:
        price, source = select_price(position, policy)
        if price is None or bool(position.get("stale")):
            return {
                "status": "unknown",
                "reason": "PRICE_UNAVAILABLE",
                "policy_version": policy_version,
            }
        raw_lots = position.get("lots", ())
        if not isinstance(raw_lots, (tuple, list)):
            return {
                "status": "unknown",
                "reason": "LOTS_UNAVAILABLE",
                "policy_version": policy_version,
            }
        lots = tuple((Decimal(str(q)), Decimal(str(p))) for q, p in raw_lots)
        basis = cost_basis(lots, lot_method)
        quantity = sum((q for q, _ in lots), Decimal(0))
        costs = Decimal(str(position.get("costs", "0")))
        pnl = (Decimal(str(price)) - basis) * quantity - costs
        total += pnl
        lineage.append(
            {
                "position_id": position.get("position_id"),
                "source": source,
                "pnl": str(pnl),
            }
        )
    return {
        "status": "known",
        "policy_version": policy_version,
        "lot_method": lot_method,
        "net_pnl": str(total),
        "lineage": lineage,
        "fx_evidence_id": fx_evidence.get("evidence_id"),
    }
