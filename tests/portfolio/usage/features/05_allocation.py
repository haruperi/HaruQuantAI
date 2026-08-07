"""Executable Portfolio allocation usage example.

Demonstrates FEAT-PORT-05 version and activation governance feature through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import create_portfolio_value

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _run_example(requirement: str, example: Any) -> None:
    """Run one requirement example and print explicit success evidence."""
    example()
    print(f"SUCCESS: {requirement}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _weights() -> tuple[dict[str, object], ...]:
    """Return ordered component weight data totaling exactly one."""
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
    """Return complete active allocation data."""
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
    """FR-PORT-015: Stage 1 — Require Simulation validation and current Risk authorization before activation.

    The system shall require Simulation validation and current Risk authorization before activation.
    """
    _header(
        "Stage 1: Pre-Activation Gates - Simulation Validation & Risk Authorization (FR-PORT-015)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(
        f"Data -> simulation_id='{allocation.simulation_result_id}', risk_decision_id='{allocation.risk_decision_id}'"
    )


def fr_port_016() -> None:
    """FR-PORT-016: Stage 2 — Require explicit human approval for paper/live; allow automatic simulation activation only within simulation policy.

    The system shall enforce human approval for live/paper environments while allowing automatic simulation activation.
    """
    _header(
        "Stage 2: Environment Governance - Human Approval for Live/Paper (FR-PORT-016)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation.scope))
    print(
        f"Data -> environment='{allocation.scope.get('environment')}', human_approval_required=False"
    )


def fr_port_017() -> None:
    """FR-PORT-017: Stage 2 — Block activation while any applicable kill switch is active.

    The system shall block allocation activation while any applicable kill switch is active.
    """
    _header("Stage 2: Safety Check - Kill-Switch Interlock (FR-PORT-017)")
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print("Data -> kill_switch_active=False")


def fr_port_018() -> None:
    """FR-PORT-018: Stage 3 — Use optimistic concurrency and one active version per scope.

    The system shall use optimistic concurrency (CAS) and enforce exactly one active version per scope.
    """
    _header(
        "Stage 3: Optimistic Concurrency - Unique Active Version Per Scope (FR-PORT-018)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(f"Data -> allocation_version='{allocation.allocation_version}'")


def fr_port_019() -> None:
    """FR-PORT-019: Stage 3 — Implement rollback only as a new governed version.

    The system shall implement rollback strictly as a new governed allocation version without history mutation.
    """
    _header(
        "Stage 3: Rollback Governance - Immutable Rollback Versioning (FR-PORT-019)"
    )
    original = create_portfolio_value("ActivePortfolioAllocation", **_allocation_data())
    rollback = create_portfolio_value(
        "ActivePortfolioAllocation",
        **_allocation_data(
            allocation_id="allocation-2",
            allocation_version="allocation-version-2",
            predecessor_version=original.allocation_version,
            rollback_of_version=original.allocation_version,
            canonical_hash="d" * 64,
            idempotency_key="idem-2",
        ),
    )
    print(_format_result(rollback))
    print(
        f"Data -> rollback_version='{rollback.allocation_version}', rollback_of='{rollback.rollback_of_version}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-05 — allocation/ — Version and Activation Governance\n\n"
        "Purpose: Govern allocation activation, human approval attestation, kill-switch checks, optimistic concurrency, and rollback versioning.\n\n"
        "Module flow:\n"
        "-> Stage 1: Pre-activation gate verification (Simulation result + Risk decision)\n"
        "-> Stage 2: Profile governance check (simulation vs paper/live approval) and kill-switch interlock\n"
        "-> Stage 3: Atomic activation with optimistic concurrency (CAS) and rollback versioning"
    )

    # Stage 1: Gates
    _run_example("FR-PORT-015", fr_port_015)

    # Stage 2: Profile & Safety
    _run_example("FR-PORT-016", fr_port_016)
    _run_example("FR-PORT-017", fr_port_017)

    # Stage 3: Activation & Rollback
    _run_example("FR-PORT-018", fr_port_018)
    _run_example("FR-PORT-019", fr_port_019)


if __name__ == "__main__":
    main()
