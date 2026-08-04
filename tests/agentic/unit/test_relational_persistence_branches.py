"""Concurrency and uniqueness branches for Agentic relational persistence."""

from pathlib import Path

import pytest
from app.agentic.operations import build_incident_record
from app.agentic.operations.runtime import DurableOperationsStore
from app.agentic.orchestration import build_workflow_definition, submit_task
from app.agentic.orchestration.runtime import DurableWorkflowStore
from app.services.data import data_settings_context

from tests.agentic.fixtures import NOW
from tests.agentic.integration.test_durable_runtime import (
    _run_agentic_migrations,
    _settings,
)
from tests.agentic.unit.test_operations import (
    _definition_fields,
    _incident_fields,
    _task,
)


def test_workflow_compare_and_swap_rejects_a_stale_revision(
    tmp_path: Path,
) -> None:
    """Only the caller-observed workflow revision may advance."""
    with data_settings_context(_settings(tmp_path)):
        _run_agentic_migrations()
        store = DurableWorkflowStore()
        run = submit_task(
            store,
            build_workflow_definition(_definition_fields()),
            _task(),
            at_time=NOW,
        )
        committed = store.save_run(run, run.revision)

        with pytest.raises(ValueError, match="revision conflict"):
            store.save_run(run, run.revision)

        conflicting_identity = run.model_copy(
            update={"idempotency_key": "idem-conflicting-run-identity"}
        )
        with pytest.raises(ValueError, match="identity conflicts"):
            store.reserve_run(conflicting_identity)

        assert DurableWorkflowStore().load_run(run.run_id) == committed


def test_incident_unique_constraint_survives_store_reconstruction(
    tmp_path: Path,
) -> None:
    """One run/correlation/kind classification can be recorded only once."""
    with data_settings_context(_settings(tmp_path)):
        _run_agentic_migrations()
        incident = build_incident_record(_incident_fields())
        DurableOperationsStore().record_incident(incident)

        with pytest.raises(ValueError, match="already recorded"):
            DurableOperationsStore().record_incident(incident)
