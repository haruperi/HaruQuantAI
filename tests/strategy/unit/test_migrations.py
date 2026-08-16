"""Strategy migration-definition tests."""

import pytest
from app.services.strategy import (
    list_strategy_versions,
    validate_strategy_ref,
)
from app.services.strategy.contracts import StrategyRef
from app.services.strategy.contracts.responses import unwrap_strategy_response
from app.services.strategy.migrations.definitions import _strategy_migration_steps
from app.utils import get_logger

from tests.strategy.unit.test_models import (
    make_manifest,
    make_policy,
)

logger = get_logger(__name__)


def test_strategy_migrations_are_ordered_and_owned() -> None:
    """Verify Strategy owns a stable ordered migration set."""
    logger.debug("Testing Strategy migration definitions")
    steps = _strategy_migration_steps()
    assert tuple(step.migration_id for step in steps) == (
        "0001_strategy_domain",
        "0002_strategy_seven_table_runtime",
        "0003_strategy_operational_planning",
        "0004_route_vocabulary",
    )
    assert all(step.domain == "strategy" for step in steps)


def test_registry_reads_do_not_run_migrations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify initialized registry reads never trigger schema migration."""
    logger.debug("Testing migration-free Strategy registry reads")
    manifest = make_manifest()
    policy = make_policy()
    row = {
        "manifest_json": manifest.model_dump_json(),
        "lifecycle_status": "APPROVED",
        "policy_json": policy.model_dump_json(),
        "record_hash": "b" * 64,
        "request_id": "req-11111111-1111-4111-8111-111111111111",
        "correlation_id": "cor-33333333-3333-4333-8333-333333333333",
    }

    monkeypatch.setattr(
        "app.services.strategy.registry.listing.read_strategy_versions",
        lambda *_args, **_kwargs: (row,),
    )
    monkeypatch.setattr(
        "app.services.strategy.registry.resolution.read_strategy_versions",
        lambda *_args, **_kwargs: (row,),
    )

    def fail_migration(_request: object) -> None:
        """Reject any hidden migration execution.

        Args:
            _request: Database transaction request payload.

        Returns:
            None.

        Raises:
            AssertionError: Always raised if called.
        """
        raise AssertionError("registry read triggered unexpected migration")

    monkeypatch.setattr(
        "app.services.strategy.migrations.definitions._ensure_strategy_storage",
        fail_migration,
    )

    versions = unwrap_strategy_response(
        list_strategy_versions(), operation="list_versions"
    )
    assert len(versions) == 1

    ref_res = unwrap_strategy_response(
        validate_strategy_ref(
            StrategyRef(
                strategy_id="mean-reversion",
                exact_version="1.0.0",
                environment="RESEARCH",
                request_id="req-11111111-1111-4111-8111-111111111111",
                correlation_id="cor-33333333-3333-4333-8333-333333333333",
            ),
            policy,
        ),
        operation="validate_strategy_ref",
    )
    assert ref_res.manifest.strategy_id == "mean-reversion"
