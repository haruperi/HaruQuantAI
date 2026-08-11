"""Structural guarantees for Strategy-owned CRUD persistence."""

import ast
import inspect
from pathlib import Path

from app.services.strategy import persistence
from app.services.strategy.persistence import delete
from app.utils import get_logger

logger = get_logger(__name__)

_STRATEGY_ROOT = Path(__file__).parents[3] / "app" / "services" / "strategy"
_PERSISTENCE_ROOT = _STRATEGY_ROOT / "persistence"
_EXPECTED_FILES = {"__init__.py", "create.py", "read.py", "update.py", "delete.py"}
_EXPECTED_EXPORTS = {
    "create_strategy_automation_policy_record",
    "create_strategy_checkpoint_record",
    "create_strategy_lifecycle_record",
    "create_strategy_plan_record",
    "create_strategy_playbook_record",
    "create_strategy_profile_record",
    "create_strategy_setup_evaluation_record",
    "create_strategy_signal_records",
    "create_strategy_version_record",
    "read_strategy_automation_policies",
    "read_strategy_checkpoint_record",
    "read_strategy_checkpoints",
    "read_strategy_config_record",
    "read_strategy_configs",
    "read_strategy_definitions",
    "read_strategy_lifecycle",
    "read_strategy_manifest_record",
    "read_strategy_mutation_record",
    "read_strategy_plans",
    "read_strategy_playbooks",
    "read_strategy_policy_record",
    "read_strategy_profiles",
    "read_strategy_setup_evaluations",
    "read_strategy_signals",
    "read_strategy_state_record",
    "read_strategy_versions",
    "update_strategy_configuration_record",
    "update_strategy_mutation_publication",
    "update_strategy_runtime_state_record",
    "update_strategy_signal_publication_record",
}
_SQL_PREFIXES = ("SELECT ", "INSERT ", "UPDATE ", "DELETE ")


def _business_module_trees() -> tuple[tuple[Path, ast.AST], ...]:
    """Parse Strategy business modules once during test-module discovery."""
    return tuple(
        (path, ast.parse(path.read_text(encoding="utf-8")))
        for path in _STRATEGY_ROOT.rglob("*.py")
        if _PERSISTENCE_ROOT not in path.parents and "migrations" not in path.parts
    )


_BUSINESS_MODULE_TREES = _business_module_trees()


def test_persistence_package_has_exact_crud_layout() -> None:
    """Verify the private package has only its boundary and four CRUD modules."""
    logger.debug("Checking exact Strategy persistence package layout")
    assert {path.name for path in _PERSISTENCE_ROOT.glob("*.py")} == _EXPECTED_FILES


def test_persistence_boundary_exports_only_crud_functions() -> None:
    """Verify the internal boundary exports the intended standalone functions."""
    logger.debug("Checking Strategy persistence function exports")
    assert set(persistence.__all__) == _EXPECTED_EXPORTS
    assert all(
        inspect.isfunction(getattr(persistence, name)) for name in persistence.__all__
    )
    assert delete.__all__ == []


def _sql_confinement_violations() -> list[str]:
    """Compute Strategy business-module SQL confinement violations once."""
    violations: list[str] = []
    for path, tree in _BUSINESS_MODULE_TREES:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", None) or getattr(
                    node.func, "attr", None
                )
                if name == "execute_transaction":
                    violations.append(f"{path}: execute_transaction")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                normalized = " ".join(node.value.upper().split())
                if normalized.startswith(_SQL_PREFIXES):
                    violations.append(f"{path}: SQL literal")
    return violations


_SQL_CONFINEMENT_VIOLATIONS = _sql_confinement_violations()


def test_strategy_sql_is_confined_to_persistence_and_migrations() -> None:
    """Verify Strategy business modules contain no CRUD SQL or transaction calls."""
    logger.debug("Checking Strategy SQL ownership boundary")
    assert not _SQL_CONFINEMENT_VIOLATIONS, _SQL_CONFINEMENT_VIOLATIONS
