"""WF-STR-008 mutation-result publication integration."""

# ruff: noqa: PT018

from pathlib import Path

from app.services.strategy import register_strategy_version
from app.utils import logger

from tests.strategy.unit.test_catalog import make_registration, storage_context
from tests.strategy.unit.test_models import make_auth, make_policy


def test_registration_workflow(tmp_path: Path) -> None:
    """Commit registry and direct mutation truth in one workflow."""
    logger.debug("Testing WF-STR-008 registration workflow")
    with storage_context(tmp_path):
        outcome = register_strategy_version(
            make_registration(), make_auth(), make_policy()
        )
    assert outcome.data is not None and outcome.data.validated_ref is not None
