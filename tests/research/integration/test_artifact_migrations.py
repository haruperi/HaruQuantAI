"""Data-backed integration evidence for Research migration governance."""

from pathlib import Path

from app.kernel.identity import generate_id
from app.services.data import (
    build_data_settings,
    build_migration_request,
    build_migration_step,
    data_settings_context,
    run_data_migrations,
    run_domain_migrations,
)
from app.services.research import build_research_migration_request


def _settings(tmp_path: Path, database: str) -> object:
    """Build isolated non-production Data settings."""
    return build_data_settings(
        database_url=f"sqlite:///{database}",
        data_dir=tmp_path,
        sqlite_busy_timeout_seconds=1.0,
        write_lock_lease_seconds=10.0,
        approved_storage_roots=(tmp_path,),
    )


def test_research_migration_runs_idempotently_through_data(tmp_path: Path) -> None:
    """FR-RES-105: Data applies and then skips the checksummed manifest."""
    with data_settings_context(_settings(tmp_path, "research-migrations.db")):
        run_data_migrations(generate_id("req"))
        first = run_domain_migrations(
            build_research_migration_request(generate_id("req"))
        )
        second = run_domain_migrations(
            build_research_migration_request(generate_id("req"))
        )
    assert first.status == "success"
    assert first.data is not None
    assert first.data.applied_ids == (
        "001_research_artifacts_v1",
        "002_research_expectancy_profiles_v1",
        "003_research_governed_evidence_v1",
        "004_research_runs_v1",
    )
    assert second.status == "success"
    assert second.data is not None
    assert second.data.skipped_ids == (
        "001_research_artifacts_v1",
        "002_research_expectancy_profiles_v1",
        "003_research_governed_evidence_v1",
        "004_research_runs_v1",
    )


def test_research_migration_checksum_mismatch_fails_closed(tmp_path: Path) -> None:
    """FR-RES-106: an applied migration cannot change checksum."""
    with data_settings_context(_settings(tmp_path, "research-checksum.db")):
        run_data_migrations(generate_id("req"))
        request = build_research_migration_request(generate_id("req"))
        applied = run_domain_migrations(request)
        changed = build_migration_request(
            domain="research",
            steps=(
                build_migration_step(
                    domain="research",
                    migration_id="001_research_artifacts_v1",
                    checksum="0" * 64,
                    statements=request.steps[0].statements,
                ),
            ),
            request_id=generate_id("req"),
        )
        rejected = run_domain_migrations(changed)
    assert applied.status == "success"
    assert rejected.status == "error"
