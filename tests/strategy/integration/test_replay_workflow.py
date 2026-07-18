"""WF-STR-005 deterministic replay/checkpoint integration."""

from pathlib import Path

from app.services.strategy import (
    create_strategy_checkpoint,
    create_strategy_replay_manifest,
    validate_strategy_checkpoint,
)
from app.utils import logger

from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import (
    HASH,
    make_auth,
    make_config,
    make_context,
    make_ref,
)


def test_replay_workflow(tmp_path: Path) -> None:
    """Create replay identity and round-trip persisted local state."""
    logger.debug("Testing WF-STR-005 replay workflow")
    replay = create_strategy_replay_manifest(
        make_ref(), make_config(), make_context(), HASH, HASH
    )
    auth = make_auth(checkpoint=True)
    with storage_context(tmp_path):
        checkpoint = create_strategy_checkpoint(
            make_ref(), make_config(), {"counter": 1}, "checkpoint-auth", auth
        )
        assert checkpoint.data is not None
        restored = validate_strategy_checkpoint(
            checkpoint.data, make_ref(), make_config(), auth
        )
    assert replay.status == restored.status == "success"
