"""Structural guards for the private Agentic persistence boundary."""

import ast
import inspect
from pathlib import Path

from app.agentic import persistence
from app.agentic.persistence import delete

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_AGENTIC_ROOT = _PROJECT_ROOT / "app" / "agentic"
_PERSISTENCE_ROOT = _AGENTIC_ROOT / "persistence"
_PERSISTENCE_EXPORTS = {
    "create_agentic_persistence_store",
    "create_evidence_claim",
    "create_experiment_holdout_use",
    "create_experiment_run",
    "create_experiment_spec",
    "create_experiment_verdict",
    "create_incident_record",
    "create_lifecycle_packet_record",
    "create_lifecycle_record",
    "create_memory_record",
    "create_operation_trace_record",
    "create_replay_record",
    "create_workflow_checkpoint_record",
    "create_workflow_run_reservation",
    "read_incident_records",
    "read_evidence_claims",
    "read_experiment_holdout_use",
    "read_experiment_runs",
    "read_experiment_spec",
    "read_experiment_verdict",
    "read_lifecycle_packet_record",
    "read_lifecycle_records",
    "read_memory_records",
    "read_operation_trace_record",
    "read_workflow_checkpoint_records",
    "read_workflow_idempotency_record",
    "read_workflow_run_record",
    "update_workflow_run_record",
}
_FORBIDDEN_RUNTIME_OPERATIONS = {
    "build_agentic_runtime_store",
    "execute_runtime_store_operation",
    "execute_runtime_store_transition",
}


def test_private_persistence_package_has_exact_crud_layout_and_exports() -> None:
    """Keep Agentic database operations behind one predictable boundary."""
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


def test_generic_runtime_store_is_absent_from_agentic() -> None:
    """Reject the generic runtime store throughout Agentic production code."""
    violations: list[str] = []
    for path in _AGENTIC_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in _FORBIDDEN_RUNTIME_OPERATIONS
            ):
                violations.append(f"{path.relative_to(_PROJECT_ROOT)}:{node.lineno}")
    assert violations == []


def test_relational_uniqueness_and_updates_remain_guarded() -> None:
    """Keep uniqueness relational and workflow replacement revision guarded."""
    incident_source = inspect.getsource(persistence.create_incident_record)
    reservation_source = inspect.getsource(persistence.create_workflow_run_reservation)
    update_source = inspect.getsource(persistence.update_workflow_run_record)

    assert "INSERT OR IGNORE INTO agentic_operations_incidents" in incident_source
    assert "INSERT OR IGNORE INTO agentic_workflow_runs" in reservation_source
    assert "WHERE run_id=? AND revision=?" in update_source
    persistence_source = "".join(
        path.read_text(encoding="utf-8") for path in _PERSISTENCE_ROOT.glob("*.py")
    )
    assert "data_runtime_records" not in persistence_source
