"""Integration evidence for durable Agentic public-API composition."""

import sqlite3
from contextlib import closing
from pathlib import Path

from app.agentic import (
    build_durable_agentic_dependencies,
    build_evidence_claim,
    get_firm_run,
    retrieve_evidence_claims,
    run_agentic_migrations,
    store_evidence_claim,
    store_memory,
    submit_firm_request,
)
from app.agentic.context_memory.runtime import DurableMemoryStore
from app.agentic.lifecycle.models import build_lifecycle_record
from app.agentic.lifecycle.runtime import DurableLifecycleStore
from app.agentic.operations import build_incident_record, build_replay_request
from app.agentic.operations.models import build_replay_outcome
from app.agentic.operations.runtime import DurableOperationsStore
from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    data_settings_context,
)

from tests.agentic.fixtures import NOW
from tests.agentic.integration.test_public_api_boundary import (
    WORKFLOW_NAME,
    _dependencies,
    _Operator,
)
from tests.agentic.unit.test_lifecycle import _packet, _record_fields
from tests.agentic.unit.test_operations import (
    _incident_fields,
    _replay_fields,
    _trace,
)


def _settings(tmp_path: Path) -> object:
    """Build isolated Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///agentic-runtime.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def _durable_dependencies() -> object:
    """Replace reference stores with the canonical durable bundle.

    Returns:
        Opaque Agentic dependency bundle.
    """
    reference = _dependencies()
    return build_durable_agentic_dependencies(
        reference.settings,
        reference.mandate,
        reference.registry,
        reference.definitions,
        reference.agent_policies,
        reference.tool_policies,
    )


def _run_agentic_migrations() -> None:
    """Apply the complete authoritative Agentic migration manifest."""
    response = run_agentic_migrations(generate_id("req"))
    assert response.status == "success"


def test_agentic_run_survives_dependency_reconstruction(tmp_path: Path) -> None:
    """A submitted run remains inspectable after all handles are rebuilt."""
    with data_settings_context(_settings(tmp_path)):
        _run_agentic_migrations()
        auth = _Operator()
        submitted = submit_firm_request(
            _durable_dependencies(),
            auth,
            WORKFLOW_NAME,
            "Assess EURUSD H1 trend evidence.",
            ("evidence-market-1",),
            "idem-durable-runtime",
            at_time=NOW,
        )
        inspected = get_firm_run(
            _durable_dependencies(), auth, str(submitted.payload["run_id"])
        )

    assert submitted.status == "ok"
    assert inspected.status == "ok"
    assert inspected.payload["run_id"] == submitted.payload["run_id"]


def test_evidence_claim_survives_store_reconstruction(tmp_path: Path) -> None:
    """A governed claim round-trips through its Agentic-owned table."""
    claim = build_evidence_claim(
        {
            "claim_id": "claim-durable-1",
            "task_id": "task-durable-1",
            "statement": "The governed source reports a bounded observation.",
            "source_ref": "research:source:1",
            "source_trust": "authoritative",
            "licence_ref": "licence:internal",
            "available_at": NOW,
            "observed_at": NOW,
            "content_hash": "a" * 64,
            "confidence_basis": "The receiver supplied a governed projection.",
            "falsifier": "The source withdraws or revises the observation.",
            "injection_status": "clean",
        }
    )
    with data_settings_context(_settings(tmp_path)):
        _run_agentic_migrations()
        store_evidence_claim(DurableMemoryStore(), claim)
        restored = retrieve_evidence_claims(DurableMemoryStore(), claim.task_id)

    assert restored == (claim,)


def test_agentic_relational_stores_round_trip_losslessly(tmp_path: Path) -> None:
    """Active Agentic stores reconstruct every persisted contract field."""
    with data_settings_context(_settings(tmp_path)):
        _run_agentic_migrations()

        memory = DurableMemoryStore()
        memory_record = store_memory(
            memory,
            "audit",
            "task-relational",
            "technical_analyst",
            {"span_kind": "model", "detail": "bounded trace evidence"},
            {"environment": "sandbox"},
            "audit-730d",
            source_evidence_refs=("data.market:eurusd-h1",),
            at_time=NOW,
        )
        assert DurableMemoryStore().list_records("audit", "task-relational") == (
            memory_record,
        )

        lifecycle = DurableLifecycleStore()
        lifecycle_record = build_lifecycle_record(
            _record_fields(unresolved_concerns=("cost sensitivity",))
        )
        packet = _packet()
        lifecycle.append_record(lifecycle_record)
        lifecycle.save_packet(packet)
        rebuilt_lifecycle = DurableLifecycleStore()
        assert rebuilt_lifecycle.list_records(lifecycle_record.artifact_hash) == (
            lifecycle_record,
        )
        assert rebuilt_lifecycle.load_packet(packet.packet_hash) == packet

        operations = DurableOperationsStore()
        trace = _trace()
        incident = build_incident_record(_incident_fields())
        request = build_replay_request(_replay_fields())
        outcome = build_replay_outcome(
            {
                "replay_id": request.replay_id,
                "run_id": request.run_id,
                "environment": "sandbox",
                "verified_references": tuple(request.reference_hashes),
                "side_effects_attempted": 0,
                "executed": False,
                "completed_at": NOW.isoformat(),
            }
        )
        operations.save_trace(trace)
        operations.record_incident(incident)
        operations.record_replay(request, outcome)
        rebuilt_operations = DurableOperationsStore()
        assert rebuilt_operations.load_trace(trace.trace_hash) == trace
        assert rebuilt_operations.list_incidents(incident.run_id) == (incident,)

    database_path = tmp_path / "agentic-runtime.db"
    with closing(sqlite3.connect(database_path)) as connection:
        replay_row = connection.execute(
            "SELECT verified_references_json, completed_at "
            "FROM agentic_operations_replays WHERE replay_id=?",
            (request.replay_id,),
        ).fetchone()
        generic_count = connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' "
            "AND name='data_runtime_records'"
        ).fetchone()
    assert replay_row == ('["record-a"]', NOW.isoformat())
    assert generic_count == (0,)
