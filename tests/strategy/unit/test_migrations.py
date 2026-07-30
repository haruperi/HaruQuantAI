"""Strategy migration-definition tests."""

from pathlib import Path

import pytest
from app.services.strategy import (
    list_strategy_versions,
    register_strategy_version,
    validate_strategy_ref,
)
from app.services.strategy.contracts import StrategyRef
from app.services.strategy.migrations.definitions import _strategy_migration_steps
from app.utils import get_logger

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import make_auth, make_policy

logger = get_logger(__name__)


def test_strategy_migrations_are_ordered_and_owned() -> None:
    """Verify Strategy owns a stable ordered migration set."""
    logger.debug("Testing Strategy migration definitions")
    steps = _strategy_migration_steps()
    assert tuple(step.migration_id for step in steps) == ("0001_strategy_domain",)
    assert all(step.domain == "strategy" for step in steps)


def test_registry_reads_do_not_run_migrations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify initialized registry reads never trigger schema migration."""
    logger.debug("Testing migration-free Strategy registry reads")
    with storage_context(tmp_path):
        registered = register_strategy_version(
            make_registration(),
            make_auth(),
            make_policy(),
        )
        assert registered.data is not None

        def fail_migration(_request: object) -> None:
            """Reject any hidden migration execution."""
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
                request_id="req-11111111-1111-4111-8111-111111111111",
                correlation_id="cor-33333333-3333-4333-8333-333333333333",
            ),
            make_policy(),
        )
    assert listed.status == "success"
    assert resolved.status == "success"
