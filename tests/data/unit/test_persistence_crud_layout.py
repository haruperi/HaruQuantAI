"""Structural regression tests for centralized Data-owned CRUD persistence."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.services.data import persistence
from app.services.data.persistence import update

DATA_ROOT = Path("app/services/data")
CRUD_MODULES = frozenset({"create.py", "read.py", "update.py", "delete.py"})
_CRUD_SQL = re.compile(
    r"^\s*(?:SELECT\b.+\bFROM|INSERT\s+(?:OR\s+\w+\s+)?INTO|UPDATE\s+\w+|DELETE\s+FROM)\b",
)


def _production_files_outside_persistence() -> tuple[Path, ...]:
    """Return Data production modules that may consume persistence operations."""
    return tuple(
        path
        for path in DATA_ROOT.rglob("*.py")
        if "persistence" not in path.parts
        and path.name != "migrations.py"
        and "__pycache__" not in path.parts
    )


def test_data_persistence_contains_the_four_crud_modules() -> None:
    """Keep the approved CRUD naming convention beside persistence infrastructure."""
    actual = {path.name for path in (DATA_ROOT / "persistence").glob("*.py")}
    assert actual >= CRUD_MODULES


def test_crud_operations_are_exported_by_the_persistence_boundary() -> None:
    """Expose Data-owned CRUD only through the persistence package boundary."""
    for prefix in ("create_", "read_", "update_", "delete_"):
        names = {name for name in persistence.__all__ if name.startswith(prefix)}
        assert names
        assert all(callable(getattr(persistence, name)) for name in names)


def test_data_modules_do_not_execute_transactions_or_embed_crud_sql() -> None:
    """Prevent Data feature runtimes from becoming parallel CRUD owners again."""
    offenders: dict[str, list[str]] = {}
    for path in _production_files_outside_persistence():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        findings: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in {
                "app.services.data.persistence.create",
                "app.services.data.persistence.delete",
                "app.services.data.persistence.read",
                "app.services.data.persistence.update",
            }:
                findings.append(f"deep persistence import on line {node.lineno}")
            if isinstance(node, ast.Name) and node.id in {
                "_execute_transaction_raw",
                "execute_transaction",
            }:
                findings.append(node.id)
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and _CRUD_SQL.search(node.value)
            ):
                findings.append(f"CRUD SQL on line {node.lineno}")
        if findings:
            offenders[str(path.relative_to(DATA_ROOT))] = sorted(set(findings))
    assert not offenders


def test_compound_state_changes_remain_single_transactions() -> None:
    """Guard atomic source, backfill, and runtime-store compound mutations."""
    module_source = Path(update.__file__).read_text(encoding="utf-8")
    tree = ast.parse(module_source)
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    for name in (
        "update_source_state_with_audit",
        "update_backfill_finalization",
        "update_runtime_transition_records",
    ):
        calls = [
            node
            for node in ast.walk(functions[name])
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_execute_update"
        ]
        assert len(calls) == 1

    assert "data_source_state" in module_source
    assert "data_audit_events" in module_source
    assert "data_backfill_checkpoints" in module_source
    assert "data_update_jobs" in module_source
    assert "WHERE changes() = 1" in module_source
