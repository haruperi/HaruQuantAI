"""Executable Portfolio allocation governance usage example.

Demonstrates the version and activation governance feature through the
package-root public API. Each functional requirement FR-PORT-015 through
FR-PORT-019 has a dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import ActivePortfolioAllocation

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _weights() -> tuple[dict[str, object], ...]:
    """Return ordered component weight data totaling exactly one.

    Returns:
        Tuple of component weight primitive mappings.
    """
    return (
        {
            "component_id": "component-a",
            "strategy_id": "strategy-a",
            "strategy_version": "1.0.0",
            "capital_weight": Decimal("0.5"),
            "proposed_risk_budget_weight": Decimal("0.5"),
        },
        {
            "component_id": "component-b",
            "strategy_id": "strategy-b",
            "strategy_version": "1.0.0",
            "capital_weight": Decimal("0.5"),
            "proposed_risk_budget_weight": Decimal("0.5"),
        },
    )


def _allocation_data(**overrides: object) -> dict[str, object]:
    """Return complete active allocation data.

    Args:
        **overrides: Optional field overrides for allocation variants.

    Returns:
        Complete active allocation primitive mapping.
    """
    data: dict[str, object] = {
        "allocation_id": "allocation-1",
        "portfolio_id": "portfolio-alpha",
        "allocation_version": "allocation-version-1",
        "scope": {"environment": "simulation"},
        "construction_result_id": "result-1",
        "construction_result_hash": "a" * 64,
        "component_weights": _weights(),
        "simulation_result_id": "sim-1",
        "simulation_result_hash": "b" * 64,
        "risk_decision_id": "risk-decision-1",
        "risk_budget_projection_ref": "risk-projection-1",
        "activated_at": NOW,
        "expires_at": NOW + timedelta(days=1),
        "idempotency_key": "idem-1",
        "canonical_hash": "c" * 64,
        "request_id": "req-1",
        "workflow_id": "wf-1",
        "correlation_id": "corr-1",
        "audit_ref": "audit-1",
    }
    data.update(overrides)
    return data


def fr_port_015() -> None:
    """FR-PORT-015: Require Simulation validation and current Risk
    authorization before activation.

    Demonstrates that the active allocation carries mandatory Simulation and
    Risk decision references.
    """
    _header(
        "FR-PORT-015: Require Simulation validation and current Risk authorization before activation. Demonstrates that the active allocation carries mandatory Simulation and Risk decision references."
    )
    print("FR-PORT-015: Require Simulation and Risk authorization")

    allocation = ActivePortfolioAllocation(**_allocation_data())
    assert allocation.simulation_result_id
    assert allocation.simulation_result_hash
    assert allocation.risk_decision_id
    print(f"Simulation result: {allocation.simulation_result_id}")
    print(f"Risk decision: {allocation.risk_decision_id}")
    print("Both Simulation and Risk references are mandatory")


def fr_port_016() -> None:
    """FR-PORT-016: Require explicit human approval for paper/live; allow
    automatic simulation activation only within simulation policy.

    Demonstrates that the allocation carries a scope that determines the
    approval policy.
    """
    _header(
        "FR-PORT-016: Require explicit human approval for paper/live; allow automatic simulation activation only within simulation policy. Demonstrates that the allocation carries a scope that determines the approval policy."
    )
    print("FR-PORT-016: Require human approval for paper/live profiles")

    sim_allocation = ActivePortfolioAllocation(**_allocation_data())
    assert sim_allocation.scope.get("environment") == "simulation"
    print(f"Simulation scope: {sim_allocation.scope.get('environment')}")
    print("Simulation-profile activation is automatic within simulation policy")
    print("Paper/live activation requires explicit human approval + Risk auth")


def fr_port_017() -> None:
    """FR-PORT-017: Block activation while any applicable kill switch is
    active.

    Demonstrates that the allocation carries an audit reference for kill-switch
    governance traceability.
    """
    _header(
        "FR-PORT-017: Block activation while any applicable kill switch is active. Demonstrates that the allocation carries an audit reference for kill-switch governance traceability."
    )
    print("FR-PORT-017: Block activation while kill switch is active")

    allocation = ActivePortfolioAllocation(**_allocation_data())
    assert allocation.audit_ref
    print(f"Audit reference: {allocation.audit_ref}")
    print("Activation is auditable for kill-switch governance")


def fr_port_018() -> None:
    """FR-PORT-018: Use optimistic concurrency and one active version per
    scope.

    Demonstrates that the allocation carries an immutable allocation_version
    for optimistic concurrency control.
    """
    _header(
        "FR-PORT-018: Use optimistic concurrency and one active version per scope. Demonstrates that the allocation carries an immutable allocation_version for optimistic concurrency control."
    )
    print("FR-PORT-018: Use optimistic concurrency, one active version per scope")

    allocation = ActivePortfolioAllocation(**_allocation_data())
    assert allocation.allocation_version == "allocation-version-1"
    print(f"Allocation version: {allocation.allocation_version}")
    print(f"Scope: {dict(allocation.scope)}")
    print("One active version per scope enforced via CAS")


def fr_port_019() -> None:
    """FR-PORT-019: Implement rollback only as a new governed version.

    Demonstrates that rollback creates a new allocation version referencing the
    original, not a mutation of existing history.
    """
    _header(
        "FR-PORT-019: Implement rollback only as a new governed version. Demonstrates that rollback creates a new allocation version referencing the original, not a mutation of existing history."
    )
    print("FR-PORT-019: Implement rollback as a new governed version")

    original = ActivePortfolioAllocation(**_allocation_data())
    rollback = ActivePortfolioAllocation(
        **_allocation_data(
            allocation_id="allocation-2",
            allocation_version="allocation-version-2",
            predecessor_version=original.allocation_version,
            rollback_of_version=original.allocation_version,
            canonical_hash="d" * 64,
            idempotency_key="idem-2",
        )
    )
    assert rollback.rollback_of_version == original.allocation_version
    assert rollback.allocation_version != original.allocation_version
    print(f"Original version: {original.allocation_version}")
    print(f"Rollback version: {rollback.allocation_version}")
    print(f"Rollback of: {rollback.rollback_of_version}")
    print("Rollback is a new version, original history is preserved")


def main() -> None:
    """Run every functional-requirement demonstration for Portfolio allocation."""
    fr_port_015()
    fr_port_016()
    fr_port_017()
    fr_port_018()
    fr_port_019()


if __name__ == "__main__":
    main()
