"""Integration test for Strategy initialized registry reads."""

from pathlib import Path

import pytest
from app.services.strategy import (
    list_strategy_versions,
    register_strategy_version,
    validate_strategy_ref,
)
from app.services.strategy.contracts import StrategyRef

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import COR, REQ, make_auth, make_policy


def test_initialized_registry_reads_do_not_run_migrations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify initialized SQLite reads perform no hidden migration.

    Args:
        tmp_path: Temporary directory fixture for isolated SQLite storage.
        monkeypatch: Pytest monkeypatch fixture to intercept migrations.

    Returns:
        None.
    """
    with storage_context(tmp_path):
        registered = register_strategy_version(
            make_registration(),
            make_auth(),
            make_policy(),
        )
        assert registered.data is not None

        def fail_migration(_request: object) -> None:
            """Reject any hidden migration execution.

            Args:
                _request: Database transaction request payload.

            Returns:
                Never returns; always raises AssertionError.

            Raises:
                AssertionError: Always raised if migration is triggered.
            """
            raise AssertionError("read operation triggered a migration")

        monkeypatch.setattr(
            "app.services.strategy.migrations.definitions.run_domain_migrations",
            fail_migration,
        )
        listed = list_strategy_versions()
        resolved = validate_strategy_ref(
            StrategyRef(
                strategy_id="mean-reversion",
                exact_version="1.0.0",
                environment="RESEARCH",
                request_id=REQ,
                correlation_id=COR,
            ),
            make_policy(),
        )
    assert listed.status == "success"
    assert resolved.status == "success"
