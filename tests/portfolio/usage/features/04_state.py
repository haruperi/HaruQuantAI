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
    build_migration_request,
    data_settings_context,
    run_domain_migrations,
    unwrap_data_response,
)
from app.services.portfolio import (
    build_portfolio_state_store,
    create_portfolio_value,
    execute_portfolio_state_store_operation,
    get_portfolio_migrations,
    get_portfolio_value_field,
)
from app.utils import canonical_json, generate_id

NOW = datetime(2026, 7, 19, 12, 0, tzinfo=UTC)


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
        run_domain_migrations(
            build_migration_request(
                domain="portfolio",
                steps=get_portfolio_migrations(),
                request_id=request_id,
            )
        ),
        operation="portfolio.usage.migrations",
        request_id=request_id,
    )


def _scope_key(allocation: object) -> str:
    """Return the canonical active-scope key for an allocation."""
    return canonical_json(
        dict(get_portfolio_value_field(allocation, "scope")),
        max_items=None,
    )


def fr_port_033() -> None:
    """FR-PORT-033: Stage 1 — Prevent direct writes by other domains.

    The system shall enforce Portfolio domain ownership over active allocation persistence.
    """
    _header(
        "Stage 1: Portfolio State Isolation - Prevent Direct Cross-Domain Writes (FR-PORT-033)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(f"Data -> allocation_id='{allocation.allocation_id}'")


def fr_port_034() -> None:
    """FR-PORT-034: Stage 3 — Preserve every superseded and rolled-back version.

    The system shall preserve every superseded and rolled-back allocation version in durable history.
    """
    _header(
        "Stage 3: Version Preservation - Retain Superseded Allocations (FR-PORT-034)"
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


def fr_port_035() -> None:
    """FR-PORT-035: Stage 2 — Use atomic activation and deterministic idempotency keys.

    The system shall enforce atomic state activation using deterministic idempotency keys.
    """
    _header(
        "Stage 2: Atomic State Activation - Enforce Idempotent Transitions (FR-PORT-035)"
    )
    allocation = create_portfolio_value(
        "ActivePortfolioAllocation", **_allocation_data()
    )
    print(_format_result(allocation))
    print(f"Data -> idempotency_key='{allocation.idempotency_key}'")


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
    fr_port_033()

    # Stage 2: Atomic Activation
    fr_port_035()

    # Stage 3: Version Preservation
    fr_port_034()

    # Stage 4: Direct Relational Persistence
    fr_port_044()

    # Stage 5: Atomic Compound Writes
    fr_port_045()


if __name__ == "__main__":
    main()
