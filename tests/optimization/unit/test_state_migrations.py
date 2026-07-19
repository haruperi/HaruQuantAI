"""Tests for Optimization-owned additive migration definitions."""

# ruff: noqa: INP001

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
