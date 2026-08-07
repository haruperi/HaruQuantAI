"""Structural guards for the private Trading persistence boundary."""

# ruff: noqa: INP001

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.services.trading import persistence
from app.services.trading.persistence import delete, update

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_TRADING_ROOT = _PROJECT_ROOT / "app" / "services" / "trading"
_PERSISTENCE_ROOT = _TRADING_ROOT / "persistence"
_PERSISTENCE_EXPORTS = {
    "create_closed_position_record",
    "create_event_record",
    "create_idempotency_record",
    "create_projection_record",
    "create_trading_runtime_store",
    "read_all_event_records",
    "read_event_records",
    "read_idempotency_record",
    "read_idempotency_record_with_revision",
    "read_projection_record",
    "read_projection_record_with_revision",
    "update_event_projection_records",
    "update_idempotency_record",
    "update_projection_record",
}
_DATA_RUNTIME_OPERATIONS = {
    "build_trading_runtime_store",
    "execute_runtime_store_operation",
}


def test_private_persistence_package_has_exact_crud_layout_and_exports() -> None:
    """Keep Trading database operations behind one predictable boundary."""
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
    """Reject direct Data runtime CRUD calls elsewhere in Trading."""
    violations: list[str] = []
    for path in _TRADING_ROOT.rglob("*.py"):
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


def test_mutable_records_remain_compare_and_swap_guarded() -> None:
    """Keep mutable records guarded by relational revision predicates."""
    idempotency_source = inspect.getsource(persistence.update_idempotency_record)
    projection_source = inspect.getsource(persistence.update_projection_record)

    assert "AND status = ?" in idempotency_source
    assert "WHEN projection_version = ? THEN ? ELSE -1 END" in projection_source


def test_trading_persistence_no_longer_uses_generic_runtime_records() -> None:
    """Trading CRUD targets owned tables through Data transactions only."""
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in _PERSISTENCE_ROOT.glob("*.py")
    )
    assert "data_runtime_records" not in source
    assert "execute_runtime_store_operation" not in source
    assert "build_trading_runtime_store" not in source
    assert "execute_transaction" in source


def test_idempotency_update_detects_revision_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A zero-row compare-and-swap fails closed."""
    value = SimpleNamespace(
        status="completed",
        receipt_id="receipt-1",
        reserved_at=SimpleNamespace(isoformat=lambda: "2026-08-06T00:00:00Z"),
    )
    monkeypatch.setattr(update, "_require_store", lambda store: store)

    def execute(*_args: object) -> SimpleNamespace:
        return SimpleNamespace(affected_rows=0)

    monkeypatch.setattr(update, "_execute", execute)
    with pytest.raises(ValueError, match="revision conflict"):
        update.update_idempotency_record(
            object(), key="key-1", value=value, expected_revision="new"
        )
