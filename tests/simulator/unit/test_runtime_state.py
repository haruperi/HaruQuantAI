"""Simulator completed-result public boundary tests."""

from types import SimpleNamespace

import pytest
from app.services import simulator
from app.services.simulator.persistence import create, update


def test_get_simulation_result_reads_exact_run_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The package-root read delegates one run ID without synthesis."""
    calls: list[tuple[object, str, str]] = []
    store = object()
    expected = object()
    monkeypatch.setattr(simulator, "build_simulation_state_store", lambda **_: store)

    def execute(value: object, operation: str, run_id: str) -> object:
        calls.append((value, operation, run_id))
        return expected

    monkeypatch.setattr(simulator, "execute_simulation_state_store_operation", execute)
    assert (
        simulator.get_simulation_result("run-1", artifact_root="artifacts") is expected
    )
    assert calls == [(store, "load_result", "run-1")]


def test_completed_run_and_result_use_one_atomic_transition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lifecycle completion and its immutable result use one relational CAS."""
    captured: list[tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]] = []

    def execute(
        statements: tuple[str, ...],
        parameters: tuple[tuple[object, ...], ...],
        **_: object,
    ) -> object:
        captured.append((statements, parameters))
        return SimpleNamespace(affected_rows=1)

    monkeypatch.setattr(update, "_execute", execute)
    update.complete_run_record(
        create.create_simulator_persistence_store(lambda payload: payload),
        key="request-1",
        value={
            "request_id": "request-1",
            "request_hash": "a" * 64,
            "run_id": "run-1",
            "status": "completed",
            "result_payload": {"schema_id": "simulation.result.v1"},
        },
        expected_status="started",
        expected_result_payload=None,
    )
    assert len(captured) == 1
    assert len(captured[0][0]) == 1
    assert "UPDATE sim_runs" in captured[0][0][0]
    assert "request_hash=?" in captured[0][0][0]
