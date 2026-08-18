"""Structural guards for the private Simulator persistence boundary."""

import ast
import inspect
from pathlib import Path

from app.services.simulator import persistence
from app.services.simulator.persistence import delete

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SIMULATOR_ROOT = _PROJECT_ROOT / "app" / "services" / "simulator"
_PERSISTENCE_ROOT = _SIMULATOR_ROOT / "persistence"
_PERSISTENCE_EXPORTS = {
    "append_interactive_intent_and_checkpoint",
    "complete_run_record",
    "create_interactive_intent_record",
    "create_interactive_session_record",
    "create_recovery_checkpoint_record",
    "create_run_record",
    "create_session_record",
    "create_simulator_persistence_store",
    "read_completed_run_record",
    "read_interactive_intent_records",
    "read_interactive_session_record",
    "read_recovery_checkpoint_records",
    "read_result_record",
    "read_run_record",
    "read_session_record",
    "update_interactive_session_record",
    "update_run_record",
    "update_secured_session_record",
    "update_session_record",
}
_DATA_RUNTIME_OPERATIONS = {
    "build_simulator_runtime_store",
    "execute_runtime_store_operation",
    "execute_runtime_store_transition",
}


def test_private_persistence_package_has_exact_crud_layout_and_exports() -> None:
    """Keep Simulator database operations behind one predictable boundary."""
    assert {path.name for path in _PERSISTENCE_ROOT.glob("*.py")} == {
        "__init__.py",
        "create.py",
        "delete.py",
        "read.py",
        "update.py",
    }
    assert set(persistence.__all__) == _PERSISTENCE_EXPORTS
    assert all(
        inspect.isfunction(getattr(persistence, name)) for name in persistence.__all__
    )
    assert delete.__all__ == []


def test_generic_data_runtime_crud_is_absent_from_simulator() -> None:
    """Reject every generic runtime-store operation in Simulator."""
    violations: list[str] = []
    for path in _SIMULATOR_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in _DATA_RUNTIME_OPERATIONS
            ):
                violations.append(f"{path.relative_to(_PROJECT_ROOT)}:{node.lineno}")
    assert violations == []


def test_run_lifecycle_updates_remain_compare_and_swap_guarded() -> None:
    """Keep Simulator replacement identity and prior-state guarded."""
    source = inspect.getsource(persistence.update_run_record)

    assert "UPDATE sim_runs" in source
    assert "request_hash=?" in source
    assert "run_id=?" in source
    assert "status=?" in source
