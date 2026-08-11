"""Deterministic broker-truth reconciliation."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal


def reconcile_portfolio(
    rebuilt: Mapping[str, Decimal],
    broker: Mapping[str, Decimal] | None,
    *,
    tolerance: Decimal,
    incident_id: str,
) -> Mapping[str, object]:
    """Compare rebuilt state with broker truth and preserve unknown.

    Args:
        rebuilt: Mapping of rebuilt account/position balances.
        broker: Optional mapping of broker truth balances.
        tolerance: Numerical tolerance threshold.
        incident_id: Incident tracking ID string.

    Returns:
        Reconciliation status and material differences.
    """
    if broker is None:
        return {
            "incident_id": incident_id,
            "status": "unknown",
            "reason": "BROKER_TRUTH_UNAVAILABLE",
        }
    differences = {
        key: str(rebuilt.get(key, Decimal(0)) - broker.get(key, Decimal(0)))
        for key in sorted(set(rebuilt) | set(broker))
        if abs(rebuilt.get(key, Decimal(0)) - broker.get(key, Decimal(0))) > tolerance
    }
    return {
        "incident_id": incident_id,
        "status": "mismatch" if differences else "reconciled",
        "differences": differences,
        "tolerance": str(tolerance),
    }
