"""Executable Portfolio contracts usage example.

Demonstrates portfolio construction request model construction and serialization.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio.contracts import PortfolioConstructionRequest

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


def example_contracts() -> None:
    """Demonstrate Portfolio contracts and serialization."""
    print("=" * 80)
    print("Portfolio Example 1: Construction Request Contracts")
    print("=" * 80)

    request_data = {
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
        "evidence": {
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
        },
        "measurement_start": datetime(2026, 7, 1, tzinfo=UTC),
        "measurement_end": NOW,
        "base_currency": "USD",
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "simulation_policy_version": "v1",
        "requested_at": NOW,
    }

    request = PortfolioConstructionRequest(**request_data)
    wire_value = request.model_dump(mode="json")

    print(f"Contract version: {wire_value['contract_version']}")
    print(f"Schema ID: {wire_value['schema_id']}")
    print(f"Components count: {len(wire_value['components'])}")
    print(f"First component strategy ID: {wire_value['components'][0]['strategy_id']}")


def main() -> None:
    """Run Portfolio contracts usage example."""
    example_contracts()


if __name__ == "__main__":
    main()
