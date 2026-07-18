"""Strategy replay-manifest builder tests."""

# ruff: noqa: PT018

from app.services.strategy import create_strategy_replay_manifest
from app.utils import logger

from tests.strategy.unit.test_models import HASH, make_config, make_context, make_ref


def test_replay_manifest_is_deterministic() -> None:
    """Verify identical lineage produces an identical manifest hash."""
    logger.debug("Testing deterministic Strategy replay manifest")
    first = create_strategy_replay_manifest(
        make_ref(), make_config(), make_context(), HASH, HASH
    )
    second = create_strategy_replay_manifest(
        make_ref(), make_config(), make_context(), HASH, HASH
    )
    assert first.data is not None and second.data is not None
    assert first.data.manifest_hash == second.data.manifest_hash
