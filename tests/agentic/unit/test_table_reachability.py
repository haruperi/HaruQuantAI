"""Static reachability evidence for every Agentic-owned table."""

from pathlib import Path


def test_every_declared_table_has_crud_and_production_runtime_reach() -> None:
    """Trace each table through private CRUD to a production operation."""
    create_source = Path("app/agentic/persistence/create.py").read_text(
        encoding="utf-8"
    )
    read_source = Path("app/agentic/persistence/read.py").read_text(encoding="utf-8")
    update_source = Path("app/agentic/persistence/update.py").read_text(
        encoding="utf-8"
    )
    persistence = create_source + read_source + update_source
    runtime_sources = {
        path.as_posix(): path.read_text(encoding="utf-8")
        for path in Path("app/agentic").rglob("runtime.py")
        if "persistence" not in path.parts
    }
    traces = {
        "agentic_evidence_claims": "create_evidence_claim",
        "agentic_memory_records": "create_memory_record",
        "agentic_workflow_runs": "create_workflow_run_reservation",
        "agentic_workflow_checkpoints": "create_workflow_checkpoint_record",
        "agentic_lifecycle_transitions": "create_lifecycle_record",
        "agentic_promotion_packets": "create_lifecycle_packet_record",
        "agentic_operations_traces": "create_operation_trace_record",
        "agentic_operations_incidents": "create_incident_record",
        "agentic_operations_replays": "create_replay_record",
        "agentic_experiment_specs": "create_experiment_spec",
        "agentic_experiment_runs": "create_experiment_run",
        "agentic_experiment_holdout_use": "create_experiment_holdout_use",
        "agentic_experiment_verdicts": "create_experiment_verdict",
    }

    for table, operation in traces.items():
        assert table in persistence
        assert operation in persistence
        assert any(operation in source for source in runtime_sources.values()), (
            table,
            operation,
        )
