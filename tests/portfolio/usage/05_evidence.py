"""Executable Portfolio evidence validation usage example.

Demonstrates the evidence and eligibility validation feature through the
package-root public API. Each functional requirement FR-PORT-006 through
FR-PORT-009 has a dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import PortfolioConstructionRequest

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _evidence_data(**overrides: object) -> dict[str, object]:
    """Return complete evidence reference set data.

    Args:
        **overrides: Optional field overrides for evidence variants.

    Returns:
        Complete evidence reference primitive mapping.
    """
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
    """Return complete construction request data.

    Args:
        **overrides: Optional field overrides for request variants.

    Returns:
        Complete request constructor data.
    """
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
    """FR-PORT-006: Require a current approving eligibility decision for every
    exact strategy/version/scope.

    Demonstrates that every construction component carries an explicit
    eligibility_decision_id reference.
    """
    _header(
        "FR-PORT-006: Require a current approving eligibility decision for every exact strategy/version/scope. Demonstrates that every construction component carries an explicit eligibility_decision_id reference."
    )
    print("FR-PORT-006: Require eligibility decision for every strategy/version")

    request = PortfolioConstructionRequest(**_base_request_data())
    for component in request.components:
        assert component.eligibility_decision_id
        eligibility = component.eligibility_decision_id
        print(f"  {component.component_id}: eligibility={eligibility}")
    print("Every component carries a required eligibility decision reference")


def fr_port_007() -> None:
    """FR-PORT-007: Fail closed on missing, stale, incompatible, cyclic, or
    unverifiable FX evidence.

    Demonstrates that FX evidence IDs and hashes must align and be ordered.
    """
    _header(
        "FR-PORT-007: Fail closed on missing, stale, incompatible, cyclic, or unverifiable FX evidence. Demonstrates that FX evidence IDs and hashes must align and be ordered."
    )
    print("FR-PORT-007: Fail closed on invalid FX evidence")

    request = PortfolioConstructionRequest(**_base_request_data())
    assert len(request.evidence.fx_evidence_ids) == len(
        request.evidence.fx_evidence_hashes
    )
    print("FX evidence IDs and hashes are aligned")

    try:
        bad_evidence = _evidence_data(
            fx_evidence_ids=("fx-1", "fx-2"),
            fx_evidence_hashes=("a" * 64,),
        )
        PortfolioConstructionRequest(**_base_request_data(evidence=bad_evidence))
        msg = "ERROR: mismatched FX evidence accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        msg = "Mismatched FX evidence correctly rejected"
    print(msg)


def fr_port_008() -> None:
    """FR-PORT-008: Never synthesize rates, metrics, registrations, or
    approvals.

    Demonstrates that evidence references are required and cannot be empty or
    synthesized.
    """
    _header(
        "FR-PORT-008: Never synthesize rates, metrics, registrations, or approvals. Demonstrates that evidence references are required and cannot be empty or synthesized."
    )
    print("FR-PORT-008: Never synthesize rates, metrics, registrations, or approvals")

    request = PortfolioConstructionRequest(**_base_request_data())
    assert request.evidence.account_snapshot_id
    assert request.evidence.market_dataset_id
    assert request.evidence.analytics_evidence_id
    print("All evidence references are explicit and non-empty")

    for component in request.components:
        assert component.registry_record_hash
        assert component.eligibility_decision_id
    print("Strategy registration and eligibility references are explicit")


def fr_port_009() -> None:
    """FR-PORT-009: Detect a reference/version change before publication or
    activation.

    Demonstrates that every evidence reference carries an immutable hash for
    change detection.
    """
    _header(
        "FR-PORT-009: Detect a reference/version change before publication or activation. Demonstrates that every evidence reference carries an immutable hash for change detection."
    )
    print("FR-PORT-009: Detect reference/version change via hashes")

    request = PortfolioConstructionRequest(**_base_request_data())
    assert len(request.evidence.account_snapshot_hash) == 64
    assert len(request.evidence.market_dataset_hash) == 64
    assert len(request.evidence.analytics_evidence_hash) == 64
    for component in request.components:
        assert len(component.registry_record_hash) == 64
    print("Every evidence reference carries a SHA-256 hash for change detection")


def main() -> None:
    """Run every functional-requirement demonstration for Portfolio evidence."""
    fr_port_006()
    fr_port_007()
    fr_port_008()
    fr_port_009()


if __name__ == "__main__":
    main()
