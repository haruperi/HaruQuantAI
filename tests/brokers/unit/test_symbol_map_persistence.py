"""Unit evidence for the remaining Broker migration and persistence support."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import pytest
from app.services.brokers import persistence
from app.services.brokers.migrations import (
    BROKER_MIGRATIONS,
    BROKER_SCHEMA_VERSION,
    get_broker_migrations,
    run_broker_migrations,
)
from app.services.brokers.migrations import definitions as migration_definitions
from app.services.brokers.persistence import create, delete, read, update

_FAKE_RESULT: dict[str, object] = {"status": "success", "data": ("row",)}


def _capture_executor(
    monkeypatch: pytest.MonkeyPatch, module: ModuleType
) -> dict[str, Any]:
    """Capture the transaction request built by one persistence module."""
    captured: dict[str, Any] = {}

    def fake_build_statement_plan(**kwargs: Any) -> dict[str, Any]:
        return kwargs

    def fake_build_transaction_request(
        *, plan: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        request = {**plan, "request_id": request_id}
        captured["request"] = request
        return request

    def fake_execute_transaction(request: object) -> dict[str, object]:
        captured["executed"] = request
        return _FAKE_RESULT

    monkeypatch.setattr(
        module, "build_transaction_request", fake_build_transaction_request
    )
    monkeypatch.setattr(module, "build_statement_plan", fake_build_statement_plan)
    monkeypatch.setattr(module, "execute_transaction", fake_execute_transaction)
    return captured


def test_remaining_persistence_exports_exclude_symbol_identity() -> None:
    """Expose only temporary operational state operations."""
    assert persistence.__all__ == [
        "create_health_record",
    ]
    assert delete.__all__ == []
    assert read.__all__ == []
    assert update.__all__ == []


def test_remaining_create_read_update_operations_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep the non-symbol persistence operations behind Data transactions."""
    create_capture = _capture_executor(monkeypatch, create)
    assert create.create_health_record(("health",), request_id="req-1") is _FAKE_RESULT
    assert create_capture["request"]["max_rows"] == 1


def test_manifest_preserves_history_and_adds_guarded_retirement() -> None:
    """Keep immutable steps 001/002 and append retirement steps 003/004/005."""
    migrations = get_broker_migrations()
    assert migrations == BROKER_MIGRATIONS
    assert [step.migration_id for step in migrations] == [
        "001_broker_symbol_map_v1",
        "002_broker_channel_state_v1",
        "003_retire_broker_symbol_map",
        "004_retire_broker_environment_permissions",
        "005_retire_broker_event_and_route_recovery",
    ]
    assert BROKER_SCHEMA_VERSION == "v5"
    retirement_symbol = migrations[2]
    assert any("CHECK (row_count = 0)" in sql for sql in retirement_symbol.statements)
    assert "DROP TABLE broker_symbol_map" in retirement_symbol.statements
    retirement_permissions = migrations[3]
    assert any(
        "CHECK (row_count = 0)" in sql for sql in retirement_permissions.statements
    )
    assert (
        "DROP TABLE broker_environment_permissions" in retirement_permissions.statements
    )
    retirement_event_route = migrations[4]
    assert any(
        "CHECK (row_count = 0)" in sql for sql in retirement_event_route.statements
    )
    assert "DROP TABLE broker_event_checkpoints" in retirement_event_route.statements
    assert "DROP TABLE broker_route_recovery" in retirement_event_route.statements


def test_run_broker_migrations_delegates_complete_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delegate the complete immutable manifest through Data's runner."""
    captured: dict[str, object] = {}

    def build_request(**values: object) -> object:
        captured.update(values)
        return values

    def run(request: object) -> object:
        captured["request"] = request
        return _FAKE_RESULT

    monkeypatch.setattr(migration_definitions, "build_migration_request", build_request)
    monkeypatch.setattr(migration_definitions, "run_domain_migrations", run)

    assert run_broker_migrations("req-migration") is _FAKE_RESULT
    assert captured["domain"] == "brokers"
    assert captured["steps"] == BROKER_MIGRATIONS
    assert captured["complete_manifest"] is True
