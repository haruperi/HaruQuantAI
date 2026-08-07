"""Tests for Optimization-owned additive migration definitions."""

from app.services.optimization import run_optimization_migrations
from app.services.optimization.state import get_optimization_migrations


def test_migrations_are_owned_additive_and_ordered() -> None:
    """Migration definitions own only additive Optimization tables."""
    migrations = get_optimization_migrations()
    assert tuple(step.migration_id for step in migrations) == (
        "001_optimization_schema_v1",
    )
    statements = " ".join(migrations[0].statements).lower()
    assert "create table if not exists optimization_results" in statements
    assert "create table if not exists optimization_checkpoints" in statements
    assert "drop " not in statements
    assert "alter " not in statements


def test_migration_runner_submits_complete_manifest(mocker) -> None:
    """Execute the complete manifest only through Data's public runner."""
    run = mocker.patch(
        "app.services.optimization.migrations.definitions.run_domain_migrations",
        return_value="migration-response",
    )
    assert (
        run_optimization_migrations("req-11111111-1111-4111-8111-111111111111")
        == "migration-response"
    )
    request = run.call_args.args[0]
    assert request.domain == "optimization"
    assert request.complete_manifest is True
    assert request.steps == get_optimization_migrations()
