"""Branch coverage for Simulator relational persistence and JSONL state."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
from app.services.simulator.persistence import create, read, update
from app.services.simulator.state import runtime
from app.utils import canonical_json


def _store() -> object:
    """Build one private persistence handle."""
    return create.create_simulator_persistence_store(json.loads)


def _run_value(**overrides: object) -> dict[str, object]:
    """Build one valid lifecycle mapping."""
    value: dict[str, object] = {
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "request_hash": "a" * 64,
        "run_id": "run-one",
        "status": "started",
        "result_payload": None,
    }
    value.update(overrides)
    return value


def test_persistence_rejects_invalid_handles_values_and_data_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed private inputs and failed Data responses fail closed."""
    with pytest.raises(TypeError, match="persistence store"):
        create._require_store(object())
    with pytest.raises(TypeError, match="mapping"):
        create._run_value(object())
    with pytest.raises(TypeError, match="request_hash"):
        create.create_run_record(_store(), "request", {"request_id": "request"})
    with pytest.raises(ValueError, match="inconsistent"):
        create.create_run_record(_store(), "different", _run_value())
    with pytest.raises(TypeError, match="result payload"):
        create._result_json({"result_payload": []})
    monkeypatch.setattr(
        create,
        "execute_transaction",
        lambda _: SimpleNamespace(status="error", data=None),
    )
    with pytest.raises(ValueError, match="transaction failed"):
        create._execute(("SELECT 1",), ((),))


def test_read_and_update_malformed_or_conflicting_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed JSON and zero-row compare-and-swap results are rejected."""
    with pytest.raises(TypeError, match="malformed"):
        read._decode_payload("[]")
    monkeypatch.setattr(
        update,
        "_execute",
        lambda *_args, **_kwargs: SimpleNamespace(affected_rows=0),
    )
    assert not update.update_run_record(
        _store(),
        key=cast("str", _run_value()["request_id"]),
        value=_run_value(status="failed"),
        expected_status="started",
        expected_result_payload=None,
    )
    with pytest.raises(ValueError, match="state conflict"):
        update.complete_run_record(
            _store(),
            key=cast("str", _run_value()["request_id"]),
            value=_run_value(
                status="completed",
                result_payload={"schema_id": "simulation.result.v1"},
            ),
            expected_status="started",
            expected_result_payload=None,
        )


def test_result_decoder_routes_both_owner_contracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Single and portfolio schema identifiers select their exact contracts."""
    single = object()
    portfolio = object()
    monkeypatch.setattr(
        runtime.SimulationResult,
        "model_validate",
        lambda _: single,
    )
    monkeypatch.setattr(
        runtime.PortfolioSimulationResult,
        "model_validate",
        lambda _: portfolio,
    )
    assert runtime._decode_result('{"schema_id":"simulation.result.v1"}') is single
    assert (
        runtime._decode_result('{"schema_id":"simulation.portfolio_result.v1"}')
        is portfolio
    )
    with pytest.raises(TypeError, match="object"):
        runtime._decode_result("[]")
    with pytest.raises(ValueError, match="unsupported"):
        runtime._decode_result('{"schema_id":"unknown"}')


def test_jsonl_helpers_reject_unsafe_or_discontinuous_material(tmp_path: Path) -> None:
    """Unsafe identities, noncanonical JSON, and sequence gaps fail closed."""
    with pytest.raises(ValueError, match="invalid"):
        runtime._validate_identity("../escape", "run_id")
    with pytest.raises(TypeError, match="object"):
        runtime._parse_event("[]")
    with pytest.raises(ValueError, match="canonical"):
        runtime._parse_event('{"event_hash": "a", "sequence": 0}')
    path = tmp_path / "journal.jsonl.partial"
    path.write_text(
        canonical_json({"sequence": 1, "event_hash": "a" * 64}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="contiguous"):
        runtime._read_journal(path)


def test_runtime_lifecycle_and_journal_failures_are_normalized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Terminal conflicts and journal mismatches surface controlled errors."""
    store = cast("Any", runtime.build_simulation_state_store(artifact_root=tmp_path))
    monkeypatch.setattr(
        runtime,
        "read_run_record",
        lambda *_: {
            "request_hash": "a" * 64,
            "run_id": "run-one",
            "status": "completed",
            "result_payload": {"schema_id": "simulation.result.v1"},
        },
    )
    response = store.record_idempotency(
        _run_value()["request_id"],
        "a" * 64,
        "run-one",
        "failed",
    )
    assert response.status == "error"
    assert response.error.code == "SIM_PERSISTENCE_FAILED"

    event = canonical_json({"sequence": 0, "event_hash": "b" * 64})
    assert store.append_journal("run-journal", event).status == "success"
    mismatch = store.finalize_journal("run-journal", 1, "c" * 64)
    assert mismatch.status == "error"
    assert mismatch.error.code == "SIM_PERSISTENCE_FAILED"


def test_public_runtime_rejects_invalid_result_identity(tmp_path: Path) -> None:
    """An empty result identity fails before any persistence read."""
    store = cast("Any", runtime.build_simulation_state_store(artifact_root=tmp_path))
    response = store.load_result("")
    assert response.status == "error"
    assert response.error.code == "SIM_INVALID_CONFIG"
