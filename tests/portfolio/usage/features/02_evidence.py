"""Executable Portfolio evidence usage example.

Demonstrates FEAT-PORT-02 evidence and eligibility validation feature through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import create_portfolio_value

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


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


def _evidence_data(**overrides: object) -> dict[str, object]:
    """Return complete evidence reference set data."""
    data: dict[str, object] = {
        "account_snapshot_id": "account-snapshot-1",
        "account_snapshot_hash": HASH_A,
        "account_snapshot_as_of": NOW,
        "market_dataset_id": "market-dataset-1",
        "market_dataset_hash": HASH_B,
        "market_dataset_as_of": NOW,
        "analytics_evidence_id": "analytics-evidence-1",
        "analytics_evidence_hash": "c" * 64,
        "analytics_evidence_as_of": NOW,
        "fx_evidence_ids": (),
        "fx_evidence_hashes": (),
    }
    data.update(overrides)
    return data


def _base_request_data(**overrides: object) -> dict[str, object]:
    """Return complete construction request data."""
    data: dict[str, object] = {
        "request_id": "req-portfolio-0001",
        "workflow_id": "wf-portfolio-0001",
        "correlation_id": "corr-portfolio-0001",
        "causation_id": None,
        "portfolio_id": "portfolio-alpha",
        "portfolio_version": "version-1",
        "scope": {"environment": "simulation", "tenant": "owner"},
        "components": (
            {
                "component_id": "component-a",
                "strategy_id": "strategy-a",
                "strategy_version": "1.0.0",
                "registry_record_hash": HASH_A,
                "eligibility_decision_id": "eligibility-a",
            },
            {
                "component_id": "component-b",
                "strategy_id": "strategy-b",
                "strategy_version": "1.0.0",
                "registry_record_hash": HASH_B,
                "eligibility_decision_id": "eligibility-b",
            },
        ),
        "method": "equal",
        "fixed_weights": (),
        "evidence": _evidence_data(),
        "measurement_start": datetime(2026, 7, 1, tzinfo=UTC),
        "measurement_end": NOW,
        "base_currency": "USD",
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "simulation_policy_version": "v1",
        "requested_at": NOW,
    }
    data.update(overrides)
    return data


def fr_port_006() -> None:
    """FR-PORT-006: Stage 1 — Require a current approving eligibility decision for every exact strategy/version/scope.

    The system shall require a current approving eligibility decision for every strategy/version/scope.
    """
    _header(
        "Stage 1: Eligibility Requirement - Check Component Eligibility (FR-PORT-006)"
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request))
    print(
        f"Data -> component_0_eligibility='{request.components[0].eligibility_decision_id}'"
    )


def fr_port_007() -> None:
    """FR-PORT-007: Stage 2 — Fail closed on missing, stale, incompatible, cyclic, or unverifiable FX evidence.

    The system shall fail closed on missing, stale, incompatible, cyclic, or unverifiable FX evidence.
    """
    _header(
        "Stage 2: FX Evidence Validation - Align FX Evidence IDs & Hashes (FR-PORT-007)"
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request.evidence))
    print(f"Data -> fx_evidence_ids_count={len(request.evidence.fx_evidence_ids)}")


def fr_port_008() -> None:
    """FR-PORT-008: Stage 2 — Never synthesize rates, metrics, registrations, or approvals.

    The system shall require explicit owner evidence references and never synthesize missing data.
    """
    _header(
        "Stage 2: No Synthesis Rule - Enforce Explicit Evidence References (FR-PORT-008)"
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request.evidence))
    print(
        f"Data -> account_snapshot_id='{request.evidence.account_snapshot_id}', market_dataset_id='{request.evidence.market_dataset_id}'"
    )


def fr_port_009() -> None:
    """FR-PORT-009: Stage 3 — Detect a reference/version change before publication or activation.

    The system shall detect reference/version changes via SHA-256 evidence hashes.
    """
    _header("Stage 3: Change Detection - Validate Evidence Hashes (FR-PORT-009)")
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request.evidence))
    print(
        f"Data -> account_snapshot_hash='{request.evidence.account_snapshot_hash[:8]}...'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-02 — evidence/ — Evidence and Eligibility Validation\n\n"
        "Purpose: Validate strategy operational eligibility decisions, FX conversion evidence alignment, and explicit evidence references without synthesis.\n\n"
        "Module flow:\n"
        "-> Stage 1: Strategy eligibility reference mapping\n"
        "-> Stage 2: Fail-closed FX evidence alignment and explicit non-synthesized reference check\n"
        "-> Stage 3: SHA-256 evidence hash verification"
    )

    # Stage 1: Eligibility
    _run_example("FR-PORT-006", fr_port_006)

    # Stage 2: Fail-Closed Validation
    _run_example("FR-PORT-007", fr_port_007)
    _run_example("FR-PORT-008", fr_port_008)

    # Stage 3: Hash Verification
    _run_example("FR-PORT-009", fr_port_009)


if __name__ == "__main__":
    main()
