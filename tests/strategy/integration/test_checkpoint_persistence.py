"""Integration evidence for persisted Strategy checkpoints."""

from pathlib import Path

from app.services.strategy import (
    create_strategy_checkpoint,
    validate_strategy_checkpoint,
)

from tests.strategy.unit.test_catalog import storage_context
from tests.strategy.unit.test_models import make_auth, make_config, make_ref


def test_checkpoint_round_trips_through_strategy_storage(
    tmp_path: Path,
) -> None:
    """Verify a bounded redacted checkpoint persists and restores.

    Args:
        tmp_path: Temporary directory fixture for isolated SQLite storage.

    Returns:
        None.
    """
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
    assert restored.data == {"counter": 1, "token": "[REDACTED]"}
