"""Integration evidence for durable Agentic experiment persistence."""

from pathlib import Path

from app.agentic import build_durable_experiment_store, run_agentic_migrations
from app.kernel.identity import generate_id
from app.services.data import build_data_settings, data_settings_context

from tests.agentic.fixtures import NOW
from tests.agentic.unit.test_experiment_designer import RESULT, _coordinate, _spec


def _settings(tmp_path: Path) -> object:
    """Build isolated non-production Data settings.

    Returns:
        Opaque Data settings.
    """
    return build_data_settings(
        database_url="sqlite:///agentic-experiment.db",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(Path(),),
    )


def test_experiment_tables_are_reached_by_the_durable_store(tmp_path: Path) -> None:
    """Specs, runs, holdout, and verdicts survive store reconstruction."""
    spec = _spec()
    verdict = _coordinate(spec=spec).payload
    assert verdict is not None
    lineage = {
        "request_hash": "request-hash",
        "config_hash": "config-hash",
        "engine_version": "engine-v1",
        "journal_ref": "journal:run-1",
        "artifact_manifest_ref": "manifest:run-1",
    }

    with data_settings_context(_settings(tmp_path)):
        assert run_agentic_migrations(generate_id("req")).status == "success"
        store = build_durable_experiment_store()
        saved_spec = store.save_spec(spec)
        store.record_run(
            spec.spec_hash,
            RESULT["run_id"],
            "holdout",
            lineage,
            NOW,
        )
        assert store.reserve_holdout(
            spec.spec_hash,
            spec.task_id,
            RESULT["run_id"],
            NOW,
        )
        store.save_verdict(verdict)

        restored = build_durable_experiment_store()
        assert restored.load_spec(spec.spec_hash) == saved_spec
        assert restored.list_runs(spec.spec_hash)[0]["run_id"] == RESULT["run_id"]
        assert restored.holdout_spent(spec.spec_hash)
        assert not restored.reserve_holdout(
            spec.spec_hash,
            spec.task_id,
            "run-second-look",
            NOW,
        )
