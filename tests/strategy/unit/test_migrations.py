"""Strategy migration-definition tests."""

from app.services.strategy.registry.migrations import _strategy_migration_steps
from app.utils import logger


def test_strategy_migrations_are_ordered_and_owned() -> None:
    """Verify Strategy owns a stable ordered migration set."""
    logger.debug("Testing Strategy migration definitions")
    steps = _strategy_migration_steps()
    assert tuple(step.migration_id for step in steps) == ("0001_strategy_domain",)
    assert all(step.domain == "strategy" for step in steps)
