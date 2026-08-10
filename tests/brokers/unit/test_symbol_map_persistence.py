"""Unit evidence for the Brokers symbol-map persistence support package."""

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
    """Capture the transaction request built by one persistence module.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        module: Persistence module whose Data boundary functions are replaced.

    Returns:
        Mutable capture dict populated with the built request and result.
    """
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


def test_create_symbol_map_record_executes_one_bounded_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build exactly one INSERT with the caller parameters and request ID."""
    captured = _capture_executor(monkeypatch, create)
    parameters = ("map-1", "mt5", "EURUSD", "EURUSD.r")

    result = create.create_symbol_map_record(parameters, request_id="req-1")

    request = captured["request"]
    assert len(request["statements"]) == 1
    assert "INSERT INTO broker_symbol_map" in request["statements"][0]
    assert request["parameter_sets"] == (parameters,)
    assert request["max_rows"] == 1
    assert request["request_id"] == "req-1"
    assert captured["executed"] is request
    assert result is _FAKE_RESULT


def test_read_provider_symbol_selects_the_forward_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read the active provider symbol for one canonical instrument."""
    captured = _capture_executor(monkeypatch, read)

    result = read.read_provider_symbol("mt5", "EURUSD", request_id="req-2")

    request = captured["request"]
    statement = request["statements"][0]
    assert "FROM broker_symbol_map" in statement
    assert "provider_code = ? AND symbol_id = ?" in statement
    assert "enabled = 1 AND effective_to IS NULL" in statement
    assert request["parameter_sets"] == (("mt5", "EURUSD"),)
    assert request["max_rows"] == 1
    assert result is _FAKE_RESULT


def test_read_canonical_symbol_selects_the_reverse_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read the canonical instrument for one provider symbol."""
    captured = _capture_executor(monkeypatch, read)

    read.read_canonical_symbol("mt5", "EURUSD.r", request_id="req-3")

    request = captured["request"]
    assert "provider_code = ? AND provider_symbol = ?" in request["statements"][0]
    assert request["parameter_sets"] == (("mt5", "EURUSD.r"),)
    assert request["max_rows"] == 1


def test_read_provider_symbol_as_of_selects_the_point_in_time_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read the mapping that applied at one historical instant."""
    captured = _capture_executor(monkeypatch, read)

    read.read_provider_symbol_as_of("mt5", "EURUSD", "2020-06-01", request_id="req-4")

    request = captured["request"]
    statement = request["statements"][0]
    assert "effective_from <= ?" in statement
    assert "(effective_to IS NULL OR effective_to > ?)" in statement
    assert "ORDER BY effective_from DESC" in statement
    assert request["parameter_sets"] == (("mt5", "EURUSD", "2020-06-01", "2020-06-01"),)
    assert request["max_rows"] == 1


def test_close_symbol_mapping_closes_the_open_validity_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Close the open mapping instead of rewriting it."""
    captured = _capture_executor(monkeypatch, update)

    update.close_symbol_mapping(
        "2024-01-01", "2026-08-04", "mt5", "EURUSD", request_id="req-5"
    )

    request = captured["request"]
    statement = request["statements"][0]
    assert "UPDATE broker_symbol_map" in statement
    assert "SET effective_to = ?, updated_at = ?" in statement
    assert "effective_to IS NULL" in statement
    assert request["parameter_sets"] == (("2024-01-01", "2026-08-04", "mt5", "EURUSD"),)
    assert request["max_rows"] == 1


def test_disable_symbol_mapping_disables_without_closing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disable one mapping without altering its validity window."""
    captured = _capture_executor(monkeypatch, update)

    update.disable_symbol_mapping("2026-08-04", "map-1", request_id="req-6")

    request = captured["request"]
    assert "SET enabled = 0, updated_at = ?" in request["statements"][0]
    assert request["parameter_sets"] == (("2026-08-04", "map-1"),)
    assert request["max_rows"] == 1


def test_delete_verb_remains_an_empty_module() -> None:
    """Keep the delete verb empty: mappings are closed, never removed."""
    assert delete.__all__ == []


def test_persistence_package_exports_exactly_the_crud_boundary() -> None:
    """Expose exactly the approved domain-record CRUD operations."""
    assert persistence.__all__ == [
        "close_symbol_mapping",
        "create_environment_permission_record",
        "create_health_record",
        "create_symbol_map_record",
        "disable_symbol_mapping",
        "read_canonical_symbol",
        "read_environment_permission",
        "read_event_checkpoint",
        "read_provider_symbol",
        "read_provider_symbol_as_of",
        "read_route_recovery",
        "upsert_event_checkpoint_record",
        "upsert_route_recovery_record",
    ]
    for name in persistence.__all__:
        assert callable(getattr(persistence, name))


def test_get_broker_migrations_returns_the_immutable_steps() -> None:
    """Return both immutable Brokers migration steps in application order."""
    migrations = get_broker_migrations()
    assert migrations == BROKER_MIGRATIONS
    assert len(migrations) == 2
    assert migrations[1].migration_id == "002_broker_channel_state_v1"
    assert BROKER_SCHEMA_VERSION == "v2"


def test_run_broker_migrations_delegates_complete_manifest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delegate the complete immutable manifest through Data's runner."""
    captured: dict[str, object] = {}

    def build_request(**values: object) -> object:
        captured.update(values)
        captured["built"] = values
        return values

    def run(request: object) -> object:
        captured["request"] = request
        return _FAKE_RESULT

    monkeypatch.setattr(
        migration_definitions,
        "build_migration_request",
        build_request,
    )
    monkeypatch.setattr(migration_definitions, "run_domain_migrations", run)

    result = run_broker_migrations("req-migration")

    assert captured["domain"] == "brokers"
    assert captured["steps"] == BROKER_MIGRATIONS
    assert captured["request_id"] == "req-migration"
    assert captured["complete_manifest"] is True
    assert captured["request"] is captured["built"]
    assert result is _FAKE_RESULT
