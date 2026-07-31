"""Executable Portfolio contracts usage example.

Demonstrates FEAT-PORT-01 public Portfolio boundary contract models through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import create_portfolio_value, dump_portfolio_value

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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


def _base_request_data(**overrides: object) -> dict[str, object]:
    """Return complete primitive construction request input."""
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
    data.update(overrides)
    return data


def fr_port_001() -> None:
    """FR-PORT-001: Stage 2 — Reject unknown fields and unsafe runtime objects.

    The system shall reject unknown fields and unsafe runtime objects via strict Pydantic validation.
    """
    _header("Stage 2: Validation - Reject Unknown Fields (FR-PORT-001)")
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request))
    print(f"Data -> component_count={len(request.components)}")


def fr_port_002() -> None:
    """FR-PORT-002: Stage 1 — Separate contract_version from namespaced schema_id.

    The system shall separate fixed contract_version from namespaced schema_id in all contracts.
    """
    _header(
        "Stage 1: Versioning - Separate Contract Version from Schema ID (FR-PORT-002)"
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    wire_value = dump_portfolio_value(request)
    print(_format_result(request))
    print(
        f"Data -> contract_version='{wire_value.get('contract_version')}', schema_id='{wire_value.get('schema_id')}'"
    )


def fr_port_003() -> None:
    """FR-PORT-003: Stage 1 — Require UTC timestamps, trace IDs, immutable owner references, and finite numbers.

    The system shall enforce UTC timezone awareness, non-empty trace IDs, and finite numbers.
    """
    _header(
        "Stage 1: Field Invariants - Require UTC Timestamps and Trace IDs (FR-PORT-003)"
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request))
    print(
        f"Data -> request_id='{request.request_id}', workflow_id='{request.workflow_id}'"
    )


def fr_port_004() -> None:
    """FR-PORT-004: Stage 1 — Represent capital weights separately from Risk-authoritative budget projection references.

    The system shall represent capital weights separately from Risk-authoritative budget projection references.
    """
    _header(
        "Stage 1: Weight Representation - Capital Weights vs Risk Budgets (FR-PORT-004)"
    )
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request.evidence))
    print("Data -> risk_budget_projection_embedded=False")


def fr_port_005() -> None:
    """FR-PORT-005: Stage 3 — Version breaking contract changes and update every producer/consumer document together.

    The system shall version breaking contract changes explicitly via fixed compatibility versions.
    """
    _header("Stage 3: Contract Versioning - Fixed Version Compatibility (FR-PORT-005)")
    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    print(_format_result(request))
    print(f"Data -> contract_version='{request.contract_version}'")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-01 — contracts/ — Portfolio Boundary Contracts\n\n"
        "Purpose: Define immutable public Portfolio boundary contracts, schema identities, UTC invariants, and validation models.\n\n"
        "Module flow:\n"
        "-> Stage 1: Contract schema definition and payload mapping\n"
        "-> Stage 2: Fail-closed strict Pydantic payload validation and unknown field rejection\n"
        "-> Stage 3: Immutable contract envelope construction"
    )

    # Stage 1: Schemas & Invariants
    fr_port_002()
    fr_port_003()
    fr_port_004()

    # Stage 2: Strict Validation
    fr_port_001()

    # Stage 3: Contract Construction
    fr_port_005()


if __name__ == "__main__":
    main()
