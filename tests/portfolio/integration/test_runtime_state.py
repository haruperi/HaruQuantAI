"""Integration evidence for durable Portfolio runtime state."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from app.services.data import (
    build_data_settings,
    build_migration_request,
    build_statement_plan,
    build_transaction_request,
    data_settings_context,
    execute_transaction,
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

_ROW_COUNT_STATEMENTS = {
    "portfolio_active_scopes": (
        "SELECT COUNT(*) AS row_count FROM portfolio_active_scopes"
    ),
    "portfolio_allocation_versions": (
        "SELECT COUNT(*) AS row_count FROM portfolio_allocation_versions"
    ),
    "portfolio_audit_outbox": (
        "SELECT COUNT(*) AS row_count FROM portfolio_audit_outbox"
    ),
    "portfolio_construction_results": (
        "SELECT COUNT(*) AS row_count FROM portfolio_construction_results"
    ),
    "portfolio_idempotency": (
        "SELECT COUNT(*) AS row_count FROM portfolio_idempotency"
    ),
    "portfolio_rebalance_plans": (
        "SELECT COUNT(*) AS row_count FROM portfolio_rebalance_plans"
    ),
}


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///portfolio-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _run_portfolio_migrations() -> None:
    """Apply the Portfolio manifest through Data's public executor."""
    request_id = generate_id("req")
    unwrap_data_response(
        run_domain_migrations(
            build_migration_request(
                domain="portfolio",
                steps=get_portfolio_migrations(),
                request_id=request_id,
            )
        ),
        operation="tests.portfolio.migrations",
        request_id=request_id,
    )


def _row_count(table: str) -> int:
    """Return one bounded table row count through Data's public executor."""
    request_id = generate_id("req")
    result = unwrap_data_response(
        execute_transaction(
            build_transaction_request(
                plan=build_statement_plan(
                    statements=(_ROW_COUNT_STATEMENTS[table],),
                    parameter_sets=((),),
                    max_rows=1,
                ),
                request_id=request_id,
            )
        ),
        operation="tests.portfolio.row_count",
        request_id=request_id,
    )
    return int(result.rows[0]["row_count"])


def _plan() -> object:
    """Build one immutable plan through Portfolio's public value factory."""
    return create_portfolio_value(
        "PortfolioRebalancePlan",
        plan_id="plan-one",
        plan_version="v1",
        portfolio_id="portfolio-alpha",
        allocation_version="allocation-version-1",
        scope={"environment": "simulation"},
        observations=(
            {
                "component_id": "component-one",
                "target_risk_budget": Decimal("0.5"),
                "actual_risk_budget": Decimal("0.5"),
                "drift": Decimal(0),
                "threshold_breached": False,
            },
        ),
        actions=(),
        status="no_action",
        block_reasons=(),
        evidence_hash="a" * 64,
        config_hash="b" * 64,
        canonical_hash="c" * 64,
        observed_at=datetime(2026, 8, 4, tzinfo=UTC),
        created_at=datetime(2026, 8, 4, tzinfo=UTC),
        risk_decision_id=None,
        trading_execution_ref=None,
        analytics_measurement_ref=None,
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )


def test_portfolio_activation_and_history_are_durable(
    tmp_path: Path,
    active_allocation: object,
) -> None:
    """Active state and history survive adapter reconstruction."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        allocation = cast("Any", active_allocation)
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
        scope = canonical_json(
            dict(get_portfolio_value_field(allocation, "scope")),
            max_items=None,
        )
        active = execute_portfolio_state_store_operation(
            reconstructed,
            "load_active",
            get_portfolio_value_field(allocation, "portfolio_id"),
            scope,
        )
        history = execute_portfolio_state_store_operation(
            reconstructed,
            "load_history",
            get_portfolio_value_field(allocation, "portfolio_id"),
        )
        assert active is not None
        assert active[0] == allocation
        assert history == (allocation,)

        replay = execute_portfolio_state_store_operation(
            reconstructed,
            "activate_allocation",
            allocation,
            None,
            0,
            allocation.canonical_hash,
            {"event": "portfolio.activated"},
        )
        assert replay == allocation
        assert execute_portfolio_state_store_operation(
            reconstructed,
            "load_history",
            allocation.portfolio_id,
        ) == (allocation,)

        stale = allocation.model_copy(
            update={
                "allocation_id": "allocation-stale",
                "allocation_version": "allocation-version-stale",
                "predecessor_version": allocation.allocation_version,
                "idempotency_key": "activation-idempotency-stale",
                "canonical_hash": "7" * 64,
            }
        )
        with pytest.raises(ValueError, match="revision conflicts"):
            execute_portfolio_state_store_operation(
                reconstructed,
                "activate_allocation",
                stale,
                allocation.allocation_version,
                0,
                stale.canonical_hash,
                {"event": "portfolio.activation-rejected"},
            )
        unchanged_history = execute_portfolio_state_store_operation(
            reconstructed,
            "load_history",
            allocation.portfolio_id,
        )
        assert unchanged_history == (allocation,)
        assert _row_count("portfolio_allocation_versions") == 1
        assert _row_count("portfolio_active_scopes") == 1
        assert _row_count("portfolio_idempotency") == 1
        assert _row_count("portfolio_audit_outbox") == 1


def test_portfolio_construction_and_plan_are_durable(
    tmp_path: Path,
    construction_result: object,
) -> None:
    """Construction and plan rows survive adapter reconstruction."""
    with data_settings_context(_settings(tmp_path)):
        _run_portfolio_migrations()
        store = build_portfolio_state_store()
        execute_portfolio_state_store_operation(
            store,
            "save_construction",
            construction_result,
            {"event": "portfolio.constructed"},
        )
        plan = _plan()
        execute_portfolio_state_store_operation(
            store,
            "save_plan",
            plan,
            {"event": "portfolio.plan-created"},
        )
        reconstructed = build_portfolio_state_store()
        assert (
            execute_portfolio_state_store_operation(
                reconstructed,
                "save_construction",
                construction_result,
                {"event": "portfolio.constructed"},
            )
            == construction_result
        )
        assert (
            execute_portfolio_state_store_operation(
                reconstructed,
                "load_plan",
                cast("Any", plan).plan_id,
                cast("Any", plan).plan_version,
            )
            == plan
        )
        assert _row_count("portfolio_construction_results") == 1
        assert _row_count("portfolio_rebalance_plans") == 1
        assert _row_count("portfolio_audit_outbox") == 2
