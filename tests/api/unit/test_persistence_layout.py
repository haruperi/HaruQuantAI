"""Structural guarantees for API-owned CRUD persistence."""

import ast
import inspect
import re
from pathlib import Path

from app.services.api.identity import persistence as identity_persistence
from app.services.api.workstation.simulation_workbench import (
    persistence as simulation_workbench_persistence,
)
from app.services.api.workstation.watchlists import persistence as watchlist_persistence
from app.utils import get_logger

logger = get_logger(__name__)

_API_ROOT = Path(__file__).parents[3] / "app" / "services" / "api"
_PERSISTENCE_ROOTS = (
    _API_ROOT / "identity" / "persistence",
    _API_ROOT / "workstation" / "watchlists" / "persistence",
    _API_ROOT / "workstation" / "simulation_workbench" / "persistence",
)
_EXPECTED_FILES = {"__init__.py", "create.py", "read.py", "update.py", "delete.py"}
_IDENTITY_EXPORTS = {
    "consume_approval_record",
    "create_account_record",
    "create_approval_record",
    "create_idempotency_record",
    "create_settings_record",
    "delete_auth_failure_record",
    "delete_idempotency_record",
    "finalize_idempotency_record",
    "read_account_identity_by_user_id",
    "read_account_record",
    "read_approval_record",
    "read_auth_failure_record",
    "read_auth_lock_record",
    "read_credential_record",
    "read_csrf_record",
    "read_idempotency_record",
    "read_session_record",
    "read_settings_record",
    "replace_active_session_record",
    "revoke_session_record",
    "update_account_last_login",
    "update_auth_failure_record",
    "update_credential_record",
    "update_settings_record",
}
_WATCHLIST_EXPORTS = {
    "create_watchlist_items",
    "create_watchlist_record",
    "delete_watchlist_record",
    "read_watchlist_items",
    "read_watchlist_items_for_account",
    "read_watchlist_record",
    "read_watchlists_for_account",
    "rename_watchlist_record",
    "reorder_watchlists_record",
    "replace_watchlist_items_record",
    "set_default_watchlist_record",
}
_SIMULATION_WORKBENCH_EXPORTS = {
    "create_simulation_batch_item_records",
    "create_simulation_batch_record",
    "create_simulation_result_record",
    "create_simulation_session_record",
    "read_simulation_batch_items",
    "read_simulation_batch_record",
    "read_simulation_result_record",
    "read_simulation_results_page",
    "read_simulation_session_record",
    "read_simulation_sessions",
    "annotate_simulation_result_record",
    "archive_simulation_result_record",
    "cancel_simulation_batch_item_records",
    "retry_simulation_batch_item_record",
    "transition_simulation_batch_item_record",
    "transition_simulation_result_completion",
    "update_simulation_batch_record",
    "update_simulation_session_record",
}
_SQL_PATTERNS = (
    re.compile(r"^SELECT\s+.+\s+FROM\s+"),
    re.compile(r"^INSERT\s+(?:OR\s+\w+\s+)?INTO\s+"),
    re.compile(r"^UPDATE\s+.+\s+SET\s+"),
    re.compile(r"^DELETE\s+FROM\s+"),
)


def test_persistence_package_has_exact_crud_layout() -> None:
    """Verify the private package has only its boundary and four CRUD modules."""
    logger.debug("Checking exact API persistence package layout")
    for root in _PERSISTENCE_ROOTS:
        assert {path.name for path in root.glob("*.py")} == _EXPECTED_FILES


def test_persistence_boundary_exports_only_crud_functions() -> None:
    """Verify the internal boundary exports the intended standalone functions."""
    logger.debug("Checking API persistence function exports")
    boundaries = (
        (identity_persistence, _IDENTITY_EXPORTS),
        (watchlist_persistence, _WATCHLIST_EXPORTS),
        (simulation_workbench_persistence, _SIMULATION_WORKBENCH_EXPORTS),
    )
    for boundary, expected in boundaries:
        assert set(boundary.__all__) == expected
        assert all(inspect.isfunction(getattr(boundary, name)) for name in expected)


def test_api_sql_is_confined_to_persistence_and_migrations() -> None:
    """Verify API business modules contain no CRUD SQL or transaction calls."""
    logger.debug("Checking API SQL ownership boundary")
    violations: list[str] = []
    for path in _API_ROOT.rglob("*.py"):
        if (
            any(root in path.parents for root in _PERSISTENCE_ROOTS)
            or "migrations" in path.parts
            or path.name == "migrations.py"
        ):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(
                    node.func,
                    "attr",
                    None,
                )
                if name == "execute_transaction":
                    violations.append(f"{path}: execute_transaction")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                normalized = " ".join(node.value.upper().split())
                if any(pattern.search(normalized) for pattern in _SQL_PATTERNS):
                    violations.append(f"{path}: SQL literal")
    assert not violations, violations
