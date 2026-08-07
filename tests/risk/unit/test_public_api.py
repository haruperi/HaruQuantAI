"""Unit tests for the exact public and persistence Risk package ports."""

import ast
import inspect
from pathlib import Path

from app.services import risk
from app.services.risk import persistence
from app.services.risk.persistence import delete
from app.utils import get_standard_response_type

from tests.risk import _support as examples

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_RISK_ROOT = _PROJECT_ROOT / "app" / "services" / "risk"
_PERSISTENCE_ROOT = _RISK_ROOT / "persistence"
_PERSISTENCE_EXPORTS = {
    "create_active_allocation_record",
    "create_allocation_review_record",
    "create_approval_state_record",
    "create_audit_record",
    "create_decision_record",
    "create_eligibility_record",
    "create_policy_version",
    "create_risk_runtime_store",
    "read_active_allocation_record",
    "read_active_allocation_record_with_revision",
    "read_approval_index_records",
    "read_approval_state_record",
    "read_approval_state_record_with_revision",
    "read_audit_record",
    "read_audit_records",
    "read_decision_record",
    "read_decision_records",
    "read_kill_switch_record",
    "read_policy_version",
    "update_active_allocation_record",
    "update_approval_state_record",
    "update_kill_switch_with_audit",
}
_DATA_RUNTIME_OPERATIONS = {
    "build_risk_runtime_store",
    "execute_runtime_store_operation",
    "execute_runtime_store_transition",
}


def test_root_public_api_is_exact_and_resolvable() -> None:
    """Expose every approved standalone operation and no private state port."""
    expected = {name for name in risk.__all__ if callable(getattr(risk, name))}
    assert set(risk.__all__) == expected
    assert all(hasattr(risk, name) for name in risk.__all__)
    assert all(
        getattr(risk, name).__class__.__name__ == "function" for name in risk.__all__
    )
    assert not any(name.startswith("_") for name in risk.__all__)


def test_public_operation_uses_standard_response_boundary() -> None:
    """Expose raw Risk results inside the shared response envelope."""
    response = risk.compute_config_hash(examples._config())

    assert isinstance(response, get_standard_response_type())
    assert response.status == "success"
    assert len(response.data) == 64
    assert response.error is None
    assert response.metadata.domain == "risk"
    assert response.metadata.read_only is True
    assert response.metadata.places_trade is False
    assert response.metadata.requires_network is False


def test_private_persistence_package_has_exact_crud_layout_and_exports() -> None:
    """Keep Risk database operations behind one predictable private boundary."""
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


def test_data_runtime_crud_calls_are_confined_to_persistence() -> None:
    """Reject direct Data runtime CRUD calls elsewhere in the Risk domain."""
    violations: list[str] = []
    for path in _RISK_ROOT.rglob("*.py"):
        if _PERSISTENCE_ROOT in path.parents:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in _DATA_RUNTIME_OPERATIONS
            ):
                violations.append(f"{path.relative_to(_PROJECT_ROOT)}:{node.lineno}")
    assert violations == []


def test_compound_persistence_writes_remain_single_transitions() -> None:
    """Keep approval issuance and kill-switch audit writes relational."""
    approval_source = inspect.getsource(persistence.create_approval_state_record)
    kill_switch_source = inspect.getsource(persistence.update_kill_switch_with_audit)

    assert approval_source.count("_execute(") == 1
    assert "risk_approval_tokens" in approval_source
    assert kill_switch_source.count("_execute(") == 1
    assert "risk_kill_switch_states" in kill_switch_source
    assert "risk_audit_records" in kill_switch_source


def test_risk_persistence_no_longer_uses_generic_runtime_records() -> None:
    """Risk CRUD targets owned tables through Data transactions only."""
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in _PERSISTENCE_ROOT.glob("*.py")
    )
    assert "data_runtime_records" not in source
    assert "execute_runtime_store_operation" not in source
    assert "execute_runtime_store_transition" not in source
    assert "build_risk_runtime_store" not in source
    assert "execute_transaction" in source
