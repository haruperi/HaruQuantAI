"""Integration evidence for durable Portfolio runtime state."""

from pathlib import Path
from typing import Any, cast

from app.services.data import (
    build_data_settings,
    data_settings_context,
    run_runtime_store_migrations,
    unwrap_data_response,
)
from app.services.portfolio import (
    build_portfolio_state_store,
    execute_portfolio_state_store_operation,
    get_portfolio_value_field,
)
from app.utils import canonical_json, generate_id


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


def test_portfolio_activation_and_history_are_durable(
    tmp_path: Path,
    active_allocation: object,
) -> None:
    """Active state and history survive adapter reconstruction."""
    with data_settings_context(_settings(tmp_path)):
        request_id = generate_id("req")
        unwrap_data_response(
            run_runtime_store_migrations(request_id),
            operation="tests.portfolio.runtime.migrations",
            request_id=request_id,
        )
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
