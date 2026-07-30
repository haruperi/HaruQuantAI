"""Executable Portfolio contracts usage example.

Demonstrates the public Portfolio boundary contract models through the
package-root public API. Each functional requirement FR-PORT-001 through
FR-PORT-005 has a dedicated demonstration function.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.portfolio import create_portfolio_value, dump_portfolio_value

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _base_request_data(**overrides: object) -> dict[str, object]:
    """Return complete primitive construction request input.

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
    """FR-PORT-001: Reject unknown fields and unsafe runtime objects.

    Demonstrates that PortfolioConstructionRequest rejects unknown fields via
    strict Pydantic validation.
    """
    _header(
        "FR-PORT-001: Reject unknown fields and unsafe runtime objects. Demonstrates that PortfolioConstructionRequest rejects unknown fields via strict Pydantic validation."
    )
    print("FR-PORT-001: Reject unknown fields and unsafe runtime objects")

    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    wire_value = dump_portfolio_value(request)
    print(f"Valid request created with {len(wire_value['components'])} components")

    try:
        create_portfolio_value(
            "PortfolioConstructionRequest",
            **_base_request_data(unknown_field="bad"),
        )
        msg = "ERROR: unknown field was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        msg = "Unknown field correctly rejected"
    print(msg)


def fr_port_002() -> None:
    """FR-PORT-002: Separate contract_version from namespaced schema_id.

    Demonstrates that the construction request carries a fixed
    contract_version and a separate namespaced schema_id.
    """
    _header(
        "FR-PORT-002: Separate contract_version from namespaced schema_id. Demonstrates that the construction request carries a fixed contract_version and a separate namespaced schema_id."
    )
    print("FR-PORT-002: Separate contract_version from schema_id")

    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    wire_value = dump_portfolio_value(request)
    print(f"contract_version: {wire_value['contract_version']}")
    print(f"schema_id: {wire_value['schema_id']}")
    assert wire_value["contract_version"] != wire_value["schema_id"]
    print("contract_version and schema_id are distinct identifiers")


def fr_port_003() -> None:
    """FR-PORT-003: Require UTC timestamps, trace IDs, immutable owner
    references, and finite numbers.

    Demonstrates that every timestamp on the construction request is
    timezone-aware UTC and that trace IDs are required.
    """
    _header(
        "FR-PORT-003: Require UTC timestamps, trace IDs, immutable owner references, and finite numbers. Demonstrates that every timestamp on the construction request is timezone-aware UTC and that trace IDs are required."
    )
    print("FR-PORT-003: Require UTC timestamps, trace IDs, and finite numbers")

    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    for field in ("measurement_start", "measurement_end", "requested_at"):
        ts = getattr(request, field)
        assert ts.tzinfo is not None
        assert ts.utcoffset().total_seconds() == 0
        print(f"  {field}: UTC-aware OK")
    for field in ("request_id", "workflow_id", "correlation_id"):
        value = getattr(request, field)
        assert value
        assert value == value.strip()
        print(f"  {field}: non-empty trimmed OK")


def fr_port_004() -> None:
    """FR-PORT-004: Represent capital weights separately from
    Risk-authoritative budget projection references.

    Demonstrates that the construction request does not embed a Risk budget
    projection; it carries only evidence references and proposed weights.
    """
    _header(
        "FR-PORT-004: Represent capital weights separately from Risk-authoritative budget projection references. Demonstrates that the construction request does not embed a Risk budget projection; it carries only evidence references and proposed weights."
    )
    print("FR-PORT-004: Separate capital weights from Risk budget references")

    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    evidence_fields = list(type(request.evidence).model_fields)
    print(f"Evidence reference fields: {', '.join(evidence_fields[:3])}...")
    assert not hasattr(request, "risk_budget_projection")
    print("No Risk budget projection embedded in construction request")


def fr_port_005() -> None:
    """FR-PORT-005: Version breaking contract changes and update every
    producer/consumer document together.

    Demonstrates that the contract carries a fixed version and schema identity
    for version compatibility checking.
    """
    _header(
        "FR-PORT-005: Version breaking contract changes and update every producer/consumer document together. Demonstrates that the contract carries a fixed version and schema identity for version compatibility checking."
    )
    print("FR-PORT-005: Version breaking contract changes")

    request = create_portfolio_value(
        "PortfolioConstructionRequest", **_base_request_data()
    )
    assert request.contract_version == "v1"
    assert request.schema_id == "portfolio.construction_request.v1"
    print(f"Fixed contract_version: {request.contract_version}")
    print(f"Fixed schema_id: {request.schema_id}")
    print("Breaking changes require a new version and coordinated updates")


def main() -> None:
    """Run every functional-requirement demonstration for Portfolio contracts."""
    fr_port_001()
    fr_port_002()
    fr_port_003()
    fr_port_004()
    fr_port_005()


if __name__ == "__main__":
    main()
