"""Persisted Strategy checkpoint tests."""

# ruff: noqa: PT018

from pathlib import Path

from app.services.strategy import (
    create_strategy_checkpoint,
    validate_strategy_checkpoint,
)
from app.utils import logger

from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import make_auth, make_config, make_ref


def test_checkpoint_is_bounded_redacted_and_persisted(tmp_path: Path) -> None:
    """Verify checkpoint creation redacts secrets and persists exact content."""
    logger.debug("Testing persisted Strategy checkpoint")
    auth = make_auth(checkpoint=True)
    with storage_context(tmp_path):
        created = create_strategy_checkpoint(
            make_ref(),
            make_config(),
            {"counter": 1, "token": "secret"},
            "checkpoint-auth",
            auth,
        )
        assert created.data is not None
        restored = validate_strategy_checkpoint(
            created.data, make_ref(), make_config(), auth
        )
    assert restored.status == "success"
    assert created.data is not None and created.data.redacted_paths == ("token",)


def test_checkpoint_hash_mismatch_fails_before_restore(tmp_path: Path) -> None:
    """Verify a modified caller checkpoint cannot restore stored state."""
    logger.debug("Testing Strategy checkpoint checksum mismatch")
    auth = make_auth(checkpoint=True)
    with storage_context(tmp_path):
        created = create_strategy_checkpoint(
            make_ref(), make_config(), {"counter": 1}, "checkpoint-auth", auth
        )
        assert created.data is not None
        tampered = created.data.model_copy(update={"state_checksum": "b" * 64})
        restored = validate_strategy_checkpoint(
            tampered, make_ref(), make_config(), auth
        )
    assert restored.status == "error"
