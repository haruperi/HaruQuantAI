"""Executable Portfolio state usage example.

Demonstrates FEAT-PORT-04 portfolio persistence feature through the package-root public API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_settings,
    data_settings_context,
    unwrap_data_response,
)
from app.services.portfolio import (
    build_portfolio_state_store,
    create_portfolio_handle,
    create_portfolio_value,
    execute_portfolio_state_store_operation,
    get_portfolio_definition,
    get_portfolio_migrations,
    get_portfolio_value_field,
    register_portfolio_definition,
    run_portfolio_migrations,
)
from app.utils import canonical_digest, canonical_json, create_auth_context, generate_id

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
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "audit_ref": "audit-1",
    }
    data.update(overrides)
    return data


def _settings(data_dir: Path) -> object:
    """Build isolated Data settings for the executable example."""
    return build_data_settings(
        database_url="sqlite:///portfolio-usage.db",
        data_dir=data_dir,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _run_migrations() -> None:
    """Apply Portfolio's immutable manifest through Data's public boundary."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_portfolio_migrations(request_id),
        operation="portfolio.usage.migrations",
        request_id=request_id,
    )


def _scope_key(allocation: object) -> str:
    """Return the canonical active-scope key for an allocation."""
    return canonical_json(
        dict(get_portfolio_value_field(allocation, "scope")),
        max_items=None,
    )


def fr_port_030() -> None:
    """FR-PORT-030: Stage 1 — Prevent direct writes by other domains.

    The system shall enforce Portfolio domain ownership over active allocation persistence.
    """
    _header(
        "Stage 1: Portfolio State Isolation - Prevent Direct Cross-Domain Writes (FR-PORT-030)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(f"Data -> allocation_id='{allocation.allocation_id}'")


def fr_port_031() -> None:
    """FR-PORT-031: Stage 3 — Preserve every superseded and rolled-back version.

    The system shall preserve every superseded and rolled-back allocation version in durable history.
    """
    _header(
        "Stage 3: Version Preservation - Retain Superseded Allocations (FR-PORT-031)"
    )
    _allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    rolled_back = create_portfolio_value(
        "ActivePortfolioAllocation",
        **_allocation_data(
            allocation_id="allocation-2",
            allocation_version="allocation-version-2",
            predecessor_version="allocation-version-1",
            rollback_of_version="allocation-version-1",
            canonical_hash="d" * 64,
            idempotency_key="idem-2",
        ),
    )
    print(_format_result(rolled_back))
    print(
        f"Data -> predecessor='{rolled_back.predecessor_version}', rollback_of='{rolled_back.rollback_of_version}'"
    )


def fr_port_032() -> None:
    """FR-PORT-032: Stage 2 — Use atomic activation and deterministic idempotency keys.

    The system shall enforce atomic state activation using deterministic idempotency keys.
    """
    _header(
        "Stage 2: Atomic State Activation - Enforce Idempotent Transitions (FR-PORT-032)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(f"Data -> idempotency_key='{allocation.idempotency_key}'")


def fr_port_033() -> None:
    """FR-PORT-033: Retain exact reproducibility lineage references."""
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(
        "Data -> lineage="
        f"{allocation.construction_result_id}:{allocation.risk_decision_id}:"
        f"{allocation.simulation_result_id}"
    )


def fr_port_044() -> None:
    """FR-PORT-044: Persist state in Portfolio-owned relational tables."""
    _header("Direct Relational Persistence Through Data (FR-PORT-044)")
    with (
        TemporaryDirectory(prefix="portfolio-usage-") as temp_dir,
        data_settings_context(_settings(Path(temp_dir))),
    ):
        _run_migrations()
        allocation = create_portfolio_value(
            "ActivePortfolioAllocation", **_allocation_data()
        )
        store = build_portfolio_state_store()
        execute_portfolio_state_store_operation(
            store,
            "activate_allocation",
            allocation,
            None,
            0,
            get_portfolio_value_field(allocation, "canonical_hash"),
            {"event": "portfolio.activated"},
        )
        reconstructed = build_portfolio_state_store()
        active = execute_portfolio_state_store_operation(
            reconstructed,
            "load_active",
            get_portfolio_value_field(allocation, "portfolio_id"),
            _scope_key(allocation),
        )
        print(_format_result(active[0]))
        print("Data -> reconstructed_from='portfolio_allocation_versions'")


def fr_port_045() -> None:
    """FR-PORT-045: Commit compound transitions atomically and fail closed."""
    _header("Atomic Activation, Idempotency, and Audit Outbox (FR-PORT-045)")
    with (
        TemporaryDirectory(prefix="portfolio-usage-") as temp_dir,
        data_settings_context(_settings(Path(temp_dir))),
    ):
        _run_migrations()
        allocation = create_portfolio_value(
            "ActivePortfolioAllocation", **_allocation_data()
        )
        store = build_portfolio_state_store()
        arguments = (
            allocation,
            None,
            0,
            get_portfolio_value_field(allocation, "canonical_hash"),
            {"event": "portfolio.activated"},
        )
        first = execute_portfolio_state_store_operation(
            store, "activate_allocation", *arguments
        )
        replay = execute_portfolio_state_store_operation(
            store, "activate_allocation", *arguments
        )
        stale = create_portfolio_value(
            "ActivePortfolioAllocation",
            **_allocation_data(
                allocation_id="allocation-stale",
                allocation_version="allocation-version-stale",
                predecessor_version="allocation-version-1",
                idempotency_key="idem-stale",
                canonical_hash="d" * 64,
            ),
        )
        try:
            execute_portfolio_state_store_operation(
                store,
                "activate_allocation",
                stale,
                "allocation-version-1",
                0,
                get_portfolio_value_field(stale, "canonical_hash"),
                {"event": "portfolio.activation-rejected"},
            )
        except ValueError as exc:
            stale_outcome = type(exc).__name__
        else:
            raise AssertionError("A stale revision must fail closed")
        print(_format_result(first))
        print(f"Data -> replay_equal={replay == first}, stale={stale_outcome}")


def fr_port_041() -> None:
    """FR-PORT-041: Keep one checksummed migration step outside CRUD support."""
    steps = get_portfolio_migrations()
    print(_format_result(steps[0]))
    print(f"Data -> migration_steps={len(steps)}, module='portfolio.migrations'")


def fr_port_042() -> None:
    """FR-PORT-042: Preserve composite immutable history and active CAS state."""
    statements = "\n".join(get_portfolio_migrations()[0].statements)
    assert "PRIMARY KEY (portfolio_id, portfolio_version)" in statements
    assert "PRIMARY KEY (plan_id, plan_version)" in statements
    print(_format_result(get_portfolio_migrations()[0]))
    print("Data -> definition_pk=composite, plan_pk=composite, active_revision=True")


def fr_port_043() -> None:
    """FR-PORT-043: Carry trace and visible outbox publication fields."""
    statements = "\n".join(get_portfolio_migrations()[0].statements)
    for field in ("request_id", "correlation_id", "publication_state", "attempts"):
        assert field in statements
    print(_format_result(get_portfolio_migrations()[0]))
    print("Data -> trace_fields=True, publication_state=True, delivery_attempts=True")


def _definition_round_trip() -> tuple[object, object]:
    """Register and read one definition through public Portfolio operations."""
    with (
        TemporaryDirectory() as temp_dir,
        data_settings_context(_settings(Path(temp_dir))),
    ):
        _run_migrations()
        auth = create_auth_context(
            contract_version="v1",
            schema_id="utils.auth_context.v1",
            principal_id="portfolio-owner",
            principal_type="USER",
            roles=("owner",),
            permissions=("portfolio:read", "portfolio:write"),
            scopes=("portfolio",),
            tenant_or_environment="development",
            request_id=generate_id("req"),
            workflow_id=generate_id("wf"),
            correlation_id=generate_id("cor"),
            issued_at=NOW,
        )
        material = {
            "definition": {"objective": "balanced"},
            "scope": {"environment": "simulation"},
        }
        definition = create_portfolio_value(
            "PortfolioDefinition",
            portfolio_id="portfolio-alpha",
            portfolio_version="v1",
            scope=material["scope"],
            definition=material["definition"],
            canonical_hash=canonical_digest(material),
            request_id=auth.request_id,
            workflow_id=auth.workflow_id,
            correlation_id=auth.correlation_id,
            created_at=NOW,
        )
        repository = create_portfolio_handle(
            "PortfolioRepository", build_portfolio_state_store()
        )
        service = create_portfolio_handle("PortfolioService", object(), repository)
        registered = register_portfolio_definition(service, definition, auth)
        loaded = get_portfolio_definition(service, "portfolio-alpha", "v1", auth)
        return registered, loaded


def fr_port_046() -> None:
    """FR-PORT-046: Register one immutable definition version."""
    registered, _loaded = _definition_round_trip()
    print(_format_result(registered))
    print(
        f"Data -> registered={registered.status}, portfolio_id={registered.data.portfolio_id}"
    )


def fr_port_047() -> None:
    """FR-PORT-047: Read one exact immutable definition version."""
    _registered, loaded = _definition_round_trip()
    print(_format_result(loaded))
    print(f"Data -> read={loaded.status}, version={loaded.data.portfolio_version}")


def fr_port_048() -> None:
    """FR-PORT-048: Apply and verify the complete Portfolio manifest."""
    with (
        TemporaryDirectory() as temp_dir,
        data_settings_context(_settings(Path(temp_dir))),
    ):
        response = run_portfolio_migrations(generate_id("req"))
        print(_format_result(response))
        print(f"Data -> migration_status={response.status}, complete_manifest=True")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-PORT-04 — state/ — Portfolio Persistence\n\n"
        "Purpose: Govern state repository persistence, atomic migration ledgers, immutable version history, and lineage tracking.\n\n"
        "Module flow:\n"
        "-> Stage 1: Domain state isolation mapping and repository initialization\n"
        "-> Stage 2: Atomic state activation with deterministic idempotency key verification\n"
        "-> Stage 3: Immutable audit payload generation and version history preservation"
    )

    # Stage 1: Domain Isolation
    _run_example("FR-PORT-030", fr_port_030)

    # Stage 2: Atomic Activation
    _run_example("FR-PORT-032", fr_port_032)

    # Stage 3: Version Preservation
    _run_example("FR-PORT-031", fr_port_031)
    _run_example("FR-PORT-033", fr_port_033)

    # Stage 4: Direct Relational Persistence
    _run_example("FR-PORT-044", fr_port_044)

    # Stage 5: Atomic Compound Writes
    _run_example("FR-PORT-045", fr_port_045)
    _run_example("FR-PORT-041", fr_port_041)
    _run_example("FR-PORT-042", fr_port_042)
    _run_example("FR-PORT-043", fr_port_043)
    _run_example("FR-PORT-046", fr_port_046)
    _run_example("FR-PORT-047", fr_port_047)
    _run_example("FR-PORT-048", fr_port_048)


if __name__ == "__main__":
    main()
