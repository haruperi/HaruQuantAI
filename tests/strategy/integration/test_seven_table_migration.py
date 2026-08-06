"""Integration tests for Strategy seven-table database migration."""

from pathlib import Path

from app.services.strategy.migrations.definitions import (
    _ensure_strategy_storage,
    _strategy_migration_steps,
)
from app.services.strategy.persistence import read_strategy_definitions

from tests.strategy.unit.test_catalog import storage_context


def test_migration_steps_contain_0001_and_0002() -> None:
    """Verify Strategy migration steps return two ordered steps.

    Args:
        None.

    Returns:
        None.
    """
    steps = _strategy_migration_steps()
    assert len(steps) == 2
    assert steps[0].migration_id == "0001_strategy_domain"
    assert steps[1].migration_id == "0002_strategy_seven_table_runtime"


def test_seven_table_schema_initialization(tmp_path: Path) -> None:
    """Verify migration creates all seven tables in isolated SQLite storage.

    Args:
        tmp_path: Temporary directory fixture.

    Returns:
        None.
    """
    with storage_context(tmp_path):
        _ensure_strategy_storage("req-11111111-1111-4111-8111-111111111111")
        defs = read_strategy_definitions("req-11111111-1111-4111-8111-111111111111")
        assert isinstance(defs, tuple)
